from typing import Tuple, Dict, List, Optional
from pydantic_ai import Agent
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.providers.google_gla import GoogleGLAProvider
import os
import re
import json
from app.models.document_types import DocumentType
from app.config import settings

async def extract_document_text(image_base64: str) -> str:
    """
    Extract text from document image using Gemini
    
    Args:
        image_base64: Base64 encoded image
        
    Returns:
        Extracted text from the document
    """
    ocr_agent = Agent(
        GeminiModel(
            'gemini-2.0-flash', 
            provider=GoogleGLAProvider(api_key=settings.GEMINI_API_KEY)
        ),
        instrument=True,
        system_prompt="""
        You are a document OCR specialist. Extract ALL text from the provided document image.
        Include all visible text - headers, fields, values, footers, etc.
        Format the text to preserve the document's structure as much as possible.
        """
    )
    
    response = await ocr_agent.run(image_base64)
    
    return str(response.data)

def apply_pattern_rules(text: str) -> Dict[DocumentType, float]:
    """Apply regex pattern matching to identify document types"""
    scores = {doc_type: 0.0 for doc_type in DocumentType}
    
    # PAN Card patterns
    if re.search(r'(?i)permanent\s+account\s+number|income\s+tax\s+department', text):
        scores[DocumentType.PAN_CARD] += 0.4
    if re.search(r'[A-Z]{5}[0-9]{4}[A-Z]', text):  # PAN number format
        scores[DocumentType.PAN_CARD] += 0.6
        
    # Aadhaar Card patterns
    if re.search(r'(?i)आधार|aadhaar|unique\s+identification|uidai', text):
        scores[DocumentType.AADHAAR_CARD] += 0.4
    if re.search(r'(?:\d{4}[\s-]?){3}', text):  # 12-digit format
        scores[DocumentType.AADHAAR_CARD] += 0.4
    if re.search(r'(?i)government\s+of\s+india', text):
        scores[DocumentType.AADHAAR_CARD] += 0.2
        
    # Driving License patterns
    if re.search(r'(?i)driving\s+licen[cs]e', text):
        scores[DocumentType.DRIVING_LICENSE] += 0.5
    if re.search(r'(?i)dl\s+no|licen[cs]e\s+no', text):
        scores[DocumentType.DRIVING_LICENSE] += 0.3
    if re.search(r'(?i)motor\s+vehicle|transport|lmv|mcwg', text):
        scores[DocumentType.DRIVING_LICENSE] += 0.2
        
    # Rental Agreement patterns
    if re.search(r'(?i)rental\s+agreement|lease\s+agreement|tenancy', text):
        scores[DocumentType.RENTAL_AGREEMENT] += 0.4
    if re.search(r'(?i)landlord|tenant|lessor|lessee', text):
        scores[DocumentType.RENTAL_AGREEMENT] += 0.3
    if re.search(r'(?i)rent|security\s+deposit|premises|property', text):
        scores[DocumentType.RENTAL_AGREEMENT] += 0.3
        
    # Proforma Invoice patterns
    if re.search(r'(?i)proforma\s+invoice|quotation|tax\s+invoice', text):
        scores[DocumentType.PROFORMA_INVOICE] += 0.4
    if re.search(r'(?i)ex-showroom|on-road\s+price|registration\s+fee', text):
        scores[DocumentType.PROFORMA_INVOICE] += 0.3
    if re.search(r'(?i)model|variant|vehicle|chassis|engine', text):
        scores[DocumentType.PROFORMA_INVOICE] += 0.3
        
    # Utility Bill patterns
    if re.search(r'(?i)electricity|water|gas|telephone|broadband|bill', text):
        scores[DocumentType.UTILITY_BILL] += 0.4
    if re.search(r'(?i)consumer\s+id|customer\s+no|connection\s+id', text):
        scores[DocumentType.UTILITY_BILL] += 0.3
    if re.search(r'(?i)amount\s+due|due\s+date|payment|consumption|units|meter', text):
        scores[DocumentType.UTILITY_BILL] += 0.3
        
    # Bank Statement patterns
    if re.search(r'(?i)bank|statement|account|branch', text):
        scores[DocumentType.BANK_STATEMENT] += 0.3
    if re.search(r'(?i)transaction|balance|debit|credit|deposit|withdrawal', text):
        scores[DocumentType.BANK_STATEMENT] += 0.4
    if re.search(r'(?i)statement\s+period|opening\s+balance|closing\s+balance', text):
        scores[DocumentType.BANK_STATEMENT] += 0.3
    
    return scores

async def analyze_document_content(image_base64: str, extracted_text: str) -> Dict[DocumentType, float]:
    """
    Have the model analyze specific document content
    
    Args:
        image_base64: Base64 encoded image
        extracted_text: Previously extracted text
        
    Returns:
        Scores for each document type
    """
    analysis_agent = Agent(
        GeminiModel(
            'gemini-2.0-flash', 
            provider=GoogleGLAProvider(api_key=settings.GEMINI_API_KEY),
            temperature=0.1  # Low temperature for consistent outputs
        ),
        instrument=True,
        system_prompt="""
        You are a document analysis expert. Analyze the document features and determine the likelihood 
        of it belonging to each of the given categories.
        
        ONLY respond with a JSON object containing scores (0.0-1.0) for each category, like:
        {
            "pan_card": 0.1,
            "aadhaar_card": 0.9,  
            "driving_license": 0.0,
            "rental_agreement": 0.0,
            "proforma_invoice": 0.0,
            "utility_bill": 0.0,
            "bank_statement": 0.0,
            "unknown": 0.0
        }
        
        Do NOT include any other text in your response, ONLY the JSON.
        """
    )
    
    prompt = f"""
    Analyze this document and determine the likelihood it belongs to each category.
    
    Document categories:
    - pan_card: Indian PAN (Permanent Account Number) card
    - aadhaar_card: Indian Aadhaar card (national ID)
    - driving_license: Indian Driving License
    - rental_agreement: Rental or lease agreement document
    - proforma_invoice: Vehicle proforma invoice
    - utility_bill: Utility bills like electricity, water, gas, etc.
    - bank_statement: Bank account statement with transactions
    - unknown: Cannot determine document type
    
    Extracted text from document:
    {extracted_text}
    
    Assign a confidence score (0.0-1.0) for each category.
    """
    
    try:
        response = await analysis_agent.run(prompt)
        result = response.data
        
        # Parse the JSON response
        if isinstance(result, str):
            result = json.loads(result)
        
        # Convert to DocumentType enum keys
        scores = {
            DocumentType.PAN_CARD: float(result.get('pan_card', 0.0)),
            DocumentType.AADHAAR_CARD: float(result.get('aadhaar_card', 0.0)),
            DocumentType.DRIVING_LICENSE: float(result.get('driving_license', 0.0)),
            DocumentType.RENTAL_AGREEMENT: float(result.get('rental_agreement', 0.0)),
            DocumentType.PROFORMA_INVOICE: float(result.get('proforma_invoice', 0.0)),
            DocumentType.UTILITY_BILL: float(result.get('utility_bill', 0.0)),
            DocumentType.BANK_STATEMENT: float(result.get('bank_statement', 0.0)),
            DocumentType.UNKNOWN: float(result.get('unknown', 0.0))
        }
        return scores
    except Exception as e:
        print(f"Error in analysis: {e}")
        return {doc_type: 0.0 for doc_type in DocumentType}

async def classify_document(image_base64: str) -> Tuple[DocumentType, float]:
    """
    Improved document classification using multiple approaches
    
    Args:
        image_base64: Base64 encoded image
        
    Returns:
        Tuple of (DocumentType, confidence_score)
    """
    # Step 1: Extract text from document
    extracted_text = await extract_document_text(image_base64)
    print("Extracted text:", extracted_text[:200] + "..." if len(extracted_text) > 200 else extracted_text)
    
    # Step 2: Apply pattern matching rules
    pattern_scores = apply_pattern_rules(extracted_text)
    print("Pattern scores:", pattern_scores)
    
    # Step 3: Get AI analysis of document content
    ai_scores = await analyze_document_content(image_base64, extracted_text)
    print("AI scores:", ai_scores)
    
    # Step 4: Combine scores with weighting (pattern matching has higher weight)
    combined_scores = {}
    for doc_type in DocumentType:
        combined_scores[doc_type] = (pattern_scores[doc_type] * 0.7) + (ai_scores[doc_type] * 0.3)
    
    print("Combined scores:", combined_scores)
    
    # Get the document type with highest score
    best_match = max(combined_scores.items(), key=lambda x: x[1])
    doc_type, confidence = best_match
    
    print(f"Best match: {doc_type} with confidence {confidence}")
    
    # Apply minimum confidence threshold
    if confidence < 0.5:
        return DocumentType.UNKNOWN, confidence
    
    return doc_type, confidence 
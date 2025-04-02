# Product Requirements Document (PRD): Document OCR System MVP

## 1. Introduction

This PRD outlines the requirements for an MVP (Minimum Viable Product) of a document OCR (Optical Character Recognition) system. The system will extract structured information from various document types, including identity documents, utility bills, rental agreements, and more.

### 1.1 Purpose

To create an API that can:

- Accept document images or PDFs as input
- Classify document types automatically
- Extract relevant fields based on document type
- Validate extracted information
- Return structured, reliable data

### 1.2 Target Audience

Junior developers who need step-by-step guidance to implement the MVP.

## 2. System Architecture

The system will follow this high-level architecture:

```
[Client] → [FastAPI Server] → [Document Classifier] → [Document-Specific Extractors] → [Validators] → [Response]
```

### 2.1 Technology Stack

- **Language**: Python 3.10+
- **Framework**: FastAPI
- **Environment**: Pipenv
- **OCR Engine**: Google Gemini API (via pydantic-ai)
- **Models**: Pydantic for data validation
- **Additional Libraries**: python-multipart, python-dotenv, PyPDF2 (for PDF handling)

## 3. Development Setup

### 3.1 Environment Setup

```bash
# root directory is already intialized with pipenv with main.py created

# Install required packages
pipenv install fastapi uvicorn pydantic-ai python-multipart python-dotenv PyPDF2
```

### 3.2 Environment Variables (.env file)

```
# .env
GOOGLE_API_KEY=your_google_api_key_here
DEBUG=True
HOST=0.0.0.0
PORT=8000
```

## 4. Project Structure

Create the following directory structure:

```
document-ocr-api/
├── .env
├── Pipfile
├── Pipfile.lock
├── main.py
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── classifier.py
│   │   ├── preprocessing.py
│   │   ├── validators.py
│   ├── extractors/
│   │   ├── __init__.py
│   │   ├── pan_card.py
│   │   ├── aadhaar_card.py
│   │   ├── driving_license.py
│   │   ├── rental_agreement.py
│   │   ├── proforma_invoice.py
│   │   ├── utility_bill.py
│   │   ├── bank_statement.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── document_types.py
│   │   ├── response_models.py
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── image_utils.py
│   │   ├── pdf_utils.py
```

## 5. Implementation Steps

### 5.1 Basic Configuration (app/config.py)

```python
# app/config.py
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
class Settings:
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", "8000"))
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB max file size
    SUPPORTED_MIME_TYPES = [
        "image/jpeg", "image/png", "image/tiff",
        "application/pdf"
    ]

settings = Settings()
```

### 5.2 Document Type Models (app/models/document_types.py)

```python
# app/models/document_types.py
from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal

class DocumentType(str, Enum):
    PAN_CARD = "pan_card"
    AADHAAR_CARD = "aadhaar_card"
    DRIVING_LICENSE = "driving_license"
    RENTAL_AGREEMENT = "rental_agreement"
    PROFORMA_INVOICE = "proforma_invoice"
    UTILITY_BILL = "utility_bill"
    BANK_STATEMENT = "bank_statement"
    UNKNOWN = "unknown"

class DocumentField(BaseModel):
    value: str
    confidence: float = Field(ge=0.0, le=1.0)
    is_readable: bool = True

# Base document model
class DocumentBase(BaseModel):
    document_type: DocumentType

# PAN Card Model
class PANCardData(DocumentBase):
    document_type: Literal[DocumentType.PAN_CARD] = DocumentType.PAN_CARD
    name: DocumentField
    father_name: DocumentField
    date_of_birth: DocumentField
    pan_number: DocumentField
    signature_present: bool

# Aadhaar Card Model
class AadhaarCardData(DocumentBase):
    document_type: Literal[DocumentType.AADHAAR_CARD] = DocumentType.AADHAAR_CARD
    name: DocumentField
    date_of_birth: DocumentField
    gender: DocumentField
    aadhaar_number: DocumentField
    address: DocumentField

# Driving License Model
class DrivingLicenseData(DocumentBase):
    document_type: Literal[DocumentType.DRIVING_LICENSE] = DocumentType.DRIVING_LICENSE
    dl_number: DocumentField
    name: DocumentField
    date_of_birth: DocumentField
    issue_date: DocumentField
    expiry_date: DocumentField
    swd: DocumentField  # Son/Wife/Daughter of
    blood_group: Optional[DocumentField] = None
    address: DocumentField
    pincode: Optional[DocumentField] = None
    authorization_to_drive: List[Dict[str, Any]] = []
    signature_present: bool

# Rental Agreement Model
class RentalAgreementData(DocumentBase):
    document_type: Literal[DocumentType.RENTAL_AGREEMENT] = DocumentType.RENTAL_AGREEMENT
    tenant_name: DocumentField
    tenant_address: DocumentField
    property_owner_name: DocumentField
    property_owner_address: DocumentField
    property_address: DocumentField
    stamp_amount: Optional[DocumentField] = None
    rent_amount: DocumentField
    deposit_amount: DocumentField
    stamp_certificate_number: Optional[DocumentField] = None
    certificate_issue_date: Optional[DocumentField] = None
    lease_period: DocumentField
    lease_start_date: DocumentField
    lease_end_date: DocumentField
    notary_present: bool
    owner_signature_present: bool
    tenant_signature_present: bool

# Proforma Invoice Model
class ProformaInvoiceData(DocumentBase):
    document_type: Literal[DocumentType.PROFORMA_INVOICE] = DocumentType.PROFORMA_INVOICE
    manufacturer: DocumentField
    vehicle_model: DocumentField
    vehicle_variant: DocumentField
    vehicles_required: DocumentField
    ex_showroom_price: DocumentField
    insurance_price: DocumentField
    registration_charges: DocumentField
    body_attachment_cost: Optional[DocumentField] = None
    subsidy_amount: Optional[DocumentField] = None
    total_on_road_price: DocumentField

# Utility Bill Model
class UtilityBillData(DocumentBase):
    document_type: Literal[DocumentType.UTILITY_BILL] = DocumentType.UTILITY_BILL
    customer_name: DocumentField
    customer_phone_number: Optional[DocumentField] = None
    bill_type: DocumentField
    document_date: DocumentField
    bill_provider: DocumentField
    bill_amount: DocumentField
    customer_address: DocumentField
    utility_type: DocumentField

# Bank Statement Model - Simplified for MVP
class Transaction(BaseModel):
    date: str
    transaction_note: Optional[str] = None
    amount: float
    transaction_type: Literal["credit", "debit"]
    transaction_channel: Optional[str] = None
    balance: float
    description: Optional[str] = None
    reference_number: Optional[str] = None

class BankStatementData(DocumentBase):
    document_type: Literal[DocumentType.BANK_STATEMENT] = DocumentType.BANK_STATEMENT
    account_holder_name: DocumentField
    account_holder_address: DocumentField
    ifsc_code: Optional[DocumentField] = None
    account_opening_date: Optional[DocumentField] = None
    bank_name: DocumentField
    account_number: DocumentField
    transactions: List[Transaction] = []
    monthly_average_balance: Optional[float] = None
```

### 5.3 Response Models (app/models/response_models.py)

```python
# app/models/response_models.py
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
from app.models.document_types import DocumentType

class DocumentClassificationResponse(BaseModel):
    document_type: DocumentType
    confidence: float

class ValidationError(BaseModel):
    field: str
    error: str

class ExtractionResponse(BaseModel):
    document_type: DocumentType
    extracted_data: Dict[str, Any]
    confidence_scores: Dict[str, float]
    validation_errors: List[ValidationError] = []
    is_valid: bool = True
    processing_time_ms: float

class ErrorResponse(BaseModel):
    error: str
    details: Optional[Dict[str, Any]] = None
```

### 5.4 Document Classifier (app/core/classifier.py)

```python
# app/core/classifier.py
import base64
from typing import Tuple
from pydantic_ai import Agent
from app.models.document_types import DocumentType
from app.config import settings

async def classify_document(image_base64: str) -> Tuple[DocumentType, float]:
    """
    Classify document type using Gemini

    Args:
        image_base64: Base64 encoded image

    Returns:
        Tuple of (DocumentType, confidence_score)
    """

    classifier_agent = Agent(
        model_name='google-gla:gemini-1.5-flash',
        system_prompt="""
        You are a document classifier specialized in identifying types of financial and identity documents.
        Analyze the provided document image carefully and classify it into ONE of the following types:

        - pan_card: Indian PAN (Permanent Account Number) card
        - aadhaar_card: Indian Aadhaar card (national ID)
        - driving_license: Indian Driving License
        - rental_agreement: Rental or lease agreement document
        - proforma_invoice: Vehicle proforma invoice
        - utility_bill: Utility bills like electricity, water, gas, etc.
        - bank_statement: Bank account statement with transactions

        Return ONLY the exact document type from the list above along with your confidence level (0.0-1.0).
        Format your response as JSON: {"document_type": "type_here", "confidence": 0.95}
        If you cannot confidently determine the type, use "unknown" with the appropriate confidence.
        """
    )

    # Run classification
    response = await classifier_agent.run(image_base64)

    # Parse response to get document type and confidence
    try:
        result = response.data
        doc_type = result.get('document_type', 'unknown')
        confidence = float(result.get('confidence', 0.0))

        # Convert to enum
        return DocumentType(doc_type), confidence
    except Exception as e:
        print(f"Error parsing classification response: {e}")
        return DocumentType.UNKNOWN, 0.0
```

### 5.5 Image Preprocessing (app/core/preprocessing.py)

```python
# app/core/preprocessing.py
import base64
import io
from typing import Union, Optional, Tuple
from PIL import Image
import PyPDF2

def preprocess_image(file_content: bytes) -> str:
    """
    Preprocess image for OCR
    - Resize if too large
    - Enhance contrast
    - Convert to base64

    Args:
        file_content: Raw bytes of the image file

    Returns:
        Base64 encoded processed image
    """
    try:
        # Open image with PIL
        image = Image.open(io.BytesIO(file_content))

        # Convert to RGB if necessary
        if image.mode not in ('RGB', 'L'):
            image = image.convert('RGB')

        # Resize if too large (max dimensions 2000x2000)
        max_dimension = 2000
        if image.width > max_dimension or image.height > max_dimension:
            ratio = min(max_dimension / image.width, max_dimension / image.height)
            new_width = int(image.width * ratio)
            new_height = int(image.height * ratio)
            image = image.resize((new_width, new_height), Image.LANCZOS)

        # Save processed image to bytes buffer
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=95)
        buffer.seek(0)

        # Convert to base64
        image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        return image_base64

    except Exception as e:
        raise ValueError(f"Error preprocessing image: {e}")

def extract_images_from_pdf(pdf_content: bytes) -> list[bytes]:
    """
    Extract images from each page of a PDF

    Args:
        pdf_content: Raw bytes of the PDF file

    Returns:
        List of image bytes for each page
    """
    try:
        reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
        page_count = len(reader.pages)

        # For MVP, we'll use a simple approach: render each page as an image
        # A more sophisticated approach would be to extract embedded images
        # That would require additional libraries like pdf2image with poppler

        # For MVP, return empty list - you'll need to implement this with additional libraries
        return []

    except Exception as e:
        raise ValueError(f"Error extracting images from PDF: {e}")
```

### 5.6 Document Type Extractors

Let's create one extractor as an example. The others will follow a similar pattern.

#### 5.6.1 PAN Card Extractor (app/extractors/pan_card.py)

```python
# app/extractors/pan_card.py
from pydantic_ai import Agent
from app.models.document_types import PANCardData, DocumentField
from typing import Dict

async def extract_pan_card(image_base64: str) -> PANCardData:
    """
    Extract information from a PAN card image

    Args:
        image_base64: Base64 encoded image

    Returns:
        PANCardData object with extracted fields
    """

    pan_agent = Agent(
        model_name='google-gla:gemini-1.5-flash',
        result_type=PANCardData,
        system_prompt="""
        You are an OCR system specialized in extracting information from Indian PAN cards.

        Extract the following fields from the PAN card image:

        1. Name:
           - Location: Found prominently on the card, often near the top left or center
           - It's usually under the heading "Name" or "नाम"
           - Validation: Text containing alphabets only, no numbers

        2. Father's Name:
           - Location: Usually located below the "Name" field
           - Labeled as "Father's Name", "पिता का नाम", or similar
           - Validation: Text containing alphabets only, no numbers

        3. Date of Birth:
           - Location: Found near the bottom left or center
           - Format: DD/MM/YYYY
           - Validation: Valid date format

        4. PAN Number:
           - Location: Middle of the card, labeled "Permanent Account Number"
           - Format: 5 letters, 4 numbers, 1 letter (e.g., ABCDE1234F)
           - Validation: Check format

        5. Signature Present:
           - Check if a signature is visible on the card
           - Return a boolean value (true/false)

        For each field (except signature), provide:
        - The extracted text value
        - A confidence score (0.0-1.0)
        - Whether the text is clearly readable (boolean)

        If a field is not found or unreadable, provide a low confidence score and set is_readable to false.
        """
    )

    # Run extraction
    response = await pan_agent.run(image_base64)

    # The agent will return the data in the expected PANCardData format
    return response.data
```

Create similar extractors for the other document types following the same pattern, with document-specific prompts based on the detailed field information.

### 5.7 Validators (app/core/validators.py)

```python
# app/core/validators.py
import re
from datetime import datetime
from typing import List, Tuple, Dict, Any
from app.models.document_types import (
    PANCardData, AadhaarCardData, DrivingLicenseData,
    RentalAgreementData, ProformaInvoiceData, UtilityBillData,
    BankStatementData
)
from app.models.response_models import ValidationError

# PAN Card validation
def validate_pan_card(data: PANCardData) -> List[ValidationError]:
    errors = []

    # Validate PAN Number format (5 letters + 4 digits + 1 letter)
    pan_pattern = re.compile(r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$')
    if data.pan_number.value and not pan_pattern.match(data.pan_number.value):
        errors.append(ValidationError(
            field="pan_number",
            error="PAN number must be in the format: 5 letters + 4 digits + 1 letter"
        ))

    # Validate date format
    try:
        if data.date_of_birth.value:
            # Assuming DD/MM/YYYY format
            datetime.strptime(data.date_of_birth.value, '%d/%m/%Y')
    except ValueError:
        errors.append(ValidationError(
            field="date_of_birth",
            error="Date of birth must be in DD/MM/YYYY format"
        ))

    # Add more validation rules as needed

    return errors

# Aadhaar Card validation
def validate_aadhaar_card(data: AadhaarCardData) -> List[ValidationError]:
    errors = []

    # Validate Aadhaar number (12 digits)
    if data.aadhaar_number.value:
        aadhaar_digits = re.sub(r'\D', '', data.aadhaar_number.value)
        if len(aadhaar_digits) != 12:
            errors.append(ValidationError(
                field="aadhaar_number",
                error="Aadhaar number must contain exactly 12 digits"
            ))

    # Add more validation rules

    return errors

# Add similar validation functions for each document type
# ...

# Main validation dispatcher
def validate_document(document_data: Any) -> List[ValidationError]:
    """
    Validate extracted document data based on document type

    Args:
        document_data: Extracted document data object

    Returns:
        List of validation errors
    """
    if isinstance(document_data, PANCardData):
        return validate_pan_card(document_data)
    elif isinstance(document_data, AadhaarCardData):
        return validate_aadhaar_card(document_data)
    # Add other document types...
    else:
        return [ValidationError(field="document_type", error="Unsupported document type")]
```

### 5.8 API Routes (app/api/routes.py)

```python
# app/api/routes.py
import time
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from typing import Dict, Any
import base64

from app.core.classifier import classify_document
from app.core.preprocessing import preprocess_image, extract_images_from_pdf
from app.core.validators import validate_document
from app.models.response_models import ExtractionResponse, ErrorResponse
from app.models.document_types import DocumentType

# Import all extractors
from app.extractors.pan_card import extract_pan_card
from app.extractors.aadhaar_card import extract_aadhaar_card
from app.extractors.driving_license import extract_driving_license
from app.extractors.rental_agreement import extract_rental_agreement
from app.extractors.proforma_invoice import extract_proforma_invoice
from app.extractors.utility_bill import extract_utility_bill
from app.extractors.bank_statement import extract_bank_statement

router = APIRouter()

# Extractor registry
extractors = {
    DocumentType.PAN_CARD: extract_pan_card,
    DocumentType.AADHAAR_CARD: extract_aadhaar_card,
    DocumentType.DRIVING_LICENSE: extract_driving_license,
    DocumentType.RENTAL_AGREEMENT: extract_rental_agreement,
    DocumentType.PROFORMA_INVOICE: extract_proforma_invoice,
    DocumentType.UTILITY_BILL: extract_utility_bill,
    DocumentType.BANK_STATEMENT: extract_bank_statement,
}

@router.post("/extract", response_model=ExtractionResponse)
async def extract_document(file: UploadFile = File(...)):
    """
    Extract information from a document image

    Takes a document image file, classifies it, and extracts information based on document type
    """
    start_time = time.time()

    try:
        # Read file content
        content = await file.read()

        # Check file type
        if file.content_type.startswith('image/'):
            # Process image file
            image_base64 = preprocess_image(content)

            # Classify document
            doc_type, confidence = await classify_document(image_base64)

            if doc_type == DocumentType.UNKNOWN or confidence < 0.6:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unable to confidently classify document (confidence: {confidence})"
                )

            # Extract information based on document type
            if doc_type in extractors:
                extractor = extractors[doc_type]
                document_data = await extractor(image_base64)

                # Validate extracted data
                validation_errors = validate_document(document_data)

                # Create response
                processing_time = (time.time() - start_time) * 1000  # ms

                # Extract confidence scores
                confidence_scores = {}
                for field_name, field_value in document_data.__dict__.items():
                    if hasattr(field_value, 'confidence'):
                        confidence_scores[field_name] = field_value.confidence

                # Convert data to dict, handling DocumentField objects
                extracted_data = {}
                for field_name, field_value in document_data.__dict__.items():
                    if hasattr(field_value, 'value'):
                        extracted_data[field_name] = field_value.value
                    elif field_name != 'document_type':
                        extracted_data[field_name] = field_value

                return ExtractionResponse(
                    document_type=doc_type,
                    extracted_data=extracted_data,
                    confidence_scores=confidence_scores,
                    validation_errors=validation_errors,
                    is_valid=len(validation_errors) == 0,
                    processing_time_ms=processing_time
                )
            else:
                raise HTTPException(
                    status_code=501,
                    detail=f"Extractor for document type '{doc_type}' not implemented"
                )

        elif file.content_type == 'application/pdf':
            # For MVP, just return an error that PDF processing is not implemented
            # Later, you can implement PDF processing using extract_images_from_pdf
            raise HTTPException(
                status_code=501,
                detail="PDF processing not implemented in MVP"
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {file.content_type}"
            )

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Handle all other exceptions
        raise HTTPException(
            status_code=500,
            detail=f"Error processing document: {str(e)}"
        )
```

### 5.9 Main Application (main.py)

```python
# main.py
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router as api_router
from app.config import settings

# Create FastAPI application
app = FastAPI(
    title="Document OCR API",
    description="API for extracting information from various document types",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development only, restrict this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"error": str(exc)}
    )

# Include API routes
app.include_router(api_router, prefix="/api")

# Health check endpoint
@app.get("/health")
def health_check():
    return {"status": "healthy"}

# Run application
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
```

## 6. Implementing the Remaining Extractors

Now, let's create one more extractor as an example.

### 6.1 Aadhaar Card Extractor (app/extractors/aadhaar_card.py)

```python
# app/extractors/aadhaar_card.py
from pydantic_ai import Agent
from app.models.document_types import AadhaarCardData, DocumentField

async def extract_aadhaar_card(image_base64: str) -> AadhaarCardData:
    """
    Extract information from an Aadhaar card image

    Args:
        image_base64: Base64 encoded image

    Returns:
        AadhaarCardData object with extracted fields
    """

    aadhaar_agent = Agent(
        model_name='google-gla:gemini-1.5-flash',
        result_type=AadhaarCardData,
        system_prompt="""
        You are an OCR system specialized in extracting information from Indian Aadhaar cards.

        Extract the following fields from the Aadhaar card image:

        1. Name:
           - Location: Look for the name directly under the "Government of India" or "भारत सरकार" header
           - It's often the most prominent text after the header
           - Validation: Should contain alphabetic characters and spaces

        2. Date of Birth:
           - Location: Look for text near the name labeled with "Date of Birth," "DOB," or "जन्म तिथि"
           - Format: DD/MM/YYYY or similar
           - Validation: Must be a valid date

        3. Gender:
           - Location: Near the name and DOB
           - Format: "Male", "Female", or "Other" (may be abbreviated)
           - Validation: Standardize to "Male", "Female", or "Other"

        4. Aadhaar Number:
           - Location: Usually printed prominently, often grouped as 4 digits + 4 digits + 4 digits
           - Format: 12 digits total
           - Validation: Must contain exactly 12 digits

        5. Address:
           - Location: Usually on the back of the card, under "Address" or "पता"
           - Format: Multi-line text
           - Validation: Should include house/street, locality, city, state, and PIN code

        For each field, provide:
        - The extracted text value
        - A confidence score (0.0-1.0)
        - Whether the text is clearly readable (boolean)

        If a field is not found or unreadable, provide a low confidence score and set is_readable to false.
        Always convert text to English if it's in another language.
        """
    )

    # Run extraction
    response = await aadhaar_agent.run(image_base64)

    # The agent will return the data in the expected AadhaarCardData format
    return response.data
```

## 7. Testing the API

### 7.1 Manual Testing

After implementing all the required components, you can test the API manually:

1. Run the application:

   ```bash
   pipenv run python main.py
   ```

2. Open your browser and go to `http://localhost:8000/docs` to access the Swagger UI

3. Use the `/api/extract` endpoint to upload a document image and test the extraction

### 7.2 Automated Testing Script

Create a simple script to test the API:

```python
# test_api.py
import requests
import os
import sys
import json

def test_document_extraction(api_url, image_path):
    """
    Test document extraction API

    Args:
        api_url: URL of the API endpoint
        image_path: Path to the test image file
    """
    try:
        # Check if file exists
        if not os.path.exists(image_path):
            print(f"Error: File not found: {image_path}")
            return

        # Open file
        with open(image_path, "rb") as file:
            # Upload file to API
            files = {"file": (os.path.basename(image_path), file, "image/jpeg")}
            response = requests.post(api_url, files=files)

        # Print response
        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            # Pretty print JSON response
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"Error: {response.text}")

    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    # Check arguments
    if len(sys.argv) < 2:
        print("Usage: python test_api.py <image_path>")
        sys.exit(1)

    # Get image path from arguments
    image_path = sys.argv[1]

    # API URL
    api_url = "http://localhost:8000/api/extract"

    # Test API
    test_document_extraction(api_url, image_path)
```

Run the test script:

```bash
pipenv run python test_api.py /path/to/test/image.jpg
```

## 8. Implementation Checklist

Here's a checklist to ensure you've implemented all required components:

- [ ] Project setup and dependencies
- [ ] Base configuration
- [ ] Document type models
- [ ] Response models
- [ ] Document classifier
- [ ] Image preprocessing
- [ ] All document extractors:
- [ ] PAN Card extractor
- [ ] Aadhaar Card extractor
- [ ] Driving License extractor
- [ ] Rental Agreement extractor
- [ ] Proforma Invoice extractor

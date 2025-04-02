import time
from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import Dict, Any
import base64

from app.core.classifier import classify_document
from app.core.preprocessing import preprocess_image, extract_images_from_pdf
from app.core.validators import validate_document
from app.models.response_models import ExtractionResponse, ErrorResponse
from app.models.document_types import DocumentType

# Import all extractors
from app.extractors import (
    extract_pan_card,
    extract_aadhaar_card,
    extract_driving_license,
    extract_rental_agreement,
    extract_proforma_invoice,
    extract_utility_bill,
    extract_bank_statement
)

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
    Extract information from a document image or PDF

    Takes a document file, classifies it, and extracts information based on document type
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
                document_data = await extractor(image_base64, file.content_type)

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
            # Extract images from PDF
            images = await extract_images_from_pdf(content)
            
            if not images:
                raise HTTPException(
                    status_code=400,
                    detail="No images found in PDF"
                )

            # Process first page for classification
            first_page_base64 = base64.b64encode(images[0]).decode('utf-8')
            doc_type, confidence = await classify_document(first_page_base64)

            if doc_type == DocumentType.UNKNOWN or confidence < 0.6:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unable to confidently classify document (confidence: {confidence})"
                )

            # Extract information based on document type
            if doc_type in extractors:
                extractor = extractors[doc_type]
                document_data = await extractor(content, file.content_type)

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

@router.post("/extract_by_type/{document_type}", response_model=ExtractionResponse)
async def extract_document_by_type(
    document_type: DocumentType,
    file: UploadFile = File(...)
):
    """
    Extract information from a document image or PDF based on specified document type.
    Skips document classification and directly applies the specified extractor.
    """
    start_time = time.time()

    try:
        # Read file content
        content = await file.read()

        # Check if extractor exists for the document type
        if document_type in extractors:
            extractor = extractors[document_type]
            document_data = await extractor(content, file.content_type)

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
                document_type=document_type,
                extracted_data=extracted_data,
                confidence_scores=confidence_scores,
                validation_errors=validation_errors,
                is_valid=len(validation_errors) == 0,
                processing_time_ms=processing_time
            )
        else:
            raise HTTPException(
                status_code=501,
                detail=f"Extractor for document type '{document_type}' not implemented"
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
 
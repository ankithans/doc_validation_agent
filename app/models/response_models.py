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
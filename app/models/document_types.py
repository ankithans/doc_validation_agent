from enum import Enum
from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import List
from datetime import date, datetime
from decimal import Decimal
import re

class DocumentType(str, Enum):
    PAN_CARD = "pan_card"
    AADHAAR_CARD = "aadhaar_card"
    DRIVING_LICENSE = "driving_license"
    RENTAL_AGREEMENT = "rental_agreement"
    PROFORMA_INVOICE = "proforma_invoice"
    UTILITY_BILL = "utility_bill"
    BANK_STATEMENT = "bank_statement"

class DocumentField(BaseModel):
    """Base model for document fields with confidence scores"""
    value: str
    confidence: float = Field(ge=0.0, le=1.0)
    is_readable: bool = True

    model_config = ConfigDict(extra='forbid')

class DateField(BaseModel):
    """Specialized field for date values"""
    value: date
    confidence: float = Field(ge=0.0, le=1.0)
    is_readable: bool = True

    @field_validator('value', mode='before')
    @classmethod
    def parse_date(cls, v):
        # If it's already a date object, return it
        if isinstance(v, date):
            return v
            
        # If it's a datetime object, convert 
        if isinstance(v, datetime):
            return v.date()
            
        # If it's a string, try to parse it
        if isinstance(v, str):
            # Try DD/MM/YYYY format first
            try:
                day, month, year = map(int, v.split('/'))
                return date(year, month, day)
            except ValueError:
                # Try YYYY-MM-DD format
                try:
                    return date.fromisoformat(v)
                except ValueError:
                    # Try DD-MM-YYYY format
                    try:
                        day, month, year = map(int, v.split('-'))
                        return date(year, month, day)
                    except ValueError:
                        # Try DD.MM.YYYY format
                        try:
                            day, month, year = map(int, v.split('.'))
                            return date(year, month, day)
                        except ValueError:
                            # Try DD MMM YYYY format (e.g., "15 Jan 2024")
                            try:
                                return datetime.strptime(v, '%d %b %Y').date()
                            except ValueError:
                                # Try DD MMMM YYYY format (e.g., "15 January 2024")
                                try:
                                    return datetime.strptime(v, '%d %B %Y').date()
                                except ValueError:
                                    # Try MMM DD, YYYY format (e.g., "Jan 15, 2024")
                                    try:
                                        return datetime.strptime(v, '%b %d, %Y').date()
                                    except ValueError:
                                        # Try MMMM DD, YYYY format (e.g., "January 15, 2024")
                                        try:
                                            return datetime.strptime(v, '%B %d, %Y').date()
                                        except ValueError:
                                            raise ValueError(f"Invalid date format: {v}")
        
        raise ValueError(f"Invalid date value: {v}")

    model_config = ConfigDict(extra='forbid')

class AmountField(BaseModel):
    """Specialized field for monetary amounts"""
    value: Decimal
    confidence: float = Field(ge=0.0, le=1.0)
    is_readable: bool = True

    @field_validator('value', mode='before')
    @classmethod
    def parse_amount(cls, v):
        # If it's already a Decimal, return it
        if isinstance(v, Decimal):
            return v
            
        # If it's a float or int, convert to Decimal
        if isinstance(v, (float, int)):
            return Decimal(str(v))
            
        # If it's a string, try to parse it
        if isinstance(v, str):
            # Remove currency symbols and spaces
            v = re.sub(r'[^\d.]', '', v)
            try:
                return Decimal(v)
            except ValueError:
                raise ValueError(f"Invalid amount format: {v}")
        
        raise ValueError(f"Invalid amount value: {v}")

    model_config = ConfigDict(extra='forbid')

class PANCardData(BaseModel):
    """Data model for PAN card information"""
    document_type: DocumentType = DocumentType.PAN_CARD
    name: DocumentField
    father_name: DocumentField
    date_of_birth: DateField
    pan_number: DocumentField
    signature_present: bool

    model_config = ConfigDict(extra='forbid')

class AadhaarCardData(BaseModel):
    """Data model for Aadhaar card information"""
    document_type: DocumentType = DocumentType.AADHAAR_CARD
    name: DocumentField
    date_of_birth: DateField
    gender: DocumentField
    aadhaar_number: DocumentField
    address: DocumentField

    model_config = ConfigDict(extra='forbid')

class DrivingLicenseData(BaseModel):
    """Data model for Driving License information"""
    document_type: DocumentType = DocumentType.DRIVING_LICENSE
    dl_number: DocumentField
    name: DocumentField
    date_of_birth: DateField
    issue_date: DateField
    expiry_date: DateField
    swd: DocumentField  # Son/Wife/Daughter of
    address: DocumentField
    authorization_to_drive: List[str]

    model_config = ConfigDict(extra='forbid')

class RentalAgreementData(BaseModel):
    """Data model for Rental Agreement information"""
    document_type: DocumentType = DocumentType.RENTAL_AGREEMENT
    tenant_name: DocumentField
    tenant_address: DocumentField
    property_owner_name: DocumentField
    property_owner_address: DocumentField
    property_address: DocumentField
    rent_amount: AmountField
    deposit_amount: AmountField
    lease_period: DocumentField
    lease_start_date: DateField
    lease_end_date: DateField
    notary_present: bool
    owner_signature_present: bool
    tenant_signature_present: bool

    model_config = ConfigDict(extra='forbid')

class ProformaInvoiceData(BaseModel):
    """Data model for Proforma Invoice information"""
    document_type: DocumentType = DocumentType.PROFORMA_INVOICE
    manufacturer: DocumentField
    vehicle_model: DocumentField
    vehicle_variant: DocumentField
    vehicles_required: DocumentField
    ex_showroom_price: AmountField
    insurance_price: AmountField
    registration_charges: AmountField
    total_on_road_price: AmountField

    model_config = ConfigDict(extra='forbid')

class UtilityBillData(BaseModel):
    """Data model for Utility Bill information"""
    document_type: DocumentType = DocumentType.UTILITY_BILL
    customer_name: DocumentField
    bill_type: DocumentField
    document_date: DateField
    bill_provider: DocumentField
    bill_amount: AmountField
    customer_address: DocumentField
    utility_type: DocumentField

    model_config = ConfigDict(extra='forbid')

class BankStatementData(BaseModel):
    """Data model for Bank Statement information"""
    document_type: DocumentType = DocumentType.BANK_STATEMENT
    account_holder_name: DocumentField
    account_holder_address: DocumentField
    bank_name: DocumentField
    account_number: DocumentField
    transactions: List[dict]

    model_config = ConfigDict(extra='forbid') 
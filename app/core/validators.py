import re
from datetime import datetime, date
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
    if data.date_of_birth.value:
        if not isinstance(data.date_of_birth.value, date):
            errors.append(ValidationError(
                field="date_of_birth",
                error="Date of birth must be a valid date"
            ))

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

    # Validate date format
    if data.date_of_birth.value:
        if not isinstance(data.date_of_birth.value, date):
            errors.append(ValidationError(
                field="date_of_birth",
                error="Date of birth must be a valid date"
            ))

    return errors

# Driving License validation
def validate_driving_license(data: DrivingLicenseData) -> List[ValidationError]:
    errors = []

    # Validate date formats
    date_fields = ["date_of_birth", "issue_date", "expiry_date"]
    for field in date_fields:
        if hasattr(data, field) and getattr(data, field).value:
            if not isinstance(getattr(data, field).value, date):
                errors.append(ValidationError(
                    field=field,
                    error=f"{field.replace('_', ' ').title()} must be a valid date"
                ))

    # Check if expiry date is after issue date
    if (hasattr(data, "issue_date") and data.issue_date.value and 
        hasattr(data, "expiry_date") and data.expiry_date.value):
        if data.expiry_date.value <= data.issue_date.value:
            errors.append(ValidationError(
                field="expiry_date",
                error="Expiry date must be after issue date"
            ))

    return errors

# Rental Agreement validation
def validate_rental_agreement(data: RentalAgreementData) -> List[ValidationError]:
    errors = []

    # Validate date formats
    date_fields = ["lease_start_date", "lease_end_date"]
    for field in date_fields:
        if hasattr(data, field) and getattr(data, field).value:
            if not isinstance(getattr(data, field).value, date):
                errors.append(ValidationError(
                    field=field,
                    error=f"{field.replace('_', ' ').title()} must be a valid date"
                ))

    # Check if end date is after start date
    if data.lease_start_date.value and data.lease_end_date.value:
        if data.lease_end_date.value <= data.lease_start_date.value:
            errors.append(ValidationError(
                field="lease_end_date",
                error="Lease end date must be after start date"
            ))

    return errors

# Proforma Invoice validation
def validate_proforma_invoice(data: ProformaInvoiceData) -> List[ValidationError]:
    errors = []
    return errors

# Utility Bill validation
def validate_utility_bill(data: UtilityBillData) -> List[ValidationError]:
    errors = []

    # Validate date format
    if data.document_date.value:
        if not isinstance(data.document_date.value, date):
            errors.append(ValidationError(
                field="document_date",
                error="Document date must be a valid date"
            ))

    return errors

# Bank Statement validation
def validate_bank_statement(data: BankStatementData) -> List[ValidationError]:
    errors = []
    return errors

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
    elif isinstance(document_data, DrivingLicenseData):
        return validate_driving_license(document_data)
    elif isinstance(document_data, RentalAgreementData):
        return validate_rental_agreement(document_data)
    elif isinstance(document_data, ProformaInvoiceData):
        return validate_proforma_invoice(document_data)
    elif isinstance(document_data, UtilityBillData):
        return validate_utility_bill(document_data)
    elif isinstance(document_data, BankStatementData):
        return validate_bank_statement(document_data)
    else:
        return [ValidationError(field="document_type", error="Unsupported document type")] 
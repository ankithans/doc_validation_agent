from pydantic_ai import Agent, BinaryContent
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.providers.google_gla import GoogleGLAProvider
from app.models.document_types import RentalAgreementData, DocumentField
from app.config import settings
from app.core.preprocessing import get_binary_content, extract_images_from_pdf
from typing import Union

async def extract_rental_agreement(input_data: Union[str, bytes], content_type: str) -> RentalAgreementData:
    """
    Extract information from a Rental Agreement image or PDF

    Args:
        input_data: Either base64 encoded string or bytes
        content_type: MIME type of the input (e.g., 'image/jpeg', 'application/pdf')

    Returns:
        RentalAgreementData object with extracted fields
    """
    rental_agent = Agent(
        GeminiModel(
            settings.GEMINI_MODEL, 
            provider=GoogleGLAProvider(api_key=settings.GEMINI_API_KEY)
        ),
        instrument=True,
        result_type=RentalAgreementData,
        system_prompt="""
        You are an OCR system specialized in extracting information from Rental Agreements.

        Extract the following fields from the Rental Agreement document:

        1. Landlord Name:
           - Location: Look for "Landlord", "Lessor", or "Owner" section
           - Format: Full name of the property owner
           - Validation: Should contain alphabetic characters and spaces

        2. Tenant Name:
           - Location: Look for "Tenant", "Lessee", or "Renter" section
           - Format: Full name of the tenant
           - Validation: Should contain alphabetic characters and spaces

        3. Property Address:
           - Location: Look for "Property Address" or "Premises" section
           - Format: Complete address including house/street, locality, city, state, and PIN code
           - Validation: Should include all address components

        4. Rent Amount:
           - Location: Look for "Rent", "Monthly Rent", or "Rental Amount" section
           - Format: Numeric value with currency symbol (e.g., "₹15,000")
           - Validation: Should be a valid currency amount

        5. Deposit Amount:
           - Location: Look for "Security Deposit", "Deposit", or "Advance" section
           - Format: Numeric value with currency symbol (e.g., "₹30,000")
           - Validation: Should be a valid currency amount

        6. Lease Start Date:
           - Location: Look for "Commencement Date", "Start Date", or "From Date" section
           - Format: DD/MM/YYYY
           - Validation: Must be a valid date

        7. Lease End Date:
           - Location: Look for "End Date", "Termination Date", or "Till Date" section
           - Format: DD/MM/YYYY
           - Validation: Must be a valid date after start date

        8. Property Type:
           - Location: Look for "Property Type" or "Type of Premises" section
           - Format: Type of property (e.g., "Apartment", "House", "Commercial Space")
           - Validation: Should be a valid property type

        For each field, provide:
        - The extracted text value
        - A confidence score (0.0-1.0)
        - Whether the text is clearly readable (boolean)

        If a field is not found or unreadable, provide a low confidence score and set is_readable to false.
        Always convert text to English if it's in another language.
        """
    )

    # Convert input to BinaryContent
    binary_content = get_binary_content(input_data, content_type)

    # Run extraction with BinaryContent
    response = await rental_agent.run([
        "Extract information from this Rental Agreement document.",
        "Convert all the text to English after extracting it.",
        binary_content
    ])

    print(f"Extracted Rental Agreement data: {response.data}")

    # The agent will return the data in the expected RentalAgreementData format
    return response.data 
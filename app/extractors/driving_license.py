from pydantic_ai import Agent, BinaryContent
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.providers.google_gla import GoogleGLAProvider
from app.models.document_types import DrivingLicenseData, DocumentField
from app.config import settings
from app.core.preprocessing import get_binary_content, extract_images_from_pdf
from typing import Union

async def extract_driving_license(input_data: Union[str, bytes], content_type: str) -> DrivingLicenseData:
    """
    Extract information from a Driving License image or PDF

    Args:
        input_data: Either base64 encoded string or bytes
        content_type: MIME type of the input (e.g., 'image/jpeg', 'application/pdf')

    Returns:
        DrivingLicenseData object with extracted fields
    """
    dl_agent = Agent(
        GeminiModel(
            settings.GEMINI_MODEL, 
            provider=GoogleGLAProvider(api_key=settings.GEMINI_API_KEY)
        ),
        instrument=True,
        result_type=DrivingLicenseData,
        system_prompt="""
        You are an OCR system specialized in extracting information from Indian Driving Licenses.

        Extract the following fields from the Driving License document:

        1. Name:
           - Location: Look for "Name" or "नाम" label
           - Format: Full name in English or Hindi
           - Validation: Should contain alphabetic characters and spaces

        2. Date of Birth:
           - Location: Look for "Date of Birth" or "जन्म तिथि" label
           - Format: DD/MM/YYYY
           - Validation: Must be a valid date

        3. Address:
           - Location: Look for "Address" or "पता" section
           - Format: Multi-line text
           - Validation: Should include house/street, locality, city, state, and PIN code

        4. DL Number:
           - Location: Look for "DL No." or "डीएल नंबर" label
           - Format: State code + 2 digits + 4 digits + 7 digits
           - Validation: Must match the format (e.g., DL-0120160000000)

        5. Issue Date:
           - Location: Look for "Issue Date" or "जारी करने की तिथि"
           - Format: DD/MM/YYYY
           - Validation: Must be a valid date

        6. Valid Until:
           - Location: Look for "Valid Until" or "मान्यता की अवधि"
           - Format: DD/MM/YYYY
           - Validation: Must be a valid date

        7. Vehicle Categories:
           - Location: Look for "Vehicle Class" or "वाहन श्रेणी" section
           - Format: List of vehicle categories (e.g., ["MCWG", "LMV"])
           - Validation: Should be a list of valid vehicle categories

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
    response = await dl_agent.run([
        "Extract information from this Driving License document.",
        binary_content
    ])

    print(f"Extracted Driving License data: {response.data}")

    # The agent will return the data in the expected DrivingLicenseData format
    return response.data 
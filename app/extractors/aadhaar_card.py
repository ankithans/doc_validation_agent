from pydantic_ai import Agent, BinaryContent
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.providers.google_gla import GoogleGLAProvider
from app.models.document_types import AadhaarCardData, DocumentField
from app.config import settings
from app.core.preprocessing import get_binary_content, extract_images_from_pdf
from typing import Union

async def extract_aadhaar_card(input_data: Union[str, bytes], content_type: str) -> AadhaarCardData:
    """
    Extract information from an Aadhaar card image or PDF

    Args:
        input_data: Either base64 encoded string or bytes
        content_type: MIME type of the input (e.g., 'image/jpeg', 'application/pdf')

    Returns:
        AadhaarCardData object with extracted fields
    """
    aadhaar_agent = Agent(
        GeminiModel(
            settings.GEMINI_MODEL, 
            provider=GoogleGLAProvider(api_key=settings.GEMINI_API_KEY)
        ),
        instrument=True,
        result_type=AadhaarCardData,
        system_prompt="""
        You are an OCR system specialized in extracting information from Indian Aadhaar cards.

        Extract the following fields from the Aadhaar card document:

        1. Name:
           - Location: Look for "Name" or "नाम" label
           - Format: Full name in English or Hindi
           - Validation: Should contain alphabetic characters and spaces

        2. Date of Birth:
           - Location: Look for "Date of Birth" or "जन्म तिथि" label
           - Format: DD/MM/YYYY
           - Validation: Must be a valid date

        3. Gender:
           - Location: Look for "Gender" or "लिंग" label
           - Format: Single character (M/F/T)
           - Validation: Must be one of M, F, or T

        4. Aadhaar Number:
           - Location: Look for "Aadhaar No." or "आधार नंबर" label
           - Format: 12-digit number
           - Validation: Must be exactly 12 digits

        5. Address:
           - Location: Look for "Address" or "पता" section
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

    # Convert input to BinaryContent
    binary_content = get_binary_content(input_data, content_type)

    # Run extraction with BinaryContent
    response = await aadhaar_agent.run([
        "Extract information from this Aadhaar card document.",
        binary_content
    ])

    print(f"Extracted Aadhaar card data: {response.data}")

    # The agent will return the data in the expected AadhaarCardData format
    return response.data 
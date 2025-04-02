from pydantic_ai import Agent, BinaryContent
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.providers.google_gla import GoogleGLAProvider
from app.models.document_types import PANCardData, DocumentField
from app.config import settings
from app.core.preprocessing import get_binary_content, extract_images_from_pdf
from typing import Union
import base64

async def extract_pan_card(input_data: Union[str, bytes], content_type: str) -> PANCardData:
    """
    Extract information from a PAN card image or PDF

    Args:
        input_data: Either base64 encoded string or bytes
        content_type: MIME type of the input (e.g., 'image/jpeg', 'application/pdf')

    Returns:
        PANCardData object with extracted fields
    """
    pan_agent = Agent(
        GeminiModel(
            settings.GEMINI_MODEL, 
            provider=GoogleGLAProvider(api_key=settings.GEMINI_API_KEY)
        ),
        instrument=True,
        result_type=PANCardData,
        system_prompt="""
        You are an OCR system specialized in extracting information from Indian PAN cards.

        Extract the following fields from the PAN card document:

        1. Name:
           - Location: Look for "Name" or "नाम" label
           - Format: Full name in English or Hindi
           - Validation: Should contain alphabetic characters and spaces

        2. Father's Name:
           - Location: Look for "Father's Name" or "पिता का नाम" label
           - Format: Full name in English or Hindi
           - Validation: Should contain alphabetic characters and spaces

        3. Date of Birth:
           - Location: Look for "Date of Birth" or "जन्म तिथि" label
           - Format: DD/MM/YYYY
           - Validation: Must be a valid date

        4. PAN Number:
           - Location: Look for "Permanent Account Number" or "पैन नंबर" label
           - Format: 5 letters + 4 numbers + 1 letter (e.g., ABCDE1234F)
           - Validation: Must match the format

        5. Signature Present:
           - Check if a signature is visible on the card
           - Return a boolean value (true/false)

        For each field (except signature), provide:
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
    response = await pan_agent.run([
        "Extract information from this PAN card document.",
        binary_content
    ])

    print(f"Extracted PAN card data: {response.data}")

    # The agent will return the data in the expected PANCardData format
    return response.data 
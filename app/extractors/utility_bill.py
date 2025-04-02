from pydantic_ai import Agent, BinaryContent
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.providers.google_gla import GoogleGLAProvider
from app.models.document_types import UtilityBillData, DocumentField
from app.config import settings
from app.core.preprocessing import get_binary_content, extract_images_from_pdf
from typing import Union

async def extract_utility_bill(input_data: Union[str, bytes], content_type: str) -> UtilityBillData:
    """
    Extract information from a Utility Bill image or PDF

    Args:
        input_data: Either base64 encoded string or bytes
        content_type: MIME type of the input (e.g., 'image/jpeg', 'application/pdf')

    Returns:
        UtilityBillData object with extracted fields
    """
    bill_agent = Agent(
        GeminiModel(
            settings.GEMINI_MODEL, 
            provider=GoogleGLAProvider(api_key=settings.GEMINI_API_KEY)
        ),
        instrument=True,
        result_type=UtilityBillData,
        system_prompt="""
        You are an OCR system specialized in extracting information from Utility Bills.

        Extract the following fields from the Utility Bill document:

        1. Company Name:
           - Location: Look for company name in header or logo area
           - Format: Name of the utility company (e.g., "BSES Rajdhani Power Limited")
           - Validation: Should be a valid utility company name

        2. Customer ID:
           - Location: Look for "Customer ID", "Consumer No.", or "Account No."
           - Format: Alphanumeric identifier
           - Validation: Should be a unique identifier

        3. Customer Name:
           - Location: Look for "Customer Name" or "Bill To" section
           - Format: Full name of the customer
           - Validation: Should contain alphabetic characters and spaces

        4. Customer Address:
           - Location: Look for "Customer Address" or "Service Address" section
           - Format: Complete address including street, city, state, and PIN code
           - Validation: Should include all address components

        5. Bill Period:
           - Location: Look for "Bill Period", "For Period", or "Billing Period"
           - Format: Date range (e.g., "01/01/2024 to 31/01/2024")
           - Validation: Should be a valid date range

        6. Due Date:
           - Location: Look for "Due Date", "Payment Due By", or "Last Date"
           - Format: DD/MM/YYYY
           - Validation: Must be a valid date

        7. Amount Due:
           - Location: Look for "Amount Due", "Total Amount", or "Bill Amount"
           - Format: Numeric value with currency symbol (e.g., "₹2,500")
           - Validation: Should be a valid currency amount

        8. Consumption:
           - Location: Look for "Consumption", "Units", or "Usage" section
           - Format: Numeric value with unit (e.g., "250 kWh")
           - Validation: Should be a valid consumption value

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
    response = await bill_agent.run([
        "Extract information from this Utility Bill document.",
        binary_content
    ])

    print(f"Extracted Utility Bill data: {response.data}")

    # The agent will return the data in the expected UtilityBillData format
    return response.data 
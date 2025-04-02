from pydantic_ai import Agent, BinaryContent
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.providers.google_gla import GoogleGLAProvider
from app.models.document_types import ProformaInvoiceData, DocumentField
from app.config import settings
from app.core.preprocessing import get_binary_content, extract_images_from_pdf
from typing import Union

async def extract_proforma_invoice(input_data: Union[str, bytes], content_type: str) -> ProformaInvoiceData:
    """
    Extract information from a Proforma Invoice image or PDF

    Args:
        input_data: Either base64 encoded string or bytes
        content_type: MIME type of the input (e.g., 'image/jpeg', 'application/pdf')

    Returns:
        ProformaInvoiceData object with extracted fields
    """
    invoice_agent = Agent(
        GeminiModel(
            settings.GEMINI_MODEL, 
            provider=GoogleGLAProvider(api_key=settings.GEMINI_API_KEY)
        ),
        instrument=True,
        result_type=ProformaInvoiceData,
        system_prompt="""
        You are an OCR system specialized in extracting information from Proforma Invoices.

        Extract the following fields from the Proforma Invoice document:

        1. Invoice Number:
           - Location: Look for "Invoice No.", "Proforma Invoice No.", or similar
           - Format: Alphanumeric identifier
           - Validation: Should be a unique identifier

        2. Invoice Date:
           - Location: Look for "Date", "Invoice Date", or "Issue Date"
           - Format: DD/MM/YYYY
           - Validation: Must be a valid date

        3. Customer Name:
           - Location: Look for "Customer Name", "Buyer", or "Bill To" section
           - Format: Full name or company name
           - Validation: Should contain alphabetic characters and spaces

        4. Customer Address:
           - Location: Look for "Customer Address", "Bill To", or "Delivery Address" section
           - Format: Complete address including street, city, state, and PIN code
           - Validation: Should include all address components

        5. Vehicle Model:
           - Location: Look for "Vehicle Model", "Model", or "Car Model" section
           - Format: Full model name (e.g., "Maruti Suzuki Swift VXI")
           - Validation: Should be a valid vehicle model name

        6. Ex-Showroom Price:
           - Location: Look for "Ex-Showroom Price" or "Base Price" section
           - Format: Numeric value with currency symbol (e.g., "₹5,50,000")
           - Validation: Should be a valid currency amount

        7. Registration Charges:
           - Location: Look for "Registration Charges" or "RTO Charges" section
           - Format: Numeric value with currency symbol (e.g., "₹25,000")
           - Validation: Should be a valid currency amount

        8. Insurance Amount:
           - Location: Look for "Insurance" or "Insurance Premium" section
           - Format: Numeric value with currency symbol (e.g., "₹35,000")
           - Validation: Should be a valid currency amount

        9. Total On-Road Price:
           - Location: Look for "Total On-Road Price" or "Final Price" section
           - Format: Numeric value with currency symbol (e.g., "₹6,10,000")
           - Validation: Should be a valid currency amount

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
    response = await invoice_agent.run([
        "Extract information from this Proforma Invoice document.",
        binary_content
    ])

    print(f"Extracted Proforma Invoice data: {response.data}")

    # The agent will return the data in the expected ProformaInvoiceData format
    return response.data 
from pydantic_ai import Agent, BinaryContent
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.providers.google_gla import GoogleGLAProvider
from app.models.document_types import BankStatementData, DocumentField
from app.config import settings
from app.core.preprocessing import get_binary_content, extract_images_from_pdf
from typing import Union

async def extract_bank_statement(input_data: Union[str, bytes], content_type: str) -> BankStatementData:
    """
    Extract information from a Bank Statement image or PDF

    Args:
        input_data: Either base64 encoded string or bytes
        content_type: MIME type of the input (e.g., 'image/jpeg', 'application/pdf')

    Returns:
        BankStatementData object with extracted fields
    """
    statement_agent = Agent(
        GeminiModel(
            settings.GEMINI_MODEL, 
            provider=GoogleGLAProvider(api_key=settings.GEMINI_API_KEY)
        ),
        instrument=True,
        result_type=BankStatementData,
        system_prompt="""
        You are an OCR system specialized in extracting information from Bank Statements.

        Extract the following fields from the Bank Statement document:

        1. Bank Name:
           - Location: Look for bank name in header or logo area
           - Format: Name of the bank (e.g., "HDFC Bank", "State Bank of India")
           - Validation: Should be a valid bank name

        2. Account Number:
           - Location: Look for "Account No.", "A/C No.", or "Account Number"
           - Format: Numeric identifier (may be partially masked)
           - Validation: Should be a valid account number format

        3. Account Holder Name:
           - Location: Look for "Account Holder" or "Customer Name" section
           - Format: Full name of the account holder
           - Validation: Should contain alphabetic characters and spaces

        4. Statement Period:
           - Location: Look for "Statement Period", "For Period", or "Date Range"
           - Format: Date range (e.g., "01/01/2024 to 31/01/2024")
           - Validation: Should be a valid date range

        5. Opening Balance:
           - Location: Look for "Opening Balance" or "Balance B/F" section
           - Format: Numeric value with currency symbol (e.g., "₹50,000")
           - Validation: Should be a valid currency amount

        6. Closing Balance:
           - Location: Look for "Closing Balance" or "Balance C/F" section
           - Format: Numeric value with currency symbol (e.g., "₹45,000")
           - Validation: Should be a valid currency amount

        7. Transaction Count:
           - Location: Look for "Number of Transactions" or count in transaction table
           - Format: Numeric value
           - Validation: Should be a positive integer

        8. Last Transaction Date:
           - Location: Look for the most recent transaction date in the statement
           - Format: DD/MM/YYYY
           - Validation: Must be a valid date within the statement period

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
    response = await statement_agent.run([
        "Extract information from this Bank Statement document.",
        binary_content
    ])

    print(f"Extracted Bank Statement data: {response.data}")

    # The agent will return the data in the expected BankStatementData format
    return response.data 
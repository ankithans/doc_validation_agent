import base64
import io
from typing import Union, Optional, Tuple, List
from PIL import Image
import PyPDF2
from pydantic_ai import BinaryContent

def preprocess_image(file_content: bytes) -> str:
    """
    Preprocess image for OCR
    - Resize if too large
    - Enhance contrast
    - Convert to base64

    Args:
        file_content: Raw bytes of the image file

    Returns:
        Base64 encoded processed image
    """
    try:
        # Open image with PIL
        image = Image.open(io.BytesIO(file_content))

        # Convert to RGB if necessary
        if image.mode not in ('RGB', 'L'):
            image = image.convert('RGB')

        # Resize if too large (max dimensions 2000x2000)
        max_dimension = 2000
        if image.width > max_dimension or image.height > max_dimension:
            ratio = min(max_dimension / image.width, max_dimension / image.height)
            new_width = int(image.width * ratio)
            new_height = int(image.height * ratio)
            image = image.resize((new_width, new_height), Image.LANCZOS)

        # Save processed image to bytes buffer
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=95)
        buffer.seek(0)

        # Convert to base64
        image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        return image_base64

    except Exception as e:
        raise ValueError(f"Error preprocessing image: {e}")

def get_binary_content(input_data: Union[str, bytes], content_type: str) -> BinaryContent:
    """
    Convert input data to BinaryContent format
    
    Args:
        input_data: Either base64 string or bytes
        content_type: MIME type of the content (e.g., 'image/jpeg', 'application/pdf')
        
    Returns:
        BinaryContent object
    """
    if isinstance(input_data, str):
        # If input is base64 string, decode it
        data = base64.b64decode(input_data)
    else:
        # If input is already bytes, use it directly
        data = input_data
        
    return BinaryContent(data=data, media_type=content_type)

async def extract_images_from_pdf(pdf_content: bytes) -> list[bytes]:
    """
    Extract images from each page of a PDF

    Args:
        pdf_content: Raw bytes of the PDF file

    Returns:
        List of image bytes for each page
    """
    try:
        reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
        page_count = len(reader.pages)

        # For MVP, we'll use a simple approach: render each page as an image
        # A more sophisticated approach would be to extract embedded images
        # That would require additional libraries like pdf2image with poppler

        # For MVP, return empty list - you'll need to implement this with additional libraries
        return []

    except Exception as e:
        raise ValueError(f"Error extracting images from PDF: {e}") 
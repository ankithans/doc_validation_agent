import gradio as gr
import requests
import json
from typing import Dict, Any, Tuple, List
import base64
from app.models.document_types import DocumentType
import os
from PIL import Image
import io
import fitz  # PyMuPDF for PDF preview

# API endpoint from environment variable
API_URL = os.getenv("API_URL", "http://localhost:8000/api")

def format_response(response: Dict[str, Any]) -> str:
    """Format the API response for display"""
    if not response:
        return "Error: No response from server"
    
    # Format extracted data
    extracted_data = response.get("extracted_data", {})
    confidence_scores = response.get("confidence_scores", {})
    validation_errors = response.get("validation_errors", [])
    
    output = []
    output.append("📄 Extracted Information:")
    output.append("-" * 50)
    
    for field, value in extracted_data.items():
        confidence = confidence_scores.get(field, 0.0)
        output.append(f"{field.replace('_', ' ').title()}: {value}")
        output.append(f"Confidence: {confidence:.2%}")
        output.append("-" * 30)
    
    if validation_errors:
        output.append("\n⚠️ Validation Errors:")
        output.append("-" * 50)
        for error in validation_errors:
            output.append(f"• {error['field']}: {error['error']}")
    
    output.append(f"\n⏱️ Processing Time: {response.get('processing_time_ms', 0):.2f} ms")
    output.append(f"✅ Valid: {response.get('is_valid', False)}")
    
    return "\n".join(output)

def get_preview(file_path: str) -> List[Image.Image]:
    """Get preview of the document (image or PDF)"""
    if file_path is None:
        return None
    
    try:
        file_type = os.path.splitext(file_path)[1].lower()
        
        if file_type in ['.jpg', '.jpeg', '.png', '.tiff']:
            # For images, return the PIL Image as a single-item list
            return [Image.open(file_path)]
        elif file_type == '.pdf':
            # For PDFs, convert all pages to images
            doc = fitz.open(file_path)
            images = []
            for page_num in range(len(doc)):
                page = doc[page_num]
                pix = page.get_pixmap(matrix=fitz.Matrix(300/72, 300/72))
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                images.append(img)
            doc.close()
            return images
        else:
            return None
            
    except Exception as e:
        print(f"Error creating preview: {str(e)}")
        return None

def process_document(file_path, doc_type: str) -> Tuple[str, List[Image.Image]]:
    """Process the document using the API and return preview"""
    if file_path is None:
        return "Please upload a document", None
    
    try:
        # Get preview
        preview_images = get_preview(file_path)
        
        # Get file name and type
        file_name = os.path.basename(file_path)
        file_type = os.path.splitext(file_name)[1].lower()
        
        # Map file extension to MIME type
        mime_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.tiff': 'image/tiff',
            '.pdf': 'application/pdf'
        }
        content_type = mime_types.get(file_type, 'application/octet-stream')
        
        # Read file content
        with open(file_path, 'rb') as f:
            file_content = f.read()
            
        # Convert to base64
        file_base64 = base64.b64encode(file_content).decode('utf-8')
        
        # Prepare request data
        data = {
            "file": file_base64,
            "content_type": content_type
        }
        
        # Make API request
        try:
            response = requests.post(
                f"{API_URL}/extract_by_type/{doc_type}",
                json=data,
                timeout=30  # Add timeout
            )
            response.raise_for_status()  # Raise exception for bad status codes
            result = response.json()
        except requests.exceptions.ConnectionError:
            return f"Error: Could not connect to API server at {API_URL}. Please check if the server is running and accessible.", preview_images
        except requests.exceptions.Timeout:
            return "Error: Request timed out. The server took too long to respond.", preview_images
        except requests.exceptions.RequestException as e:
            return f"Error making API request: {str(e)}", preview_images
        except json.JSONDecodeError:
            return "Error: Received invalid response from server.", preview_images
        
        # Format response
        formatted_response = format_response(result)
        
        return formatted_response, preview_images
        
    except Exception as e:
        return f"Error processing document: {str(e)}", None

def create_interface():
    """Create the Gradio interface"""
    # Document type choices
    doc_types = [doc_type.value for doc_type in DocumentType]
    
    # Create the interface
    with gr.Blocks(title="Document Validation System") as interface:
        gr.Markdown("# 📄 Document Validation System")
        gr.Markdown("Upload a document and select its type to extract and validate information.")
        
        with gr.Row():
            with gr.Column(scale=1):
                file_input = gr.File(
                    label="Upload Document",
                    file_types=[".jpg", ".jpeg", ".png", ".tiff", ".pdf"],
                    type="filepath"
                )
                doc_type = gr.Dropdown(
                    choices=doc_types,
                    label="Document Type",
                    info="Select the type of document"
                )
                submit_btn = gr.Button("Process Document")
                preview = gr.Gallery(
                    label="Document Preview",
                    show_label=True,
                    elem_id="gallery",
                    columns=1,
                    rows=3,
                    height=400,
                    show_download_button=False,
                    allow_preview=True
                )
            
            with gr.Column(scale=1):
                output = gr.Textbox(
                    label="Results",
                    lines=20,
                    max_lines=30
                )
        
        # Update preview when file is uploaded
        file_input.change(
            fn=get_preview,
            inputs=[file_input],
            outputs=[preview]
        )
        
        # Process document and update results
        submit_btn.click(
            fn=process_document,
            inputs=[file_input, doc_type],
            outputs=[output, preview],
            show_progress="full",
            api_name="process_document"
        )
    
    return interface

if __name__ == "__main__":
    interface = create_interface()
    # Use environment variables for host and port
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "7860"))
    interface.launch(server_name=host, server_port=port) 
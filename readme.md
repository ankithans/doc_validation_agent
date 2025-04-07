# Document Validation System - API and Frontend Documentation

## Environment Setup

### Prerequisites

- Python 3.8+
- pipenv
- Git

### Installation

1. Clone the repository:

```bash
git clone <repository-url>
cd doc_validation_agent
```

2. Install dependencies using pipenv:

```bash
pipenv install
```

3. Create a `.env` file in the root directory with the following variables:

```env
# Default model type (gemini, openai, ollama)
DEFAULT_MODEL_TYPE=gemini

# Gemini Configuration
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-2.0-flash

# API Configuration
API_URL=http://localhost:8000
```

4. Activate the virtual environment:

```bash
pipenv shell
```

5. Start the server:

```bash
python run.py
```

## API Documentation

The API is built using FastAPI and provides endpoints for document processing and validation.

### Base URL

```
http://localhost:8000/api
```

### Endpoints

#### 1. Extract Document Information

```
POST /extract
```

Extracts information from a document image or PDF.

**Request:**

- Content-Type: multipart/form-data
- Body: file (document image or PDF)

**Response:**

```json
{
  "document_type": "string",
  "extracted_data": {
    "field1": "value1",
    "field2": "value2"
  },
  "confidence_scores": {
    "field1": 0.95,
    "field2": 0.87
  },
  "validation_errors": [],
  "processing_time_ms": 1234,
  "is_valid": true
}
```

#### 2. Extract Document by Type

```
POST /extract_by_type/{document_type}
```

Extracts information from a document with a specified type.

**Parameters:**

- document_type: One of the supported document types (PAN_CARD, AADHAAR_CARD, etc.)

**Request:**

- Content-Type: multipart/form-data
- Body: file (document image or PDF)

**Response:**
Same as the /extract endpoint

## Frontend Access

The system provides two ways to interact with the document validation system:

### 1. Gradio Interface

Access the Gradio interface at:

```
http://localhost:8000/gradio
```

Features:

- Upload documents (images or PDFs)
- Select document type manually
- View extracted information
- See confidence scores
- Preview document
- View validation results

### 2. API Integration

You can integrate the API into your own applications using the following example:

```python
import requests

def process_document(file_path, api_url="http://localhost:8000/api"):
    with open(file_path, 'rb') as f:
        files = {'file': f}
        response = requests.post(f"{api_url}/extract", files=files)
        return response.json()
```

## Supported Document Types

- PAN Card
- Aadhaar Card
- Driving License
- Rental Agreement
- Proforma Invoice
- Utility Bill
- Bank Statement

## Error Handling

The API returns appropriate HTTP status codes and error messages:

- 400: Bad Request (invalid file type, missing file)
- 422: Unprocessable Entity (invalid document type)
- 500: Internal Server Error

Error response format:

```json
{
  "detail": "Error message"
}
```

## Development

### Running Tests

```bash
pipenv run pytest
```

### API Documentation

Access the interactive API documentation at:

```
http://localhost:8000/docs
```

### Swagger UI

Access the Swagger UI at:

```
http://localhost:8000/redoc
```

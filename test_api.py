import requests
import os
import sys
import json

def test_document_extraction(api_url, image_path):
    """
    Test document extraction API

    Args:
        api_url: URL of the API endpoint
        image_path: Path to the test image file
    """
    try:
        # Check if file exists
        if not os.path.exists(image_path):
            print(f"Error: File not found: {image_path}")
            return

        # Open file
        with open(image_path, "rb") as file:
            # Upload file to API
            files = {"file": (os.path.basename(image_path), file, "image/jpeg")}
            response = requests.post(api_url, files=files)

        # Print response
        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            # Pretty print JSON response
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"Error: {response.text}")

    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    # Check arguments
    if len(sys.argv) < 2:
        print("Usage: python test_api.py <image_path>")
        sys.exit(1)

    # Get image path from arguments
    image_path = sys.argv[1]

    # API URL
    api_url = "http://localhost:8000/api/extract"

    # Test API
    test_document_extraction(api_url, image_path) 
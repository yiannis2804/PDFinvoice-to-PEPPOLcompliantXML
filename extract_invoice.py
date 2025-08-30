import sys
from google.cloud import documentai_v1 as documentai
import os
import json

# Accept filename as command-line argument
if len(sys.argv) < 2:
    print("❌ Please provide the PDF file name as an argument.")
    sys.exit(1)

pdf_filename = sys.argv[1]  # e.g., uploads/invoice123.pdf

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "docai-key.json"

# Read values from .env
project_id = os.getenv("PROJECT_ID")
location = os.getenv("LOCATION")
processor_id = os.getenv("PROCESSOR_ID")

client = documentai.DocumentProcessorServiceClient(
    client_options={"api_endpoint": "us-documentai.googleapis.com"}
)

name = f"projects/{project_id}/locations/{location}/processors/{processor_id}"

# Read your invoice PDF
with open(pdf_filename, "rb") as file:
    document = {"content": file.read(), "mime_type": "application/pdf"}

# Send to Document AI
request = {"name": name, "raw_document": document}
result = client.process_document(request=request)

# Save output
doc = result.document
data = documentai.Document.to_dict(doc)

with open("invoice_data_new.json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)

print("✅ Extracted data saved to invoice_data_new.json")

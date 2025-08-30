# PDF Invoice to PEPPOL-Compliant XML

This project converts PDF invoices into **PEPPOL-compliant UBL 2.1 XML** files.  
It uses:
- **Google Cloud Document AI** → for extracting structured data from invoices.  
- **OpenAI GPT** → for parsing and extracting line items (description, quantity, unit price).  
- **Flask Web App** → for uploading PDFs, entering missing/manual fields, editing line items, and generating the final XML.  

---

## 🚀 Features
- Upload invoice PDFs in different formats.
- Extract key fields (supplier, buyer, totals, VAT, etc.) using Document AI.
- Use GPT to intelligently extract line items (descriptions, quantities, prices).
- Manually edit or add missing fields (buyer reference, project code, tax exemption reason, notes).
- Regenerate line items with GPT at any time.
- Export invoices as **PEPPOL-compliant UBL 2.1 XML**.

---

## 🛠️ Installation

### 1. Clone the repository
```bash
git clone https://github.com/yiannis2804/PDFinvoice-to-PEPPOLcompliantXML.git
cd PDFinvoice-to-PEPPOLcompliantXML
```

### 2. Create a virtual environment (optional but recommended)
```bash
python -m venv venv
source venv/bin/activate   # Linux / Mac
venv\Scripts\activate      # Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

---

## ⚙️ Configuration

### 1. Google Cloud Credentials
Download your **Document AI Service Account JSON key** and place it in the project root.  
This file should be named `docai-key.json` (or update `.env` accordingly).  

⚠️ **Important:** This file is in `.gitignore` so it won’t be uploaded to GitHub.

### 2. Environment Variables
Create a `.env` file in the project root:

```ini
GOOGLE_APPLICATION_CREDENTIALS=docai-key.json
PROJECT_ID=your_project_id
LOCATION=us
PROCESSOR_ID=your_processor_id
OPENAI_API_KEY=your_openai_api_key
```

---

## ▶️ Usage

### 1. Run the Flask app
```bash
python app.py
```

### 2. Upload a PDF
- Go to `http://127.0.0.1:5000/`  
- Drag & drop or upload an invoice PDF.  

### 3. Fill in Manual Fields
- Enter buyer reference, project code, tax exemption reason, etc.  

### 4. Edit Line Items
- Review extracted items.  
- Optionally click **Regenerate** to re-run GPT extraction.  

### 5. Generate XML
- Click **Generate XML** to produce a PEPPOL-compliant UBL 2.1 file.  
- The file will be saved locally and available for download.  

---

## 📂 Project Structure
```
new py trial/
│── app.py                        # Flask backend
│── extract_invoice.py             # Extracts data from PDFs with Document AI
│── extract_line_items_with_gpt.py # GPT-powered line item extraction
│── generate_xml_dynamic.py        # Generates PEPPOL-compliant XML
│── templates/                     # Frontend HTML templates
│── static/                        # Static assets (CSS, JS, Lottie animations)
│── uploads/                       # Uploaded invoice PDFs
│── docai-key.json                 # Google Cloud credentials (ignored in Git)
│── .env                           # Environment variables (ignored in Git)
│── requirements.txt               # Python dependencies
```

---

## 🔐 Security Notes
- `.env` and `docai-key.json` are ignored via `.gitignore` and **must not be shared**.
- Always keep your API keys private.
- This repo is safe for GitHub since secrets are excluded.

---

## 📖 Example Workflow
1. Upload `invoice123.pdf`  
2. Extracted fields & line items appear in the UI  
3. Add missing references (buyer/project)  
4. Adjust line items if necessary  
5. Download final `invoice123.xml` (PEPPOL-compliant UBL 2.1)

---

## 📜 License
This project is licensed under the MIT License — you are free to use, modify, and distribute it.

---

## ✨ Future Improvements
- Add support for batch PDF uploads.
- Improve GPT prompt engineering for edge cases.
- Optional database integration to store processed invoices.

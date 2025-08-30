import json
import re
from jinja2 import Environment, FileSystemLoader
import os
from datetime import datetime, timezone

with open("invoice_data_new.json", encoding="utf-8") as f:
    raw_data = json.load(f)

entities = raw_data.get("entities", [])

def extract_field(entities, entity_type):
    for entity in entities:
        if entity.get("type_") == entity_type:
            return entity.get("mention_text", "")
    return ""

def extract_address_field(entities, entity_type):
    for entity in entities:
        if entity.get("type_") == entity_type:
            address = entity.get("normalized_value", {}).get("address_value", {})
            return {
                "address_lines": address.get("address_lines", [""])[0],
                "postal_code": address.get("postal_code", ""),
                "locality": address.get("locality", ""),
                "region_code": address.get("region_code", "")
            }
    return {"address_lines": "", "postal_code": "", "locality": "", "region_code": ""}

def parse_multiline_description(desc):
    lines = [line.strip() for line in desc.splitlines() if line.strip()]
    return lines if lines else [desc.strip()]

invoice_data = {
    "invoice_id": extract_field(entities, "invoice_id"),
    "issue_date": extract_field(entities, "invoice_date"),
    "due_date": extract_field(entities, "due_date"),
    "currency": extract_field(entities, "currency") or "EUR",
    "net_total": extract_field(entities, "total_amount"),
    "tax_amount": extract_field(entities, "total_tax_amount") or "0.00",
    "gross_total": extract_field(entities, "total_amount"),
    "tax_percent": extract_field(entities, "tax_percent") or "0.0",
    "allowance_total": extract_field(entities, "allowance_total") or "0.00",
    "payment_id": extract_field(entities, "payment_id") or "",
    "account_iban": re.sub(r"\s+", "", extract_field(entities, "supplier_iban")),
    "bank_name": extract_field(entities, "bank_name"),
    "swift_code": extract_field(entities, "swift_code"),
    "note": extract_field(entities,"payment_terms"),
    "customer_name": extract_field(entities, "ship_to_name").replace("\n", " "),
    "messageID": extract_field(entities, "invoice_id") or "AUTOID123",
    "timestampUTC": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"),
    "supplier_legal_entity": extract_field(entities, "supplier_name"),
    "supplier_phone": extract_field(entities, "supplier_phone") or "",
    "customer_vat":extract_field(entities,"receiver_tax_id"),
    "line_items": []
    
}

raw_phone = extract_field(entities, "supplier_phone")
cleaned_phone = re.sub(r"\s+", "", raw_phone)  # removes all whitespace
invoice_data["supplier_phone"] = cleaned_phone




raw_issue_date = extract_field(entities, "invoice_date")
raw_due_date = extract_field(entities, "due_date")
# Convert to ISO format (if parsing fails, fallback to original)
def convert_date_format(date_str):
    try:
        return datetime.strptime(date_str, "%d/%m/%Y").strftime("%Y-%m-%d")
    except (ValueError, TypeError):
        return date_str  # fallback in case of incorrect format

invoice_data["issue_date"] = convert_date_format(raw_issue_date)
invoice_data["due_date"] = convert_date_format(raw_due_date)

supplier_addr = extract_address_field(entities, "supplier_address")
invoice_data.update({
    "supplier_name": extract_field(entities, "supplier_name"),
    "supplier_tax_id": extract_field(entities, "supplier_tax_id"),
    "supplier_vat": extract_field(entities, "supplier_vat_id"),
    "supplier_address": supplier_addr["address_lines"],
    "supplier_postcode": supplier_addr["postal_code"],
    "supplier_city": supplier_addr["locality"],
    "supplier_country": supplier_addr["region_code"]
})

# Step 1: Get and sanitize the raw address
raw_address = extract_field(entities, "ship_to_address").replace("\n", " ")

# Step 2: Remove anything in parentheses (like "(CERTH)")
cleaned_address = re.sub(r"\(.*?\)", "", raw_address)

# Step 3: Extract the postcode (first 5-digit number)
postcode_match = re.search(r"\b\d{5}\b", cleaned_address)
customer_postcode = postcode_match.group(0) if postcode_match else ""

# Step 4: Keep only part before postcode if found
if customer_postcode:
    address_before_postcode = cleaned_address.split(customer_postcode)[0]
else:
    address_before_postcode = cleaned_address

# Step 5: Strip leading/trailing whitespace and punctuation
address_before_postcode = address_before_postcode.strip()                   # remove leading/trailing spaces
address_before_postcode = re.sub(r"^[^\w]+|[^\w]+$", "", address_before_postcode)  # remove punctuation from start/end

# Step 6: Normalize internal spacing
address_before_postcode = re.sub(r"\s+", " ", address_before_postcode)

# Assign to invoice_data
invoice_data["customer_address"] = address_before_postcode
invoice_data["customer_postcode"] = customer_postcode

invoice_data["customer_city"] = raw_data.get("customer_city", "")
invoice_data["buyer_reference"] = raw_data.get("buyer_reference_manual", "")
invoice_data["project_reference"] = raw_data.get("project_reference_manual", "")
invoice_data["tax_exemption_reason"] = raw_data.get("tax_exemption_reason_manual", "")
invoice_data["tax_exemption_code"] = raw_data.get("tax_exemption_reason_code_manual", "")
invoice_data["endpoint_id"] = raw_data.get("endpoint_id_manual", "")
invoice_data["partyidentification_id"] = raw_data.get("partyidentification_id_manual", "")
invoice_data["payment_means_method"] = raw_data.get("payment_means_method_manual", "")
invoice_data["payment_means_number"] = raw_data.get("payment_means_number_manual", "")
invoice_data["invoiced_quantity_unit_code"] = raw_data.get("invoiced_quantity_unit_code_manual", "")
invoice_data["tax_category_id"] = raw_data.get("tax_category_id_manual", "")
invoice_data["contract_reference"] = raw_data.get("contract_reference_manual", "")






raw_tax_id = invoice_data.get("supplier_tax_id", "").strip()
country_code = invoice_data.get("supplier_country", "").strip().upper()
full_text = raw_data.get("text", "")

# Attempt to find a tax ID pattern in text like "IT12345678901" or "IT 12345678901"
matched_tax_id = ""
if country_code:
    tax_id_pattern = rf"\b{country_code}\s?\d{{8,15}}\b"  # Match IT123456789 or IT 123456789
    match = re.search(tax_id_pattern, full_text)
    if match:
        matched_tax_id = match.group(0).replace(" ", "")  # Remove internal space if present

# Use the matched one if found, otherwise apply fallback logic
if matched_tax_id:
    invoice_data["supplier_tax_id"] = matched_tax_id
elif raw_tax_id and country_code and not raw_tax_id.startswith(country_code):
    invoice_data["supplier_tax_id"] = country_code + raw_tax_id
else:
    invoice_data["supplier_tax_id"] = raw_tax_id



# Extract raw text
full_text = raw_data.get("text", "")
country_code = invoice_data.get("supplier_country", "").upper()

# Match all 11-character SWIFT codes
swift_candidates = re.findall(r'\b[A-Z]{4}' + country_code + r'[A-Z0-9]{2}[A-Z0-9]{3}\b', full_text)

# Choose the first valid match
invoice_data["swift_code"] = swift_candidates[0] if swift_candidates else ""


# Step: Load GPT-extracted line items
line_items_path = "edited_line_items.json" if os.path.exists("edited_line_items.json") else "gpt_extracted_line_items.json"
with open(line_items_path, encoding="utf-8") as f:
    gpt_line_items = json.load(f)

line_extension_amount_total = 0.0
invoice_data["line_items"] = []

for idx, item in enumerate(gpt_line_items, start=1):
    try:
        description = item.get("description", "").strip().replace("&", "and")
        quantity = float(item.get("quantity", 1))
        unit_price = float(item.get("unit_price", 0))
        line_total = quantity * unit_price
        line_extension_amount_total += line_total

        invoice_data["line_items"].append({
            "id": str(idx),
            "descriptions": [description],
            "quantity": str(quantity),
            "unit_code": "C62",
            "unit_price": f"{unit_price:.2f}",
            "line_extension_amount": f"{line_total:.2f}"
        })
    except Exception as e:
        print(f"❌ Error processing line {idx}: {e}")



def parse_number(value):
    """
    Converts a number string (e.g., '6.508,88' or '6,508.88') into a float.
    Handles both European and US formats.
    """
    if not isinstance(value, str):
        return float(value)

    value = value.strip()

    if "," in value and "." in value:
        if value.find(",") > value.find("."):
            # European format: 6.508,88 → 6508.88
            value = value.replace(".", "").replace(",", ".")
        else:
            # US format: 6,508.88 → 6508.88
            value = value.replace(",", "")
    elif "," in value:
        # European format without thousands separator: 508,88 → 508.88
        value = value.replace(",", ".")
    # else: plain float string (e.g., 508.88)

    try:
        return float(value)
    except ValueError:
        return 0.0

# Parse numbers robustly
net_total_value = parse_number(invoice_data.get("net_total", "0"))
gross_total_value = parse_number(invoice_data.get("gross_total", "0"))

# Compute allowance
allowance_amount_total = line_extension_amount_total - net_total_value

# Format for XML (no commas)
invoice_data["gross_total"] = f"{gross_total_value:.2f}"
invoice_data["net_total"] = f"{net_total_value:.2f}"
invoice_data["line_extension_total"] = f"{line_extension_amount_total:.2f}"
invoice_data["allowance_total"] = f"{allowance_amount_total:.2f}"


    
env = Environment(loader=FileSystemLoader("."))
template = env.get_template("peppol_template_dynamic_reviewed.xml.j2")
rendered = template.render(**invoice_data)


with open("output_invoice_dynamic_new.xml", "w", encoding="utf-8") as f:
    f.write(rendered)

print("✅ Produced output")
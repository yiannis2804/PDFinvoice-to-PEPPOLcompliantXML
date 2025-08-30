import json
import os
from openai import OpenAI
from dotenv import load_dotenv
import re

# Load API key
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

# Load invoice text
with open("invoice_data_new.json", encoding="utf-8") as f:
    raw_data = json.load(f)
full_text = raw_data.get("text", "")
ship_to_address = ""
for entity in raw_data.get("entities", []):
    if entity.get("type_") == "ship_to_address":
        ship_to_address = entity.get("mention_text", "")
        break

# Define the prompt
prompt = f"""
You are an expert in invoice understanding and you do very careful analysis and you double check many times

Given the following raw invoice text:

\"\"\"{full_text}\"\"\"

Extract all line items from the invoice.

For each item, provide:
- description 
- quantity
- unit_price

if shipping exists include it as an item


Return the result as a JSON array like this:
[
  {{"description": "...", "quantity": 1, "unit_price": 100.00}},
  ...
]
"""

# Make the OpenAI API call
response = client.chat.completions.create(
    model="gpt-4o",  # You can use "gpt-3.5-turbo" if you prefer
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": prompt}
    ],
    temperature=0
)

# Extract and clean up response
# Extract JSON array from GPT response using regex
match = re.search(r'\[\s*{.*}\s*]', response.choices[0].message.content, re.DOTALL)
if match:
    raw_output = match.group(0)
else:
    raw_output = ""
if raw_output.startswith("```json"):
    raw_output = raw_output.replace("```json", "").strip()
if raw_output.endswith("```"):
    raw_output = raw_output[:-3].strip()

# Save to file
try:
    line_items = json.loads(raw_output)
    with open("gpt_extracted_line_items.json", "w", encoding="utf-8") as f:
        json.dump(line_items, f, indent=2, ensure_ascii=False)
    print("✅ GPT line items saved to gpt_extracted_line_items.json")
except json.JSONDecodeError as e:
    print("❌ Failed to decode JSON from GPT response")
    print("Raw output:\n", raw_output)
    print("Error:", e)

city_prompt = f"""
You are an expert in address understanding.

Extract the greek city from the following shipping address:

\"\"\"{ship_to_address}\"\"\"

Return only the city name, no extra text or explanation.
"""

response2 = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": city_prompt}
    ],
    temperature=0
)

customer_city = response2.choices[0].message.content.strip()

# Store in invoice_data so it can be passed to XML
raw_data["customer_city"] = customer_city

# Save back into the JSON file so the XML generator can access it
with open("invoice_data_new.json", "w", encoding="utf-8") as f:
    json.dump(raw_data, f, indent=2, ensure_ascii=False)





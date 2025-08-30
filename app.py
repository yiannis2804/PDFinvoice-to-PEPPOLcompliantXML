from flask import Flask, request, render_template, redirect, url_for
import os
import subprocess
import json

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


@app.route('/')
def index():
    return render_template('index.html', show_fields=False, xml_ready=False, xml_file=None)


@app.route('/upload', methods=['POST'])
def upload():
    if 'pdf' not in request.files:
        return "No file part", 400

    file = request.files['pdf']
    if file.filename == '':
        return "No selected file", 400

    filename = file.filename
    upload_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(upload_path)

    try:
        subprocess.run(['python', 'extract_invoice.py', upload_path], check=True)
        subprocess.run(['python', 'extract_line_items_with_gpt.py'], check=True)

        return render_template('index.html', show_fields=True, xml_ready=False, xml_file=None)

    except subprocess.CalledProcessError as e:
        return f"❌ Processing failed: {str(e)}", 500


@app.route('/submit_fields', methods=['POST'])
def submit_fields():
    with open("invoice_data_new.json", encoding="utf-8") as f:
        data = json.load(f)

    data['buyer_reference_manual'] = request.form.get('buyer_reference')
    data['project_reference_manual'] = request.form.get('project_reference')
    data['tax_exemption_reason_manual'] = request.form.get('tax_exemption_reason')
    data['tax_exemption_reason_code_manual'] = request.form.get('tax_exemption_reason_code')
    data['endpoint_id_manual'] = request.form.get('endpoint_id')
    data['partyidentification_id_manual'] = request.form.get('partyidentification_id')
    data['payment_means_method_manual'] = request.form.get('payment_means_method')
    data['payment_means_number_manual'] = request.form.get('payment_means_number')
    data['tax_category_id_manual'] = request.form.get('tax_category_id')
    data['invoiced_quantity_unit_code_manual'] = request.form.get('invoiced_quantity_unit_code')
    data['contract_reference_manual'] = request.form.get('contract_reference')




    with open("invoice_data_new.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    # Load line items for review/edit
    with open("gpt_extracted_line_items.json", encoding="utf-8") as f:
        line_items = json.load(f)

    return render_template('edit_items.html', items=line_items)




@app.route('/update_items', methods=['POST'])
def update_items():
    # Collect submitted items from form
    descriptions = {k: v for k, v in request.form.items() if k.startswith('description_')}
    quantities = {k: v for k, v in request.form.items() if k.startswith('quantity_')}
    prices = {k: v for k, v in request.form.items() if k.startswith('unit_price_')}

    updated_items = []

    for key in descriptions:
        index = key.split('_')[1]
        description = descriptions.get(f'description_{index}', '').strip()
        quantity = float(quantities.get(f'quantity_{index}', 1))
        unit_price = float(prices.get(f'unit_price_{index}', 0))

        updated_items.append({
            "description": description,
            "quantity": quantity,
            "unit_price": unit_price
        })

    # Save updated items to new JSON
    with open("edited_line_items.json", "w", encoding="utf-8") as f:
        json.dump(updated_items, f, indent=2)

    # Then call generate_xml_dynamic.py
    try:
        subprocess.run(["python", "generate_xml_dynamic.py"], check=True)
        return redirect(url_for('index', xml_file="output_invoice_dynamic_new.xml"))
    except subprocess.CalledProcessError as e:
        return f"❌ XML Generation failed: {str(e)}", 500


@app.route('/generate_xml', methods=['POST'])
def generate_xml():
    try:
        subprocess.run(['python', 'generate_xml_dynamic.py'], check=True)
        xml_file = 'output_invoice_dynamic_new.xml'
        return render_template('index.html', show_fields=False, xml_ready=True, xml_file=xml_file)
    except subprocess.CalledProcessError as e:
        return f"❌ XML Generation failed: {str(e)}", 500

if __name__ == '__main__':
    app.run(debug=True)

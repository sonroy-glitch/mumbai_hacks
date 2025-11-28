from flask import Flask, request, jsonify
from flask_cors import CORS
from google import genai
import pandas as pd
import numpy as np
import psycopg2
import re
import json
import smtplib
from email.mime.text import MIMEText

def send_email(to_email, subject, body):
    # clean_subject = subject.replace("\n", " ").strip()
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    from_email = "rsounak55@gmail.com"
    password = "zeuj aylo ngek ijlq"   

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = from_email
    msg["To"] = to_email

    s = smtplib.SMTP(smtp_server, smtp_port)
    s.starttls()
    s.login(from_email, password)
    s.send_message(msg)
    s.quit()

FINSIGHT_SYSTEM_PROMPT = """
You are FinSight, an autonomous financial reconciliation agent.

Your responsibilities:
- Read transactions and invoices.
- Determine which transactions match invoices.
- Identify unmatched items.
- Summarize matches.

Return ONLY valid JSON using the following format:

{
    "matched": <int>,
    "unmatched": <int>,
    "results": [
        {
            "transaction_id": 1,
            "amount": 15000,
            "date": "2025-10-05",
            "description": "Payment from Acme",
            "match": {"invoice_id": "INV-1001"}
        }
    ]
}
Rules:
1.Dont return any markdown text. Just normal string
"""
DB_URL = "postgresql://rsounak55:9MNGXL7KochR@ep-frosty-star-42942474-pooler.us-east-2.aws.neon.tech/bank?sslmode=require&channel_binding=require"
conn = psycopg2.connect(DB_URL)
cur = conn.cursor()
app = Flask(__name__)
CORS(app)
client = genai.Client(api_key="AIzaSyAh1jI5-q9VxkihuIHIrl7EHOtpgR94egE")
@app.route('/upload/statement', methods=['POST'])
def upload_statement():
    """
    Upload a bank statement CSV/PDF.
    Placeholder: just returns success.
    """
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "No file uploaded"}), 400
    df = pd.read_csv(file)

    for i in range(len(df)):
        row = df.iloc[i]

        cur.execute("""
            INSERT INTO transactions (date, description, amount, matched_invoice_id, fixed)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            row['Date'],                   
            row['Description'],            
            float(row['Amount']),         
            None,                          
            False                        
        ))
        conn.commit()
    
    return jsonify({"status": "statement_received", "filename": file.filename})



@app.route('/upload/invoices', methods=['POST'])
@app.route("/upload/invoices", methods=["POST"])
def upload_invoices():
    files = request.files.getlist("file")

    if not files:
        return jsonify({"error": "No files uploaded"}), 400

    saved = 0

    for f in files:
        filename = f.filename.lower()

        
        if filename.endswith(".csv"):
            try:
                df = pd.read_csv(f)        
                for i, row in df.iterrows():
                    invoice_id = str(row.get("invoice_id") or row.get("InvoiceID"))
                    customer = str(row.get("customer") or row.get("Customer", ""))
                    amount = float(row.get("amount") or row.get("Amount", 0))
                    due_date = row.get("due_date") or row.get("DueDate")

                    cur.execute("""
                        INSERT INTO invoices (invoice_id, customer, amount, due_date, paid)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (invoice_id, customer, amount, due_date, False))

                saved += len(df)

            except Exception as e:
                return jsonify({"error": f"CSV parse failed: {str(e)}"}), 500

        
        # elif filename.endswith(".pdf"):
        #     try:
        #         content = f.read()
        #         parsed = parse_invoice_pdf_bytes(content)  # your existing function

        #         cur.execute("""
        #             INSERT INTO invoices (invoice_id, customer, amount, due_date, paid)
        #             VALUES (%s, %s, %s, %s, %s)
        #         """, (
        #             parsed["invoice_id"],
        #             parsed.get("customer", ""),
        #             parsed.get("amount", 0),
        #             parsed.get("due_date", None),
        #             False
        #         ))

        #         saved += 1

        #     except Exception as e:
        #         return jsonify({"error": f"PDF parse failed: {str(e)}"}), 500

        else:
            return jsonify({"error": "Unsupported file type"}), 400

    conn.commit()

    return jsonify({"status": "ok", "saved": saved})




@app.route('/reconcile', methods=['POST'])

def reconcile():
    cur.execute("SELECT id, date, description, amount FROM transactions")
    tx_rows = cur.fetchall()

    cur.execute("SELECT invoice_id, customer, amount, due_date FROM invoices WHERE paid = FALSE")
    inv_rows = cur.fetchall()

    tx_list = []
    for t in tx_rows:
        tx_list.append({
            "transaction_id": t[0],
            "date": str(t[1]),
            "description": t[2],
            "amount": float(t[3])
        })

    inv_list = []
    for inv in inv_rows:
        inv_list.append({
            "invoice_id": inv[0],
            "customer": inv[1],
            "amount": float(inv[2]),
            "due_date": str(inv[3]) if inv[3] else None
        })

    llm_input = {
        "transactions": tx_list,
        "invoices": inv_list
    }

    user_message = f"""
    Reconcile the following:

    Transactions:
    {tx_list}

    Invoices:
    {inv_list}
    """

    final_prompt = f"""You are FinSight.
    {FINSIGHT_SYSTEM_PROMPT}

    User request:
    {user_message}
    """

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=final_prompt
    )

    output = response.text
    try:
        result_json = json.loads(output)
    except:
        return jsonify({"error": "LLM returned invalid JSON", "raw": output}), 500
    print(result_json)
    for item in result_json.get("results", []):
        tx_id = item.get("transaction_id")
        match = item.get("match")
        if match and match.get("invoice_id"):
            cur.execute("UPDATE transactions SET matched_invoice_id=%s WHERE id=%s", (match["invoice_id"], tx_id))
    conn.commit()

    return jsonify(result_json)



@app.route('/generate_email/<int:tx_id>', methods=['GET'])
def generate_email(tx_id):
    cur.execute("SELECT id, date, description, amount, matched_invoice_id FROM transactions WHERE id=%s", (tx_id,))
    tx = cur.fetchone()

    if not tx:
        return jsonify({"error": "Transaction not found"}), 404

    tx_id, tx_date, tx_desc, tx_amount, matched_invoice = tx

    if matched_invoice:
        cur.execute("SELECT invoice_id, customer, amount, due_date FROM invoices WHERE id=%s", (matched_invoice,))
        inv = cur.fetchone()
    else:
        inv = None

    prompt = f"""
    Generate a professional finance email.

    Transaction:
    - ID: {tx_id}
    - Date: {tx_date}
    - Description: {tx_desc}
    - Amount: {tx_amount}

    Invoice:
    {inv if inv else "No matching invoice."}

    The email should be:
    - Professional
    - Clear
    - Short
    - Asking for confirmation or clarification
    - Include subject + body
    Return JSON:
    {{
        "subject": "...",
        "body": "..."
    }}
    No markdown text. Just normal string.
    """

    llm = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    try:
        email_json = json.loads(llm.text)
    except:
        return jsonify({"error": "Invalid email JSON from LLM", "raw": llm.text})

    subject = email_json.get("subject")
    body = email_json.get("body")

    send_email("skmondal191062@gmail.com", subject, body)


    return jsonify({
        "status": "email_sent",
        "subject": subject,
        "body": body
    })


@app.route('/autofix/<int:tx_id>', methods=['POST'])
def autofix(tx_id):
    """
    Automatically mark invoice as paid + update DB.
    """
    # TODO: Update DB 
    return jsonify({"status": "fixed", "transaction": tx_id})




@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"})


if __name__ == '__main__':
    app.run(port=5001, debug=True)

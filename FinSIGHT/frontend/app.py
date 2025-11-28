# frontend/streamlit_app.py
import streamlit as st
import requests
import pandas as pd

API_BASE = "http://localhost:5001"

st.set_page_config(page_title="FinSight – Autonomous Finance Ops", layout="wide")
st.title("FinSight — Autonomous Financial Operations Dashboard")

left, right = st.columns([1, 2])

# =====================================================
# LEFT PANEL — UPLOAD + RUN AGENT
# =====================================================
with left:
    st.header("1. Upload Data")

    # Upload Bank Statement
    statement_file = st.file_uploader("Upload Bank Statement (CSV)", type=["csv"])

    if st.button("Upload Statement"):
        if not statement_file:
            st.error("Please select a CSV file first.")
        else:
            files = {"file": ("statement.csv", statement_file.getvalue())}
            resp = requests.post(f"{API_BASE}/upload/statement", files=files)
            st.write(resp.json()['status'])

    # Upload Invoices (CSV or PDF)
    invoice_files = st.file_uploader(
        "Upload Invoices (CSV or PDF)", 
        type=["csv", "pdf"], 
        accept_multiple_files=True
    )

    if st.button("Upload Invoices"):
        if not invoice_files:
            st.error("Please upload at least one invoice file.")
        else:
            files_payload = [
                ("file", (file.name, file.getvalue())) for file in invoice_files
            ]
            resp = requests.post(f"{API_BASE}/upload/invoices", files=files_payload)
            st.write(resp.json()['status'])

    # Run reconciliation
    if st.button("Run Reconciliation"):
        resp = requests.post(f"{API_BASE}/reconcile")
        if resp.status_code == 200:
            st.session_state["recon"] = resp.json()
            st.success("Reconciliation completed successfully!")
        else:
            st.error(resp.text)

    # Debug route
    if st.button("Dump Backend State"):
        resp = requests.get(f"{API_BASE}/dump_state")
        st.write(resp.json())

# =====================================================
# RIGHT PANEL — RESULTS
# =====================================================
with right:
    st.header("2. Results & Insights")

    recon = st.session_state.get("recon")

    if recon:
        # ------- Forecast -------
        st.subheader("Cashflow Forecast")
        fc = recon.get("forecast", {})

        colA, colB = st.columns(2)
        colA.metric(
            label="Upcoming Receivables (Next 30 Days)",
            value=f"₹{fc.get('upcoming_receivables_30d', 0):,.2f}"
        )
        colB.metric(
            label="Avg Monthly Outflow",
            value=f"₹{fc.get('avg_monthly_outflow', 0):,.2f}"
        )

        # ------- Transaction Matches -------
        st.subheader("Reconciliation Results")

        results = recon.get("results", [])

        df_rows = []
        for r in results:
            match = r.get("match")
            df_rows.append({
                "Transaction ID": r["transaction_id"],
                "Date": r["date"],
                "Description": r["description"],
                "Amount": r["amount"],
                "Matched Invoice": match["invoice_id"] if match else "—"
            })
        

        df = pd.DataFrame(df_rows)
        st.dataframe(df, use_container_width=True)

        # ------- Email Draft + Auto Fix -------
        st.subheader("Take Actions")

        tx_id = st.number_input("Select Transaction ID", min_value=0, step=1)

        if st.button("Generate Email Draft"):
            resp = requests.get(f"{API_BASE}/generate_email/{tx_id}")
            if resp.status_code == 200:
                d = resp.json()
                st.subheader("Email Subject")
                st.write(d)
                # st.subheader("Email Body")
                # st.code(d["body"])
            else:
                st.error("Invalid Transaction ID")

        if st.button("Auto-Fix"):
            resp = requests.post(f"{API_BASE}/autofix/{tx_id}")
            if resp.status_code == 200:
                st.success("Auto-fix applied successfully!")
            else:
                st.error(resp.text)

    else:
        st.info("Run reconciliation to see results here.")

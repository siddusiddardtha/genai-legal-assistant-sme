import streamlit as st
import pandas as pd

# =========================================================
# PAGE CONFIG (MUST BE FIRST)
# =========================================================
st.set_page_config(
    page_title="GenAI Legal Assistant for SMEs",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =========================================================
# DARK MODE TOGGLE
# =========================================================
dark_mode = st.toggle("🌙 Dark Mode", value=False)

# =========================================================
# STYLE (ONLY BACKGROUND + SIMPLE PROFESSIONAL LOOK)
# =========================================================
if dark_mode:
    st.markdown("""
    <style>
    .stApp {
        background-color: #0f172a;
        color: #e5e7eb;
    }

    h1, h2, h3 {
        color: #f8fafc;
    }

    [data-testid="metric-container"] {
        background-color: #1e293b;
        border-radius: 10px;
        padding: 16px;
    }

    .streamlit-expanderHeader {
        background-color: #020617;
        border-radius: 8px;
    }

    .stButton > button {
        background-color: #2563eb;
        color: white;
        border-radius: 6px;
        font-weight: 600;
    }
    </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <style>
    .stApp {
        background-color: #f9fafb;
        color: #111827;
    }

    h1, h2, h3 {
        color: #111827;
    }

    [data-testid="metric-container"] {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 16px;
        border: 1px solid #e5e7eb;
    }

    .streamlit-expanderHeader {
        background-color: #f3f4f6;
        border-radius: 8px;
    }

    .stButton > button {
        background-color: #2563eb;
        color: white;
        border-radius: 6px;
        font-weight: 600;
    }
    </style>
    """, unsafe_allow_html=True)

# =========================================================
# IMPORTS (UNCHANGED)
# =========================================================
from core.ingestion import extract_text
from core.language import detect_language
from core.clause_extraction import classify_contract_type, extract_clauses
from core.risk_engine import (
    classify_clause_type,
    calculate_risk_score,
    calculate_contract_risk
)
from core.audit_logger import log_event
from llm.gemini_client import (
    explain_clause_gemini,
    suggest_alternative_gemini
)
from exports.pdf_generator import generate_contract_report

# =========================================================
# HEADER
# =========================================================
st.title("📄 GenAI-Powered Legal Assistant for Indian SMEs")
st.write(
    "Upload a contract to identify legal risks, understand clauses in plain language, "
    "and compare safer alternatives."
)

use_ai = st.toggle("🤖 Enable AI (Gemini)", value=True)

# =========================================================
# FILE UPLOAD
# =========================================================
uploaded_file = st.file_uploader(
    "Upload Contract (PDF, DOCX, or TXT)",
    type=["pdf", "docx", "txt"]
)

# =========================================================
# MAIN LOGIC (UNCHANGED)
# =========================================================
if uploaded_file:
    with st.spinner("Analyzing contract..."):
        contract_text = extract_text(uploaded_file)

    if not contract_text.strip():
        st.error("Could not extract text from the uploaded file.")
        st.stop()

    language = detect_language(contract_text)
    contract_type = classify_contract_type(contract_text)
    clauses = extract_clauses(contract_text)

    clause_risk_levels = []

    for clause in clauses:
        clause_type = classify_clause_type(clause["text"])
        risk, score, reasons = calculate_risk_score(clause["text"], clause_type)

        clause["clause_type"] = clause_type
        clause["risk_level"] = risk
        clause["risk_reasons"] = reasons

        clause_risk_levels.append(risk)

    contract_risk = calculate_contract_risk(clause_risk_levels)

    log_event(
        "contract_analyzed",
        {
            "language": language,
            "contract_type": contract_type,
            "overall_risk": contract_risk,
            "total_clauses": len(clauses)
        }
    )

    st.subheader("📌 Executive Summary")

    summary = (
        f"This **{contract_type.lower()}** is written in **{language}** and "
        f"contains **{len(clauses)} clauses**. "
        f"Overall legal risk is **{contract_risk.upper()}**."
    )

    if contract_risk == "High":
        st.error(summary + " Immediate legal review recommended.")
    elif contract_risk == "Medium":
        st.warning(summary + " Some clauses should be renegotiated.")
    else:
        st.success(summary + " Contract appears balanced.")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Language", language)
    c2.metric("Contract Type", contract_type)
    c3.metric("Total Clauses", len(clauses))
    c4.metric("Overall Risk", contract_risk)

    st.divider()

    st.subheader("📊 Risk Distribution")

    chart_df = pd.DataFrame({
        "Risk Level": ["High", "Medium", "Low"],
        "Count": [
            clause_risk_levels.count("High"),
            clause_risk_levels.count("Medium"),
            clause_risk_levels.count("Low")
        ]
    }).set_index("Risk Level")

    st.bar_chart(chart_df)

    st.divider()

    st.subheader("🧠 Clause-Level Intelligence")

    icon = {"High": "🔴", "Medium": "🟠", "Low": "🟢"}

    for clause in clauses:
        with st.expander(
            f"{icon[clause['risk_level']]} Clause {clause['clause_id']} — {clause['risk_level']} Risk"
        ):
            st.markdown(f"**Clause Type:** {clause['clause_type']}")
            st.write(clause["text"])

            if clause["risk_level"] != "Low":
                st.write("### ⚠️ Why this is risky")
                for r in clause["risk_reasons"]:
                    st.markdown(f"- {r}")

                st.write("### 🔁 Safer Alternative")
                if use_ai:
                    try:
                        st.success(suggest_alternative_gemini(clause["text"]))
                    except Exception:
                        st.success("Add notice periods and mutual protections.")
                else:
                    st.success("Add notice periods and mutual protections.")

                st.write("### 🧠 Plain Explanation")
                if use_ai:
                    try:
                        st.info(explain_clause_gemini(clause["text"]))
                    except Exception:
                        st.info("This clause creates imbalance and business risk.")
                else:
                    st.info("This clause creates imbalance and business risk.")
            else:
                st.success("This clause appears balanced.")

    st.divider()
    st.subheader("📤 Export")

    if st.button("Generate PDF Report"):
        pdf_path = "exports/contract_analysis_report.pdf"
        generate_contract_report(
            filename=pdf_path,
            contract_type=contract_type,
            language=language,
            overall_risk=contract_risk,
            clauses=clauses
        )

        with open(pdf_path, "rb") as f:
            st.download_button(
                "📄 Download PDF",
                f,
                file_name="contract_analysis_report.pdf",
                mime="application/pdf"
            )

    st.divider()
    with st.expander("⚖️ Legal Disclaimer"):
        st.write(
            "This tool provides automated analysis for educational purposes only "
            "and does not constitute legal advice."
        )

import streamlit as st
import pandas as pd

# -----------------------------
# Page Config (MUST BE FIRST)
# -----------------------------
st.set_page_config(
    page_title="GenAI Legal Assistant for SMEs",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# -----------------------------
# Premium UI Theme
# -----------------------------
dark_mode = st.toggle("🌙 Dark Mode", value=False)

if dark_mode:
    st.markdown("""
    <style>
    .stApp {
        background: radial-gradient(circle at top, #020617, #020617);
        color: #e5e7eb;
        font-family: 'Inter', sans-serif;
    }

    h1, h2, h3 {
        color: #f8fafc;
        font-weight: 700;
    }

    [data-testid="metric-container"],
    .stExpander {
        background: linear-gradient(145deg, #0f172a, #020617);
        border-radius: 16px;
        padding: 16px;
        border: 1px solid #1e293b;
        box-shadow: 0 10px 30px rgba(0,0,0,0.6);
    }

    .stButton > button {
        background: linear-gradient(135deg, #6366f1, #4f46e5);
        color: white;
        border-radius: 12px;
        padding: 0.6rem 1.4rem;
        font-weight: 600;
        border: none;
        transition: all 0.3s ease;
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 30px rgba(99,102,241,0.5);
    }

    .stAlert {
        border-radius: 14px;
        background: #020617;
        border-left: 5px solid #6366f1;
    }
    </style>
    """, unsafe_allow_html=True)

else:
    st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(180deg, #f9fafb, #eef2ff);
        color: #0f172a;
        font-family: 'Inter', sans-serif;
    }

    h1, h2, h3 {
        color: #020617;
        font-weight: 700;
    }

    [data-testid="metric-container"],
    .stExpander {
        background: white;
        border-radius: 16px;
        padding: 16px;
        border: 1px solid #e5e7eb;
        box-shadow: 0 12px 28px rgba(0,0,0,0.08);
    }

    .stButton > button {
        background: linear-gradient(135deg, #4f46e5, #6366f1);
        color: white;
        border-radius: 12px;
        padding: 0.6rem 1.4rem;
        font-weight: 600;
        border: none;
        transition: all 0.3s ease;
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 28px rgba(79,70,229,0.35);
    }

    .stAlert {
        border-radius: 14px;
        background: #f8fafc;
        border-left: 5px solid #4f46e5;
    }
    </style>
    """, unsafe_allow_html=True)

# -----------------------------
# Core Imports (UNCHANGED)
# -----------------------------
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

# -----------------------------
# Header
# -----------------------------
st.title("📄 GenAI-Powered Legal Assistant for Indian SMEs")
st.write(
    "Upload contracts, identify legal risks, understand clauses in plain language, "
    "and compare safer alternatives using AI."
)

use_ai = st.toggle("🤖 Enable AI (Gemini)", value=True)

# -----------------------------
# File Upload
# -----------------------------
uploaded_file = st.file_uploader(
    "📤 Upload Contract (PDF, DOCX, TXT)",
    type=["pdf", "docx", "txt"]
)

# -----------------------------
# Main Processing
# -----------------------------
if uploaded_file:
    with st.spinner("🔍 Analyzing contract..."):
        contract_text = extract_text(uploaded_file)

    if not contract_text or not contract_text.strip():
        st.error("❌ Could not extract text from the uploaded file.")
        st.stop()

    language = detect_language(contract_text)
    contract_type = classify_contract_type(contract_text)
    clauses = extract_clauses(contract_text)

    if not clauses:
        st.warning("⚠️ No clauses detected in this document.")
        st.stop()

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

    # -----------------------------
    # Dashboard
    # -----------------------------
    st.success("✅ Contract analyzed successfully")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🌐 Language", language)
    c2.metric("📘 Contract Type", contract_type)
    c3.metric("📑 Total Clauses", len(clauses))
    c4.metric("⚠️ Overall Risk", contract_risk)

    st.divider()

    # -----------------------------
    # Risk Distribution
    # -----------------------------
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

    # -----------------------------
    # Clause-Level Analysis
    # -----------------------------
    st.subheader("🧠 Clause-Level Intelligence")

    for clause in clauses:
        with st.expander(
            f"Clause {clause['clause_id']} — {clause['risk_level']} Risk"
        ):
            st.markdown(f"**Clause Type:** {clause['clause_type']}")
            st.write("### 📄 Original Clause")
            st.write(clause["text"])

            if clause["risk_level"] != "Low":
                if clause["risk_reasons"]:
                    st.write("### ⚠️ Why this is risky")
                    for r in clause["risk_reasons"]:
                        st.markdown(f"- {r}")

                st.write("### 🔁 Clause Comparison")

                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("**Original Clause**")
                    st.info(clause["text"])

                with col2:
                    st.markdown("**Safer Alternative**")
                    if use_ai:
                        try:
                            st.success(suggest_alternative_gemini(clause["text"]))
                        except Exception:
                            st.success("Consider adding notice periods and safeguards.")
                    else:
                        st.success("Add notice periods and balanced termination rights.")

                st.write("### 🧠 Plain-Language Explanation")
                if use_ai:
                    try:
                        st.info(explain_clause_gemini(clause["text"]))
                    except Exception:
                        st.info("This clause may expose the business to risk.")
                else:
                    st.info("This clause may expose the business to risk.")
            else:
                st.success("✅ This clause appears balanced.")

    # -----------------------------
    # PDF Export
    # -----------------------------
    st.divider()
    st.subheader("📤 Export for Legal Review")

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
                "📄 Download Contract Analysis PDF",
                f,
                file_name="contract_analysis_report.pdf",
                mime="application/pdf"
            )

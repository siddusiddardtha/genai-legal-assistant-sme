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
# Dark Mode Toggle
# -----------------------------
dark_mode = st.toggle("🌙 Dark Mode", value=False)

if dark_mode:
    st.markdown("""
    <style>
    .stApp { background: #0f172a; color: #e5e7eb; }
    h1,h2,h3 { color: #f8fafc; }
    [data-testid="metric-container"] {
        background: #1e293b;
        color: white;
        border-radius: 14px;
    }
    .streamlit-expanderHeader { color: #e5e7eb; }
    .stAlert { background: #1e293b; }
    </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <style>
    .stApp { background: linear-gradient(180deg,#f8fafc,#eef2ff); }
    [data-testid="metric-container"] {
        background: white;
        border-radius: 14px;
        box-shadow: 0 8px 22px rgba(0,0,0,0.06);
    }
    </style>
    """, unsafe_allow_html=True)

# -----------------------------
# Imports
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
    "Upload a contract to identify risks, understand clauses in plain language, "
    "and compare safer alternatives."
)

use_ai = st.toggle("🤖 Enable AI (Gemini)", value=True)

# -----------------------------
# File Upload
# -----------------------------
uploaded_file = st.file_uploader(
    "Upload Contract (PDF, DOCX, or TXT)",
    type=["pdf", "docx", "txt"]
)

# -----------------------------
# Main Processing
# -----------------------------
if uploaded_file:
    with st.spinner("Analyzing contract..."):
        contract_text = extract_text(uploaded_file)

    if not contract_text.strip():
        st.error("Could not extract text.")
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
            "risk": contract_risk
        }
    )

    # -----------------------------
    # Dashboard
    # -----------------------------
    st.success("Contract analyzed successfully")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Language", language)
    c2.metric("Contract Type", contract_type)
    c3.metric("Total Clauses", len(clauses))
    c4.metric("Overall Risk", contract_risk)

    st.divider()

    # -----------------------------
    # Risk Charts (FEATURE #2)
    # -----------------------------
    st.subheader("📊 Risk Distribution")

    risk_df = pd.DataFrame({
        "Risk": ["High", "Medium", "Low"],
        "Count": [
            clause_risk_levels.count("High"),
            clause_risk_levels.count("Medium"),
            clause_risk_levels.count("Low")
        ]
    })

    colA, colB = st.columns(2)
    colA.bar_chart(risk_df.set_index("Risk"))
    colB.pyplot(
       st.subheader("📊 Risk Distribution")

chart_df = {
    "High Risk": clause_risk_levels.count("High"),
    "Medium Risk": clause_risk_levels.count("Medium"),
    "Low Risk": clause_risk_levels.count("Low")
}

st.bar_chart(chart_df)

    )

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
                st.write("### ⚠️ Why this is risky")
                for r in clause["risk_reasons"]:
                    st.markdown(f"- {r}")

                # -----------------------------
                # Clause Comparison (FEATURE #3)
                # -----------------------------
                st.write("### 🔁 Clause Comparison")

                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("**Original Clause**")
                    st.info(clause["text"])

                with col2:
                    st.markdown("**Safer Alternative**")
                    if use_ai:
                        try:
                            safer = suggest_alternative_gemini(clause["text"])
                            st.success(safer)
                        except Exception:
                            st.success(
                                "Add notice periods, mutual rights, and payment protections."
                            )
                    else:
                        st.success(
                            "Add notice periods and balance termination rights."
                        )

                # Explanation
                st.write("### 🧠 Plain-Language Explanation")
                if use_ai:
                    try:
                        st.info(explain_clause_gemini(clause["text"]))
                    except Exception:
                        st.info(
                            "This clause gives one party excessive control and increases business risk."
                        )
                else:
                    st.info(
                        "This clause may expose the business to financial or operational risk."
                    )
            else:
                st.success("This clause appears balanced.")

    # -----------------------------
    # PDF Export
    # -----------------------------
    st.divider()
    st.subheader("📤 Export")

    if st.button("Generate PDF Report"):
        pdf_path = "exports/contract_analysis_report.pdf"
        generate_contract_report(
            pdf_path, contract_type, language, contract_risk, clauses
        )
        with open(pdf_path, "rb") as f:
            st.download_button(
                "📄 Download PDF",
                f,
                file_name="contract_analysis_report.pdf"
            )

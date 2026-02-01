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
# THEME & DARK MODE
# =========================================================
dark_mode = st.toggle("🌙 Dark Mode", value=False)

if dark_mode:
    st.markdown("<body class='dark'></body>", unsafe_allow_html=True)
else:
    st.markdown("<body class='light'></body>", unsafe_allow_html=True)

st.markdown("""
<style>

/* ---------- GLOBAL ---------- */
.stApp {
    font-family: "Inter", system-ui, -apple-system, BlinkMacSystemFont;
}

/* ---------- LIGHT MODE ---------- */
.light .stApp {
    background: linear-gradient(180deg, #f8fafc 0%, #eef2ff 100%);
    color: #0f172a;
}

/* ---------- DARK MODE ---------- */
.dark .stApp {
    background: linear-gradient(180deg, #020617 0%, #020617 100%);
    color: #e5e7eb;
}

/* ---------- HEADERS ---------- */
h1 {
    font-weight: 800;
    letter-spacing: -0.03em;
}
h2, h3 {
    font-weight: 700;
    margin-top: 1.5rem;
}

/* ---------- METRIC CARDS ---------- */
[data-testid="metric-container"] {
    background: rgba(255,255,255,0.85);
    backdrop-filter: blur(12px);
    border-radius: 18px;
    padding: 18px;
    box-shadow: 0 10px 28px rgba(0,0,0,0.08);
    border: 1px solid rgba(0,0,0,0.05);
}

.dark [data-testid="metric-container"] {
    background: rgba(30,41,59,0.85);
    border: 1px solid rgba(255,255,255,0.08);
}

/* ---------- EXPANDERS ---------- */
.streamlit-expanderHeader {
    font-size: 16px;
    font-weight: 600;
    padding: 12px;
    border-radius: 12px;
}

/* ---------- ALERTS ---------- */
.stAlert {
    border-radius: 14px;
    font-size: 15px;
}

/* ---------- BUTTONS ---------- */
.stButton > button {
    background: linear-gradient(90deg, #4f46e5, #6366f1);
    color: white;
    font-weight: 700;
    border-radius: 14px;
    padding: 12px 22px;
    border: none;
}

/* ---------- DIVIDERS ---------- */
hr {
    margin: 2.5rem 0;
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# IMPORTS
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
    "Upload a contract to identify risks, understand clauses in plain language, "
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
# MAIN PROCESSING
# =========================================================
if uploaded_file:
    with st.spinner("Analyzing contract..."):
        contract_text = extract_text(uploaded_file)

    if not contract_text or not contract_text.strip():
        st.error("Could not extract text from the uploaded file.")
        st.stop()

    language = detect_language(contract_text)
    contract_type = classify_contract_type(contract_text)
    clauses = extract_clauses(contract_text)

    if not clauses:
        st.warning("No clauses could be extracted from this document.")
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

    # =====================================================
    # EXECUTIVE SUMMARY
    # =====================================================
    st.subheader("📌 Executive Summary")

    summary = (
        f"This **{contract_type.lower()}** is written in **{language}** and "
        f"contains **{len(clauses)} clauses**. "
        f"The overall legal risk is **{contract_risk.upper()}**."
    )

    if contract_risk == "High":
        st.error(summary + " Immediate legal review is recommended.")
    elif contract_risk == "Medium":
        st.warning(summary + " Some clauses should be renegotiated.")
    else:
        st.success(summary + " The contract appears generally balanced.")

    # =====================================================
    # DASHBOARD
    # =====================================================
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Language", language)
    c2.metric("Contract Type", contract_type)
    c3.metric("Total Clauses", len(clauses))
    c4.metric("Overall Risk", contract_risk)

    st.divider()

    # =====================================================
    # RISK DISTRIBUTION
    # =====================================================
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

    # =====================================================
    # CLAUSE-LEVEL ANALYSIS
    # =====================================================
    st.subheader("🧠 Clause-Level Intelligence")

    risk_icon = {"High": "🔴", "Medium": "🟠", "Low": "🟢"}

    for clause in clauses:
        with st.expander(
            f"{risk_icon[clause['risk_level']]} Clause {clause['clause_id']} — {clause['risk_level']} Risk"
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
                            st.success(
                                "Add notice periods, mutual rights, or payment safeguards."
                            )
                    else:
                        st.success(
                            "Add notice periods and balance termination rights."
                        )

                st.write("### 🧠 Plain-Language Explanation")
                if use_ai:
                    try:
                        st.info(explain_clause_gemini(clause["text"]))
                    except Exception:
                        st.info(
                            "This clause may expose the business to financial or operational risk."
                        )
                else:
                    st.info(
                        "This clause may expose the business to financial or operational risk."
                    )
            else:
                st.success("This clause appears balanced.")

    # =====================================================
    # PDF EXPORT
    # =====================================================
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

    # =====================================================
    # DISCLAIMER
    # =====================================================
    st.divider()
    with st.expander("⚖️ Legal Disclaimer"):
        st.write(
            "This tool provides automated analysis for educational and "
            "informational purposes only and does not constitute legal advice. "
            "Users should consult a qualified legal professional before making "
            "contractual decisions."
        )

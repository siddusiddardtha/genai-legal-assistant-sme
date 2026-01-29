import streamlit as st

from core.ingestion import extract_text
from core.language import detect_language
from core.clause_extraction import classify_contract_type, extract_clauses
from core.risk_engine import (
    classify_clause_type,
    calculate_risk_score,
    calculate_contract_risk
)
from core.audit_logger import log_event
from llm.legal_reasoning import explain_clause, suggest_alternative_clause
from exports.pdf_generator import generate_contract_report


# -----------------------------
# Streamlit Page Config
# -----------------------------
st.set_page_config(
    page_title="GenAI Legal Assistant for SMEs",
    layout="wide"
)

st.title("📄 GenAI-Powered Legal Assistant for Indian SMEs")
st.write(
    "Upload an employment or service contract to identify risks, "
    "understand clauses in plain language, and export a legal summary."
)
from llm.legal_reasoning import llm_available

st.markdown("### 🤖 GPT Connection Status")

if llm_available():
    st.success("✅ GPT is connected and ready")
else:
    st.warning("⚠️ GPT not connected (using fallback explanations)")
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
        st.error("Could not extract text from the uploaded file.")
    else:
        # ---- Core Analysis ----
        language = detect_language(contract_text)
        contract_type = classify_contract_type(contract_text)
        clauses = extract_clauses(contract_text)

        clause_risk_levels = []

        for clause in clauses:
            clause_type = classify_clause_type(clause["text"])
            risk_level, score, reasons = calculate_risk_score(
                clause["text"], clause_type
            )

            clause["clause_type"] = clause_type
            clause["risk_level"] = risk_level
            clause["risk_reasons"] = reasons

            clause_risk_levels.append(risk_level)

        contract_risk = calculate_contract_risk(clause_risk_levels)

        # ---- Audit Log (FIXED SCOPE) ----
        log_event(
            event_type="contract_analyzed",
            details={
                "language": language,
                "contract_type": contract_type,
                "overall_risk": contract_risk,
                "total_clauses": len(clauses)
            }
        )

        # -----------------------------
        # Dashboard
        # -----------------------------
        st.success("Contract analyzed successfully!")

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Language", language)
        col2.metric("Contract Type", contract_type)
        col3.metric("Total Clauses", len(clauses))
        col4.metric("Overall Risk", contract_risk)

        st.divider()

        # -----------------------------
        # Risk Overview
        # -----------------------------
        st.subheader("📊 Risk Overview")

        c1, c2, c3 = st.columns(3)
        c1.metric("High Risk Clauses", clause_risk_levels.count("High"))
        c2.metric("Medium Risk Clauses", clause_risk_levels.count("Medium"))
        c3.metric("Low Risk Clauses", clause_risk_levels.count("Low"))

        st.divider()

        # -----------------------------
        # Clause-Level Intelligence
        # -----------------------------
        st.subheader("🧠 Clause-Level Analysis")

        for clause in clauses:
            with st.expander(
                f"Clause {clause['clause_id']} — Risk: {clause['risk_level']}"
            ):
                st.markdown(f"**Clause Type:** {clause['clause_type']}")
                st.write("**Original Clause:**")
                st.write(clause["text"])

                if clause["risk_level"] != "Low":
                    st.write("**Plain-Language Explanation**")
                    st.info(explain_clause(clause["text"]))

                    st.write("**Suggested Safer Alternative**")
                    st.warning(suggest_alternative_clause(clause["text"]))
                else:
                    st.success("This clause appears balanced.")

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
                    label="📄 Download Contract Analysis PDF",
                    data=f,
                    file_name="contract_analysis_report.pdf",
                    mime="application/pdf"
                )

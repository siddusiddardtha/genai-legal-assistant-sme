import streamlit as st
from exports.pdf_generator import generate_contract_report
from core.audit_logger import log_event
from core.ingestion import extract_text
from core.language import detect_language
from core.clause_extraction import classify_contract_type, extract_clauses
from core.risk_engine import (
    classify_clause_type,
    calculate_risk_score,
    calculate_contract_risk
)
from llm.legal_reasoning import explain_clause, suggest_alternative_clause

st.set_page_config(page_title="GenAI Legal Assistant", layout="wide")

st.title("📄 GenAI-Powered Legal Assistant for Indian SMEs")

uploaded_file = st.file_uploader(
    "Upload Contract (PDF, DOCX, or TXT)",
    type=["pdf", "docx", "txt"]
)

if uploaded_file:
    with st.spinner("Processing contract..."):
        contract_text = extract_text(uploaded_file)

    if contract_text.strip():
        language = detect_language(contract_text)
        contract_type = classify_contract_type(contract_text)
        clauses = extract_clauses(contract_text)

        clause_risks = []

        for clause in clauses:
            clause_type = classify_clause_type(clause["text"])
            risk_level, score, reasons = calculate_risk_score(
                clause["text"], clause_type
            )
            clause["risk_level"] = risk_level
            clause["risk_reasons"] = reasons
            clause_risks.append(risk_level)

        contract_risk = calculate_contract_risk(clause_risks)

        # 🔹 DASHBOARD
        st.success("Contract analyzed successfully!")

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Language", language)
        col2.metric("Contract Type", contract_type)
        col3.metric("Total Clauses", len(clauses))
        col4.metric("Overall Risk", contract_risk)

        st.divider()

        # 🔹 CLAUSE INTELLIGENCE
        st.subheader("🧠 Clause Intelligence (GenAI)")

        for clause in clauses:
            with st.expander(
                f"Clause {clause['clause_id']} — Risk: {clause['risk_level']}"
            ):
                st.write("**Original Clause**")
                st.write(clause["text"])

                if clause["risk_level"] != "Low":
                    st.write("**Plain-Language Explanation**")
                    st.info(explain_clause(clause["text"]))

                    st.write("**Suggested Safer Alternative**")
                    st.warning(suggest_alternative_clause(clause["text"]))
                else:
                    st.success("This clause appears balanced.")

    else:
        st.error("Could not extract text from the uploaded file.")

log_event(
    event_type="contract_analyzed",
    details={
        "language": language,
        "contract_type": contract_type,
        "overall_risk": contract_risk,
        "total_clauses": len(clauses)
    }
)
st.divider()
st.subheader("📤 Export Report")

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

from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4


def generate_contract_report(
    filename,
    contract_type,
    language,
    overall_risk,
    clauses
):
    doc = SimpleDocTemplate(filename, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("<b>Contract Analysis Report</b>", styles["Title"]))
    story.append(Paragraph(f"Contract Type: {contract_type}", styles["Normal"]))
    story.append(Paragraph(f"Language: {language}", styles["Normal"]))
    story.append(Paragraph(f"Overall Risk Level: <b>{overall_risk}</b>", styles["Normal"]))
    story.append(Paragraph("<br/>", styles["Normal"]))

    for clause in clauses:
        story.append(
            Paragraph(
                f"<b>Clause {clause['clause_id']} — Risk: {clause['risk_level']}</b>",
                styles["Heading3"]
            )
        )
        story.append(Paragraph(clause["text"], styles["Normal"]))

        if clause["risk_reasons"]:
            for reason in clause["risk_reasons"]:
                story.append(
                    Paragraph(f"- {reason}", styles["Normal"])
                )

        story.append(Paragraph("<br/>", styles["Normal"]))

    doc.build(story)

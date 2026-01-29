def classify_contract_type(text: str) -> str:
    """
    Classifies contract type based on keyword heuristics.
    Returns: 'Employment Agreement', 'Service Agreement', or 'Unknown'
    """

    text_lower = text.lower()

    employment_keywords = [
        "employment", "employee", "employer",
        "salary", "termination of employment",
        "notice period", "designation"
    ]

    service_keywords = [
        "service", "services", "service provider",
        "client", "fees", "scope of work",
        "deliverables"
    ]

    employment_score = sum(1 for kw in employment_keywords if kw in text_lower)
    service_score = sum(1 for kw in service_keywords if kw in text_lower)

    if employment_score > service_score and employment_score > 0:
        return "Employment Agreement"
    elif service_score > employment_score and service_score > 0:
        return "Service Agreement"
    else:
        return "Unknown"
import re


def extract_clauses(text: str):
    """
    Extracts clauses from contract text.
    Returns a list of dictionaries:
    [{clause_id, clause_text}]
    """

    clauses = []

    # Pattern for numbered clauses like 1., 1.1, 2.3.4 etc.
    pattern = r'\n\s*(\d+(\.\d+)*)\s+(.*?)(?=\n\s*\d+(\.\d+)*\s+|\Z)'

    matches = re.finditer(pattern, text, re.DOTALL)

    for match in matches:
        clause_id = match.group(1)
        clause_text = match.group(3).strip()

        clauses.append({
            "clause_id": clause_id,
            "text": clause_text
        })

    # Fallback: if no numbered clauses found
    if not clauses:
        paragraphs = [p.strip() for p in text.split("\n") if len(p.strip()) > 40]

        for idx, para in enumerate(paragraphs, start=1):
            clauses.append({
                "clause_id": f"C{idx}",
                "text": para
            })

    return clauses

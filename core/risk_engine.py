def classify_clause_type(clause_text: str) -> str:
    """
    Classifies clause as Obligation, Right, Prohibition, or Neutral
    """

    text = clause_text.lower()

    if "shall not" in text or "must not" in text:
        return "Prohibition"

    if "shall" in text or "must" in text:
        return "Obligation"

    if "may" in text or "entitled to" in text:
        return "Right"

    return "Neutral"
def detect_risk_signals(clause_text: str):
    """
    Detects early legal risk signals in a clause
    """
    text = clause_text.lower()
    risks = []

    if "terminate" in text and "without notice" in text:
        risks.append("Unilateral termination without notice")

    if "penalty" in text or "liquidated damages" in text:
        risks.append("Financial penalty clause")

    if "indemnify" in text or "indemnity" in text:
        risks.append("Indemnity obligation")

    if "non-compete" in text or "competing business" in text:
        risks.append("Non-compete restriction")

    if "exclusive" in text:
        risks.append("Exclusivity clause")

    return risks
def calculate_risk_score(clause_text: str, clause_type: str):
    """
    Calculates risk score and level for a clause
    Returns: (risk_level, score, reasons)
    """

    score = 0
    reasons = []
    text = clause_text.lower()

    # High-impact risks
    if "terminate" in text and "without notice" in text:
        score += 3
        reasons.append("Unilateral termination without notice")

    if "non-compete" in text or "competing business" in text:
        score += 3
        reasons.append("Non-compete restriction")

    if "indemnify" in text or "indemnity" in text:
        score += 3
        reasons.append("Indemnity obligation")

    # Medium risks
    if "penalty" in text or "liquidated damages" in text:
        score += 2
        reasons.append("Financial penalty clause")

    if "exclusive" in text:
        score += 2
        reasons.append("Exclusivity clause")

    # Clause type risks
    if clause_type == "Prohibition":
        score += 2
        reasons.append("Restrictive prohibition")

    if clause_type == "Obligation":
        score += 1
        reasons.append("Mandatory obligation")

    # Risk level
    if score >= 6:
        risk_level = "High"
    elif score >= 3:
        risk_level = "Medium"
    else:
        risk_level = "Low"

    return risk_level, score, reasons
def calculate_contract_risk(clause_risks):
    """
    Aggregates clause risks to determine overall contract risk
    clause_risks: list of risk_level strings
    """

    high_count = clause_risks.count("High")
    medium_count = clause_risks.count("Medium")

    if high_count >= 1:
        return "High"
    elif medium_count >= 2:
        return "Medium"
    else:
        return "Low"

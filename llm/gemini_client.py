import os
import google.generativeai as genai

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash")
else:
    model = None


def gemini_available():
    return model is not None


def explain_clause_gemini(clause_text: str) -> str:
    if not gemini_available():
        return (
            "This clause may create business risk because it allows one party "
            "to act without adequate safeguards."
        )

    prompt = (
        "Explain the following contract clause in simple business English. "
        "Do not give legal advice.\n\n"
        f"Clause:\n{clause_text}"
    )

    response = model.generate_content(prompt)
    return response.text.strip()


def suggest_alternative_gemini(clause_text: str) -> str:
    if not gemini_available():
        return (
            "Consider adding a notice period or making the clause mutual "
            "to reduce business risk."
        )

    prompt = (
        "Suggest a safer, more balanced alternative wording for the "
        "following contract clause. Keep it practical.\n\n"
        f"Clause:\n{clause_text}"
    )

    response = model.generate_content(prompt)
    return response.text.strip()

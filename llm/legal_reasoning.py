import os
from openai import OpenAI
from llm.prompts import (
    CLAUSE_EXPLANATION_PROMPT,
    ALTERNATIVE_CLAUSE_PROMPT
)

# Initialize OpenAI client safely
client = None
api_key = os.getenv("OPENAI_API_KEY")

if api_key:
    client = OpenAI(api_key=api_key)


def llm_available():
    return client is not None


def explain_clause(clause_text: str) -> str:
    """
    Uses GPT to explain a legal clause in simple business language.
    Falls back gracefully if GPT is not available.
    """
    if not llm_available():
        return (
            "This clause may create business risk because it gives one party "
            "significant power without adequate safeguards."
        )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "You explain legal contract clauses in simple business English."
            },
            {
                "role": "user",
                "content": CLAUSE_EXPLANATION_PROMPT.format(
                    clause_text=clause_text
                )
            }
        ],
        temperature=0.2
    )

    return response.choices[0].message.content.strip()


def suggest_alternative_clause(clause_text: str) -> str:
    """
    Uses GPT to suggest a safer, more balanced alternative clause.
    """
    if not llm_available():
        return (
            "Suggested improvement: consider adding a reasonable notice period "
            "or making termination rights mutual."
        )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You suggest balanced contract wording. "
                    "Do not give legal advice. Keep it practical."
                )
            },
            {
                "role": "user",
                "content": ALTERNATIVE_CLAUSE_PROMPT.format(
                    clause_text=clause_text
                )
            }
        ],
        temperature=0.3
    )

    return response.choices[0].message.content.strip()

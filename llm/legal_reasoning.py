import os
import openai
from llm.prompts import (
    CLAUSE_EXPLANATION_PROMPT,
    ALTERNATIVE_CLAUSE_PROMPT
)

openai.api_key = os.getenv("OPENAI_API_KEY")


def llm_available():
    return openai.api_key is not None


def explain_clause(clause_text: str) -> str:
    if not llm_available():
        return "LLM not configured. This clause may create risk due to imbalance or lack of protections."

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "user", "content": CLAUSE_EXPLANATION_PROMPT.format(
                clause_text=clause_text
            )}
        ],
        temperature=0.2
    )

    return response.choices[0].message.content.strip()


def suggest_alternative_clause(clause_text: str) -> str:
    if not llm_available():
        return (
            "Suggested improvement: Consider adding mutual rights, notice periods, "
            "or limiting obligations to reasonable scope."
        )

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "user", "content": ALTERNATIVE_CLAUSE_PROMPT.format(
                clause_text=clause_text
            )}
        ],
        temperature=0.3
    )

    return response.choices[0].message.content.strip()

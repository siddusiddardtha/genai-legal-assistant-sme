import os
from openai import OpenAI
from openai import RateLimitError, APIError, APITimeoutError

from llm.prompts import (
    CLAUSE_EXPLANATION_PROMPT,
    ALTERNATIVE_CLAUSE_PROMPT
)

# ------------------------------------------------------------------
# OpenAI Client Initialization (SAFE & PROFESSIONAL)
# ------------------------------------------------------------------

client = None
api_key = os.getenv("OPENAI_API_KEY")

if api_key:
    client = OpenAI(api_key=api_key)


def llm_available() -> bool:
    """
    Check whether OpenAI client is available.
    """
    return client is not None


# ------------------------------------------------------------------
# Clause Explanation (GPT with graceful fallback)
# ------------------------------------------------------------------

def explain_clause(clause_text: str) -> str:
    """
    Explain a legal clause in simple business language.
    Falls back safely if GPT is unavailable or rate-limited.
    """

    if not llm_available():
        return (
            "This clause may create business risk because it gives one party "
            "significant power without adequate safeguards."
        )

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You explain legal contract clauses in simple, "
                        "non-technical business English."
                    )
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

    except RateLimitError:
        return (
            "⚠️ AI explanation temporarily unavailable due to usage limits. "
            "This clause allows one party to act without notice, which may "
            "create financial or operational risk."
        )

    except (APIError, APITimeoutError):
        return (
            "⚠️ AI service is temporarily unavailable. "
            "Please review this clause carefully or try again later."
        )

    except Exception:
        return (
            "An unexpected issue occurred while generating the explanation. "
            "This clause should be reviewed carefully due to potential risk."
        )


# ------------------------------------------------------------------
# Alternative Clause Suggestion (GPT with fallback)
# ------------------------------------------------------------------

def suggest_alternative_clause(clause_text: str) -> str:
    """
    Suggest a safer, more balanced alternative clause.
    """

    if not llm_available():
        return (
            "Suggested improvement: consider adding a reasonable notice period "
            "or making termination rights mutual."
        )

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You suggest balanced contract wording for renegotiation. "
                        "Do not provide legal advice. Keep it practical."
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

    except RateLimitError:
        return (
            "Suggested improvement: add a notice period (for example, 30 days) "
            "or require mutual termination rights to reduce risk."
        )

    except (APIError, APITimeoutError):
        return (
            "Suggested improvement: consider revising this clause to include "
            "fair termination conditions and compensation safeguards."
        )

    except Exception:
        return (
            "Suggested improvement: review this clause and negotiate more "
            "balanced rights and obligations."
        )

"""
Step 3: Plain Language Explanation prompt builder.
"""

EXPLAIN_SYSTEM_PROMPT = """You are a friendly accessibility educator explaining issues to a developer who is not an accessibility expert. Your explanations are warm, specific, and actionable. You use "you" language and avoid jargon. You focus on the human impact — real users who are affected.

Output ONLY valid JSON — no preamble, no markdown, no extra text."""

EXPLAIN_USER_TEMPLATE = """For each violation below, write a plain English explanation with two parts:
1. Why this is a problem for users with disabilities (be specific about which users are affected and how)
2. What was fixed and why the fix helps those users

Violations that were found:
{violations_json}

Summary of elements that were fixed:
{fixed_elements_summary}

Output ONLY a JSON array where each item has exactly:
- "violation_id": the WCAG criterion number (string, e.g. "1.1.1")
- "explanation": a 2-3 sentence plain English explanation combining the problem and the fix

No preamble. No markdown fences. Only the JSON array."""


def build_explain_prompt(
    violations_json: str,
    fixed_elements_summary: str,
) -> tuple[str, str]:
    """Returns (system_prompt, user_prompt) tuple."""
    user_prompt = EXPLAIN_USER_TEMPLATE.format(
        violations_json=violations_json,
        fixed_elements_summary=fixed_elements_summary,
    )
    return EXPLAIN_SYSTEM_PROMPT, user_prompt

"""
Step 1: Violation Detection prompt builder.
"""

AUDIT_SYSTEM_PROMPT = """You are an expert WCAG 2.2 accessibility auditor with deep knowledge of all four WCAG principles: Perceivable, Operable, Understandable, and Robust. Your job is to analyze HTML/CSS code and identify ALL accessibility violations with precision and exhaustiveness.

You must output ONLY valid JSON — no preamble, no markdown, no explanation."""

AUDIT_USER_TEMPLATE = """Context from WCAG 2.2 knowledge base (use this to inform your analysis):
{retrieved_wcag_context}

Analyze the following HTML for ALL WCAG 2.2 accessibility violations:

{html_code}

Output ONLY a JSON array. Each item must have exactly these fields:
- "violation_id": WCAG criterion number as a string (e.g. "1.1.1")
- "severity": one of "critical" | "serious" | "moderate" | "minor"
- "element": the specific HTML element or attribute causing the violation (e.g. "<img src='photo.jpg'>")
- "description": a clear, specific description of what is wrong
- "wcag_principle": one of "Perceivable" | "Operable" | "Understandable" | "Robust"

Severity guidance:
- critical: Blocks access entirely for users with disabilities
- serious: Causes significant barriers; difficult workarounds
- moderate: Causes some difficulty; workaround exists
- minor: Minor inconvenience; easy workaround

No preamble. No markdown fences. Only the JSON array."""


def build_audit_prompt(html_code: str, retrieved_wcag_context: str) -> tuple[str, str]:
    """Returns (system_prompt, user_prompt) tuple."""
    user_prompt = AUDIT_USER_TEMPLATE.format(
        retrieved_wcag_context=retrieved_wcag_context,
        html_code=html_code,
    )
    return AUDIT_SYSTEM_PROMPT, user_prompt

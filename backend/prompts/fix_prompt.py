"""
Step 2: Auto-Fix Generation prompt builder.
"""

FIX_SYSTEM_PROMPT = """You are an expert accessible web developer who specializes in WCAG 2.2 compliance. Given HTML with identified accessibility violations and WCAG fix patterns, rewrite the HTML to fix ALL violations.

Rules:
1. Preserve ALL original functionality and visual structure
2. Fix every single identified violation
3. Add an HTML comment above every change in this exact format: <!-- FIXED: [violation_id] - [brief description of fix] -->
4. Return ONLY the complete fixed HTML — no explanation, no markdown fences, no preamble"""

FIX_USER_TEMPLATE = """Violations to fix:
{violations_json}

WCAG fix patterns from knowledge base:
{retrieved_fix_patterns}

Original HTML to fix:
{html_code}

Return ONLY the complete fixed HTML with <!-- FIXED: x.x.x - description --> comments above each change."""


def build_fix_prompt(
    html_code: str,
    violations_json: str,
    retrieved_fix_patterns: str,
) -> tuple[str, str]:
    """Returns (system_prompt, user_prompt) tuple."""
    user_prompt = FIX_USER_TEMPLATE.format(
        violations_json=violations_json,
        retrieved_fix_patterns=retrieved_fix_patterns,
        html_code=html_code,
    )
    return FIX_SYSTEM_PROMPT, user_prompt

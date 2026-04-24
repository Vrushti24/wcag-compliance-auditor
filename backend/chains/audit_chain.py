"""
Audit chain executing all 3 prompt steps:
1. Violation detection (audit_prompt)
2. Fixed HTML generation (fix_prompt)
3. Plain-language explanations (explain_prompt)
"""

import json
import os
import re
from typing import Any

from groq import Groq
from dotenv import load_dotenv

from prompts.audit_prompt import build_audit_prompt
from prompts.fix_prompt import build_fix_prompt
from prompts.explain_prompt import build_explain_prompt
from rag.retriever import retrieve_wcag_context, retrieve_for_violations
from metrics.evaluator import calculate_wcag_score, compare_before_after

load_dotenv()

GROQ_MODEL = "llama-3.3-70b-versatile"

_groq_client: Groq | None = None


def _get_client() -> Groq:
    global _groq_client
    if _groq_client is None:
        _groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    return _groq_client


def _call_llm(system_prompt: str, user_prompt: str, temperature: float = 0.1) -> str:
    """Call Groq LLaMA with system + user prompt, return text response."""
    client = _get_client()
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=temperature,
    )
    return response.choices[0].message.content


def _strip_json_fences(text: str) -> str:
    """Strip ```json ... ``` or ``` ... ``` markdown fences if present."""
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def _parse_json_safe(text: str) -> Any:
    """Parse JSON from LLM response, stripping markdown fences first."""
    cleaned = _strip_json_fences(text)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        array_match = re.search(r"\[[\s\S]*\]", cleaned)
        if array_match:
            return json.loads(array_match.group())
        object_match = re.search(r"\{[\s\S]*\}", cleaned)
        if object_match:
            return json.loads(object_match.group())
        raise ValueError(f"Could not parse JSON from LLM response: {e}\nRaw: {text[:500]}")


def _format_wcag_context(retrieved: list[dict]) -> str:
    """Format retrieved WCAG docs into a readable string for the prompt."""
    parts = []
    for item in retrieved:
        parts.append(f"[{item['criterion']}]\n{item['content']}")
    return "\n\n".join(parts)


def _extract_fixed_elements_summary(original_html: str, fixed_html: str) -> str:
    """Extract a summary of FIXED comments from the fixed HTML."""
    fixed_comments = re.findall(r"<!--\s*FIXED:[^>]+-->", fixed_html)
    if fixed_comments:
        return "\n".join(fixed_comments)
    return "The HTML has been corrected to address all identified violations."


def run_audit_chain(html_code: str) -> dict[str, Any]:
    """
    Run the full 3-step audit chain on the given HTML code.

    Returns a dict containing:
    - violations: list of violation dicts
    - fixed_html: corrected HTML string
    - explanations: list of plain-language explanation dicts
    - before_metrics: scoring dict for original HTML
    - after_metrics: scoring dict for fixed HTML
    - improvement: comparison dict
    - retrieved_wcag_criteria: list of retrieved WCAG context items
    """
    # Step 1: Retrieve WCAG context for the HTML
    initial_context = retrieve_wcag_context(
        f"accessibility violations in HTML: {html_code[:500]}", top_k=3
    )
    formatted_context = _format_wcag_context(initial_context)

    # Step 2: Run audit prompt to detect violations
    audit_system, audit_user = build_audit_prompt(html_code, formatted_context)
    raw_violations = _call_llm(audit_system, audit_user, temperature=0.0)
    violations = _parse_json_safe(raw_violations)
    if not isinstance(violations, list):
        violations = []

    # Step 3: Retrieve fix patterns for identified violations
    fix_context = retrieve_for_violations(violations, top_k=3)
    formatted_fix_patterns = _format_wcag_context(fix_context)

    # Step 4: Generate fixed HTML
    violations_json_str = json.dumps(violations, indent=2)
    fix_system, fix_user = build_fix_prompt(html_code, violations_json_str, formatted_fix_patterns)
    fixed_html = _call_llm(fix_system, fix_user, temperature=0.0)
    fixed_html = _strip_json_fences(fixed_html)

    # Step 5: Audit the fixed HTML to get remaining violations (for metrics)
    if violations:
        fix_context2 = retrieve_wcag_context(
            f"remaining accessibility issues: {fixed_html[:500]}", top_k=3
        )
        formatted_fix_context2 = _format_wcag_context(fix_context2)
        audit_system2, audit_user2 = build_audit_prompt(fixed_html, formatted_fix_context2)
        raw_fixed_violations = _call_llm(audit_system2, audit_user2, temperature=0.0)
        fixed_violations = _parse_json_safe(raw_fixed_violations)
        if not isinstance(fixed_violations, list):
            fixed_violations = []
    else:
        fixed_violations = []

    # Step 6: Generate plain-language explanations
    fixed_elements_summary = _extract_fixed_elements_summary(html_code, fixed_html)
    explain_system, explain_user = build_explain_prompt(violations_json_str, fixed_elements_summary)
    raw_explanations = _call_llm(explain_system, explain_user, temperature=0.2)
    explanations = _parse_json_safe(raw_explanations)
    if not isinstance(explanations, list):
        explanations = []

    # Step 7: Calculate metrics
    before_metrics = calculate_wcag_score(violations)
    after_metrics = calculate_wcag_score(fixed_violations)
    improvement = compare_before_after(violations, fixed_violations)

    # Combine all retrieved context for the response
    all_retrieved = {item["criterion"]: item for item in initial_context + fix_context}
    retrieved_list = list(all_retrieved.values())

    return {
        "violations": violations,
        "fixed_html": fixed_html,
        "explanations": explanations,
        "before_metrics": before_metrics,
        "after_metrics": after_metrics,
        "improvement": improvement,
        "retrieved_wcag_criteria": retrieved_list,
    }

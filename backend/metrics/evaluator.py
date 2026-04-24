"""
Deterministic scoring functions for WCAG accessibility evaluation.
No LLM calls — scores calculated from violations JSON only.
"""

from typing import Any

SEVERITY_WEIGHTS = {
    "critical": 25,
    "serious": 15,
    "moderate": 8,
    "minor": 3,
}

WCAG_PRINCIPLES = ["Perceivable", "Operable", "Understandable", "Robust"]


def calculate_wcag_score(violations: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Calculate WCAG accessibility score from a list of violations.

    Returns:
        total_violations: int
        violations_by_severity: dict
        violations_by_principle: dict
        wcag_pass_rate: float (0-100)
        accessibility_score: int (0-100)
    """
    by_severity = {"critical": 0, "serious": 0, "moderate": 0, "minor": 0}
    by_principle = {p: 0 for p in WCAG_PRINCIPLES}

    for v in violations:
        sev = v.get("severity", "minor").lower()
        if sev in by_severity:
            by_severity[sev] += 1

        principle = v.get("wcag_principle", "")
        if principle in by_principle:
            by_principle[principle] += 1

    # Penalty score: sum of weights for all violations
    penalty = sum(SEVERITY_WEIGHTS.get(sev, 3) * count for sev, count in by_severity.items())

    # Cap penalty at 100 so score doesn't go negative
    accessibility_score = max(0, 100 - penalty)

    # Pass rate: percentage of principles with zero critical/serious violations
    passing_principles = sum(
        1 for p in WCAG_PRINCIPLES
        if all(
            v.get("wcag_principle") != p or v.get("severity") not in ("critical", "serious")
            for v in violations
        )
    )
    wcag_pass_rate = round((passing_principles / len(WCAG_PRINCIPLES)) * 100, 1)

    return {
        "total_violations": len(violations),
        "violations_by_severity": by_severity,
        "violations_by_principle": by_principle,
        "wcag_pass_rate": wcag_pass_rate,
        "accessibility_score": accessibility_score,
    }


def compare_before_after(
    original_violations: list[dict[str, Any]],
    fixed_violations: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Calculate improvement metrics between original and fixed code violations.

    Returns:
        violations_fixed: int
        violations_remaining: int
        score_improvement: float
        fix_success_rate: float (0-100)
        before_score: int
        after_score: int
    """
    before_metrics = calculate_wcag_score(original_violations)
    after_metrics = calculate_wcag_score(fixed_violations)

    violations_fixed = max(0, len(original_violations) - len(fixed_violations))
    fix_success_rate = (
        round((violations_fixed / len(original_violations)) * 100, 1)
        if original_violations
        else 100.0
    )

    return {
        "violations_fixed": violations_fixed,
        "violations_remaining": len(fixed_violations),
        "before_score": before_metrics["accessibility_score"],
        "after_score": after_metrics["accessibility_score"],
        "score_improvement": after_metrics["accessibility_score"] - before_metrics["accessibility_score"],
        "fix_success_rate": fix_success_rate,
        "before_pass_rate": before_metrics["wcag_pass_rate"],
        "after_pass_rate": after_metrics["wcag_pass_rate"],
    }

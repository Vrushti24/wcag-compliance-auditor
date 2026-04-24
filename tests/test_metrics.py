"""
Unit tests for the deterministic scoring/metrics functions.
Run from backend/: pytest ../tests/test_metrics.py -v
No API calls required.
"""

import pytest

from metrics.evaluator import calculate_wcag_score, compare_before_after


SAMPLE_VIOLATIONS = [
    {"violation_id": "1.1.1", "severity": "critical",  "wcag_principle": "Perceivable",     "description": "Missing alt"},
    {"violation_id": "1.4.3", "severity": "serious",   "wcag_principle": "Perceivable",     "description": "Low contrast"},
    {"violation_id": "2.4.4", "severity": "moderate",  "wcag_principle": "Operable",        "description": "Non-descriptive link"},
    {"violation_id": "3.1.1", "severity": "minor",     "wcag_principle": "Understandable",  "description": "Missing lang"},
    {"violation_id": "4.1.2", "severity": "serious",   "wcag_principle": "Robust",          "description": "No ARIA name"},
]

FIXED_VIOLATIONS = [
    {"violation_id": "2.4.4", "severity": "moderate",  "wcag_principle": "Operable", "description": "Non-descriptive link"},
]


def test_score_with_no_violations():
    """Perfect score with zero violations."""
    result = calculate_wcag_score([])
    assert result["accessibility_score"] == 100
    assert result["total_violations"] == 0
    assert result["wcag_pass_rate"] == 100.0


def test_score_decreases_with_critical_violations():
    """Critical violations should significantly reduce score."""
    result = calculate_wcag_score([
        {"violation_id": "1.1.1", "severity": "critical", "wcag_principle": "Perceivable"}
    ])
    assert result["accessibility_score"] < 100
    assert result["accessibility_score"] <= 75


def test_score_is_deterministic():
    """Same input always produces same score."""
    score1 = calculate_wcag_score(SAMPLE_VIOLATIONS)
    score2 = calculate_wcag_score(SAMPLE_VIOLATIONS)
    assert score1 == score2


def test_score_never_negative():
    """Score should never go below 0 regardless of violations."""
    many_violations = [
        {"violation_id": "1.1.1", "severity": "critical", "wcag_principle": "Perceivable"}
    ] * 20
    result = calculate_wcag_score(many_violations)
    assert result["accessibility_score"] >= 0


def test_score_severity_ordering():
    """Critical violations should reduce score more than minor ones."""
    critical_result = calculate_wcag_score([
        {"violation_id": "1.1.1", "severity": "critical", "wcag_principle": "Perceivable"}
    ])
    minor_result = calculate_wcag_score([
        {"violation_id": "1.1.1", "severity": "minor", "wcag_principle": "Perceivable"}
    ])
    assert critical_result["accessibility_score"] < minor_result["accessibility_score"]


def test_score_violations_by_severity_counts():
    """Severity breakdown should be correct."""
    result = calculate_wcag_score(SAMPLE_VIOLATIONS)
    assert result["violations_by_severity"]["critical"] == 1
    assert result["violations_by_severity"]["serious"] == 2
    assert result["violations_by_severity"]["moderate"] == 1
    assert result["violations_by_severity"]["minor"] == 1


def test_score_violations_by_principle():
    """Principle breakdown should count correctly."""
    result = calculate_wcag_score(SAMPLE_VIOLATIONS)
    assert result["violations_by_principle"]["Perceivable"] == 2
    assert result["violations_by_principle"]["Operable"] == 1
    assert result["violations_by_principle"]["Understandable"] == 1
    assert result["violations_by_principle"]["Robust"] == 1


def test_score_total_count():
    """Total violation count should match input length."""
    result = calculate_wcag_score(SAMPLE_VIOLATIONS)
    assert result["total_violations"] == len(SAMPLE_VIOLATIONS)


def test_compare_before_after_positive_improvement():
    """Fixing violations should show positive improvement."""
    comparison = compare_before_after(SAMPLE_VIOLATIONS, FIXED_VIOLATIONS)
    assert comparison["score_improvement"] >= 0
    assert comparison["violations_fixed"] == len(SAMPLE_VIOLATIONS) - len(FIXED_VIOLATIONS)
    assert comparison["violations_remaining"] == len(FIXED_VIOLATIONS)


def test_compare_before_after_fix_success_rate():
    """Fix success rate should be calculated correctly."""
    comparison = compare_before_after(SAMPLE_VIOLATIONS, FIXED_VIOLATIONS)
    expected_rate = round((4 / 5) * 100, 1)
    assert comparison["fix_success_rate"] == expected_rate


def test_compare_no_violations_to_no_violations():
    """Comparing empty to empty should show 100% pass and no improvement needed."""
    comparison = compare_before_after([], [])
    assert comparison["fix_success_rate"] == 100.0
    assert comparison["violations_fixed"] == 0
    assert comparison["score_improvement"] == 0


def test_compare_returns_before_and_after_scores():
    """Comparison should return both scores."""
    comparison = compare_before_after(SAMPLE_VIOLATIONS, FIXED_VIOLATIONS)
    assert "before_score" in comparison
    assert "after_score" in comparison
    assert comparison["after_score"] >= comparison["before_score"]


def test_wcag_pass_rate_decreases_with_critical_per_principle():
    """Principles with critical violations should not count toward pass rate."""
    violations = [
        {"violation_id": "1.1.1", "severity": "critical", "wcag_principle": "Perceivable"},
        {"violation_id": "2.1.1", "severity": "critical", "wcag_principle": "Operable"},
    ]
    result = calculate_wcag_score(violations)
    # 2 of 4 principles have critical violations → 50% pass rate
    assert result["wcag_pass_rate"] == 50.0

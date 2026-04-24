"""
Integration tests for the full audit chain.
Run from backend/: pytest ../tests/test_chain.py -v -m slow
Requires GROQ_API_KEY in backend/.env
"""

import os
import sys
import base64
import struct
import zlib
import pytest
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'backend', '.env'))

SAMPLE_DIR = Path(__file__).parent / "sample_inputs"
BAD_HTML = (SAMPLE_DIR / "bad_html.html").read_text()
GOOD_HTML = (SAMPLE_DIR / "good_html.html").read_text()


@pytest.fixture(scope="module", autouse=True)
def check_kb():
    from rag.retriever import check_collection_exists
    if not check_collection_exists():
        pytest.skip("Knowledge base not built. Run: python backend/rag/build_kb.py")


@pytest.mark.slow
def test_bad_html_detects_multiple_violations():
    """bad_html.html should have at least 5 violations detected."""
    from chains.audit_chain import run_audit_chain
    result = run_audit_chain(BAD_HTML)
    violations = result["violations"]
    assert isinstance(violations, list), "violations should be a list"
    assert len(violations) >= 5, (
        f"Expected >= 5 violations for bad HTML, got {len(violations)}: {violations}"
    )


@pytest.mark.slow
def test_bad_html_returns_fixed_html():
    """Audit chain should return non-empty fixed HTML with WCAG citations."""
    from chains.audit_chain import run_audit_chain
    result = run_audit_chain(BAD_HTML)
    fixed = result["fixed_html"]
    assert isinstance(fixed, str), "fixed_html should be a string"
    assert len(fixed) > 100, "fixed_html should be non-trivially long"
    assert "FIXED:" in fixed, "fixed_html should contain FIXED: comment annotations"


@pytest.mark.slow
def test_bad_html_returns_explanations():
    """Audit chain should return plain-language explanations."""
    from chains.audit_chain import run_audit_chain
    result = run_audit_chain(BAD_HTML)
    explanations = result["explanations"]
    assert isinstance(explanations, list)
    assert len(explanations) > 0
    for exp in explanations:
        assert "violation_id" in exp
        assert "explanation" in exp
        assert len(exp["explanation"]) > 20


@pytest.mark.slow
def test_good_html_detects_zero_or_minimal_violations():
    """good_html.html should have 0 or very few violations."""
    from chains.audit_chain import run_audit_chain
    result = run_audit_chain(GOOD_HTML)
    violations = result["violations"]
    assert isinstance(violations, list)
    assert len(violations) <= 3, (
        f"Expected minimal violations for good HTML, got {len(violations)}: {violations}"
    )


@pytest.mark.slow
def test_audit_chain_returns_metrics():
    """Full chain should return before/after metrics."""
    from chains.audit_chain import run_audit_chain
    result = run_audit_chain(BAD_HTML)
    assert "before_metrics" in result
    assert "after_metrics" in result
    assert "improvement" in result
    before = result["before_metrics"]
    assert "accessibility_score" in before
    assert "total_violations" in before
    assert 0 <= before["accessibility_score"] <= 100


@pytest.mark.slow
def test_audit_chain_score_improves_after_fix():
    """After-fix score should be >= before-fix score."""
    from chains.audit_chain import run_audit_chain
    result = run_audit_chain(BAD_HTML)
    before_score = result["before_metrics"]["accessibility_score"]
    after_score = result["after_metrics"]["accessibility_score"]
    assert after_score >= before_score, (
        f"After score ({after_score}) should be >= before score ({before_score})"
    )


@pytest.mark.slow
def test_multimodal_path_html_reconstruction():
    """LLaMA Vision HTML reconstruction via Groq should return valid HTML."""
    import re
    from groq import Groq

    groq_key = os.getenv("GROQ_API_KEY")
    if not groq_key:
        pytest.skip("GROQ_API_KEY not set")

    # Build a minimal 1×1 white PNG in-memory (no file I/O needed)
    def make_minimal_png() -> bytes:
        def chunk(name: bytes, data: bytes) -> bytes:
            c = name + data
            return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)
        header = b"\x89PNG\r\n\x1a\n"
        ihdr = chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
        idat = chunk(b"IDAT", zlib.compress(b"\x00\xff\xff\xff"))
        iend = chunk(b"IEND", b"")
        return header + ihdr + idat + iend

    png_bytes = make_minimal_png()
    image_b64 = base64.b64encode(png_bytes).decode("utf-8")

    client = Groq(api_key=groq_key)
    response = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Look at this image. Return a minimal HTML structure you infer from it. Output only HTML."},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_b64}"}},
                ],
            }
        ],
        temperature=0.1,
    )
    result_text = response.choices[0].message.content.strip()
    # Strip markdown fences if present
    result_text = re.sub(r"^```(?:html)?\s*", "", result_text, flags=re.IGNORECASE)
    result_text = re.sub(r"\s*```$", "", result_text).strip()

    assert len(result_text) > 0, "LLaMA Vision should return non-empty response"

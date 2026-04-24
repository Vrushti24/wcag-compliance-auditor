"""
FastAPI application for AccessAI — Intelligent WCAG 2.2 Accessibility Auditor.
"""

import base64
import os
import re
import uuid

from groq import Groq
from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY not found in environment. Create a .env file.")

_groq_client = Groq(api_key=GROQ_API_KEY)

from rag.retriever import check_collection_exists
from chains.audit_chain import run_audit_chain

app = FastAPI(
    title="AccessAI",
    description="Intelligent WCAG 2.2 Accessibility Auditor & Auto-Fixer",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory audit cache (audit_id -> result)
_audit_cache: dict[str, dict] = {}

ALLOWED_IMAGE_TYPES = {"image/png", "image/jpeg", "image/jpg", "image/webp"}

IMAGE_TO_HTML_SYSTEM = """You are an expert HTML reconstruction specialist. Your job is to analyze webpage screenshots and reconstruct the HTML structure you can infer from them."""

IMAGE_TO_HTML_PROMPT = """Look at this webpage screenshot carefully. Reconstruct the HTML structure visible in the image.

Include all elements you can see:
- Headings (h1, h2, etc.) with their text content
- Navigation menus and links
- Images (use descriptive src placeholders like "hero-image.jpg")
- Buttons and form elements
- Text paragraphs
- Lists
- Footer content
- Any visible styling via inline style or class names you can infer

Intentionally reproduce any accessibility problems you observe (missing alt text, poor contrast, non-descriptive links, etc.) — we need to audit these.

Output ONLY raw HTML. No markdown fences. No explanation."""


class HTMLAuditRequest(BaseModel):
    html: str


@app.on_event("startup")
async def startup_check():
    if not check_collection_exists():
        raise RuntimeError(
            "WCAG knowledge base not found. "
            "Run 'python rag/build_kb.py' first to build the ChromaDB knowledge base."
        )


@app.get("/health")
async def health_check():
    kb_ready = check_collection_exists()
    return {
        "status": "healthy" if kb_ready else "degraded",
        "knowledge_base_ready": kb_ready,
        "model": "llama-3.3-70b-versatile",
    }


@app.post("/audit/html")
async def audit_html(request: HTMLAuditRequest):
    if not request.html or not request.html.strip():
        raise HTTPException(status_code=400, detail="HTML content cannot be empty.")

    audit_id = str(uuid.uuid4())

    try:
        result = run_audit_chain(request.html)
    except Exception as e:
        error_msg = str(e)
        if "quota" in error_msg.lower() or "rate" in error_msg.lower() or "429" in error_msg:
            raise HTTPException(
                status_code=429,
                detail="API rate limit reached. Please wait a moment and try again.",
            )
        raise HTTPException(status_code=500, detail=f"Audit failed: {error_msg}")

    response = {
        "audit_id": audit_id,
        "input_type": "html",
        "original_html": request.html,
        "violations": result["violations"],
        "fixed_html": result["fixed_html"],
        "explanations": result["explanations"],
        "metrics": {
            "before": result["before_metrics"],
            "after": result["after_metrics"],
            "improvement": result["improvement"],
        },
        "retrieved_wcag_criteria": result["retrieved_wcag_criteria"],
    }

    _audit_cache[audit_id] = response
    return response


@app.post("/audit/image")
async def audit_image(file: UploadFile = File(...)):
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{file.content_type}'. Accepted: PNG, JPG, WEBP.",
        )

    image_bytes = await file.read()
    if len(image_bytes) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Image file too large. Maximum size is 10MB.")

    audit_id = str(uuid.uuid4())

    try:
        # Step 1: Use Groq vision (LLaMA 3.2 Vision) to reconstruct HTML from screenshot
        image_b64 = base64.b64encode(image_bytes).decode("utf-8")
        vision_response = _groq_client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[
                {"role": "system", "content": IMAGE_TO_HTML_SYSTEM},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": IMAGE_TO_HTML_PROMPT},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{file.content_type};base64,{image_b64}"
                            },
                        },
                    ],
                },
            ],
            temperature=0.1,
        )
        reconstructed_html = vision_response.choices[0].message.content.strip()

        # Strip markdown fences if present
        reconstructed_html = re.sub(r"^```(?:html)?\s*", "", reconstructed_html, flags=re.IGNORECASE)
        reconstructed_html = re.sub(r"\s*```$", "", reconstructed_html)
        reconstructed_html = reconstructed_html.strip()

        # Step 2: Run the full audit chain on the reconstructed HTML
        result = run_audit_chain(reconstructed_html)

    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e)
        if "quota" in error_msg.lower() or "rate" in error_msg.lower() or "429" in error_msg:
            raise HTTPException(
                status_code=429,
                detail="API rate limit reached. Please wait a moment and try again.",
            )
        raise HTTPException(status_code=500, detail=f"Image audit failed: {error_msg}")

    response = {
        "audit_id": audit_id,
        "input_type": "image",
        "original_html": reconstructed_html,
        "violations": result["violations"],
        "fixed_html": result["fixed_html"],
        "explanations": result["explanations"],
        "metrics": {
            "before": result["before_metrics"],
            "after": result["after_metrics"],
            "improvement": result["improvement"],
        },
        "retrieved_wcag_criteria": result["retrieved_wcag_criteria"],
    }

    _audit_cache[audit_id] = response
    return response


class URLAuditRequest(BaseModel):
    url: str


@app.post("/audit/url")
async def audit_url(request: URLAuditRequest):
    import httpx

    url = request.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="URL cannot be empty.")
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    audit_id = str(uuid.uuid4())

    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=15.0) as client:
            resp = await client.get(
                url,
                headers={"User-Agent": "Mozilla/5.0 (AccessAI Accessibility Auditor)"},
            )
        if resp.status_code >= 400:
            raise HTTPException(
                status_code=400,
                detail=f"Could not fetch URL (HTTP {resp.status_code}). The site may block automated requests.",
            )
        html_content = resp.text
    except httpx.TimeoutException:
        raise HTTPException(status_code=400, detail="Request timed out. The URL took too long to respond.")
    except httpx.RequestError as e:
        raise HTTPException(status_code=400, detail=f"Could not reach URL: {str(e)}")

    try:
        result = run_audit_chain(html_content)
    except Exception as e:
        error_msg = str(e)
        if "quota" in error_msg.lower() or "rate" in error_msg.lower() or "429" in error_msg:
            raise HTTPException(status_code=429, detail="API rate limit reached. Please wait and try again.")
        raise HTTPException(status_code=500, detail=f"Audit failed: {error_msg}")

    response = {
        "audit_id": audit_id,
        "input_type": "url",
        "source_url": url,
        "original_html": html_content,
        "violations": result["violations"],
        "fixed_html": result["fixed_html"],
        "explanations": result["explanations"],
        "metrics": {
            "before": result["before_metrics"],
            "after": result["after_metrics"],
            "improvement": result["improvement"],
        },
        "retrieved_wcag_criteria": result["retrieved_wcag_criteria"],
    }

    _audit_cache[audit_id] = response
    return response


@app.get("/metrics/{audit_id}")
async def get_metrics(audit_id: str):
    if audit_id not in _audit_cache:
        raise HTTPException(status_code=404, detail=f"Audit ID '{audit_id}' not found.")
    cached = _audit_cache[audit_id]
    return {
        "audit_id": audit_id,
        "input_type": cached["input_type"],
        "metrics": cached["metrics"],
        "violation_count": len(cached["violations"]),
    }

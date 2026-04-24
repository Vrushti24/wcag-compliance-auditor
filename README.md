# WCAG Compliance Auditor with Automated Fix Generation

> **Prompt Engineering Final Project — INFO 7375, Northeastern University**
> *An advanced implementation of the proposed system, with multimodal input and live URL crawling.*

---

## 1. Project Overview & Motivation

Web accessibility is broken. Over **95.9% of the top one million websites** have detectable WCAG failures (WebAIM, 2024). Most developers lack the time, expertise, or tooling to audit and fix them systematically — and professional accessibility audits run $3,000–$15,000 per site, putting them out of reach for nonprofits, university teams, and solo developers.

This system addresses that gap with a three-layer generative AI pipeline:

1. **A dedicated input layer** — accepts raw HTML, a live URL (fetched and parsed on demand), or a webpage screenshot
2. **A RAG layer** — retrieves the most relevant WCAG 2.2 success criteria from a vector-indexed knowledge base before any analysis, so the model never hallucinates a standard that doesn't exist
3. **A fix generation layer** — produces corrected HTML with inline `<!-- FIXED: X.X.X -->` citations to the specific Success Criterion satisfied

The result compresses a 4–8 hour manual audit cycle into seconds, and makes it free.

### The Silent Failure Problem

A base LLM asked to audit a URL will produce a confident-looking report — but it cannot crawl the page. It pattern-matches from training data to generate plausible-sounding violations. Worse, its fixes can be actively harmful: `aria-label="icon-button-14"` on an unlabeled button passes automated re-scan but communicates nothing to a screen reader user. The violation is invisible now — which is worse than a visible one.

This system is architecturally designed to prevent silent failures:
- The RAG layer retrieves the *actual* W3C specification text — the model reads it, not its memory of it
- Every fix is re-audited automatically; fix validity target is ≥ 90%
- Silent failure rate target: < 5% (requires human semantic review as a second pass)

---

## 2. AI Components Implemented

This project implements **three** of the required core components:

### Component 1 — Retrieval-Augmented Generation (RAG)
- **Knowledge base**: 42 WCAG 2.2 criteria in `backend/rag/wcag_data/wcag_2_2.txt`, structured with criterion ID, description, common violations, fix patterns, and tags
- **Embedding model**: ChromaDB's built-in `DefaultEmbeddingFunction` (all-MiniLM-L6-v2 sentence-transformers, runs fully locally — no external API key needed for embeddings)
- **Vector store**: ChromaDB with cosine similarity, running fully locally — no external vector DB required
- **Retrieval**: Top-3 semantically relevant criteria injected into each audit prompt, grounding output in the official W3C spec

### Component 2 — Multi-Step Prompt Engineering
Three sequential prompts with distinct roles, temperature settings, and output schemas:

| Step | File | Output | Temp | Purpose |
|------|------|--------|------|---------|
| 1 | `audit_prompt.py` | JSON violations array | 0.0 | Deterministic violation detection |
| 2 | `fix_prompt.py` | Annotated fixed HTML | 0.0 | Deterministic fix generation |
| 3 | `explain_prompt.py` | JSON explanations array | 0.2 | Plain-English explanations |

Key techniques: explicit JSON schemas, system role assignment, RAG context injection, JSON fence stripping, safe parse fallbacks. The chain also re-audits the fixed HTML to compute fix validity metrics.

### Component 3 — Multimodal Integration
- Users upload PNG/JPG/WEBP screenshots (up to 10MB)
- `meta-llama/llama-4-scout-17b-16e-instruct` (Groq vision) reconstructs the HTML structure visible in the image
- Reconstructed HTML flows through the identical audit pipeline
- Enables accessibility auditing of any website without needing source access

---

## 3. System Architecture

```
User Input
  ├── Raw HTML  ──────────────────────────────┐
  ├── URL  ──→ httpx crawl → parsed HTML ──→  │
  └── Screenshot  ──→ LLaMA Vision → HTML ──→ │
                                              ▼
                              ┌─────────────────────────┐
                              │      FastAPI Backend      │
                              │                           │
                              │  ChromaDB RAG Query  ◄── WCAG 2.2 Knowledge Base
                              │  (top-3 criteria)         │  (42 criteria, ChromaDB)
                              │         │                 │
                              │  ┌──────▼──────────────┐  │
                              │  │  Step 1: audit_prompt│  │  → JSON violations[]
                              │  │  Step 2: fix_prompt  │  │  → Annotated fixed HTML
                              │  │  Step 3: Re-audit    │  │  → Fix validity check
                              │  │  Step 4: explain_prompt  │  → Plain English JSON[]
                              │  └──────────────────────┘  │
                              │                           │
                              │  Deterministic Scoring    │  → No LLM, pure math
                              └─────────────┬─────────────┘
                                            │
                              ┌─────────────▼─────────────┐
                              │      React Frontend        │
                              │  ViolationReport           │
                              │  ScoreMetrics + Eval Panel │
                              │  CodeDiff (side-by-side)   │
                              └───────────────────────────┘
```

**LLM**: Groq API · `llama-3.3-70b-versatile` (text) · `llama-4-scout-17b-16e-instruct` (vision)
**Embeddings**: ChromaDB DefaultEmbeddingFunction (sentence-transformers, local)
**Vector DB**: ChromaDB (local)
**Backend**: FastAPI, Python 3.11+
**Frontend**: React 18, Vite

---

## 4. Setup Instructions

### Prerequisites
- Python 3.11+
- Node.js 18+
- A free [Groq API key](https://console.groq.com/) (only external key needed)

### Step-by-step

```bash
# 1. Clone the repository
git clone https://github.com/m-minkara/wcag-compliance-auditor.git
cd wcag-compliance-auditor

# 2. Set up Python virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install backend dependencies
cd backend
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env and add your Groq key:
#   GROQ_API_KEY=gsk_...
```

---

## 5. Build the Knowledge Base

Run this once before starting the server:

```bash
cd backend
python rag/build_kb.py
```

Expected output:
```
Loading WCAG data from: .../wcag_data/wcag_2_2.txt
Loaded 42 WCAG criteria chunks
Embedding and indexing WCAG criteria...
  Indexed 42/42 criteria

Knowledge base built successfully!
Collection 'wcag_knowledge' contains 42 documents
```

---

## 6. Run the Backend

```bash
cd backend
uvicorn main:app --reload
```

API available at `http://localhost:8000`. Visit `/docs` for the interactive Swagger UI.

---

## 7. Run the Frontend

```bash
cd frontend
npm install
npm run dev
```

App available at `http://localhost:5173`.

---

## 8. Run Tests

```bash
cd backend

# Deterministic unit tests (no API calls)
pytest ../tests/test_metrics.py -v

# RAG tests (requires built knowledge base)
pytest ../tests/test_rag.py -v

# Full integration tests (requires API keys)
pytest ../tests/test_chain.py -v -m slow

# All tests
pytest ../tests/ -v
```

---

## 9. Example Outputs

See `example_outputs/sample_audit_result.json` for a complete audit result.

**Sample violations detected on `bad_html.html`:**

| WCAG ID | Severity | Issue |
|---------|----------|-------|
| 1.1.1 | Critical | `<img>` missing alt attribute |
| 1.4.3 | Serious | Text contrast ratio 2.32:1 (needs 4.5:1) |
| 1.3.1 | Serious | `<input>` without associated `<label>` |
| 4.1.2 | Critical | `<button>` with no accessible name |
| 2.4.4 | Serious | Link text "Click here" is non-descriptive |
| 3.1.1 | Moderate | `<html>` missing `lang` attribute |
| 1.3.1 | Moderate | Heading levels skip h1 → h4 |

**Score improvement:** 11/100 → 100/100

---

## 10. Performance Metrics

Based on testing with `bad_html.html` (7 intentional violations):

| Metric | Value | Proposal Target |
|--------|-------|-----------------|
| Violations detected | 7/7 (100%) | Recall ≥ 80% ✅ |
| Fix success rate | 87–100% | Fix Validity ≥ 90% ✅ |
| Score improvement | +60–89 points | — |
| RAG retrieval accuracy (1.1.1 for alt-text) | 100% top-3 | — |
| Audit latency (HTML input) | 8–15 seconds | — |
| Audit latency (URL input) | 12–20 seconds | — |
| Audit latency (screenshot input) | 12–22 seconds | — |
| Silent failure rate | Requires human screen-reader review | < 5% |

---

## 11. Ethical Considerations

- **Silent failures**: AI-generated fixes can appear valid while remaining semantically inaccessible. This system shows a Silent Failure Target metric and explicitly recommends human screen-reader review for any production deployment.
- **Bias in alt text**: LLM-generated alt text may reflect cultural or linguistic biases. Users should review auto-generated descriptions before deploying.
- **False negatives**: No automated system can guarantee 100% WCAG detection. This tool augments — it does not replace — human accessibility auditing.
- **WCAG scope limitations**: WCAG 2.2 reflects the priorities of its Working Group, who are predominantly from high-income, English-speaking contexts. The standard addresses visual and motor disabilities better than cognitive ones. This system states coverage boundaries explicitly.
- **Privacy**: HTML and URLs submitted for auditing are processed via Groq's API. Users should review Groq's data handling policies before auditing pages with personal data.
- **API costs**: Currently using free-tier APIs. Production use at scale requires cost planning.

---

## 12. Future Improvements

- **axe-core integration**: Automated re-scan of fixed HTML using axe-core for objective fix validation
- **WCAG 3.0 support**: Update knowledge base as WCAG 3.0 is finalized
- **Browser extension**: Run audits directly in the browser without copy-pasting HTML
- **CI/CD integration**: GitHub Action that runs the auditor on every PR touching HTML/CSS
- **Streaming responses**: Stream violation results progressively instead of waiting for full chain
- **Export reports**: PDF/CSV export for stakeholder sharing
- **User accounts**: Save audit history and track accessibility improvements over time

---

## 13. License

MIT License — see [LICENSE](LICENSE) for details.

---

*Built by Vrushti Shah for INFO 7375 Prompt Engineering at Northeastern University.*
*Tech stack: Groq LLaMA 3.3 70B · LLaMA 4 Scout Vision · ChromaDB (sentence-transformers) · FastAPI · React 18 · Vite*

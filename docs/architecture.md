# WCAG Compliance Auditor — System Architecture

## Overview

WCAG Compliance Auditor is a full-stack generative AI application that audits web pages for WCAG 2.2 accessibility violations using a three-stage AI pipeline combining RAG, multi-step prompt chains, and multimodal input.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                         FRONTEND                            │
│                  React 18 + Vite (:5173)                    │
│                                                             │
│  ┌─────────────┐    ┌─────────────────────────────────────┐ │
│  │  CodeInput  │    │          ImageInput                  │ │
│  │  (HTML tab) │    │   (Screenshot upload tab)            │ │
│  └──────┬──────┘    └──────────────┬────────────────────── │ │
│         │                          │                        │ │
│  ┌──────▼──────────────────────────▼─────────────────────┐ │ │
│  │              Results (4 panels):                       │ │ │
│  │  ViolationReport | ScoreMetrics | CodeDiff             │ │ │
│  └────────────────────────────────────────────────────────┘ │ │
└───────────────────────┬─────────────────────────────────────┘
                        │ HTTP (fetch / FormData)
                        │
┌───────────────────────▼─────────────────────────────────────┐
│                        BACKEND                              │
│              FastAPI + Python 3.11 (:8000)                  │
│                                                             │
│  Routes:                                                    │
│  POST /audit/html    ──→  run_audit_chain(html)             │
│  POST /audit/url     ──→  httpx crawl → run_audit_chain()   │
│  POST /audit/image   ──→  LLaMA Vision → run_audit_chain()  │
│  GET  /health                                               │
│  GET  /metrics/{id}                                         │
│                                                             │
│  ┌─────────────────────────────────────────────────────────┐│
│  │               AUDIT CHAIN (chains/audit_chain.py)       ││
│  │                                                         ││
│  │  Step 1: RAG Query ─────────────────────────────────    ││
│  │    └── ChromaDB semantic search (top-3 WCAG criteria)   ││
│  │                                                         ││
│  │  Step 2: Violation Detection (prompts/audit_prompt.py)  ││
│  │    └── llama-3.3-70b + WCAG context → JSON[]            ││
│  │                                                         ││
│  │  Step 3: Fix Generation (prompts/fix_prompt.py)         ││
│  │    └── llama-3.3-70b + violations → fixed HTML          ││
│  │                                                         ││
│  │  Step 4: Explanations (prompts/explain_prompt.py)       ││
│  │    └── llama-3.3-70b → plain English JSON[]             ││
│  │                                                         ││
│  │  Step 5: Deterministic Scoring (metrics/evaluator.py)   ││
│  │    └── No LLM — pure math from violations list          ││
│  └─────────────────────────────────────────────────────────┘│
│                                                             │
│  ┌─────────────────────────────────────────────────────────┐│
│  │               RAG LAYER (rag/)                          ││
│  │                                                         ││
│  │  build_kb.py → chunks wcag_2_2.txt → embeds with       ││
│  │    DefaultEmbeddingFunction → stores in ChromaDB       ││
│  │                                                         ││
│  │  retriever.py → semantic query → top-k results         ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────┐
│                    VECTOR STORE                             │
│           ChromaDB (local filesystem)                       │
│           Collection: "wcag_knowledge" (40+ docs)          │
│           Embeddings: DefaultEmbeddingFunction (local)      │
│           Model: all-MiniLM-L6-v2 sentence-transformers     │
│           Similarity: Cosine distance                       │
└─────────────────────────────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────┐
│                    AI APIs                                  │
│  Groq API (only external API required):                     │
│  - llama-3.3-70b-versatile (audit, fix, explain)            │
│  - llama-4-scout-17b-16e-instruct (vision / screenshot)     │
│  Embeddings: local sentence-transformers (no external key)  │
└─────────────────────────────────────────────────────────────┘
```

## Component Descriptions

### Frontend (`frontend/`)
- **React 18 + Vite**: SPA with three input tabs (HTML textarea, URL input, image upload)
- **CodeInput.jsx**: HTML textarea with sample loader
- **ImageInput.jsx**: Drag-and-drop / file browser with PNG/JPG/WEBP support
- **ViolationReport.jsx**: Expandable cards with severity badges and ARIA roles
- **CodeDiff.jsx**: Side-by-side line diff with red/green highlighting
- **ScoreMetrics.jsx**: Animated SVG progress rings + Evaluation Metrics panel (fix validity, WCAG pass rate, silent failure target)
- **api/accessai.js**: Fetch wrapper for all backend calls

### Backend (`backend/`)
- **main.py**: FastAPI app with startup check, CORS, and all 4 routes (`/audit/html`, `/audit/url`, `/audit/image`, `/metrics/{id}`)
- **chains/audit_chain.py**: Orchestrates all 3 LLM calls with shared context
- **prompts/**: Three engineered prompts with explicit JSON schemas
- **rag/**: ChromaDB builder and semantic retriever
- **metrics/evaluator.py**: Deterministic scoring (no LLM calls)

### RAG System
1. `build_kb.py` chunks `wcag_2_2.txt` on `---` delimiter (40+ criteria)
2. Each chunk is embedded with `DefaultEmbeddingFunction` (all-MiniLM-L6-v2, runs locally)
3. At query time, `retriever.py` uses the same embedding function for consistent vector space
4. Top-3 cosine-similar documents are returned and injected into prompts

### Prompt Engineering
Three prompts form a sequential chain:
1. **Audit prompt**: Strict JSON-only output, violation schema enforcement
2. **Fix prompt**: HTML output with mandatory `<!-- FIXED: X.X.X -->` annotations
3. **Explain prompt**: JSON-only, 2-sentence plain English per violation

Context window management: only top-3 WCAG chunks (≈ 1200 tokens) injected per call.

### URL Crawling Path
1. URL → `httpx` async fetch with browser User-Agent header
2. Raw HTML response → identical audit_chain pipeline
3. Source URL preserved in response for display

### Multimodal Path
1. Image bytes → base64 → Groq LLaMA 4 Scout Vision API call
2. Prompt instructs reconstruction of HTML structure visible in screenshot
3. Reconstructed HTML → identical audit_chain pipeline

### Scoring Algorithm
```
penalty = critical×25 + serious×15 + moderate×8 + minor×3
score = max(0, 100 - penalty)
pass_rate = (principles with 0 critical/serious) / 4 × 100
```

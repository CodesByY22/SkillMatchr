# Multi-Agent Resume Intelligence System
## Project Documentation

**Stack:** LangGraph · ChromaDB · Groq API · FastAPI · PostgreSQL · Redis · Docker
**Environment:** Cloud-ready, local-first development

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [System Architecture](#2-system-architecture)
3. [Tech Stack](#3-tech-stack)
4. [Folder Structure](#4-folder-structure)
5. [Agent Design](#5-agent-design)
6. [Database Design](#6-database-design)
7. [API Reference](#7-api-reference)
8. [Environment Setup](#8-environment-setup)
9. [Development Phases](#9-development-phases)
10. [Testing Strategy](#10-testing-strategy)
11. [SDK Examples](#11-sdk-examples)
12. [Agentic Implementation Workflow](#12-agentic-implementation-workflow)
13. [Presentation Prompt](#13-presentation-prompt)

---

## 1. Project Overview

### Problem

Traditional ATS systems use rigid keyword matching, causing them to miss qualified candidates who use different terminology (e.g. "ReactJS" vs "React.js"), fail to infer implied skills (TensorFlow + PyTorch → Deep Learning), and struggle with varied resume formats including PDF, DOCX, LinkedIn exports, and plain text.

### Solution

A multi-agent AI pipeline where three specialized agents each own one layer of the problem:

| Agent | Responsibility |
|---|---|
| **Parsing Agent** | Extracts structured data from PDF, DOCX, LinkedIn exports, and TXT |
| **Normalization Agent** | Maps raw skills to a canonical taxonomy, infers hierarchy, flags emerging skills |
| **Matching Agent** | Semantically scores candidates against job descriptions with configurable thresholds |
| **Orchestrator** | Coordinates agents, manages retries, concurrency, and observability |

The full pipeline is exposed via a REST API consumable by any HR platform or job board.

---

## 2. System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          CLIENT LAYER                               │
│          HR Platforms · Job Boards · Enterprise HR Systems          │
└────────────────────────────┬────────────────────────────────────────┘
                             │ HTTPS REST / Webhooks
┌────────────────────────────▼────────────────────────────────────────┐
│                       API GATEWAY (FastAPI)                         │
│   Auth (API Key) · Rate Limiting · Request Validation · Swagger UI  │
└──────┬──────────────────────────────────────────────────────────────┘
       │
┌──────▼──────────────────────────────────────────────────────────────┐
│                   ORCHESTRATION LAYER (LangGraph)                   │
│                                                                     │
│  ┌─────────────────┐    ┌─────────────────┐    ┌────────────────┐  │
│  │  Parsing Agent  │───▶│  Normalization  │───▶│  Matching      │  │
│  │                 │    │  Agent          │    │  Agent         │  │
│  │ · PDF/DOCX/TXT  │    │ · Taxonomy DB   │    │ · Embeddings   │  │
│  │ · LinkedIn JSON │    │ · Synonym maps  │    │ · Gap analysis │  │
│  │ · LLM fallback  │    │ · Hierarchy inf │    │ · Threshold    │  │
│  │                 │    │ · Emerging skills│   │ · Scoring      │  │
│  └─────────────────┘    └─────────────────┘    └────────────────┘  │
│                                                                     │
│             Shared State · Retry Logic · Execution Traces           │
└──────┬─────────────────┬──────────────────┬────────────────────────┘
       │                 │                  │
┌──────▼──────┐  ┌───────▼──────┐  ┌───────▼──────────┐
│ PostgreSQL  │  │  ChromaDB    │  │   Redis           │
│ Candidates  │  │ Skill        │  │ Job Queue         │
│ Jobs        │  │ Embeddings   │  │ Result Cache      │
│ Matches     │  │ Resume Vecs  │  │ Rate Limit State  │
└─────────────┘  └──────┬───────┘  └───────────────────┘
                         │
             ┌───────────▼───────────┐
             │     Groq API (LLM)    │
             │   llama-3.1-70b       │
             └───────────────────────┘
```

### Request Lifecycle

```
POST /api/v1/parse
  │
  ├─ Validate request (auth, file type, size)
  ├─ Create ResumeState, invoke LangGraph
  │     ├── Parsing Agent      → structured resume dict
  │     ├── Normalization Agent → normalized skill profile + emerging skill flags
  │     └── Matching Agent (if job_id given) → score + gaps
  ├─ Persist to PostgreSQL, store vectors in ChromaDB
  └─ Return JSON response (or 202 + job_id for async)
```

### Batch Processing

```
POST /api/v1/parse/batch
  │
  ├─ Celery task created → returns { job_id, status: "queued" }
  ├─ Worker processes N resumes concurrently (asyncio.gather)
  ├─ Progress tracked in Redis: { total, done, failed }
  └─ On completion → webhook fired or polled via GET /api/v1/jobs/{id}/status
```

---

## 3. Tech Stack

### Application

| Technology | Role |
|---|---|
| **Python 3.11+** | Primary language |
| **FastAPI** | REST API — auto OpenAPI docs, async, Pydantic validation |
| **Pydantic v2** | Data validation and LLM output parsing |
| **Celery** | Async background tasks for batch processing |

### Multi-Agent Orchestration

| Technology | Role |
|---|---|
| **LangGraph** | StateGraph orchestration — nodes, edges, conditional routing |
| **LangChain** | LLM abstractions — chains, prompts, output parsers |
| **langchain-groq** | Groq LLM connector |

LangGraph operates as a directed graph where each node is an agent function. A shared `ResumeState` TypedDict flows between nodes — each node reads from it, mutates it, and passes it forward. Conditional edges handle routing based on state (e.g. matching only runs if a job description is present).

### LLM & Embeddings

| Technology | Role |
|---|---|
| **Groq API** | LLM inference — `llama-3.1-70b-versatile` for extraction, `llama-3.1-8b-instant` for lighter tasks |
| **sentence-transformers** | Local embeddings — `all-MiniLM-L6-v2`, no API cost |

### Document Parsing

| Technology | Role |
|---|---|
| **pdfplumber** | Text-based PDFs, table detection |
| **PyMuPDF (fitz)** | Complex PDF layouts — multi-column, creative designs |
| **python-docx** | DOCX parsing |
| **json / stdlib** | LinkedIn export parsing (JSON format) |

**Parsing decision logic:**
```
PDF  → pdfplumber first (fast, accurate)
       if multi-column detected → PyMuPDF bounding-box analysis
       if text sparse → flag for human review
DOCX → python-docx
TXT  → direct NLP section detection
JSON → LinkedIn export schema mapping (positions, skills, education keys)
All  → Groq LLM post-processing for ambiguous or malformed sections
```

### Data Layer

| Technology | Role |
|---|---|
| **PostgreSQL** | Primary store — candidates, jobs, matches, API keys |
| **ChromaDB** | Vector store — skill embeddings, resume and job vectors (persists to disk) |
| **Redis** | Celery broker, result backend, rate limit counters |
| **SQLAlchemy** | ORM |
| **Alembic** | Schema migrations |

---

## 4. Folder Structure

```
resume-ai/
│
├── app/
│   ├── agents/
│   │   ├── state.py                # Shared ResumeState TypedDict
│   │   ├── orchestrator.py         # LangGraph StateGraph definition
│   │   ├── parsing_agent.py        # Parsing node
│   │   ├── normalization_agent.py  # Normalization node
│   │   └── matching_agent.py       # Matching node
│   │
│   ├── api/
│   │   ├── main.py                 # FastAPI app init, middleware, startup
│   │   └── routes/
│   │       ├── parse.py            # POST /api/v1/parse
│   │       ├── batch.py            # POST /api/v1/parse/batch
│   │       ├── candidates.py       # GET /api/v1/candidates/{id}/skills
│   │       ├── match.py            # POST /api/v1/match
│   │       ├── skills.py           # GET /api/v1/skills/taxonomy
│   │       └── health.py           # GET /health
│   │
│   ├── models/
│   │   ├── candidate.py
│   │   ├── job.py
│   │   ├── match.py
│   │   ├── skill.py
│   │   └── api_key.py
│   │
│   ├── services/
│   │   ├── parsing_service.py      # PDF/DOCX/TXT/LinkedIn extraction
│   │   ├── embedding_service.py    # sentence-transformers wrapper
│   │   ├── chroma_service.py       # ChromaDB read/write
│   │   ├── taxonomy_service.py     # Skill taxonomy CRUD
│   │   └── webhook_service.py      # Async webhook delivery
│   │
│   ├── tasks/
│   │   ├── celery_app.py           # Celery config
│   │   └── resume_tasks.py         # Batch processing tasks
│   │
│   ├── utils/
│   │   ├── auth.py                 # API key middleware
│   │   ├── rate_limit.py           # Redis-based rate limiter
│   │   ├── logger.py               # Structured logging (structlog)
│   │   └── metrics.py              # Prometheus metric definitions
│   │
│   └── config.py                   # Pydantic settings from .env
│
├── alembic/
│   └── versions/                   # Migration files
│
├── data/
│   ├── taxonomy/
│   │   └── skills_taxonomy.json    # 5000+ skills hierarchical JSON
│   ├── sample_resumes/             # PDF, DOCX, TXT, LinkedIn JSON samples
│   └── sample_jobs/
│
├── tests/
│   ├── unit/
│   │   ├── test_parsing.py
│   │   ├── test_normalization.py
│   │   └── test_matching.py
│   ├── integration/
│   │   └── test_pipeline.py
│   └── fixtures/
│
├── docs/
│   ├── api_examples/
│   │   ├── python_sdk_example.py
│   │   └── javascript_sdk_example.js
│   └── postman_collection.json
│
├── scripts/
│   ├── seed_taxonomy.py
│   ├── seed_sample_data.py
│   └── generate_api_key.py
│
├── .env.example
├── requirements.txt
├── docker-compose.yml
├── Dockerfile
└── README.md
```

---

## 5. Agent Design

### Shared State (`app/agents/state.py`)

A single `TypedDict` flows through every node in the LangGraph graph.

```python
from typing import TypedDict, Optional, List, Dict

class ResumeState(TypedDict):
    # Input
    job_id: str
    raw_file_bytes: bytes
    file_type: str                       # "pdf" | "docx" | "txt" | "linkedin_json"
    job_description: Optional[str]
    match_threshold: Optional[float]     # 0.0 – 1.0, default 0.7

    # Parsing Agent output
    parsed_resume: Optional[Dict]
    parse_confidence: Optional[float]    # 0.0 – 1.0

    # Normalization Agent output
    normalized_skills: Optional[List]
    inferred_skills: Optional[List]      # Skills implied by context
    unknown_skills: Optional[List]       # Not in taxonomy → flagged for review
    emerging_skills: Optional[List]      # New skills flagged for taxonomy addition

    # Matching Agent output
    match_score: Optional[float]         # 0.0 – 100.0
    skill_gaps: Optional[List]
    upskilling_paths: Optional[List]

    # Orchestration
    errors: List[str]
    trace: List[Dict]                    # Per-agent execution trace with latency
    retry_count: int
```

---

### Parsing Agent (`app/agents/parsing_agent.py`)

Converts raw file bytes into a structured Python dictionary. Handles PDF, DOCX, plain text, and LinkedIn JSON exports.

**Steps:**
1. Detect format from file extension / magic bytes
2. Select extraction strategy per format (see decision logic in Section 3)
3. Detect resume sections via regex for standard headers (EXPERIENCE, EDUCATION, SKILLS, CERTIFICATIONS, PROJECTS, PUBLICATIONS)
4. Send extracted text to Groq for structured JSON output on ambiguous or non-standard sections

**LinkedIn JSON mapping:** LinkedIn exports use keys `positions`, `skills`, `education`, `certifications`. The parser maps these directly to the standard output schema without needing LLM extraction.

**Groq prompt pattern:**
```
System: You are a resume parser. Extract the following fields and return ONLY
        valid JSON matching this schema: {schema}. If a field is not present,
        return null. Do not invent values.
User:   {extracted_text}
```

**Output schema:**
```python
{
  "personal": {
    "name": str, "email": str, "phone": str,
    "location": str, "linkedin": str | None
  },
  "experience": [{
    "company": str, "role": str,
    "start_date": str, "end_date": str,
    "duration_months": int,
    "responsibilities": [str]
  }],
  "education": [{
    "institution": str, "degree": str,
    "field": str, "year": int | None
  }],
  "skills_raw": [str],
  "certifications": [str],
  "projects": [str],
  "publications": [str]
}
```

---

### Normalization Agent (`app/agents/normalization_agent.py`)

Maps raw skill strings to canonical taxonomy entries, infers implied skills, estimates proficiency, and flags skills not yet in the taxonomy.

**Steps:**
1. **Exact match** — check against taxonomy (fast path)
2. **Alias lookup** — resolve known synonyms from `skills_taxonomy.json`
3. **Fuzzy match** — Levenshtein distance for near-matches
4. **Embedding similarity** — embed unknown skill, find closest entry in ChromaDB
5. **Hierarchy inference** — e.g. TensorFlow + PyTorch → Deep Learning, Neural Networks
6. **Proficiency estimation** — parse years of experience and seniority keywords from context
7. **Emerging skill detection** — skills with embedding similarity below threshold (< 0.6) are added to `emerging_skills` and written to a review queue in PostgreSQL for human taxonomy curation

**Taxonomy JSON structure:**
```json
{
  "Technical Skills": {
    "Programming Languages": {
      "Python": {
        "aliases": ["py", "python3"],
        "implies": ["Software Development"],
        "related": ["Data Science", "Machine Learning"]
      }
    },
    "Frameworks": {},
    "Cloud Platforms": {}
  },
  "Soft Skills": {},
  "Domain Knowledge": {}
}
```

**Proficiency scale:**

| Level | Score | Indicators |
|---|---|---|
| Beginner | 1 | < 1 year, "familiar", "basic" |
| Intermediate | 2 | 1–3 years, "worked with" |
| Advanced | 3 | 3–5 years, "proficient" |
| Expert | 4 | 5+ years, "led", "expert" |

---

### Matching Agent (`app/agents/matching_agent.py`)

Scores a candidate against a job description using semantic similarity and weighted scoring. Supports a configurable threshold to tune precision vs. recall.

**Steps:**
1. Parse JD with Groq to extract required vs. nice-to-have skills
2. Embed candidate skill profile and JD requirements using `sentence-transformers`
3. Query ChromaDB for cosine similarity scores per skill
4. Apply weighted scoring — required skills get 3× weight; nice-to-have get 1×; multiply by depth and recency
5. Apply `match_threshold` from state — skills with similarity below threshold are excluded from matched count and added to gaps
6. Identify gaps (required skills absent or below threshold)
7. Suggest upskilling paths using adjacent skills the candidate already has

**Scoring formula:**
```
base_score = Σ (similarity × weight × depth_multiplier)   [only skills ≥ threshold]
score      = (base_score / max_possible) × 100 × recency_bonus
```

**Verdict thresholds:**

| Score | Verdict |
|---|---|
| < 40 | Weak Match |
| 40 – 70 | Moderate Match |
| > 70 | Strong Match |

**Configurable threshold behaviour:**
- `threshold: 0.5` → high recall (lenient, surfaces more candidates)
- `threshold: 0.85` → high precision (strict, only strong semantic matches)
- Default: `0.7`

---

### Orchestrator (`app/agents/orchestrator.py`)

Defines the LangGraph StateGraph, wires all nodes, and handles routing.

```python
from langgraph.graph import StateGraph, END

graph = StateGraph(ResumeState)

graph.add_node("parse",     parsing_agent)
graph.add_node("normalize", normalization_agent)
graph.add_node("match",     matching_agent)
graph.add_node("error",     error_handler)

graph.set_entry_point("parse")
graph.add_edge("parse", "normalize")
graph.add_conditional_edges(
    "normalize",
    should_run_matching,         # returns "match" if job_description present
    {"match": "match", END: END}
)
graph.add_edge("match", END)
```

**Retry logic:** Each node is wrapped in try/except. On failure, `retry_count` increments and the node is re-entered (max 3 attempts). After max retries, partial results are returned with `errors` populated — no request fails completely.

**Execution tracing:** Each node appends to `state["trace"]`:
```python
{
  "node": "normalization_agent",
  "status": "success",
  "latency_ms": 340,
  "quality_score": 0.94
}
```

---

## 6. Database Design

### PostgreSQL Schema

```sql
CREATE TABLE api_keys (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    key_hash    VARCHAR(64) UNIQUE NOT NULL,
    name        VARCHAR(100),
    rate_limit  INTEGER DEFAULT 100,
    is_active   BOOLEAN DEFAULT TRUE,
    created_at  TIMESTAMP DEFAULT NOW()
);

CREATE TABLE candidates (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name             VARCHAR(200),
    email            VARCHAR(200),
    phone            VARCHAR(50),
    location         VARCHAR(200),
    parsed_data      JSONB,
    chroma_doc_id    VARCHAR(100),
    parse_confidence FLOAT,
    created_at       TIMESTAMP DEFAULT NOW()
);

CREATE TABLE skills (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        VARCHAR(200) UNIQUE NOT NULL,
    canonical   VARCHAR(200),
    category    VARCHAR(100),
    subcategory VARCHAR(100),
    aliases     TEXT[],
    implies     TEXT[],
    created_at  TIMESTAMP DEFAULT NOW()
);

-- Emerging skills flagged for taxonomy review
CREATE TABLE emerging_skills (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    raw_name     VARCHAR(200) NOT NULL,
    seen_count   INTEGER DEFAULT 1,
    first_seen   TIMESTAMP DEFAULT NOW(),
    reviewed     BOOLEAN DEFAULT FALSE,
    added_to_taxonomy BOOLEAN DEFAULT FALSE
);

CREATE TABLE candidate_skills (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    candidate_id UUID REFERENCES candidates(id) ON DELETE CASCADE,
    skill_id     UUID REFERENCES skills(id),
    raw_skill    VARCHAR(200),
    proficiency  SMALLINT CHECK (proficiency BETWEEN 1 AND 4),
    years_exp    FLOAT,
    is_inferred  BOOLEAN DEFAULT FALSE
);

CREATE TABLE jobs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title           VARCHAR(200),
    company         VARCHAR(200),
    description     TEXT,
    required_skills JSONB,
    nice_to_have    JSONB,
    created_at      TIMESTAMP DEFAULT NOW()
);

CREATE TABLE matches (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    candidate_id   UUID REFERENCES candidates(id),
    job_id         UUID REFERENCES jobs(id),
    match_score    FLOAT,
    verdict        VARCHAR(20),
    matched_skills JSONB,
    skill_gaps     JSONB,
    upskilling     JSONB,
    threshold_used FLOAT,
    created_at     TIMESTAMP DEFAULT NOW(),
    UNIQUE(candidate_id, job_id)
);

CREATE TABLE batch_jobs (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    status      VARCHAR(20) DEFAULT 'queued',
    total       INTEGER,
    completed   INTEGER DEFAULT 0,
    failed      INTEGER DEFAULT 0,
    results     JSONB,
    webhook_url VARCHAR(500),
    created_at  TIMESTAMP DEFAULT NOW(),
    finished_at TIMESTAMP
);

CREATE TABLE webhooks (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    api_key_id UUID REFERENCES api_keys(id),
    url        VARCHAR(500) NOT NULL,
    events     TEXT[],
    secret     VARCHAR(100),
    is_active  BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### ChromaDB Collections

| Collection | Document | Metadata |
|---|---|---|
| `skill_embeddings` | Canonical skill name | `{category, subcategory, aliases}` |
| `resume_vectors` | Normalized skill profile text | `{candidate_id, created_at}` |
| `job_vectors` | Job requirements text | `{job_id, title, company}` |

All vectors use 384-dim embeddings from `all-MiniLM-L6-v2`.

---

## 7. API Reference

### Authentication

All endpoints except `/health` require:
```
X-API-Key: <your-api-key>
```

### Endpoints

#### `POST /api/v1/parse`
Parse a single resume.

```
Content-Type: multipart/form-data
Body:
  file       — PDF, DOCX, TXT, or LinkedIn JSON export
  job_id     — optional UUID; if provided, matching runs automatically
  threshold  — optional float 0.0–1.0 (default 0.7)

Response 200:
{
  "candidate_id": "uuid",
  "personal": { "name": "...", "email": "...", ... },
  "skills": [
    { "name": "Python", "proficiency": 4, "years": 5.0, "is_inferred": false }
  ],
  "emerging_skills": ["PromptOps", "LLMOps"],   ← flagged for taxonomy review
  "match": {                                     ← only present if job_id was given
    "score": 78.4,
    "verdict": "Strong Match",
    "threshold_used": 0.7,
    "gaps": [...],
    "upskilling": [...]
  },
  "parse_confidence": 0.94,
  "trace": [...],
  "processing_time_ms": 2340
}
```

#### `POST /api/v1/parse/batch`
Submit multiple resumes for async processing.

```
Content-Type: multipart/form-data
Body:
  files        — up to 100 files (PDF, DOCX, TXT, LinkedIn JSON)
  job_id       — optional
  threshold    — optional float, applies to all resumes in batch
  webhook_url  — optional callback URL

Response 202:
{
  "batch_job_id": "uuid",
  "status": "queued",
  "total_files": 50,
  "status_url": "/api/v1/jobs/{batch_job_id}/status"
}
```

#### `GET /api/v1/jobs/{batch_job_id}/status`
```
Response 200:
{
  "status": "processing",
  "total": 50, "completed": 23, "failed": 1,
  "results_url": "/api/v1/jobs/{id}/results"   ← available when done
}
```

#### `GET /api/v1/candidates/{id}/skills`
```
Response 200:
{
  "candidate_id": "uuid",
  "skills": [
    {
      "name": "Python", "canonical": "Python",
      "category": "Technical Skills",
      "subcategory": "Programming Languages",
      "proficiency": 4, "years_experience": 5.0, "is_inferred": false
    }
  ],
  "inferred_skills": [...],
  "unknown_skills": [...],
  "emerging_skills": [...]
}
```

#### `POST /api/v1/match`
```
Body (JSON):
{
  "candidate_id": "uuid",
  "job_description": "We are looking for a Senior Python Engineer...",
  "required_skills": ["Python", "FastAPI"],   ← optional override
  "threshold": 0.7                            ← optional, 0.0–1.0
}

Response 200:
{
  "match_score": 78.4,
  "verdict": "Strong Match",
  "threshold_used": 0.7,
  "matched_skills": [
    { "skill": "Python", "weight": "required", "similarity": 0.97, "depth": "Expert" }
  ],
  "skill_gaps": [
    { "skill": "Kubernetes", "weight": "nice_to_have", "suggestion": "..." }
  ],
  "upskilling_paths": [...]
}
```

#### `GET /api/v1/skills/taxonomy`
```
Query params: ?category=Technical Skills  ?search=python  ?limit=20&offset=0

Response 200:
{
  "total": 5000,
  "skills": [
    {
      "name": "Python", "category": "Technical Skills",
      "subcategory": "Programming Languages",
      "aliases": ["py", "python3"], "implies": ["Software Development"]
    }
  ]
}
```

#### `GET /health`
No authentication required.
```
Response 200:
{
  "status": "healthy",
  "services": { "postgres": "ok", "redis": "ok", "chromadb": "ok", "groq_api": "ok" },
  "version": "1.0.0"
}
```

### Error Format (RFC 7807)

```json
{
  "type": "https://resumeai.io/errors/validation-error",
  "title": "Validation Error",
  "status": 422,
  "detail": "File type not supported. Accepted: pdf, docx, txt, json",
  "instance": "/api/v1/parse",
  "request_id": "uuid"
}
```

### Rate Limits

| Endpoint | Limit |
|---|---|
| General | 100 requests / hour |
| Batch submit | 10 requests / hour |

Headers returned on every response:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1720000000
```

---

## 8. Environment Setup

### Prerequisites
- Python 3.11+
- Docker & Docker Compose
- Groq API key — free at `console.groq.com`

### Step 1 — Configure

```bash
git clone <your-repo> && cd resume-ai
cp .env.example .env
# Fill in GROQ_API_KEY and SECRET_KEY at minimum
```

### `.env` Reference

```bash
# Required
GROQ_API_KEY=gsk_xxxxxxxxxxxx
SECRET_KEY=<openssl rand -hex 32>
DATABASE_URL=postgresql://user:pass@localhost:5432/resumeai

# Defaults
REDIS_URL=redis://localhost:6379/0
CHROMA_PERSIST_DIR=./chroma_db
EMBEDDING_MODEL=all-MiniLM-L6-v2
GROQ_MODEL_HEAVY=llama-3.1-70b-versatile
GROQ_MODEL_FAST=llama-3.1-8b-instant
MAX_FILE_SIZE_MB=10
BATCH_CONCURRENCY=5
RATE_LIMIT_PER_HOUR=100
EMERGING_SKILL_THRESHOLD=0.6
DEFAULT_MATCH_THRESHOLD=0.7
DEBUG=true
```

### Step 2 — Start Services

```bash
docker compose up -d postgres redis
docker compose up -d app celery
```

`docker-compose.yml` defines four services: `app` (FastAPI), `postgres` (postgres:16), `redis` (redis:7-alpine), `celery` (same image as app, command overridden to `celery worker`).

### Step 3 — Initialize

```bash
alembic upgrade head
python scripts/seed_taxonomy.py
python scripts/generate_api_key.py --name "dev-key"
```

### Step 4 — Verify

```bash
curl http://localhost:8000/health

# Swagger UI
open http://localhost:8000/docs

# First parse
curl -X POST http://localhost:8000/api/v1/parse \
  -H "X-API-Key: <your-key>" \
  -F "file=@data/sample_resumes/sample.pdf"
```

---

## 9. Development Phases

### Phase 1 — Foundation (Weeks 1–2)
**Goal:** Project skeleton running with basic parsing, no LLM.

- [ ] Docker Compose with all services healthy
- [ ] SQLAlchemy models + first Alembic migration
- [ ] Skill taxonomy seeded from JSON
- [ ] API key auth middleware
- [ ] `GET /health` endpoint
- [ ] `parsing_service.py` — pdfplumber + python-docx + LinkedIn JSON extraction
- [ ] Unit tests for parsing service

**Exit criteria:** `/health` returns OK; `/api/v1/parse` returns extracted raw text.

---

### Phase 2 — Agent Core (Weeks 3–4)
**Goal:** All three agents wired into LangGraph, full pipeline working.

- [ ] `state.py` — `ResumeState` TypedDict
- [ ] `parsing_agent.py` — Groq LLM post-processing
- [ ] `normalization_agent.py` — taxonomy lookup + ChromaDB + emerging skill flagging
- [ ] `matching_agent.py` — sentence-transformers + weighted scoring + threshold
- [ ] `orchestrator.py` — StateGraph with retry and conditional routing
- [ ] Integration test: PDF in → match score out

**Exit criteria:** Single PDF → structured JSON with match score; retries on agent failure.

---

### Phase 3 — Full API (Weeks 5–6)
**Goal:** All endpoints complete with auth, rate limiting, webhooks, and docs.

- [ ] All six API routes implemented
- [ ] Celery batch processing
- [ ] Webhook registration and signed delivery
- [ ] Rate limiting middleware
- [ ] OpenAPI docs reviewed and complete
- [ ] Postman collection exported

**Exit criteria:** All endpoints live in Swagger; batch job runs async end-to-end.

---

### Phase 4 — Hardening (Week 7)
**Goal:** Observability, graceful degradation, production readiness.

- [ ] Prometheus metrics — per-agent latency, error rates, queue depth
- [ ] Structured JSON logging via `structlog`
- [ ] Per-agent execution traces stored in state
- [ ] Graceful degradation — partial results on agent failure
- [ ] Load test: 50 concurrent resumes, p95 < 10s
- [ ] Python and JavaScript SDK usage examples

**Exit criteria:** p95 < 10s under load; Grafana dashboard operational.

---

## 10. Testing Strategy

### Unit Tests

```python
# test_parsing.py
def test_pdf_extraction():
    with open("tests/fixtures/sample.pdf", "rb") as f:
        result = parse_pdf(f.read())
    assert result["personal"]["name"] is not None
    assert len(result["skills_raw"]) > 0

def test_linkedin_json_parsing():
    with open("tests/fixtures/linkedin_export.json") as f:
        result = parse_linkedin(json.load(f))
    assert result["personal"]["name"] is not None
    assert len(result["experience"]) > 0

# test_normalization.py
def test_alias_mapping():
    assert normalize_skill("K8s")["canonical"] == "Kubernetes"

def test_hierarchy_inference():
    inferred = infer_skills(["TensorFlow", "PyTorch"])
    assert "Deep Learning" in [s["name"] for s in inferred]

def test_emerging_skill_flagging():
    result = normalize_skill("PromptOps")
    assert result["status"] == "emerging"

# test_matching.py
def test_threshold_affects_gaps():
    result_strict = match(candidate, jd, threshold=0.9)
    result_lenient = match(candidate, jd, threshold=0.5)
    assert len(result_strict["skill_gaps"]) >= len(result_lenient["skill_gaps"])
```

### Integration Tests

```python
# test_pipeline.py
async def test_full_pipeline():
    with open("tests/fixtures/sample_engineer.pdf", "rb") as f:
        result = await orchestrator.ainvoke({
            "raw_file_bytes": f.read(),
            "file_type": "pdf",
            "job_description": JD_PYTHON_ENGINEER,
            "match_threshold": 0.7
        })
    assert result["match_score"] > 60
    assert len(result["normalized_skills"]) > 5
    assert result["errors"] == []

async def test_graceful_degradation():
    # Simulate normalization agent failure
    with patch("app.agents.normalization_agent", side_effect=Exception("timeout")):
        result = await orchestrator.ainvoke(valid_state)
    assert result["parsed_resume"] is not None   # partial result returned
    assert len(result["errors"]) > 0
```

### Evaluation Targets

| Metric | Target |
|---|---|
| Parse field F1-score | > 0.90 |
| Skill canonical mapping accuracy | > 0.95 |
| Emerging skill detection recall | > 0.80 |
| Match quality (NDCG@10) | > 0.80 |
| Single resume e2e latency (p95) | < 10s |
| Batch throughput | > 30 resumes / min |
| API success rate under load | > 99% |

---

## 11. SDK Examples

### Python

```python
import httpx

BASE_URL = "http://localhost:8000"
API_KEY  = "your-api-key"
HEADERS  = {"X-API-Key": API_KEY}

# Parse a single resume
def parse_resume(file_path: str, job_id: str = None, threshold: float = 0.7):
    with open(file_path, "rb") as f:
        data = {"threshold": str(threshold)}
        if job_id:
            data["job_id"] = job_id
        resp = httpx.post(
            f"{BASE_URL}/api/v1/parse",
            headers=HEADERS,
            files={"file": f},
            data=data,
        )
    resp.raise_for_status()
    return resp.json()

# Submit a batch
def submit_batch(file_paths: list[str], webhook_url: str = None):
    files = [("files", open(p, "rb")) for p in file_paths]
    data = {}
    if webhook_url:
        data["webhook_url"] = webhook_url
    resp = httpx.post(
        f"{BASE_URL}/api/v1/parse/batch",
        headers=HEADERS, files=files, data=data,
    )
    resp.raise_for_status()
    return resp.json()   # { batch_job_id, status_url }

# Poll batch status
def poll_batch(batch_job_id: str):
    resp = httpx.get(
        f"{BASE_URL}/api/v1/jobs/{batch_job_id}/status",
        headers=HEADERS,
    )
    resp.raise_for_status()
    return resp.json()

# Match a candidate to a JD
def match_candidate(candidate_id: str, job_description: str, threshold: float = 0.7):
    resp = httpx.post(
        f"{BASE_URL}/api/v1/match",
        headers=HEADERS,
        json={"candidate_id": candidate_id, "job_description": job_description,
              "threshold": threshold},
    )
    resp.raise_for_status()
    return resp.json()
```

### JavaScript

```javascript
const BASE_URL = "http://localhost:8000";
const API_KEY  = "your-api-key";
const HEADERS  = { "X-API-Key": API_KEY };

// Parse a single resume
async function parseResume(file, jobId = null, threshold = 0.7) {
  const form = new FormData();
  form.append("file", file);
  form.append("threshold", String(threshold));
  if (jobId) form.append("job_id", jobId);

  const res = await fetch(`${BASE_URL}/api/v1/parse`, {
    method: "POST", headers: HEADERS, body: form,
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

// Submit a batch
async function submitBatch(files, webhookUrl = null) {
  const form = new FormData();
  files.forEach(f => form.append("files", f));
  if (webhookUrl) form.append("webhook_url", webhookUrl);

  const res = await fetch(`${BASE_URL}/api/v1/parse/batch`, {
    method: "POST", headers: HEADERS, body: form,
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

// Poll batch status
async function pollBatch(batchJobId) {
  const res = await fetch(`${BASE_URL}/api/v1/jobs/${batchJobId}/status`, {
    headers: HEADERS,
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

// Match candidate to JD
async function matchCandidate(candidateId, jobDescription, threshold = 0.7) {
  const res = await fetch(`${BASE_URL}/api/v1/match`, {
    method: "POST",
    headers: { ...HEADERS, "Content-Type": "application/json" },
    body: JSON.stringify({ candidate_id: candidateId,
                           job_description: jobDescription, threshold }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}
```

---

## 12. Agentic Implementation Workflow

This section is a precise, ordered build plan designed so that an AI coding agent can execute it from start to finish without ambiguity or manual intervention. Each step specifies exactly what to create, what inputs it depends on, and what the verification condition is before moving to the next step.

**Ground rules for the agent:**
- Never skip a verification step. Only proceed when the stated condition passes.
- Never modify the tech stack. Use exactly the libraries listed.
- All secrets come from `.env` via `app/config.py`. Never hardcode credentials.
- All database access goes through SQLAlchemy models. Never write raw SQL in agent or route code.
- All LLM calls go through `langchain-groq`. Never call the Groq HTTP API directly.
- If a step fails after 3 attempts, log the error, mark the step failed, and halt.

---

### STEP 1 — Repository & Configuration Bootstrap

**What to do:**
Create the full folder structure as specified in Section 4. Create every `__init__.py`. Create `requirements.txt` with these exact packages and versions:

```
fastapi==0.111.0
uvicorn[standard]==0.30.1
python-multipart==0.0.9
langgraph==0.1.19
langchain==0.2.6
langchain-groq==0.1.6
langchain-community==0.2.6
langchain-core==0.2.10
groq==0.9.0
sentence-transformers==3.0.1
pdfplumber==0.11.0
PyMuPDF==1.24.7
python-docx==1.1.2
chromadb==0.5.3
sqlalchemy==2.0.31
alembic==1.13.1
psycopg2-binary==2.9.9
redis==5.0.7
celery==5.4.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
pydantic==2.7.4
pydantic-settings==2.3.3
httpx==0.27.0
python-dotenv==1.0.1
tenacity==8.4.1
structlog==24.2.0
prometheus-fastapi-instrumentator==7.0.0
pytest==8.2.2
pytest-asyncio==0.23.7
Levenshtein==0.25.1
```

Create `.env.example` with all variables listed in Section 8.

Create `app/config.py`:
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "Resume AI"
    app_version: str = "1.0.0"
    debug: bool = False
    secret_key: str
    database_url: str
    redis_url: str = "redis://localhost:6379/0"
    chroma_persist_dir: str = "./chroma_db"
    groq_api_key: str
    groq_model_heavy: str = "llama-3.1-70b-versatile"
    groq_model_fast: str = "llama-3.1-8b-instant"
    embedding_model: str = "all-MiniLM-L6-v2"
    max_file_size_mb: int = 10
    batch_concurrency: int = 5
    rate_limit_per_hour: int = 100
    emerging_skill_threshold: float = 0.6
    default_match_threshold: float = 0.7

    class Config:
        env_file = ".env"

settings = Settings()
```

**Verification:** `python -c "from app.config import settings; print(settings.app_name)"` prints `Resume AI`.

---

### STEP 2 — Docker Compose & Infrastructure

**What to do:**
Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Create `docker-compose.yml` with four services:
- `postgres`: image `postgres:16`, env `POSTGRES_DB=resumeai POSTGRES_USER=user POSTGRES_PASSWORD=pass`, port `5432:5432`, named volume `pgdata`
- `redis`: image `redis:7-alpine`, port `6379:6379`
- `app`: build from `.`, depends on postgres and redis, env_file `.env`, port `8000:8000`
- `celery`: build from `.`, command `celery -A app.tasks.celery_app worker --loglevel=info`, depends on postgres and redis, env_file `.env`

**Verification:** `docker compose up -d postgres redis` starts cleanly. `docker compose ps` shows both healthy.

---

### STEP 3 — Database Models & Migrations

**What to do:**
Create all SQLAlchemy models in `app/models/` matching the schema in Section 6 exactly. Each model file contains one class inheriting from a shared `Base = declarative_base()` defined in `app/models/__init__.py`.

Initialize Alembic: `alembic init alembic`. Edit `alembic/env.py` to import `Base` from `app/models` and set `target_metadata = Base.metadata`. Set `sqlalchemy.url` in `alembic.ini` to read from the `DATABASE_URL` env var.

Generate the initial migration: `alembic revision --autogenerate -m "initial_schema"`.

**Verification:** `alembic upgrade head` runs without errors. All 9 tables exist in the database.

---

### STEP 4 — Skill Taxonomy Data

**What to do:**
Create `data/taxonomy/skills_taxonomy.json` with at minimum 100 skills across these top-level categories: `Technical Skills`, `Soft Skills`, `Domain Knowledge`. Each skill entry must have `aliases`, `implies`, and `related` arrays. Include at least these entries to support test assertions:
- `Python` with aliases `["py", "python3"]`
- `JavaScript` with aliases `["JS", "ECMAScript", "ES6"]`
- `Kubernetes` with aliases `["K8s"]`
- `TensorFlow` with implies `["Deep Learning", "Machine Learning"]`
- `PyTorch` with implies `["Deep Learning", "Machine Learning"]`

Create `scripts/seed_taxonomy.py`. It must read `data/taxonomy/skills_taxonomy.json`, walk the hierarchy, and upsert every skill into the `skills` table. It must also embed each canonical skill name using `sentence-transformers` and upsert into the ChromaDB `skill_embeddings` collection.

Create `app/services/chroma_service.py` before running the seed script. It must expose:
- `get_client()` → returns a persistent ChromaDB client pointed at `settings.chroma_persist_dir`
- `get_or_create_collection(name: str)` → returns a ChromaDB collection
- `upsert(collection_name, ids, documents, embeddings, metadatas)`
- `query(collection_name, query_embedding, n_results, where=None)` → returns list of matches

Create `app/services/embedding_service.py`. It must load `SentenceTransformer(settings.embedding_model)` once at module level (not per call) and expose `embed(texts: list[str]) -> list[list[float]]`.

**Verification:** `python scripts/seed_taxonomy.py` completes. `SELECT COUNT(*) FROM skills` returns ≥ 100. ChromaDB `skill_embeddings` collection has matching document count.

---

### STEP 5 — Auth & API Key Infrastructure

**What to do:**
Create `scripts/generate_api_key.py`. It must generate a cryptographically random 32-byte key, SHA-256 hash it, store the hash in the `api_keys` table, and print the plaintext key to stdout (the only time it appears in plaintext).

Create `app/utils/auth.py`. It must expose a FastAPI dependency `verify_api_key(x_api_key: str = Header(...))` that SHA-256 hashes the incoming key, queries `api_keys` by hash, checks `is_active`, and raises `HTTPException(401)` on failure.

Create `app/utils/rate_limit.py`. It must expose a FastAPI dependency `rate_limiter(request: Request)` that uses Redis with key `ratelimit:{key_hash}:{hour_bucket}`, increments a counter with TTL 3600, and raises `HTTPException(429)` if over `settings.rate_limit_per_hour`.

**Verification:** Run `python scripts/generate_api_key.py --name test`. Use the printed key in a curl request. `verify_api_key` must accept it. An invalid key must return 401. After 101 requests in one hour, the 101st must return 429.

---

### STEP 6 — Document Parsing Service

**What to do:**
Create `app/services/parsing_service.py` with four functions, each accepting `bytes` and returning the standard parsed dict schema from Section 5:

`parse_pdf(data: bytes) -> dict`:
- Try `pdfplumber` first. Extract all text pages.
- Check column count: if any page has bounding boxes suggesting more than one text column (x-coordinates split into two clusters), re-parse using `PyMuPDF` with bounding-box sorting.
- If extracted text is fewer than 100 characters, add flag `{"sparse_text": true}` to result.
- Run section detection regex on the combined text to split into named sections.
- Return sections dict.

`parse_docx(data: bytes) -> dict`:
- Use `python-docx`. Iterate paragraphs and tables. Detect section headers by bold formatting or ALL CAPS style. Group content under detected section names.

`parse_txt(data: bytes) -> dict`:
- Decode as UTF-8. Run same section detection regex as PDF path.

`parse_linkedin(data: bytes) -> dict`:
- Parse JSON. Map `positions.values` → `experience`, `skills.values` → `skills_raw`, `education.values` → `education`, `certifications.values` → `certifications`.

Section detection regex must match these header variants (case-insensitive): EXPERIENCE, WORK EXPERIENCE, EMPLOYMENT, EDUCATION, SKILLS, TECHNICAL SKILLS, CERTIFICATIONS, PROJECTS, PUBLICATIONS, SUMMARY, OBJECTIVE.

**Verification:** Unit tests in `tests/unit/test_parsing.py` pass for a sample PDF, DOCX, TXT, and LinkedIn JSON in `tests/fixtures/`.

---

### STEP 7 — LangGraph State & Agent Skeletons

**What to do:**
Create `app/agents/state.py` with the `ResumeState` TypedDict exactly as defined in Section 5.

Create skeleton implementations for all three agent files. Each must be a Python function with signature `def <name>_agent(state: ResumeState) -> ResumeState`. Each must record its trace entry on entry and exit:
```python
import time
start = time.time()
# ... work ...
state["trace"].append({
    "node": "<agent_name>",
    "status": "success",
    "latency_ms": round((time.time() - start) * 1000),
    "quality_score": None   # filled in by real implementation
})
return state
```

Create `app/agents/orchestrator.py` with the full `StateGraph` as shown in Section 5. The `should_run_matching` function returns `"match"` if `state["job_description"]` is not None, else returns `END`. Compile the graph with `graph.compile()` and expose it as `orchestrator`.

**Verification:** `from app.agents.orchestrator import orchestrator` imports without error. `orchestrator.invoke(minimal_state)` returns a state dict with a `trace` list.

---

### STEP 8 — Parsing Agent (Full)

**What to do:**
Implement `app/agents/parsing_agent.py` fully. The agent must:

1. Read `state["raw_file_bytes"]` and `state["file_type"]`.
2. Call the appropriate function from `parsing_service.py`.
3. Send the extracted text to Groq using `langchain-groq` with model `settings.groq_model_heavy`. Prompt must instruct the model to return ONLY valid JSON matching the output schema from Section 5. Use `langchain` output parser `JsonOutputParser` to parse the response.
4. If Groq returns invalid JSON, retry up to 3 times with an error-correction prompt: `"Your previous response was not valid JSON. Return only JSON. Error: {error}. Text: {text}"`.
5. Write `state["parsed_resume"]` and `state["parse_confidence"]` (1.0 if no LLM fallback needed, 0.85 if LLM was used, 0.6 if LLM retry was needed).
6. On unrecoverable failure, append to `state["errors"]` and return state with `parsed_resume: None`.

**Verification:** Integration test — pass a real PDF through orchestrator, assert `state["parsed_resume"]["personal"]["name"]` is not None and `state["parse_confidence"]` is between 0 and 1.

---

### STEP 9 — Normalization Agent (Full)

**What to do:**
Implement `app/agents/normalization_agent.py` fully. The agent must:

1. Read `state["parsed_resume"]["skills_raw"]`.
2. For each raw skill, run the 7-step normalization pipeline from Section 5 in order.
3. For step 4 (embedding similarity), call `embedding_service.embed([raw_skill])`, then call `chroma_service.query("skill_embeddings", embedding, n_results=1)`. If the top result's distance > `settings.emerging_skill_threshold`, classify as emerging.
4. For each emerging skill, upsert into the `emerging_skills` table: if the row exists, increment `seen_count`; if not, insert it.
5. For proficiency estimation, use Groq `settings.groq_model_fast` with a prompt: `"Given this work experience text, estimate proficiency level (1-4) for the skill '{skill}'. Return only a JSON object: {\"proficiency\": int, \"years\": float}". Text: {experience_text}"`.
6. Write `state["normalized_skills"]`, `state["inferred_skills"]`, `state["unknown_skills"]`, and `state["emerging_skills"]`.
7. Persist all normalized skills to `candidate_skills` table.

**Verification:** Unit test — `normalize_skill("K8s")` returns `{"canonical": "Kubernetes", ...}`. Unit test — `normalize_skill("PromptOps")` returns `{"status": "emerging"}`. Integration test — normalized skills count > 0 after full pipeline run.

---

### STEP 10 — Matching Agent (Full)

**What to do:**
Implement `app/agents/matching_agent.py` fully. The agent must:

1. Parse `state["job_description"]` using Groq `settings.groq_model_heavy` to extract `required_skills: list[str]` and `nice_to_have_skills: list[str]`. Use `JsonOutputParser`.
2. Embed all required and nice-to-have skills using `embedding_service.embed(skills)`.
3. For each JD skill embedding, query `chroma_service.query("skill_embeddings", embedding, n_results=1)`. Record the similarity score.
4. Apply threshold from `state["match_threshold"]` (fall back to `settings.default_match_threshold`). Skills below threshold count as gaps.
5. Compute weighted score using the formula from Section 5. Apply depth multiplier by looking up the candidate's `years_exp` for the matched skill from `state["normalized_skills"]`. Recency bonus = 1.1 if skill appears in experience from the last 2 years, else 1.0.
6. Determine verdict using the thresholds from Section 5.
7. Build `upskilling_paths`: for each gap skill, find the most similar skill in `state["normalized_skills"]` and suggest it as a bridge.
8. Write `state["match_score"]`, `state["skill_gaps"]`, `state["upskilling_paths"]`.
9. Persist match result to the `matches` table including `threshold_used`.

**Verification:** Integration test — pass engineer resume + Python engineer JD → assert `match_score > 60`. Integration test — pass designer resume + Python engineer JD → assert `match_score < 40`. Assert `len(skill_gaps) > 0` on the designer case.

---

### STEP 11 — FastAPI Application & Health Route

**What to do:**
Create `app/api/main.py`:
- Instantiate `FastAPI(title="Resume AI", version=settings.app_version)`.
- Add `prometheus_fastapi_instrumentator` middleware.
- Add startup event that checks PostgreSQL connectivity (try a `SELECT 1`), Redis ping, and ChromaDB collection existence. If any check fails, log a critical error but do not crash — set a global health flag.
- Register all routers from `app/api/routes/` with prefix `/api/v1`.
- Register `health.py` router without prefix.

Create `app/api/routes/health.py`. The `/health` endpoint must query each service (Postgres, Redis, ChromaDB, Groq) and return their individual statuses. For Groq, send a single-token completion with `llama-3.1-8b-instant` to verify connectivity.

Create `app/utils/logger.py` using `structlog` configured for JSON output in production and pretty output when `settings.debug` is True.

**Verification:** `uvicorn app.api.main:app --reload` starts. `curl http://localhost:8000/health` returns 200 with all four services `"ok"`.

---

### STEP 12 — Parse Route

**What to do:**
Create `app/api/routes/parse.py`. The `POST /api/v1/parse` endpoint must:

1. Apply `verify_api_key` and `rate_limiter` as dependencies.
2. Accept `file: UploadFile`, `job_id: Optional[str] = Form(None)`, `threshold: float = Form(0.7)`.
3. Validate file size against `settings.max_file_size_mb`. Return 413 if exceeded.
4. Detect file type from `file.content_type` and filename extension. Accept `application/pdf`, `application/vnd.openxmlformats-officedocument.wordprocessingml.document`, `text/plain`, `application/json`. Return 422 for any other type.
5. Build initial `ResumeState` with `raw_file_bytes`, `file_type`, `job_description` (None unless job_id resolves to a job in PostgreSQL), `match_threshold`.
6. Invoke `orchestrator.invoke(state)`. Wrap in `try/except` — on exception, return 500 with RFC 7807 error body.
7. Upsert candidate to PostgreSQL from `state["parsed_resume"]`. Store `chroma_doc_id` from ChromaDB upsert of the candidate's skill profile.
8. Return the full response schema from Section 7.

**Verification:** `curl -X POST /api/v1/parse -H "X-API-Key: ..." -F "file=@sample.pdf"` returns 200 with `candidate_id` and `skills` array populated.

---

### STEP 13 — Celery & Batch Route

**What to do:**
Create `app/tasks/celery_app.py`:
```python
from celery import Celery
from app.config import settings

celery_app = Celery("resume_ai", broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.task_serializer = "json"
celery_app.conf.result_serializer = "json"
```

Create `app/tasks/resume_tasks.py`. Define a Celery task `process_single_resume(file_bytes: bytes, file_type: str, job_id: str, threshold: float, batch_job_id: str)` that:
1. Builds state and calls `orchestrator.invoke`.
2. On success, increments `batch_jobs.completed` in Redis.
3. On failure, increments `batch_jobs.failed` and logs error.
4. When `completed + failed == total`, updates `batch_jobs.status` to `"done"` and fires webhook if configured.

Create `app/api/routes/batch.py`. The `POST /api/v1/parse/batch` endpoint must:
1. Accept up to 100 files, optional `job_id`, `threshold`, `webhook_url`.
2. Insert a row in `batch_jobs` with `status="queued"` and `total=len(files)`.
3. For each file, dispatch `process_single_resume.delay(...)` with `asyncio.gather` for the dispatches themselves (not the execution).
4. Update `batch_jobs.status` to `"processing"`.
5. Return 202 with `batch_job_id` and `status_url`.

Create `app/api/routes/batch.py` also handling `GET /api/v1/jobs/{batch_job_id}/status` — reads from `batch_jobs` table and returns status, counts, and `results_url` when done.

**Verification:** Submit 5 files in batch. Poll status URL every 2 seconds. After all complete, status becomes `"done"` and `results_url` is present.

---

### STEP 14 — Remaining Routes

**What to do:**
Create `app/api/routes/candidates.py`. `GET /api/v1/candidates/{id}/skills` must:
- Query `candidate_skills` joined to `skills` by `candidate_id`.
- Return the full skill profile schema from Section 7 including `inferred_skills`, `unknown_skills`, and `emerging_skills`.

Create `app/api/routes/match.py`. `POST /api/v1/match` must:
- Accept `candidate_id`, `job_description`, optional `required_skills`, optional `threshold`.
- Load normalized skills for the candidate from PostgreSQL.
- Build a minimal `ResumeState` with only skills populated (skip parsing and normalization nodes by invoking just the matching agent directly, not the full graph).
- Return the match response schema from Section 7.

Create `app/api/routes/skills.py`. `GET /api/v1/skills/taxonomy` must:
- Support query params `category`, `search` (ILIKE on name and aliases), `limit`, `offset`.
- Return paginated taxonomy response.

Create `app/services/webhook_service.py`. It must expose `fire_webhook(url: str, secret: str, payload: dict)` that:
- Signs the JSON payload with HMAC-SHA256 using the secret.
- POSTs to the URL with header `X-Signature: sha256=<hex>`.
- Retries 3 times with exponential backoff using `tenacity`.

**Verification:** All six routes return correct responses. Webhook delivery test: start a local HTTP server, register it, submit a batch, verify signed POST arrives on completion.

---

### STEP 15 — Observability

**What to do:**
Create `app/utils/metrics.py`. Define these Prometheus metrics using `prometheus_client`:
- `resume_parse_latency_seconds` — Histogram, labels: `file_type`, `status`
- `skill_normalization_latency_seconds` — Histogram, labels: `status`
- `match_latency_seconds` — Histogram, labels: `verdict`
- `batch_queue_depth` — Gauge
- `agent_error_total` — Counter, labels: `agent_name`, `error_type`

Instrument each agent node to record its histogram and error counter. The `prometheus_fastapi_instrumentator` handles HTTP-level metrics automatically.

Add `GET /metrics` endpoint (no auth) serving Prometheus text format.

**Verification:** After running 10 parse requests, `curl http://localhost:8000/metrics` returns lines containing `resume_parse_latency_seconds_bucket`.

---

### STEP 16 — Tests & Fixtures

**What to do:**
Create `tests/fixtures/` containing:
- `sample_engineer.pdf` — generate a minimal valid PDF using `pdfplumber`/`reportlab` in a setup script containing name, email, 2 jobs, and at least 5 skills including Python
- `sample_linkedin.json` — a minimal LinkedIn export JSON with `positions`, `skills`, `education` keys
- `sample_jd_python.txt` — a job description requiring Python, FastAPI, PostgreSQL

Create all unit tests from Section 10. Create all integration tests from Section 10. Add `conftest.py` with a pytest fixture that creates a test database (separate from dev) and runs migrations on it, then tears it down after the session.

Create `pytest.ini`:
```ini
[pytest]
asyncio_mode = auto
testpaths = tests
```

**Verification:** `pytest tests/unit/` — all pass. `pytest tests/integration/` — all pass. `pytest --co` shows at least 10 test items.

---

### STEP 17 — SDK Examples & Final Documentation

**What to do:**
Create `docs/api_examples/python_sdk_example.py` and `docs/api_examples/javascript_sdk_example.js` using the full examples from Section 11.

Create `docs/postman_collection.json` — a valid Postman Collection v2.1 JSON with one request per endpoint, pre-request script setting `X-API-Key` from a collection variable, and example responses.

Update `README.md` with:
- One-paragraph project description
- Prerequisites list
- Four-command quickstart (clone, configure, docker compose, first curl)
- Link to `/docs` for Swagger UI

**Verification:** `python docs/api_examples/python_sdk_example.py` runs against a live local server and prints a candidate ID.

---

### STEP 18 — Final Integration Smoke Test

**What to do:**
Run the following sequence in order. Each command must succeed before the next:

```bash
# 1. All services up
docker compose up -d

# 2. Migrations and seed
alembic upgrade head
python scripts/seed_taxonomy.py

# 3. Generate API key
python scripts/generate_api_key.py --name "smoke-test" > /tmp/api_key.txt
export API_KEY=$(cat /tmp/api_key.txt)

# 4. Health check
curl -f http://localhost:8000/health

# 5. Single parse
curl -f -X POST http://localhost:8000/api/v1/parse \
  -H "X-API-Key: $API_KEY" \
  -F "file=@tests/fixtures/sample_engineer.pdf"

# 6. Taxonomy browsing
curl -f "http://localhost:8000/api/v1/skills/taxonomy?search=python" \
  -H "X-API-Key: $API_KEY"

# 7. Full test suite
pytest tests/ -v

# 8. Load test (requires httpx[cli] or locust)
python scripts/load_test.py --concurrency 10 --total 50
```

Create `scripts/load_test.py` that submits `--total` resumes at `--concurrency` concurrency using `asyncio` + `httpx.AsyncClient` and prints p50/p95/p99 latency. Assert p95 < 10000ms.

**Verification:** All 8 commands exit with code 0. Load test prints p95 < 10s.

---

### Agent Error Handling Reference

At every step, if the agent encounters an error it must follow this decision tree:

```
Error raised?
  │
  ├─ Is it a transient error? (network timeout, DB connection, rate limit)
  │     └─ Retry up to 3 times with 2s exponential backoff
  │           Success → continue
  │           Still failing after 3 → classify as persistent
  │
  ├─ Is it a persistent error? (invalid file, schema violation, auth failure)
  │     └─ Do NOT retry
  │         Append structured error to state["errors"]:
  │           { "step": "<step_name>", "error": "<message>", "timestamp": "<iso>" }
  │         Return partial state (never raise, never halt)
  │
  └─ Is it a fatal infrastructure error? (Postgres down, Redis down)
        └─ Log at CRITICAL level
            Return 503 from API with Retry-After header
            Do not invoke LangGraph
```

---

## 13. Presentation Prompt

Use this prompt to generate slides, a pitch script, a GitHub README, or a live demo walkthrough.

```
You are preparing a technical presentation for a mixed audience of
engineering leads, product managers, and HR tech buyers.

Project: Multi-Agent AI Resume Intelligence System

Stack:
  Orchestration:  LangGraph (Python), 3 specialized agents
  LLM:            Groq API (llama-3.1-70b) for extraction and reasoning
  Embeddings:     sentence-transformers (all-MiniLM-L6-v2), runs locally
  Vector DB:      ChromaDB for semantic skill matching
  API:            FastAPI with full OpenAPI documentation
  Storage:        PostgreSQL (structured) + Redis (queue/cache)
  Async:          Celery workers for batch processing
  Deployment:     Docker Compose, cloud-ready

What the system does:
  1. Parses resumes from PDF, DOCX, TXT, and LinkedIn exports
  2. Normalizes raw skills to a canonical 5000+ skill taxonomy
  3. Flags skills not yet in the taxonomy as "emerging" for human review
  4. Semantically matches candidates to job descriptions with configurable thresholds
  5. Exposes everything via REST API with auth, rate limiting, and webhooks

Key differentiators vs traditional ATS:
  - "React.js" = "ReactJS" = "React"              (alias resolution)
  - TensorFlow + PyTorch → implies "Deep Learning" (skill inference)
  - New skills like "PromptOps" are flagged, not dropped  (emerging skill detection)
  - Weighted semantic scoring with gap analysis and upskilling suggestions
  - Configurable precision/recall threshold per request
  - < 10 second end-to-end latency per resume

Please generate:
  A) 10-slide presentation outline with talking points
  B) 3-minute elevator pitch script
  C) Technical deep-dive for engineering reviewers
  D) README for GitHub
  E) Live demo script with curl commands
```

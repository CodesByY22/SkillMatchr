<div align="center">
  <h1>🎯 SkillMatchr</h1>
  <p><strong>Multi-Agent AI System for Intelligent Resume Parsing, Skill-Set Matching, and API-Ready Talent Intelligence.</strong></p>
</div>

---

## ⚡ Overview

Recruitment teams process thousands of diverse resumes daily. Traditional ATS (Applicant Tracking Systems) rely on rigid keyword matching that misses qualified candidates and surfaces irrelevant ones. **SkillMatchr** solves this by leveraging a Multi-Agent AI architecture to ingest, normalize, and semantically match disparate candidate profiles against complex job descriptions in real time.

Built with enterprise-grade architecture, this platform exposes the entire AI pipeline through robust REST APIs, WebSockets for immediate frontend syncing, and a high-performance React frontend for talent managers.

---

## 🔥 Key Features

### 1. Multi-Agent Agentic Parsing & Intelligence Pipeline 
* **Universal Ingestion Agent:** Accurately extracts complex layouts across **PDFs**, **DOCX**, and **TXT** files directly into structured JSON schemas utilizing `gemini-2.5-flash` natively bound to Pydantic outputs.
* **Deep Feature Extraction:** Robust processing pulls granular metadata including verifiable **Certifications**, **Projects**, and academic **Publications**.
* **Skill Taxonomy Agent:** Normalizes unstandardized keywords (e.g., `React.js` -> `ReactJS`), recognizes hierarchical skill patterns (e.g., `PyTorch` implies `Deep Learning`), and categorizes emerging skills dynamically.
* **Semantic Engine:** Leverages vector similarity (`pgvector`) & Gemini Embeddings to detect deep candidate suitability (Cosine Similarity NDCG) rather than surface-layer Boolean matching.

### 2. High-Performance Live Dashboard
* **Realtime Syncing:** Employs JWT-authenticated WebSockets to sync data extraction to the Dashboard without user-polling.
* **Dynamic Applicant Indexing:** Server-side push-down filtering leveraging multi-column `PostgreSQL` indexing allowing recruiters to instantly query candidates.
* **Interactive UI:** Glassmorphism UI built in React and Tailwind CSS displaying dynamic metrics, candidate profiles, and live matching scores.

### 3. Production & Cloud-Ready Architecture
* **V1 REST API:** Fully OpenAPI / Swagger-documented endpoints (`/docs`).
* **PostgreSQL + pgvector:** Native vector search integration via Alembic database migrations.
* **Cloud Ready:** Optimized for zero-downtime deployment on Vercel (Frontend) and Render/Railway (Backend API).

---

## 🚀 Tech Stack

| Domain | Technology |
|---|---|
| **Frontend** | React 19, Vite, Tailwind CSS, Framer Motion, WebSockets, Lucide Icons |
| **Backend API** | Python 3.11+, FastAPI, Uvicorn, LangGraph, SQLAlchemy (Async) |
| **LLM & Embeddings** | Google Gemini (`gemini-2.5-flash`), Pydantic |
| **Database** | PostgreSQL with `pgvector` & Alembic Migrations (Hosted on Neon) |
| **Infrastructure** | Vercel (Frontend), Render (Backend) |

---

## 💻 Local Setup & Installation

### 1. Clone the Repository
```bash
git clone https://github.com/CodesByY22/SkillMatchr.git
cd SkillMatchr
```

### 2. Environment Setup

#### Backend Environment (`backend/.env`):
```env
DATABASE_URL=postgresql+asyncpg://user:password@host:port/dbname
JWT_SECRET=super-secret-skillmatchr-jwt-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
CORS_ORIGIN=http://localhost:5173,http://127.0.0.1:5173
MOCK_HRMS_ENABLED=True
MOCK_GMAIL_ENABLED=True
GEMINI_API_KEY=your_gemini_api_key_here
```

#### Frontend Environment (`frontend/.env`):
```env
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws
```

### 3. Launch Backend
```bash
# Set up Python virtual environment
python -m venv backend/venv

# Activate venv:
# Windows:
.\backend\venv\Scripts\activate
# Mac/Linux:
source backend/venv/bin/activate

# Install dependencies
pip install -r backend/requirements_local.txt

# Run database migrations
alembic upgrade head

# Seed initial demo candidates & users
python -m backend.scripts.seed

# Start FastAPI server
uvicorn backend.main:app --reload --port 8000
```

### 4. Launch Frontend
```bash
cd frontend
npm install
npm run dev
```

Open **`http://localhost:5173`** in your browser.

#### Demo Credentials:
- **Email**: `demo@recruitai.com`
- **Password**: `password123`

---

## 🌐 Cloud Deployment Guide

### Deploying Backend to Render
1. Create a **Web Service** on [Render](https://render.com) linked to this repository.
2. Build Command: `pip install -r backend/requirements.txt && alembic upgrade head`
3. Start Command: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
4. Set Environment Variables: `DATABASE_URL`, `JWT_SECRET`, `CORS_ORIGIN`.

### Deploying Frontend to Vercel
1. Import repository on [Vercel](https://vercel.com).
2. Framework Preset: **Vite**. Root Directory: `frontend`.
3. Set Environment Variables: `VITE_API_URL` and `VITE_WS_URL`.

---

## 📄 License
This project is open-source under the MIT License.

# RAG GenAI Assistant

Production-grade starter structure for building a Retrieval-Augmented Generation (RAG) assistant with a FastAPI backend and a React + Vite frontend.

## Project Structure

```text
backend/
  data/
  scripts/
  utils/
  routes/
  main.py
  requirements.txt
frontend/
  public/
  src/
  package.json
  vite.config.js
README.md
```

## Backend (FastAPI)

### Setup

```bash
cd backend
python -m venv .venv
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

### Run

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Key Endpoints

- `GET /` - service heartbeat message
- `GET /health` - liveness probe
- `GET /ready` - readiness probe
- `GET /docs` - OpenAPI docs

## Frontend (React + Vite)

### Setup

```bash
cd frontend
npm install
copy .env.example .env
```

### Run

```bash
npm run dev
```

Frontend defaults to `http://localhost:5173` and checks backend health at `http://localhost:8000/health`.
Set `VITE_API_BASE_URL` in `.env` to point to a different backend URL.

## Next Steps for RAG

- Add document ingestion scripts under `backend/scripts/`
- Store source data and vector artifacts under `backend/data/`
- Implement retrieval and generation routes under `backend/routes/`
- Add retrieval, reranking, and LLM orchestration modules in `backend/utils/`
- Add evaluation and observability for answer quality, latency, and cost

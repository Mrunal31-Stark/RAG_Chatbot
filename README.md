# RAG GenAI Assistant

Production-grade starter structure for building a Retrieval-Augmented Generation (RAG) assistant with a FastAPI backend and a React + Vite frontend.

## 6. Similarity Search Explanation
The system uses **cosine similarity** to compare the query vector with stored chunk vectors.

Why cosine similarity:
- Measures directional similarity in high-dimensional space
- Scale-invariant and widely used for semantic retrieval

Threshold filtering is applied to remove low-relevance matches before selecting top chunks.

Example:
- A query about **overfitting** retrieves chunks discussing generalization, regularization, validation, and model complexity.

## 7. Prompt Design Reasoning
The prompt is designed for strict grounding:
- **Context has highest priority**
- **Chat history is secondary** and only for continuity
- If context is insufficient, the model must return: **"I don't know"**

This structure reduces hallucination and enforces traceable responses.

Example prompt snippet:

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

### Frontend
```bash
cd frontend
npm install
copy .env.example .env
```

Set in `frontend/.env`:
```env
VITE_API_URL=http://localhost:8000
```

Run frontend:
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

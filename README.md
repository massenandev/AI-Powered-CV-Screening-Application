# CV Compass

An evidence-grounded RAG prototype for asking questions about 30 entirely fictional CVs. It uses a FastAPI modular monolith, React, PostgreSQL/pgvector, PyMuPDF, and Gemini. Answers expose the supporting candidate and PDF page; the product assists human review and must not make autonomous hiring decisions.

## Quick start

Requirements: Docker Desktop and a Gemini API key from Google AI Studio.

```bash
cp .env.example .env
# Set GEMINI_API_KEY in .env
docker compose up --build -d
docker compose exec api uv run python -m app.cli index
```

Open <http://localhost:5173>. API documentation is at <http://localhost:8000/docs>.

The default chat and embedding model names are configuration, not code. If a default is unavailable for your account, update `GEMINI_CHAT_MODEL` or `GEMINI_EMBEDDING_MODEL` using a model returned by Gemini's model-list endpoint. Embeddings are fixed at 768 dimensions to match the database migration; changing that value requires a migration and full reindex.

## Commands

```bash
make up                         # build and start all services
make index                      # idempotently index changed CVs
docker compose exec api uv run python -m app.cli index --force
make test                       # deterministic tests; no Gemini quota
make lint                       # lint, type-check, and build
make generate                   # regenerate all PDFs from fixtures
docker compose down             # retain database volume
docker compose down -v          # remove local indexed data
```

For local development, run PostgreSQL with `docker compose up db`, then `cd backend && uv sync && uv run uvicorn app.main:app --reload`; in another terminal use `cd frontend && npm install && npm run dev`. Point `DATABASE_URL` at localhost.

## Demo questions

- Who has Python and PostgreSQL experience?
- Compare the machine learning candidates.
- Which candidates speak French?
- Who has worked at a company that is not present in the CVs? (grounded refusal)

## Dataset and privacy

`data/cvs` contains 30 synthetic CVs produced by `backend/scripts/generate_cvs.py`. Names, contact details, employers, schools, histories, and portraits are fictional. The portrait sheet was generated with OpenAI's built-in image generation tool for this assessment; individual portraits are crops from that source. Regeneration is deterministic from the committed fixtures and portrait sheet.

## Troubleshooting

- `NOT_READY`: wait for PostgreSQL and run migrations (`docker compose exec api uv run alembic upgrade head`).
- Empty answers: run the indexing command and inspect `docker compose logs api`.
- Gemini 401/403: confirm the API key and model access.
- Dimension mismatch: restore `EMBEDDING_DIMENSIONS=768`, migrate intentionally, then force reindex.
- Browser cannot connect: verify `VITE_API_URL` and `CORS_ORIGINS` before rebuilding.

See [architecture.md](architecture.md), [decisions.md](decisions.md), and [DEMO.md](DEMO.md).


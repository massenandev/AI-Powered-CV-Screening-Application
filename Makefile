.PHONY: up down index test lint generate
up:
	docker compose up --build
down:
	docker compose down
index:
	docker compose exec api uv run python -m app.cli index
generate:
	cd backend && uv run python scripts/generate_cvs.py
test:
	cd backend && uv run pytest
	cd frontend && npm test -- --run
lint:
	cd backend && uv run ruff check . && uv run mypy app
	cd frontend && npm run lint && npm run build


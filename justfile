set dotenv-load

up:
    docker compose up -d postgres redis minio

dev: up
    cd backend && uv run uvicorn app.main:app --reload --port 8000

migrate:
    cd backend && uv run alembic upgrade head

test:
    cd backend && uv run pytest -q

lint:
    cd backend && uv run ruff check . && uv run ruff format --check . && uv run pyright && uv run lint-imports

seed:
    cd backend && PYTHONPATH=. uv run python ../scripts/seed.py

gen-api:
    cd frontend && pnpm gen-api

.PHONY: run dev install migrate migration test lint format

run:
	uvicorn app.main:app --host 0.0.0.0 --port 8000

dev:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

install:
	pip install -r requirements.txt

migrate:
	alembic upgrade head

migration:
	alembic revision --autogenerate -m "$(name)"

test:
	pytest tests/ -v

lint:
	ruff check app/

format:
	ruff format app/

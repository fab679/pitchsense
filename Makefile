.PHONY: setup test verify replay build dev clean

setup:
	uv sync --extra dev
	cd frontend && npm install && npm run build

test:
	uv run pytest -v

verify:
	uv run pytest -v
	uv run python -m backend.generate.gen 21

replay:
	@echo "Starting PitchSense Match Intelligence Studio on http://localhost:8000 ..."
	uv run uvicorn backend.api.app:app --host 0.0.0.0 --port 8000

dev:
	uv run uvicorn backend.api.app:app --host 0.0.0.0 --port 8000 --reload &
	cd frontend && npm run dev

build:
	cd frontend && npm run build

clean:
	rm -rf .pytest_cache .venv frontend/dist frontend/node_modules

.PHONY: check format format-check install lint mypy player-page test

install:
	uv sync --locked

test:
	uv run pytest

format:
	uv run ruff format .

format-check:
	uv run ruff format --check .

lint:
	uv run ruff check .

mypy:
	uv run mypy

player-page:
	uv run uvicorn llm_system.server:create_runtime_app --factory --host 127.0.0.1 --port 8000 & \
	api_pid=$$!; \
	trap 'kill $$api_pid 2>/dev/null || true' EXIT INT TERM; \
	uv run streamlit run src/llm_system/player_page.py

check: format-check lint mypy test

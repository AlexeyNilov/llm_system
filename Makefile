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
	uv run streamlit run src/llm_system/player_page.py

check: format-check lint mypy test

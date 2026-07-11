.PHONY: check format format-check install lint mypy test

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

check: format-check lint mypy test

.PHONY: run format lint install-dev

dev:
	uv run python -m robak.main

build:
	uv run python -m robak.build

format:
	uv run ruff format .

lint:
	uv run ruff check .

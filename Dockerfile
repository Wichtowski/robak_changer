FROM python:3.12-slim AS app

COPY --from=ghcr.io/astral-sh/uv:0.11.26 /uv /uvx /bin/

ENV PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

COPY pyproject.toml uv.lock ./
COPY src ./src

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-editable

CMD ["/app/.venv/bin/robak-changer"]

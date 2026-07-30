FROM python:3.13-slim-bookworm AS base

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Camada de dependências isolada para aproveitar cache do Docker
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

# Código da aplicação (apenas o necessário para os routers ativos em main.py)
COPY main.py ./
COPY auth ./auth
COPY classes ./classes
COPY routers ./routers
COPY queries ./queries
COPY alembic ./alembic
COPY alembic.ini ./
COPY entrypoint.sh ./

RUN uv sync --frozen --no-dev \
    && mkdir -p data \
    && chmod +x entrypoint.sh \
    && useradd --create-home --uid 1000 appuser \
    && chown -R appuser:appuser /app

USER appuser

ENV PATH="/app/.venv/bin:${PATH}"

EXPOSE 8088

ENTRYPOINT ["./entrypoint.sh"]

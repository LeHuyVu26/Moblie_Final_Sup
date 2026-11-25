# syntax=docker/dockerfile:1

FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN useradd --create-home --shell /bin/bash appuser \
    && mkdir -p /data

COPY pyproject.toml README.md ./
COPY app/ ./app/
COPY migrations/ ./migrations/
COPY alembic.ini ./

RUN pip install --no-cache-dir . \
    && rm -rf /app/build /app/*.egg-info \
    && chown -R appuser:appuser /app /data

USER appuser

EXPOSE 8000

CMD ["sh", "-c", "alembic upgrade head && exec uvicorn app.main:app --host \"${HOST:-0.0.0.0}\" --port \"${PORT:-8000}\""]

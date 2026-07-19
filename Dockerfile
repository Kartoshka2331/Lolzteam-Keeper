FROM python:3.13-slim AS builder

ENV PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY pyproject.toml ./

RUN pip install --no-cache-dir --prefix=/install \
    "aiohttp" \
    "apscheduler" \
    "loguru" \
    "pydantic" \
    "pydantic-settings" \
    "tenacity"


FROM python:3.13-slim AS runtime

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 TZ=Europe/Moscow

RUN useradd --create-home --uid 1000 appuser

WORKDIR /app

COPY --from=builder /install /usr/local

COPY config ./config
COPY models ./models
COPY scheduler ./scheduler
COPY services ./services
COPY utils ./utils
COPY main.py ./main.py

RUN mkdir -p /app/logs && chown -R appuser:appuser /app

USER appuser

CMD ["python", "main.py"]
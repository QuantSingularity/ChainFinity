FROM python:3.11-slim AS builder

ARG INSTALL_ML=true

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt backend/requirements-ml.txt ./
RUN pip install --prefix=/install -r requirements.txt \
    && if [ "$INSTALL_ML" = "true" ]; then pip install --prefix=/install -r requirements-ml.txt; fi

FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PATH="/install/bin:$PATH" \
    TF_CPP_MIN_LOG_LEVEL=2 \
    AI_ARTIFACTS_DIR=/app/ai_artifacts

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libpq5 \
        curl \
        netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /install /usr/local

RUN groupadd -r chainfinity && useradd -r -g chainfinity -d /app -s /sbin/nologin chainfinity

COPY --chown=chainfinity:chainfinity backend/ .
COPY --chown=chainfinity:chainfinity ai_models/ ./ai_models/
COPY --chown=chainfinity:chainfinity backend/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

RUN mkdir -p /app/logs /app/ai_artifacts && chown chainfinity:chainfinity /app/logs /app/ai_artifacts

USER chainfinity

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2", "--log-level", "info"]

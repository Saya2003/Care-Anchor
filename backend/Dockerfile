# ── Stage 1: builder ─────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt && \
    rm -rf /root/.cache/pip


# ── Stage 2: runtime ─────────────────────────────────────────────────
FROM python:3.12-slim

RUN groupadd -r careanchor && useradd -r -g careanchor -d /app -s /sbin/nologin careanchor && \
    mkdir -p /app && chown careanchor:careanchor /app

COPY --from=builder /install /usr/local

WORKDIR /app
COPY --chown=careanchor:careanchor . .

USER careanchor

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2", "--log-level", "info"]

# Multi-stage secure container build for Gemini Live Bot
# Conforms to Google Cloud DevOps, Security & Quality Standards (Rules 5 & 6)

FROM python:3.13-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy packaging manifests
COPY pyproject.toml .

# Install dependencies into virtual environment
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

# ==========================================
# Production Runtime Stage
# ==========================================
FROM python:3.13-slim AS runner

WORKDIR /app

# Create non-privileged user for security hardening
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /bin/bash -m appuser

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application source code
COPY app/ ./app/
COPY pyproject.toml .

# Set ownership to non-root user
RUN chown -R appuser:appgroup /app

# Switch to non-root execution
USER 10001

# Cloud Run default port & configuration
ENV PORT=8080
ENV PYTHONUNBUFFERED=1
ENV GOOGLE_GENAI_USE_VERTEXAI=FALSE
EXPOSE 8080

# Cloud Run Healthcheck (Rule 6: Cloud Run Liveness Probe)
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8080}/health || exit 1

# Start Google ADK Web UI Server on Cloud Run
CMD ["sh", "-c", "adk web . --host 0.0.0.0 --port ${PORT:-8080} --session_service_uri memory://"]

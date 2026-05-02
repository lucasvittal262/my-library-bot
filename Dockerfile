FROM python:3.13-slim AS builder

# Install build dependencies for compiling Python packages (torch, transformers, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set working directory
WORKDIR /build

# Copy dependency files first (better layer caching)
COPY pyproject.toml ./

# Install dependencies using uv (creates virtual environment)
# This will compile wheels for heavy dependencies (torch, transformers, etc.)
RUN uv pip install --system --no-cache \
    -r pyproject.toml


# Copy project source code
COPY . .

# Install project in editable mode
RUN uv pip install --system --no-cache -e .


# RUNTIME STAGE
FROM python:3.13-slim AS runtime

# Install minimal runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy Python environment from builder
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy project files
COPY --from=builder /build /app

# Create non-root user for security
RUN useradd -m -u 1000 -s /bin/bash appuser && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    SKIP_INTERACTIVE=true \
    BIGQUERY_ENABLED=true

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 -c "import sys; sys.exit(0)"

# Container entry point (non-interactive mode)
ENTRYPOINT ["python3", "src/main.py"]

# Default arguments (can be overridden)
CMD ["--help"]
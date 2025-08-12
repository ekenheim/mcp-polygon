# Use Python 3.12 slim image as base
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install uv for dependency management
RUN pip install --no-cache-dir uv

# Install Python dependencies with better error handling
RUN uv sync --frozen || (echo "uv sync failed, trying without --frozen" && uv sync)

# Copy application code
COPY . .

# Create directory for ticker database
RUN mkdir -p ticker_db

# Make scripts executable
RUN chmod +x scripts/entrypoint.sh scripts/health_check.py

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV MCP_HTTP_TRANSPORT=true
ENV PORT=8000

# Expose port for HTTP transport
EXPOSE 8000

# Add health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python scripts/health_check.py

# Use entrypoint script
ENTRYPOINT ["scripts/entrypoint.sh"]

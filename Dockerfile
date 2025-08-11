# Use Python 3.12 slim image as base
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install uv for dependency management
RUN pip install uv

# Install Python dependencies
RUN uv sync --frozen

# Copy application code
COPY . .

# Create directory for ticker database
RUN mkdir -p ticker_db

# Make entrypoint script executable
RUN chmod +x scripts/entrypoint.sh

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV MCP_HTTP_TRANSPORT=true
ENV PORT=8000

# Expose port for HTTP transport
EXPOSE 8000

# Add health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health', timeout=5)" || exit 1

# Use entrypoint script
ENTRYPOINT ["scripts/entrypoint.sh"]

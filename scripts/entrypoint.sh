#!/bin/bash

# Entrypoint script for MCP Polygon Server
# This script handles different transport modes and provides startup logging

set -e

echo "🚀 Starting MCP Polygon Server..."

# Check if Polygon API key is set
if [ -z "$POLYGON_API_KEY" ]; then
    echo "❌ POLYGON_API_KEY environment variable is not set"
    echo "   Please set your Polygon API key in the .env file or environment"
    echo "   You can get a free API key at: https://polygon.io/"
    exit 1
fi

# Check if ticker_db directory exists
if [ ! -d "/app/ticker_db" ]; then
    echo "📁 Creating ticker_db directory..."
    mkdir -p /app/ticker_db
fi

# Determine transport mode
if [ "$MCP_HTTP_TRANSPORT" = "true" ]; then
    echo "🌐 Starting with HTTP transport on port ${PORT:-8000}"
    export PORT=${PORT:-8000}
    exec uv run python server.py
else
    echo "📡 Starting with stdio transport"
    exec uv run python server.py
fi

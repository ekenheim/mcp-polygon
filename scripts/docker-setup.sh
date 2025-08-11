#!/bin/bash

# Docker Setup Script for MCP Polygon Server
# This script helps automate the Docker deployment process

set -e

echo "🚀 Setting up MCP Polygon Server with Docker..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    if [ -f env.example ]; then
        cp env.example .env
        echo "✅ .env file created. Please edit it and add your Polygon API key."
        echo "   You can get a free API key at: https://polygon.io/"
        echo ""
        echo "📋 Next steps:"
        echo "   1. Edit .env file and add your POLYGON_API_KEY"
        echo "   2. Run: docker-compose up -d"
        echo "   3. Check logs: docker-compose logs mcp-server"
        exit 0
    else
        echo "❌ env.example file not found. Please create a .env file manually."
        exit 1
    fi
fi

# Check if POLYGON_API_KEY is set
if ! grep -q "POLYGON_API_KEY=your_polygon_api_key_here" .env; then
    echo "✅ .env file appears to be configured."
else
    echo "⚠️  Please edit .env file and add your Polygon API key before continuing."
    echo "   You can get a free API key at: https://polygon.io/"
    exit 1
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p ticker_db
mkdir -p logs

# Build and start the containers
echo "🔨 Building and starting containers..."
docker-compose up -d --build

# Wait a moment for the container to start
echo "⏳ Waiting for container to start..."
sleep 5

# Check container status
echo "📊 Checking container status..."
if docker-compose ps | grep -q "Up"; then
    echo "✅ Container is running successfully!"
    echo ""
    echo "📋 Useful commands:"
    echo "   View logs: docker-compose logs mcp-server"
    echo "   Stop server: docker-compose down"
    echo "   Restart server: docker-compose restart"
    echo "   Access shell: docker exec -it mcp-polygon-server /bin/bash"
    echo ""
    echo "🎉 MCP Polygon Server is now running in Docker!"
else
    echo "❌ Container failed to start. Check logs with: docker-compose logs mcp-server"
    exit 1
fi

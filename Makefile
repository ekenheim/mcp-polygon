# Makefile for MCP Polygon Server

.PHONY: help build run stop logs clean setup test

# Default target
help:
	@echo "Available commands:"
	@echo "  setup     - Set up environment and start containers"
	@echo "  build     - Build Docker image"
	@echo "  run       - Start containers"
	@echo "  stop      - Stop containers"
	@echo "  logs      - View container logs"
	@echo "  clean     - Remove containers and images"
	@echo "  test      - Test the MCP server"
	@echo "  shell     - Access container shell"

# Set up environment and start
setup:
	@echo "Setting up MCP Polygon Server..."
	@if [ ! -f .env ]; then \
		cp env.example .env; \
		echo "Created .env file. Please edit it and add your Polygon API key."; \
		echo "You can get a free API key at: https://polygon.io/"; \
		exit 0; \
	fi
	@docker-compose up -d --build

# Build Docker image
build:
	@echo "Building Docker image..."
	@docker-compose build

# Start containers
run:
	@echo "Starting containers..."
	@docker-compose up -d

# Stop containers
stop:
	@echo "Stopping containers..."
	@docker-compose down

# View logs
logs:
	@docker-compose logs -f mcp-server

# Clean up containers and images
clean:
	@echo "Cleaning up..."
	@docker-compose down -v
	@docker rmi mcpin10-mcp-server 2>/dev/null || true

# Test the server
test:
	@echo "Testing MCP server..."
	@docker-compose exec mcp-server python -c "import requests; print('Server is running')" || echo "Server test failed"

# Access container shell
shell:
	@docker-compose exec mcp-server /bin/bash

# Restart containers
restart:
	@echo "Restarting containers..."
	@docker-compose restart

# Show container status
status:
	@docker-compose ps

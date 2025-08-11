# Docker Setup for MCP Polygon Server

This guide will help you containerize and deploy the MCP Polygon Server for self-hosting.

## Prerequisites

- Docker and Docker Compose installed on your system
- A Polygon.io API key (get one at https://polygon.io/)

## Quick Start

1. **Clone the repository and navigate to it:**
   ```bash
   git clone <repository-url>
   cd MCPin10
   ```

2. **Option A: Use the setup script (Recommended):**
   ```bash
   # Windows
   .\scripts\docker-setup.ps1
   
   # Linux/Mac
   ./scripts/docker-setup.sh
   ```

3. **Option B: Use Makefile:**
   ```bash
   make setup
   ```

4. **Option C: Manual setup:**
   ```bash
   # Copy the example environment file
   cp env.example .env
   
   # Edit .env and add your Polygon API key
   nano .env
   
   # Build and run with Docker Compose
   docker-compose up -d
   ```

5. **Check if the service is running:**
   ```bash
   docker-compose ps
   docker-compose logs mcp-server
   ```

## Manual Docker Build

If you prefer to build manually:

```bash
# Build the image
docker build -t mcp-polygon-server .

# Run the container
docker run -d \
  --name mcp-polygon-server \
  -e POLYGON_API_KEY=your_api_key_here \
  -v $(pwd)/ticker_db:/app/ticker_db \
  -p 8000:8000 \
  mcp-polygon-server
```

## Configuration

### Environment Variables

- `POLYGON_API_KEY` (required): Your Polygon.io API key
- `DEBUG` (optional): Set to `true` for debug logging
- `PORT` (optional): Custom port (default: 8000)

### Volumes

- `./ticker_db:/app/ticker_db`: Persists the ChromaDB ticker database
- `./logs:/app/logs`: Mounts logs directory (optional)

### Ports

- `8000`: HTTP port for the MCP server (if using HTTP transport)

## Usage

### With MCP Client

The server runs using stdio transport by default. To connect with an MCP client:

```bash
# Using the MCP CLI
mcp dev server.py

# Or connect to the running container
docker exec -it mcp-polygon-server python server.py
```

### Available Tools

The server provides various financial data tools:

- `stock_price`: Get current stock prices
- `stock_info`: Get detailed stock information
- `income_statement`: Get financial statements
- `get_aggregates`: Get historical price data
- `get_ticker_news`: Get news for a ticker
- And many more...

## Troubleshooting

### Check Container Status
```bash
docker-compose ps
docker-compose logs mcp-server
```

### Access Container Shell
```bash
docker exec -it mcp-polygon-server /bin/bash
```

### Rebuild Container
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### View Real-time Logs
```bash
docker-compose logs -f mcp-server
```

### Using Makefile (Alternative Commands)

The project includes a Makefile for convenient operations:

```bash
make help      # Show all available commands
make setup     # Set up environment and start containers
make build     # Build Docker image
make run       # Start containers
make stop      # Stop containers
make logs      # View container logs
make clean     # Remove containers and images
make test      # Test the MCP server
make shell     # Access container shell
make restart   # Restart containers
make status    # Show container status
```

## Production Deployment

For production deployment, consider:

1. **Security:**
   - Use Docker secrets for API keys
   - Run container as non-root user
   - Enable Docker content trust

2. **Monitoring:**
   - Set up health checks
   - Configure log aggregation
   - Monitor resource usage

3. **Scaling:**
   - Use Docker Swarm or Kubernetes
   - Set up load balancing
   - Configure auto-scaling

## Example Production docker-compose.yml

```yaml
version: '3.8'

services:
  mcp-server:
    build: .
    container_name: mcp-polygon-server
    environment:
      - POLYGON_API_KEY=${POLYGON_API_KEY}
    volumes:
      - ticker_data:/app/ticker_db
    ports:
      - "8000:8000"
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '0.5'
    healthcheck:
      test: ["CMD", "python", "-c", "import requests; requests.get('http://localhost:8000/health', timeout=5)"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  ticker_data:
    driver: local
```

## Support

For issues and questions:
- Check the logs: `docker-compose logs mcp-server`
- Verify your API key is correct
- Ensure all dependencies are properly installed
- Check network connectivity for API calls

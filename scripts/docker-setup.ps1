# Docker Setup Script for MCP Polygon Server (PowerShell)
# This script helps automate the Docker deployment process on Windows

param(
    [switch]$SkipChecks
)

Write-Host "🚀 Setting up MCP Polygon Server with Docker..." -ForegroundColor Green

# Check if Docker is installed
if (-not $SkipChecks) {
    try {
        docker --version | Out-Null
        Write-Host "✅ Docker is installed" -ForegroundColor Green
    }
    catch {
        Write-Host "❌ Docker is not installed. Please install Docker Desktop first." -ForegroundColor Red
        exit 1
    }

    # Check if Docker Compose is installed
    try {
        docker-compose --version | Out-Null
        Write-Host "✅ Docker Compose is installed" -ForegroundColor Green
    }
    catch {
        Write-Host "❌ Docker Compose is not installed. Please install Docker Compose first." -ForegroundColor Red
        exit 1
    }
}

# Check if .env file exists
if (-not (Test-Path ".env")) {
    Write-Host "📝 Creating .env file from template..." -ForegroundColor Yellow
    if (Test-Path "env.example") {
        Copy-Item "env.example" ".env"
        Write-Host "✅ .env file created. Please edit it and add your Polygon API key." -ForegroundColor Green
        Write-Host "   You can get a free API key at: https://polygon.io/" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "📋 Next steps:" -ForegroundColor Yellow
        Write-Host "   1. Edit .env file and add your POLYGON_API_KEY" -ForegroundColor White
        Write-Host "   2. Run: docker-compose up -d" -ForegroundColor White
        Write-Host "   3. Check logs: docker-compose logs mcp-server" -ForegroundColor White
        exit 0
    }
    else {
        Write-Host "❌ env.example file not found. Please create a .env file manually." -ForegroundColor Red
        exit 1
    }
}

# Check if POLYGON_API_KEY is set
$envContent = Get-Content ".env" -Raw
if ($envContent -match "POLYGON_API_KEY=your_polygon_api_key_here") {
    Write-Host "⚠️  Please edit .env file and add your Polygon API key before continuing." -ForegroundColor Yellow
    Write-Host "   You can get a free API key at: https://polygon.io/" -ForegroundColor Cyan
    exit 1
}
else {
    Write-Host "✅ .env file appears to be configured." -ForegroundColor Green
}

# Create necessary directories
Write-Host "📁 Creating necessary directories..." -ForegroundColor Yellow
if (-not (Test-Path "ticker_db")) {
    New-Item -ItemType Directory -Path "ticker_db" | Out-Null
}
if (-not (Test-Path "logs")) {
    New-Item -ItemType Directory -Path "logs" | Out-Null
}

# Build and start the containers
Write-Host "🔨 Building and starting containers..." -ForegroundColor Yellow
try {
    docker-compose up -d --build
}
catch {
    Write-Host "❌ Failed to start containers. Check if Docker Desktop is running." -ForegroundColor Red
    exit 1
}

# Wait a moment for the container to start
Write-Host "⏳ Waiting for container to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Check container status
Write-Host "📊 Checking container status..." -ForegroundColor Yellow
try {
    $status = docker-compose ps
    if ($status -match "Up") {
        Write-Host "✅ Container is running successfully!" -ForegroundColor Green
        Write-Host ""
        Write-Host "📋 Useful commands:" -ForegroundColor Yellow
        Write-Host "   View logs: docker-compose logs mcp-server" -ForegroundColor White
        Write-Host "   Stop server: docker-compose down" -ForegroundColor White
        Write-Host "   Restart server: docker-compose restart" -ForegroundColor White
        Write-Host "   Access shell: docker exec -it mcp-polygon-server /bin/bash" -ForegroundColor White
        Write-Host ""
        Write-Host "🎉 MCP Polygon Server is now running in Docker!" -ForegroundColor Green
    }
    else {
        Write-Host "❌ Container failed to start. Check logs with: docker-compose logs mcp-server" -ForegroundColor Red
        exit 1
    }
}
catch {
    Write-Host "❌ Failed to check container status." -ForegroundColor Red
    exit 1
}

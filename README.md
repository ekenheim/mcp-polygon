# MCP Polygon.io Server

A comprehensive Model Context Protocol (MCP) server that provides access to Polygon.io's financial data API. This server offers real-time and historical market data, company information, financial statements, and more through a standardized MCP interface.

## Features 🚀

- **Real-time Market Data**: Access live trades, quotes, and market events
- **Historical Data**: Get historical price data, dividends, splits, and more
- **Company Information**: Retrieve detailed company profiles and financial data
- **Financial Statements**: Access income statements, balance sheets, and cash flow data
- **Market Analysis**: Get market status, gainers/losers, and trading sessions
- **Options Data**: Retrieve options contracts and snapshot data
- **News & Events**: Access company news and earnings data
- **Docker Support**: Easy deployment with Docker and Docker Compose
- **Kubernetes Ready**: Includes K8s deployment configurations

## Quick Start 🏃‍♂️

### Option 1: Docker (Recommended)

1. **Clone the repository**:
   ```bash
   git clone https://github.com/ekenheim/mcp-polygon
   cd mcp-polygon
   ```

2. **Set up environment**:
   ```bash
   cp env.example .env
   # Edit .env and add your Polygon API key
   ```

3. **Run with Docker Compose**:
   ```bash
   docker-compose up -d
   ```

4. **Check logs**:
   ```bash
   docker-compose logs mcp-server
   ```

### Option 2: Local Development

1. **Clone and setup**:
   ```bash
   git clone https://github.com/ekenheim/mcp-polygon
   cd mcp-polygon
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   uv sync
   ```

2. **Set API key**:
   ```bash
   export POLYGON_API_KEY=your_polygon_api_key_here
   ```

3. **Run the server**:
   ```bash
   uv run python server.py
   ```

## API Key Setup 🔑

1. Get a free API key from [Polygon.io](https://polygon.io/)
2. Set it in your `.env` file or environment variables
3. For real-time data, consider upgrading to a paid plan

## Available Tools 🛠️

### Market Data
- `get_last_trade(ticker)` - Get the most recent trade
- `get_last_quote(ticker)` - Get the most recent quote
- `get_previous_close(ticker)` - Get previous day's data
- `get_aggregates(ticker, multiplier, timespan, from_date, to_date)` - Get historical aggregates
- `get_intraday_aggregates(ticker, multiplier, timespan, from_date, to_date)` - Get intraday data with session info

### Company Information
- `stock_info(ticker)` - Get company background information
- `get_ticker_exchange_info(ticker)` - Get exchange and listing details
- `search_tickers(search, market, active)` - Search for ticker symbols

### Financial Data
- `income_statement(ticker)` - Get quarterly income statements
- `get_balance_sheet(ticker)` - Get balance sheet data
- `get_cash_flow(ticker)` - Get cash flow statements
- `get_earnings(ticker)` - Get earnings data
- `get_dividends(ticker)` - Get dividend history
- `get_splits(ticker)` - Get stock split history

### Market Analysis
- `get_market_status()` - Get current market status
- `get_market_gainers_losers(direction)` - Get top gainers/losers
- `get_market_hours_info()` - Get trading hours information
- `get_market_holidays()` - Get upcoming market holidays

### Options Data
- `get_options_contracts(underlying_asset)` - Get options contracts
- `get_options_snapshot(underlying_asset)` - Get options snapshot data

### News & Events
- `get_ticker_news(ticker)` - Get company news
- `get_analyst_ratings(ticker)` - Get analyst ratings
- `get_short_interest(ticker)` - Get short interest data

### Economic Data
- `get_treasury_yields()` - Get treasury yield data
- `get_inflation_data()` - Get inflation indicators

## Docker Images 🐳

The project automatically builds Docker images on GitHub Actions:

```bash
# Pull a specific version (recommended for production)
docker pull ghcr.io/ekenheim/mcp-polygon:v1.1.0

# Run with environment variable
docker run -e POLYGON_API_KEY=your_key ghcr.io/ekenheim/mcp-polygon:v1.1.0

# Or pull the latest from main branch (development)
docker pull ghcr.io/ekenheim/mcp-polygon:main
```

## Kubernetes Deployment ☸️

### Option 1: Using the provided k8s-deployment.yaml

1. **Create the secret first**:
   ```bash
   # Create the secret with your API key
   kubectl create secret generic polygon-api-secret \
     --from-literal=api-key=your_polygon_api_key_here \
     -n your-namespace
   ```

2. **Deploy the application**:
   ```bash
   kubectl apply -f k8s-deployment.yaml
   ```

### Option 2: Using Helm (recommended for production)

1. **Create the secret** (see `k8s-secret-example.yaml`):
   ```bash
   # Encode your API key
   echo -n "your_polygon_api_key_here" | base64
   
   # Apply the secret
   kubectl apply -f k8s-secret-example.yaml
   ```

2. **Update your HelmRelease** to include the API key:
   ```yaml
   env:
     POLYGON_API_KEY:
       valueFrom:
         secretKeyRef:
           name: mcp-polygon
           key: POLYGON_API_KEY
     MCP_HTTP_TRANSPORT: "true"
     PORT: "8000"
   ```

### Option 3: Direct kubectl deployment

```bash
# Create namespace
kubectl create namespace datasci

# Create secret
kubectl create secret generic mcp-polygon \
  --from-literal=POLYGON_API_KEY=your_polygon_api_key_here \
  -n datasci

# Deploy
kubectl apply -f k8s-deployment.yaml
```

## Development 🧪

### Testing with MCP Inspector

```bash
# Install MCP Inspector
pip install mcp-inspector

# Test the server
mcp dev server.py
```

### Local Testing

```bash
# Run the server
uv run python server.py

# In another terminal, run the agent
uv run python agent.py
```

## Configuration ⚙️

### Environment Variables

- `POLYGON_API_KEY` - Your Polygon.io API key (required)
- `MCP_HTTP_TRANSPORT` - Set to "true" for HTTP transport (default: false)
- `PORT` - Port for HTTP transport (default: 8000)
- `DEBUG` - Enable debug logging (default: false)

### Docker Configuration

The `docker-compose.yml` includes:
- Volume mounting for persistent data
- Environment variable configuration
- Health checks
- Logging configuration

## API Limitations 📊

- **Free Tier**: Limited to basic endpoints (previous close, ticker info, market status)
- **Paid Plans**: Access to real-time trades, quotes, and advanced features
- **Rate Limits**: Vary by subscription level

## Contributing 🤝

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License 📄

This project is licensed under the MIT License.

## Support 💬

- **Issues**: [GitHub Issues](https://github.com/ekenheim/mcp-polygon/issues)
- **Polygon.io API**: [Documentation](https://polygon.io/docs/)
- **MCP Protocol**: [Specification](https://modelcontextprotocol.io/)

## Author 👨‍💻

**Ekenheim** - [GitHub](https://github.com/ekenheim)

---

**Note**: This server requires a Polygon.io API key. Some endpoints require paid subscriptions for real-time data access.

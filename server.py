import os
import json
from datetime import datetime, timedelta, timezone, date
from typing import Dict, Any, List, Optional, Union, Literal

import requests
from colorama import Fore
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

# Load environment variables from .env file
load_dotenv()

# Create server
mcp = FastMCP("polygonserver")

# Add in a prompt function
@mcp.prompt()
def stock_summary(stock_data:str) -> str:
    """Prompt template for summarising stock price"""
    return f"""You are a helpful financial assistant designed to summarise stock data.
                Using the information below, summarise the pertintent points relevant to stock price movement
                Data {stock_data}"""
                
# Add in a resource function
import chromadb

# Initialize ChromaDB client
chroma_client = chromadb.PersistentClient(path="ticker_db")

# Get or create the collection
try:
    collection = chroma_client.get_collection(name="stock_tickers")
except Exception:
    # If collection doesn't exist, create it
    collection = chroma_client.create_collection(name="stock_tickers")
@mcp.resource("tickers://search/{stock_name}")
def list_tickers(stock_name:str)->str: 
    """This resource allows you to find a stock ticker by passing through a stock name e.g. Google, Bank of America etc. 
        It returns the result from a vector search using a similarity metric. 
    Args:
        stock_name: Name of the stock you want to find the ticker for
        Example payload: "Protor and Gamble"

    Returns:
        str:"Ticker: Last Price" 
        Example Respnse 
        {'ids': [['41', '30']], 'embeddings': None, 'documents': [['AZN - ASTRAZENECA PLC', 'NVO - NOVO NORDISK A S']], 'uris': None, 'included': ['metadatas', 'documents', 'distances'], 'data': None, 'metadatas': [[None, None]], 'distances': [[1.1703131198883057, 1.263759970664978]]}
        
    """
    try:
        results = collection.query(query_texts=[stock_name], n_results=1) 
        return str(results)
    except Exception as e:
        return f"Error searching for ticker '{stock_name}': {str(e)}" 
    
# Internal helpers for Polygon.io
def _require_polygon_api_key() -> str:
    api_key = os.environ.get("POLYGON_API_KEY")
    if not api_key:
        raise RuntimeError("POLYGON_API_KEY environment variable is not set")
    return api_key


def _polygon_get(path: str, params: Dict[str, Any] | None = None) -> Dict[str, Any]:
    api_key = _require_polygon_api_key()
    base_url = "https://api.polygon.io"
    url = f"{base_url}{path}"
    params = dict(params or {})
    params["apiKey"] = api_key
    response = requests.get(url, params=params, timeout=20)
    response.raise_for_status()
    return response.json()


def _iso_date(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d")


# Build server function
@mcp.tool()
def stock_price(stock_ticker: str) -> str:
    """This tool returns the last known price for a given stock ticker.
    Args:
        stock_ticker: a alphanumeric stock ticker 
        Example payload: "NVDA"

    Returns:
        str:"Ticker: Last Price" 
        Example Respnse "NVDA: $100.21" 
        """
    # Fetch last 30 days of daily closes from Polygon aggregates
    end_dt = datetime.now(timezone.utc)
    start_dt = end_dt - timedelta(days=30)
    path = f"/v2/aggs/ticker/{stock_ticker.upper()}/range/1/day/{_iso_date(start_dt)}/{_iso_date(end_dt)}"
    data = _polygon_get(path, params={"adjusted": "true", "sort": "asc", "limit": 5000})

    results: List[Dict[str, Any]] = data.get("results", []) or []
    closes = [
        {
            "date": datetime.fromtimestamp(point.get("t", 0) / 1000, tz=timezone.utc).strftime(
                "%Y-%m-%d"
            ),
            "close": point.get("c"),
        }
        for point in results
        if isinstance(point, dict)
    ]
    print(Fore.YELLOW + str(closes))
    return str(f"Stock price over the last month for {stock_ticker}: {closes}")

# Add in a stock info tool 
@mcp.tool()
def stock_info(stock_ticker: str) -> str:
    """This tool returns information about a given stock given it's ticker.
    Args:
        stock_ticker: a alphanumeric stock ticker
        Example payload: "IBM"

    Returns:
        str:information about the company
        Example Respnse "Background information for IBM: {'address1': 'One New Orchard Road', 'city': 'Armonk', 'state': 'NY', 'zip': '10504', 'country': 'United States', 'phone': '914 499 1900', 'website': 
                'https://www.ibm.com', 'industry': 'Information Technology Services',... }" 
        """
    path = f"/v3/reference/tickers/{stock_ticker.upper()}"
    info = _polygon_get(path).get("results", {})
    return str(f"Background information for {stock_ticker}: {info}")

# Add in an income statement tool
@mcp.tool()
def income_statement(stock_ticker: str) -> str:
    """This tool returns the quarterly income statement for a given stock ticker.
    Args:
        stock_ticker: a alphanumeric stock ticker
        Example payload: "BOA"

    Returns:
        str:quarterly income statement for the company
        Example Respnse "Income statement for BOA: 
        Tax Effect Of Unusual Items                           76923472.474289  ...          NaN
        Tax Rate For Calcs                                            0.11464  ...          NaN
        Normalized EBITDA                                        4172000000.0  ...          NaN
        """

    # Fetch latest quarterly financials
    params = {"ticker": stock_ticker.upper(), "timeframe": "quarterly", "limit": 1, "order": "desc"}
    fin = _polygon_get("/vX/reference/financials", params=params)
    results = (fin.get("results") or [])
    latest = results[0] if results else {}
    return str(f"Income statement for {stock_ticker}: {latest}")

# Enhanced Polygon API Tools

@mcp.tool()
def get_aggregates(
    ticker: str,
    multiplier: int,
    timespan: str,
    from_date: Union[str, int, datetime, date],
    to_date: Union[str, int, datetime, date],
    adjusted: Optional[bool] = None,
    sort: Optional[str] = None,
    limit: Optional[int] = None,
) -> str:
    """
    Get aggregate bars for a ticker over a given date range in custom time window sizes.
    
    Args:
        ticker: Stock ticker symbol
        multiplier: Size of the timespan multiplier
        timespan: Size of the time window (minute, hour, day, week, month, quarter, year)
        from_date: Start date for the aggregate window
        to_date: End date for the aggregate window
        adjusted: Whether the results are adjusted for splits
        sort: Sort order (asc, desc)
        limit: Limit the number of base aggregates queried
    
    Returns:
        str: JSON string containing aggregate data
    """
    try:
        # Convert dates to string format if needed
        if isinstance(from_date, (datetime, date)):
            from_date = from_date.strftime("%Y-%m-%d")
        if isinstance(to_date, (datetime, date)):
            to_date = to_date.strftime("%Y-%m-%d")
        
        path = f"/v2/aggs/ticker/{ticker.upper()}/range/{multiplier}/{timespan}/{from_date}/{to_date}"
        params = {}
        if adjusted is not None:
            params["adjusted"] = str(adjusted).lower()
        if sort:
            params["sort"] = sort
        if limit:
            params["limit"] = limit
            
        data = _polygon_get(path, params=params)
        return json.dumps(data, indent=2)
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def get_previous_close(ticker: str, adjusted: Optional[bool] = None) -> str:
    """
    Get previous day's open, close, high, and low for a specific ticker.
    
    Args:
        ticker: Stock ticker symbol
        adjusted: Whether the results are adjusted for splits
    
    Returns:
        str: JSON string containing previous close data
    """
    try:
        path = f"/v2/aggs/ticker/{ticker.upper()}/prev"
        params = {}
        if adjusted is not None:
            params["adjusted"] = str(adjusted).lower()
            
        data = _polygon_get(path, params=params)
        return json.dumps(data, indent=2)
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def get_last_trade(ticker: str) -> str:
    """
    Get the most recent trade for a ticker symbol.
    
    Args:
        ticker: Stock ticker symbol
    
    Returns:
        str: JSON string containing last trade data
    """
    try:
        path = f"/v2/last/trade/{ticker.upper()}"
        data = _polygon_get(path)
        return json.dumps(data, indent=2)
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def get_last_quote(ticker: str) -> str:
    """
    Get the most recent quote for a ticker symbol.
    
    Args:
        ticker: Stock ticker symbol
    
    Returns:
        str: JSON string containing last quote data
    """
    try:
        path = f"/v2/last/quote/{ticker.upper()}"
        data = _polygon_get(path)
        return json.dumps(data, indent=2)
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def get_snapshot_ticker(market_type: str, ticker: str) -> str:
    """
    Get snapshot for a specific ticker.
    
    Args:
        market_type: Market type (stocks, crypto, fx)
        ticker: Stock ticker symbol
    
    Returns:
        str: JSON string containing snapshot data
    """
    try:
        path = f"/v2/snapshot/locale/{market_type}/markets/{market_type}/tickers/{ticker.upper()}"
        data = _polygon_get(path)
        return json.dumps(data, indent=2)
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def get_market_status() -> str:
    """
    Get current trading status of exchanges and financial markets.
    
    Returns:
        str: JSON string containing market status data
    """
    try:
        path = "/v1/marketstatus/now"
        data = _polygon_get(path)
        return json.dumps(data, indent=2)
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def search_tickers(
    search: Optional[str] = None,
    type: Optional[str] = None,
    market: Optional[str] = None,
    active: Optional[bool] = None,
    limit: Optional[int] = None,
    sort: Optional[str] = None,
    order: Optional[str] = None,
) -> str:
    """
    Query supported ticker symbols across stocks, indices, forex, and crypto.
    
    Args:
        search: Search for tickers by name or ticker symbol
        type: Type of ticker (CS, ADRC, ADRP, ADR, NY, NAS, OTC, PINK, Q, D, etc.)
        market: Market filter (stocks, crypto, fx)
        active: Filter for active or inactive tickers
        limit: Limit the number of results
        sort: Sort field (ticker, name, market, locale, primary_exchange, type, active, currency_name, cik, composite_figi, share_class_figi)
        order: Sort order (asc, desc)
    
    Returns:
        str: JSON string containing ticker search results
    """
    try:
        path = "/v3/reference/tickers"
        params = {}
        if search:
            params["search"] = search
        if type:
            params["type"] = type
        if market:
            params["market"] = market
        if active is not None:
            params["active"] = str(active).lower()
        if limit:
            params["limit"] = limit
        if sort:
            params["sort"] = sort
        if order:
            params["order"] = order
            
        data = _polygon_get(path, params=params)
        return json.dumps(data, indent=2)
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def get_ticker_news(
    ticker: Optional[str] = None,
    published_utc: Optional[str] = None,
    limit: Optional[int] = None,
    sort: Optional[str] = None,
    order: Optional[str] = None,
) -> str:
    """
    Get recent news articles for a stock ticker.
    
    Args:
        ticker: Stock ticker symbol
        published_utc: Published date in UTC format
        limit: Limit the number of results
        sort: Sort field (published_utc, article_url, title, author, ticker, image_url, description, keywords)
        order: Sort order (asc, desc)
    
    Returns:
        str: JSON string containing news articles
    """
    try:
        path = "/v2/reference/news"
        params = {}
        if ticker:
            params["ticker"] = ticker.upper()
        if published_utc:
            params["published_utc"] = published_utc
        if limit:
            params["limit"] = limit
        if sort:
            params["sort"] = sort
        if order:
            params["order"] = order
            
        data = _polygon_get(path, params=params)
        return json.dumps(data, indent=2)
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def get_dividends(
    ticker: Optional[str] = None,
    ex_dividend_date: Optional[str] = None,
    frequency: Optional[int] = None,
    dividend_type: Optional[str] = None,
    limit: Optional[int] = None,
) -> str:
    """
    Get historical cash dividends.
    
    Args:
        ticker: Stock ticker symbol
        ex_dividend_date: Ex-dividend date
        frequency: Frequency of dividends (1 = monthly, 2 = quarterly, 4 = annually)
        dividend_type: Type of dividend (CD, SC, LT, ST)
        limit: Limit the number of results
    
    Returns:
        str: JSON string containing dividend data
    """
    try:
        path = "/v3/reference/dividends"
        params = {}
        if ticker:
            params["ticker"] = ticker.upper()
        if ex_dividend_date:
            params["ex_dividend_date"] = ex_dividend_date
        if frequency:
            params["frequency"] = frequency
        if dividend_type:
            params["dividend_type"] = dividend_type
        if limit:
            params["limit"] = limit
            
        data = _polygon_get(path, params=params)
        return json.dumps(data, indent=2)
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def get_splits(
    ticker: Optional[str] = None,
    execution_date: Optional[str] = None,
    reverse_split: Optional[bool] = None,
    limit: Optional[int] = None,
) -> str:
    """
    Get historical stock splits.
    
    Args:
        ticker: Stock ticker symbol
        execution_date: Execution date of the split
        reverse_split: Filter for reverse splits
        limit: Limit the number of results
    
    Returns:
        str: JSON string containing split data
    """
    try:
        path = "/v3/reference/splits"
        params = {}
        if ticker:
            params["ticker"] = ticker.upper()
        if execution_date:
            params["execution_date"] = execution_date
        if reverse_split is not None:
            params["reverse_split"] = str(reverse_split).lower()
        if limit:
            params["limit"] = limit
            
        data = _polygon_get(path, params=params)
        return json.dumps(data, indent=2)
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def get_treasury_yields(
    date: Optional[str] = None,
    limit: Optional[int] = None,
    sort: Optional[str] = None,
    order: Optional[str] = None,
) -> str:
    """
    Get treasury yield data.
    
    Args:
        date: Date for the yield data
        limit: Limit the number of results
        sort: Sort field (date, yield_2_yr, yield_5_yr, yield_10_yr, yield_30_yr)
        order: Sort order (asc, desc)
    
    Returns:
        str: JSON string containing treasury yield data
    """
    try:
        path = "/v1/indicators/treasury-yield"
        params = {}
        if date:
            params["date"] = date
        if limit:
            params["limit"] = limit
        if sort:
            params["sort"] = sort
        if order:
            params["order"] = order
            
        data = _polygon_get(path, params=params)
        return json.dumps(data, indent=2)
    except Exception as e:
        return f"Error: {str(e)}"

# Kick off server if file is run 
if __name__ == "__main__":
    import sys
    
    # Check if HTTP transport is requested via environment variable
    if os.environ.get("MCP_HTTP_TRANSPORT", "false").lower() == "true":
        port = int(os.environ.get("PORT", 8000))
        print(f"Starting MCP server with HTTP transport on port {port}")
        mcp.run(transport="http", port=port)
    else:
        print("Starting MCP server with stdio transport")
        mcp.run(transport="stdio")

# Market Hours and Timezone Utilities
@mcp.tool()
def get_market_hours_info() -> str:
    """
    Get information about U.S. market trading hours and timezone handling.
    
    Returns:
        str: JSON string containing market hours information
    """
    market_hours = {
        "pre_market": {
            "start": "04:00",
            "end": "09:30",
            "timezone": "ET"
        },
        "regular_market": {
            "start": "09:30", 
            "end": "16:00",
            "timezone": "ET"
        },
        "after_hours": {
            "start": "16:00",
            "end": "20:00", 
            "timezone": "ET"
        },
        "important_notes": [
            "All Polygon timestamps are in UTC (Unix timestamps)",
            "Convert UTC to ET for market hour alignment",
            "Pre-market: 4:00 AM - 9:30 AM ET",
            "Regular market: 9:30 AM - 4:00 PM ET", 
            "After-hours: 4:00 PM - 8:00 PM ET"
        ]
    }
    return json.dumps(market_hours, indent=2)

@mcp.tool()
def convert_utc_to_et(utc_timestamp: int) -> str:
    """
    Convert UTC timestamp to Eastern Time for market hour analysis.
    
    Args:
        utc_timestamp: Unix timestamp in seconds (UTC)
    
    Returns:
        str: JSON string with both UTC and ET times
    """
    try:
        from datetime import datetime, timezone, timedelta
        
        # Create UTC datetime
        utc_dt = datetime.fromtimestamp(utc_timestamp, tz=timezone.utc)
        
        # Convert to Eastern Time (ET)
        # Note: This is simplified - in production you'd want to handle DST properly
        et_offset = timedelta(hours=-5)  # EST (UTC-5)
        et_dt = utc_dt + et_offset
        
        result = {
            "utc_timestamp": utc_timestamp,
            "utc_datetime": utc_dt.strftime("%Y-%m-%d %H:%M:%S UTC"),
            "et_datetime": et_dt.strftime("%Y-%m-%d %H:%M:%S ET"),
            "market_session": _determine_market_session(et_dt.hour, et_dt.minute)
        }
        
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error: {str(e)}"

def _determine_market_session(hour: int, minute: int) -> str:
    """Helper function to determine market session based on ET time."""
    time_minutes = hour * 60 + minute
    
    if 240 <= time_minutes < 570:  # 4:00 AM - 9:30 AM
        return "pre_market"
    elif 570 <= time_minutes < 960:  # 9:30 AM - 4:00 PM
        return "regular_market"
    elif 960 <= time_minutes < 1200:  # 4:00 PM - 8:00 PM
        return "after_hours"
    else:
        return "market_closed"

# Enhanced Exchange Information
@mcp.tool()
def get_exchange_info() -> str:
    """
    Get information about major U.S. stock exchanges covered by Polygon.
    
    Returns:
        str: JSON string containing exchange information
    """
    exchanges = {
        "major_exchanges": [
            {
                "name": "New York Stock Exchange",
                "symbols": ["NYSE", "NYSE American", "NYSE Arca", "NYSE Chicago", "NYSE National"]
            },
            {
                "name": "Nasdaq",
                "symbols": ["OMX", "BX", "PSX", "Philadelphia"]
            },
            {
                "name": "Cboe Global Markets", 
                "symbols": ["BZX", "BYX", "EDGX", "EDGA"]
            },
            {
                "name": "MIAX Exchange Group",
                "symbols": ["Pearl", "Emerald", "Equities"]
            },
            {
                "name": "Members Exchange",
                "symbols": ["MEMX"]
            },
            {
                "name": "Investors Exchange",
                "symbols": ["IEX"]
            },
            {
                "name": "Long-Term Stock Exchange",
                "symbols": ["LTSE"]
            }
        ],
        "additional_sources": [
            {
                "name": "FINRA Trading Facilities",
                "description": "Provides trade reporting but not quotes",
                "facilities": ["FINRA NYSE TRF", "FINRA Nasdaq TRF Carteret", "FINRA Nasdaq TRF Chicago"]
            },
            {
                "name": "OTC Reporting Facility", 
                "description": "Captures OTC trades but not quotes"
            }
        ],
        "total_coverage": "19 major stock exchanges + dark pools + FINRA + OTC",
        "data_quality": "Direct exchange feeds + SIP consolidation for accuracy"
    }
    return json.dumps(exchanges, indent=2)

# Enhanced Market Data with Session Awareness
@mcp.tool()
def get_intraday_aggregates(
    ticker: str,
    multiplier: int,
    timespan: str,
    from_date: Union[str, int, datetime, date],
    to_date: Union[str, int, datetime, date],
    adjusted: Optional[bool] = None,
    sort: Optional[str] = None,
    limit: Optional[int] = None,
    include_otc: bool = False,
) -> str:
    """
    Get intraday aggregate bars with enhanced market session awareness.
    
    Args:
        ticker: Stock ticker symbol
        multiplier: Size of the timespan multiplier
        timespan: Size of the time window (minute, hour, day, week, month, quarter, year)
        from_date: Start date for the aggregate window
        to_date: End date for the aggregate window
        adjusted: Whether the results are adjusted for splits
        sort: Sort order (asc, desc)
        limit: Limit the number of base aggregates queried
        include_otc: Include OTC market data
    
    Returns:
        str: JSON string containing aggregate data with session information
    """
    try:
        # Convert dates to string format if needed
        if isinstance(from_date, (datetime, date)):
            from_date = from_date.strftime("%Y-%m-%d")
        if isinstance(to_date, (datetime, date)):
            to_date = to_date.strftime("%Y-%m-%d")
        
        path = f"/v2/aggs/ticker/{ticker.upper()}/range/{multiplier}/{timespan}/{from_date}/{to_date}"
        params = {}
        if adjusted is not None:
            params["adjusted"] = str(adjusted).lower()
        if sort:
            params["sort"] = sort
        if limit:
            params["limit"] = limit
        if include_otc:
            params["include_otc"] = "true"
            
        data = _polygon_get(path, params=params)
        
        # Add market session information to the response
        if "results" in data and data["results"]:
            for result in data["results"]:
                if "t" in result:  # timestamp
                    utc_time = datetime.fromtimestamp(result["t"] / 1000, tz=timezone.utc)
                    et_time = utc_time + timedelta(hours=-5)  # Convert to ET
                    result["market_session"] = _determine_market_session(et_time.hour, et_time.minute)
                    result["et_time"] = et_time.strftime("%Y-%m-%d %H:%M:%S ET")
        
        return json.dumps(data, indent=2)
    except Exception as e:
        return f"Error: {str(e)}"

# Additional Stock-Related Tools

@mcp.tool()
def get_sip_info() -> str:
    """
    Get information about Securities Information Processors (SIPs) and their role in market data.
    
    Returns:
        str: JSON string containing SIP information
    """
    sip_info = {
        "what_are_sips": "Securities Information Processors (SIPs) consolidate trade and quote data from all exchanges into a single feed",
        "sip_functions": [
            "Provide National Best Bid and Offer (NBBO)",
            "Consolidate last sale data",
            "Ensure equal access to market data",
            "Maintain transparent and fair trading environment"
        ],
        "major_sips": [
            {
                "name": "Consolidated Tape Association (CTA)",
                "coverage": "NYSE-listed and regional exchange securities",
                "tapes": ["Tape A", "Tape B"]
            },
            {
                "name": "Unlisted Trading Privileges (UTP)",
                "coverage": "All Nasdaq-listed securities", 
                "tapes": ["Tape C"]
            }
        ],
        "data_flow": [
            "Exchanges → SIPs → Polygon.io → Users",
            "Direct exchange feeds + SIP consolidation",
            "Alternative Trading Systems (ATS) report to FINRA within 10 seconds"
        ],
        "importance": "SIPs are vital infrastructure ensuring all market participants have equal access to trade and quote data"
    }
    return json.dumps(sip_info, indent=2)

@mcp.tool()
def get_market_data_coverage() -> str:
    """
    Get comprehensive information about Polygon's market data coverage and infrastructure.
    
    Returns:
        str: JSON string containing coverage information
    """
    coverage_info = {
        "infrastructure": {
            "primary_facility": "Equinix Data Center, New Jersey",
            "redundancy": "ORD11 data center, Chicago",
            "co_location": "Strategically co-located with exchanges",
            "benefits": ["Reduced latency", "Enhanced reliability", "Direct physical connections"]
        },
        "data_sources": {
            "exchanges": "All 19 major U.S. stock exchanges",
            "dark_pools": "Additional dark pool data",
            "finra": "FINRA trading facilities",
            "otc": "OTC markets",
            "ats": "Alternative Trading Systems"
        },
        "data_quality": {
            "direct_feeds": "Direct relationships with each exchange",
            "licensing": "Compliance with all licensing requirements",
            "sip_integration": "Combines direct exchange access with regulated SIP consolidation",
            "coverage": "Every trade, quote, and market event as it occurs"
        },
        "regulatory_compliance": {
            "personal_use": "Full U.S. feed available for non-industry professionals",
            "business_clients": "Tailored plans with specific exchange licensing",
            "monitoring": "Close compliance monitoring for appropriate usage"
        },
        "market_hours": {
            "pre_market": "4:00 AM - 9:30 AM ET",
            "regular_market": "9:30 AM - 4:00 PM ET", 
            "after_hours": "4:00 PM - 8:00 PM ET",
            "timestamp_format": "Unix timestamps (UTC)"
        }
    }
    return json.dumps(coverage_info, indent=2)

@mcp.tool()
def get_ticker_exchange_info(ticker: str) -> str:
    """
    Get detailed exchange and listing information for a specific ticker.
    
    Args:
        ticker: Stock ticker symbol
    
    Returns:
        str: JSON string containing exchange information for the ticker
    """
    try:
        # First get basic ticker info
        path = f"/v3/reference/tickers/{ticker.upper()}"
        data = _polygon_get(path)
        
        if "results" in data and data["results"]:
            ticker_info = data["results"]
            
            # Add exchange coverage information
            exchange_coverage = {
                "ticker": ticker.upper(),
                "primary_exchange": ticker_info.get("primary_exchange"),
                "market": ticker_info.get("market"),
                "locale": ticker_info.get("locale"),
                "type": ticker_info.get("type"),
                "active": ticker_info.get("active"),
                "currency_name": ticker_info.get("currency_name"),
                "cik": ticker_info.get("cik"),
                "composite_figi": ticker_info.get("composite_figi"),
                "share_class_figi": ticker_info.get("share_class_figi"),
                "polygon_coverage": {
                    "data_available": "Real-time trades, quotes, and market events",
                    "exchange_feed": "Direct feed from primary exchange",
                    "sip_integration": "Included in consolidated SIP feeds",
                    "market_sessions": ["pre_market", "regular_market", "after_hours"]
                }
            }
            
            return json.dumps(exchange_coverage, indent=2)
        else:
            return json.dumps({"error": f"No data found for ticker {ticker}"}, indent=2)
            
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def get_earnings(
    ticker: Optional[str] = None,
    date: Optional[str] = None,
    limit: Optional[int] = None,
    sort: Optional[str] = None,
    order: Optional[str] = None,
) -> str:
    """
    Get earnings data for stocks.
    
    Args:
        ticker: Stock ticker symbol
        date: Earnings date
        limit: Limit the number of results
        sort: Sort field (date, ticker, etc.)
        order: Sort order (asc, desc)
    
    Returns:
        str: JSON string containing earnings data
    """
    try:
        path = "/v3/reference/earnings"
        params = {}
        if ticker:
            params["ticker"] = ticker.upper()
        if date:
            params["date"] = date
        if limit:
            params["limit"] = limit
        if sort:
            params["sort"] = sort
        if order:
            params["order"] = order
            
        data = _polygon_get(path, params=params)
        return json.dumps(data, indent=2)
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def get_analyst_ratings(
    ticker: Optional[str] = None,
    date: Optional[str] = None,
    limit: Optional[int] = None,
    sort: Optional[str] = None,
    order: Optional[str] = None,
) -> str:
    """
    Get analyst ratings and price targets for stocks.
    
    Args:
        ticker: Stock ticker symbol
        date: Rating date
        limit: Limit the number of results
        sort: Sort field (date, ticker, etc.)
        order: Sort order (asc, desc)
    
    Returns:
        str: JSON string containing analyst ratings data
    """
    try:
        path = "/v2/reference/analysts"
        params = {}
        if ticker:
            params["ticker"] = ticker.upper()
        if date:
            params["date"] = date
        if limit:
            params["limit"] = limit
        if sort:
            params["sort"] = sort
        if order:
            params["order"] = order
            
        data = _polygon_get(path, params=params)
        return json.dumps(data, indent=2)
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def get_short_interest(
    ticker: Optional[str] = None,
    settlement_date: Optional[str] = None,
    limit: Optional[int] = None,
    sort: Optional[str] = None,
    order: Optional[str] = None,
) -> str:
    """
    Get short interest data for stocks.
    
    Args:
        ticker: Stock ticker symbol
        settlement_date: Settlement date for short interest
        limit: Limit the number of results
        sort: Sort field (settlement_date, ticker, etc.)
        order: Sort order (asc, desc)
    
    Returns:
        str: JSON string containing short interest data
    """
    try:
        path = "/v2/reference/short-interest"
        params = {}
        if ticker:
            params["ticker"] = ticker.upper()
        if settlement_date:
            params["settlement_date"] = settlement_date
        if limit:
            params["limit"] = limit
        if sort:
            params["sort"] = sort
        if order:
            params["order"] = order
            
        data = _polygon_get(path, params=params)
        return json.dumps(data, indent=2)
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def get_options_contracts(
    underlying_asset: str,
    contract_type: Optional[str] = None,
    strike_price: Optional[float] = None,
    expiration_date: Optional[str] = None,
    limit: Optional[int] = None,
) -> str:
    """
    Get options contracts for a stock.
    
    Args:
        underlying_asset: Stock ticker symbol
        contract_type: Type of option (call, put)
        strike_price: Strike price of the option
        expiration_date: Expiration date (YYYY-MM-DD)
        limit: Limit the number of results
    
    Returns:
        str: JSON string containing options contracts data
    """
    try:
        path = f"/v3/reference/options/contracts"
        params = {"underlying_asset": underlying_asset.upper()}
        if contract_type:
            params["contract_type"] = contract_type
        if strike_price:
            params["strike_price"] = strike_price
        if expiration_date:
            params["expiration_date"] = expiration_date
        if limit:
            params["limit"] = limit
            
        data = _polygon_get(path, params=params)
        return json.dumps(data, indent=2)
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def get_options_snapshot(
    underlying_asset: str,
    strike_price: Optional[float] = None,
    expiration_date: Optional[str] = None,
    contract_type: Optional[str] = None,
) -> str:
    """
    Get real-time options snapshot data.
    
    Args:
        underlying_asset: Stock ticker symbol
        strike_price: Strike price of the option
        expiration_date: Expiration date (YYYY-MM-DD)
        contract_type: Type of option (call, put)
    
    Returns:
        str: JSON string containing options snapshot data
    """
    try:
        path = f"/v3/snapshot/options/{underlying_asset.upper()}"
        params = {}
        if strike_price:
            params["strike_price"] = strike_price
        if expiration_date:
            params["expiration_date"] = expiration_date
        if contract_type:
            params["contract_type"] = contract_type
            
        data = _polygon_get(path, params=params)
        return json.dumps(data, indent=2)
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def get_balance_sheet(
    ticker: str,
    timeframe: str = "quarterly",
    limit: Optional[int] = None,
    order: str = "desc",
) -> str:
    """
    Get balance sheet data for a stock.
    
    Args:
        ticker: Stock ticker symbol
        timeframe: Timeframe (quarterly, annual)
        limit: Limit the number of results
        order: Sort order (asc, desc)
    
    Returns:
        str: JSON string containing balance sheet data
    """
    try:
        path = "/vX/reference/financials"
        params = {
            "ticker": ticker.upper(),
            "timeframe": timeframe,
            "order": order
        }
        if limit:
            params["limit"] = limit
            
        data = _polygon_get(path, params=params)
        return json.dumps(data, indent=2)
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def get_cash_flow(
    ticker: str,
    timeframe: str = "quarterly",
    limit: Optional[int] = None,
    order: str = "desc",
) -> str:
    """
    Get cash flow statement data for a stock.
    
    Args:
        ticker: Stock ticker symbol
        timeframe: Timeframe (quarterly, annual)
        limit: Limit the number of results
        order: Sort order (asc, desc)
    
    Returns:
        str: JSON string containing cash flow data
    """
    try:
        path = "/vX/reference/financials"
        params = {
            "ticker": ticker.upper(),
            "timeframe": timeframe,
            "order": order
        }
        if limit:
            params["limit"] = limit
            
        data = _polygon_get(path, params=params)
        return json.dumps(data, indent=2)
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def get_market_gainers_losers(
    direction: str,
    include_otc: bool = False,
    limit: Optional[int] = None,
) -> str:
    """
    Get top gainers or losers in the market.
    
    Args:
        direction: Direction (gainers, losers)
        include_otc: Include OTC stocks
        limit: Limit the number of results
    
    Returns:
        str: JSON string containing gainers/losers data
    """
    try:
        path = f"/v2/snapshot/locale/us/markets/stocks/{direction}"
        params = {}
        if include_otc:
            params["include_otc"] = "true"
        if limit:
            params["limit"] = limit
            
        data = _polygon_get(path, params=params)
        return json.dumps(data, indent=2)
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def get_market_holidays() -> str:
    """
    Get upcoming market holidays and their open/close times.
    
    Returns:
        str: JSON string containing market holidays data
    """
    try:
        path = "/v1/marketstatus/upcoming"
        data = _polygon_get(path)
        return json.dumps(data, indent=2)
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def get_inflation_data(
    date: Optional[str] = None,
    limit: Optional[int] = None,
    sort: Optional[str] = None,
) -> str:
    """
    Get inflation data from the Federal Reserve.
    
    Args:
        date: Date for the inflation data
        limit: Limit the number of results
        sort: Sort field (date, value, etc.)
    
    Returns:
        str: JSON string containing inflation data
    """
    try:
        path = "/v1/indicators/inflation"
        params = {}
        if date:
            params["date"] = date
        if limit:
            params["limit"] = limit
        if sort:
            params["sort"] = sort
            
        data = _polygon_get(path, params=params)
        return json.dumps(data, indent=2)
    except Exception as e:
        return f"Error: {str(e)}"
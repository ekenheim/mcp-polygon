#!/usr/bin/env python3
"""
Health check script for MCP Polygon Server
"""

import os
import sys
import requests
import time

def check_health():
    """Check if the server is healthy"""
    try:
        # Get port from environment or default to 8000
        port = int(os.environ.get("PORT", 8000))
        
        # Try to connect to the health endpoint
        response = requests.get(f"http://localhost:{port}/health", timeout=5)
        
        if response.status_code == 200:
            print("✅ Server is healthy")
            return True
        else:
            print(f"❌ Server returned status code: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server")
        return False
    except requests.exceptions.Timeout:
        print("❌ Health check timed out")
        return False
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

if __name__ == "__main__":
    # Give the server a moment to start up
    time.sleep(2)
    
    if check_health():
        sys.exit(0)
    else:
        sys.exit(1)

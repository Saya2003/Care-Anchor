"""
Netlify Function wrapper for CareAnchor FastAPI backend using Mangum
This function uses Mangum to adapt the FastAPI ASGI app for Netlify Functions
"""

import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# Import the FastAPI app
from backend.main import app

# Import Mangum for ASGI to Lambda/Netlify adapter
from mangum import Mangum

# Create the handler using Mangum
handler = Mangum(app, lifespan="off")

# Alternative: Custom handler function if Mangum doesn't work
def custom_handler(event, context):
    """
    Fallback handler if Mangum has issues
    """
    import json
    
    try:
        # Use Mangum to handle the event
        return handler(event, context)
    except Exception as e:
        # Fallback response
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps({
                "error": str(e),
                "message": "CareAnchor API - Netlify Functions",
                "path": event.get("path", "/"),
                "method": event.get("httpMethod", "GET"),
                "fallback": True
            })
        }


# For testing locally
if __name__ == "__main__":
    # Test event
    test_event = {
        "httpMethod": "GET",
        "path": "/api/health",
        "queryStringParameters": {},
        "headers": {"Content-Type": "application/json"},
        "body": "",
        "isBase64Encoded": False
    }
    
    result = handler(test_event, {})
    print(json.dumps(result, indent=2))
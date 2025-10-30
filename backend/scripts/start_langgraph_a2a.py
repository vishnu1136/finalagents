#!/usr/bin/env python3
"""
Startup script for LangGraph + A2A API
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Now import and run the app
if __name__ == "__main__":
    import uvicorn
    from api.main_langgraph_a2a import app
    
    print("🚀 Starting LangGraph + A2A API Server...")
    print("📍 Server will be available at: http://localhost:8000")
    print("📚 API Documentation: http://localhost:8000/docs")
    print("🔍 Health Check: http://localhost:8000/health")
    print("=" * 50)
    
    uvicorn.run(
        "api.main_langgraph_a2a:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

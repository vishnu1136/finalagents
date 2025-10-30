#!/usr/bin/env python3
"""
Startup script for the reorganized LangGraph + A2A application
"""

import sys
import os
from pathlib import Path

# Add the src directory to Python path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

# Now import and run the application
if __name__ == "__main__":
    import uvicorn
    from main_langgraph_a2a import app
    
    print("🚀 Starting LangGraph + A2A Application...")
    print(f"📁 Working directory: {os.getcwd()}")
    print(f"🐍 Python path: {sys.path[:3]}...")
    
    uvicorn.run(
        "main_langgraph_a2a:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

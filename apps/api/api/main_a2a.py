"""
Main API with A2A Architecture
=============================
FastAPI application using Agent-to-Agent architecture.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .agents.orchestrator import AgentOrchestrator
from .routes.search import router as search_router
from .routes.admin import router as admin_router
from .routes.ingest import router as ingest_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global orchestrator instance
orchestrator: AgentOrchestrator = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global orchestrator
    
    # Startup
    logger.info("Starting IKB Navigator with A2A Architecture")
    try:
        orchestrator = AgentOrchestrator()
        await orchestrator.start()
        logger.info("Agent Orchestrator started successfully")
    except Exception as e:
        logger.error(f"Failed to start orchestrator: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down IKB Navigator")
    if orchestrator:
        await orchestrator.stop()
        logger.info("Agent Orchestrator stopped")


# Create FastAPI app
app = FastAPI(
    title="IKB Navigator - A2A Architecture",
    description="AI-Powered Knowledge Assistant with Agent-to-Agent Architecture",
    version="2.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(search_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1")
app.include_router(ingest_router, prefix="/api/v1")


# Pydantic models
class SearchRequest(BaseModel):
    query: str


class SearchResponse(BaseModel):
    answer: str
    sources: list
    grouped_sources: dict
    analysis: dict = {}
    confidence: float = 0.8
    search_metadata: dict = {}
    processing_time: float = 0.0
    request_id: str = ""


class HealthResponse(BaseModel):
    status: str
    orchestrator_running: bool
    agent_count: int
    agent_status: dict
    active_requests: int
    timestamp: str


# API Endpoints
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    try:
        if orchestrator:
            status = orchestrator.get_system_status()
            return HealthResponse(
                status="healthy",
                orchestrator_running=status["orchestrator_running"],
                agent_count=status["agent_count"],
                agent_status=status["agent_status"],
                active_requests=status["active_requests"],
                timestamp=status["timestamp"]
            )
        else:
            return HealthResponse(
                status="unhealthy",
                orchestrator_running=False,
                agent_count=0,
                agent_status={},
                active_requests=0,
                timestamp=""
            )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {e}")


@app.post("/search", response_model=SearchResponse)
async def search_documents(request: SearchRequest):
    """Search documents using A2A architecture."""
    try:
        if not orchestrator:
            raise HTTPException(status_code=503, detail="Orchestrator not available")
        
        logger.info(f"Processing search request: {request.query[:100]}...")
        
        # Process query through orchestrator
        result = await orchestrator.process_query(request.query)
        
        # Convert to response format
        response = SearchResponse(
            answer=result.get("answer", "No results found"),
            sources=result.get("sources", []),
            grouped_sources=result.get("grouped_sources", {}),
            analysis=result.get("analysis", {}),
            confidence=result.get("confidence", 0.8),
            search_metadata=result.get("search_metadata", {}),
            processing_time=result.get("processing_time", 0.0),
            request_id=result.get("request_id", "")
        )
        
        logger.info(f"Search completed in {response.processing_time:.2f}s")
        return response
        
    except Exception as e:
        logger.error(f"Search request failed: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {e}")


@app.get("/agents/status")
async def get_agent_status():
    """Get detailed agent status."""
    try:
        if not orchestrator:
            raise HTTPException(status_code=503, detail="Orchestrator not available")
        
        return orchestrator.get_system_status()
        
    except Exception as e:
        logger.error(f"Failed to get agent status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get agent status: {e}")


@app.post("/agents/restart")
async def restart_agents():
    """Restart all agents."""
    try:
        if not orchestrator:
            raise HTTPException(status_code=503, detail="Orchestrator not available")
        
        logger.info("Restarting all agents")
        await orchestrator.stop()
        await asyncio.sleep(2)  # Brief pause
        await orchestrator.start()
        
        return {"message": "Agents restarted successfully"}
        
    except Exception as e:
        logger.error(f"Failed to restart agents: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to restart agents: {e}")


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "IKB Navigator - A2A Architecture",
        "version": "2.0.0",
        "status": "running",
        "architecture": "Agent-to-Agent",
        "endpoints": {
            "search": "/search",
            "health": "/health",
            "agent_status": "/agents/status",
            "docs": "/docs"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main_a2a:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

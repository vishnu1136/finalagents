"""
Main API with LangGraph + A2A Architecture
==========================================
FastAPI application using LangGraph state management with A2A agent architecture.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agents.core.langgraph_a2a import LangGraphA2AOrchestrator
from api.routes.search import router as search_router
from api.routes.admin import router as admin_router
from services.db import get_supabase_client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global orchestrator instance
orchestrator: LangGraphA2AOrchestrator = None


async def log_query_to_database(query: str, result: Dict[str, Any]) -> str:
    """Log query and results to the database."""
    try:
        db_client = get_supabase_client()
        
        # Insert query
        query_result = db_client.table('queries').insert({
            'query_text': query
        }).execute()
        
        if not query_result.data:
            logger.warning("Failed to insert query to database")
            return ""
        
        query_id = query_result.data[0]['id']
        
        # Insert query results (sources/chunks)
        if result.get('sources'):
            query_results_data = []
            for source in result['sources']:
                if source.get('chunk_id'):
                    query_results_data.append({
                        'query_id': query_id,
                        'chunk_id': source['chunk_id'],
                        'score': source.get('score', 0.0)
                    })
            
            if query_results_data:
                db_client.table('query_results').insert(query_results_data).execute()
                logger.info(f"Logged {len(query_results_data)} query results to database")
        
        return query_id
        
    except Exception as e:
        logger.error(f"Failed to log query to database: {e}")
        return ""


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global orchestrator
    
    # Startup
    logger.info("Starting IKB Navigator with LangGraph + A2A Architecture")
    try:
        orchestrator = LangGraphA2AOrchestrator()
        await orchestrator.start()
        logger.info("LangGraph A2A Orchestrator started successfully")
    except Exception as e:
        logger.error(f"Failed to start orchestrator: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down IKB Navigator")
    if orchestrator:
        await orchestrator.stop()
        logger.info("LangGraph A2A Orchestrator stopped")


# Create FastAPI app
app = FastAPI(
    title="IKB Navigator - LangGraph + A2A Architecture",
    description="AI-Powered Knowledge Assistant with LangGraph State Management and Agent-to-Agent Architecture",
    version="3.0.0",
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


# Pydantic models
class SearchRequest(BaseModel):
    query: str
    config: Dict[str, Any] = {}


class SearchResponse(BaseModel):
    answer: str
    sources: list
    grouped_sources: dict
    processing_time: float = 0.0
    request_id: str = ""
    agent_times: dict = {}
    errors: list = []


class HealthResponse(BaseModel):
    status: str
    langgraph_a2a_running: bool
    agent_count: int
    agent_status: dict
    active_requests: int
    memory_checkpoints: int
    timestamp: str


# API Endpoints
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    try:
        if orchestrator:
            status = orchestrator.get_status()
            agent_status = status["agent_orchestrator_status"]
            return HealthResponse(
                status="healthy",
                langgraph_a2a_running=status["langgraph_a2a_running"],
                agent_count=agent_status["agent_count"],
                agent_status=agent_status["agent_status"],
                active_requests=agent_status["active_requests"],
                memory_checkpoints=status["memory_checkpoints"],
                timestamp=agent_status["timestamp"]
            )
        else:
            return HealthResponse(
                status="unhealthy",
                langgraph_a2a_running=False,
                agent_count=0,
                agent_status={},
                active_requests=0,
                memory_checkpoints=0,
                timestamp=""
            )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {e}")


@app.post("/search", response_model=SearchResponse)
async def search_documents(request: SearchRequest):
    """Search documents using LangGraph + A2A architecture."""
    try:
        if not orchestrator:
            raise HTTPException(status_code=503, detail="Orchestrator not available")
        
        logger.info(f"Processing search request: {request.query[:100]}...")
        
        # Process query through LangGraph A2A orchestrator
        result = await orchestrator.process_query(request.query, request.config)
        
        # Log query and results to database
        query_id = await log_query_to_database(request.query, result)
        
        # Convert to response format
        response = SearchResponse(
            answer=result.get("answer", "No results found"),
            sources=result.get("sources", []),
            grouped_sources=result.get("grouped_sources", {}),
            processing_time=result.get("processing_time", 0.0),
            request_id=result.get("request_id", ""),
            agent_times=result.get("agent_times", {}),
            errors=result.get("errors", [])
        )
        
        logger.info(f"Search completed in {response.processing_time:.2f}s (Query ID: {query_id})")
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
        
        return orchestrator.get_status()
        
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


@app.get("/graph/status")
async def get_graph_status():
    """Get LangGraph status and statistics."""
    try:
        if not orchestrator:
            raise HTTPException(status_code=503, detail="Orchestrator not available")
        
        status = orchestrator.get_status()
        
        # Add LangGraph-specific information
        graph_info = {
            "langgraph_version": "0.2.0",
            "state_management": "MemorySaver",
            "checkpointing": "enabled",
            "memory_checkpoints": status["memory_checkpoints"],
            "graph_nodes": [
                "query_understanding",
                "strategy_decision", 
                "parallel_processing",
                "sequential_processing",
                "hybrid_processing",
                "response_generation",
                "error_handling",
                "finalization"
            ],
            "conditional_routing": True,
            "retry_mechanism": True
        }
        
        return {
            "langgraph_info": graph_info,
            "orchestrator_status": status
        }
        
    except Exception as e:
        logger.error(f"Failed to get graph status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get graph status: {e}")


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "IKB Navigator - LangGraph + A2A Architecture",
        "version": "3.0.0",
        "status": "running",
        "architecture": "LangGraph + Agent-to-Agent",
        "features": [
            "LangGraph state management",
            "A2A agent communication",
            "Conditional routing",
            "Parallel processing",
            "Error recovery",
            "Memory checkpointing"
        ],
        "endpoints": {
            "search": "/search",
            "health": "/health",
            "agent_status": "/agents/status",
            "graph_status": "/graph/status",
            "docs": "/docs"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main_langgraph_a2a:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

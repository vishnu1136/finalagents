from fastapi import APIRouter
from pydantic import BaseModel
import logging

from api.agents.graph import run_pipeline
from api.agents.nodes.direct_search_node import run_node as direct_search
from api.services.db import get_supabase_client

router = APIRouter()
logger = logging.getLogger(__name__)


class SearchRequest(BaseModel):
    query: str


class DirectSearchRequest(BaseModel):
    query: str
    include_metadata: bool = False


async def log_query_to_database(query: str, result: dict) -> str:
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


@router.post("/search")
async def search(body: SearchRequest) -> dict:
    """Legacy search endpoint using the original pipeline."""
    result = await run_pipeline(body.query)
    
    # Log query and results to database
    query_id = await log_query_to_database(body.query, result)
    logger.info(f"Query logged with ID: {query_id}")
    
    return result


@router.post("/search/direct")
async def direct_search_endpoint(body: DirectSearchRequest) -> dict:
    """Direct Google Drive search without downloading files."""
    try:
        logger.info(f"Processing direct search request: {body.query[:100]}...")
        
        # Use the direct search node
        result = await direct_search({
            "query": body.query,
            "normalized_query": body.query,
            "include_metadata": body.include_metadata
        })
        
        # Add metadata about the search method
        result["search_method"] = "direct_gdrive"
        result["query"] = body.query
        
        logger.info(f"Direct search completed: {result.get('total_found', 0)} results found")
        
        return result
        
    except Exception as e:
        logger.error(f"Direct search failed: {e}")
        return {
            "results": [],
            "total_found": 0,
            "error": str(e),
            "search_method": "direct_gdrive"
        }



from fastapi import APIRouter, Query
from typing import Optional
import logging

from api.services.db import get_supabase_client

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/healthz")
def healthz() -> dict:
    return {"ok": True}


@router.get("/queries")
async def get_query_history(limit: Optional[int] = Query(default=50, le=1000)) -> dict:
    """Get query history from the database."""
    try:
        db_client = get_supabase_client()
        
        # Get recent queries with their result counts
        queries_result = db_client.table('queries').select(
            'id, query_text, created_at'
        ).order('created_at', desc=True).limit(limit).execute()
        
        if not queries_result.data:
            return {"queries": [], "total": 0}
        
        # Get result counts for each query
        query_ids = [q['id'] for q in queries_result.data]
        results_count = {}
        
        if query_ids:
            results_result = db_client.table('query_results').select(
                'query_id'
            ).in_('query_id', query_ids).execute()
            
            # Count results per query
            for result in results_result.data:
                query_id = result['query_id']
                results_count[query_id] = results_count.get(query_id, 0) + 1
        
        # Add result counts to queries
        for query in queries_result.data:
            query['result_count'] = results_count.get(query['id'], 0)
        
        return {
            "queries": queries_result.data,
            "total": len(queries_result.data)
        }
        
    except Exception as e:
        logger.error(f"Failed to get query history: {e}")
        return {"error": str(e), "queries": [], "total": 0}


@router.get("/queries/{query_id}/results")
async def get_query_results(query_id: str) -> dict:
    """Get detailed results for a specific query."""
    try:
        db_client = get_supabase_client()
        
        # Get query details
        query_result = db_client.table('queries').select(
            'id, query_text, created_at'
        ).eq('id', query_id).execute()
        
        if not query_result.data:
            return {"error": "Query not found"}
        
        query_info = query_result.data[0]
        
        # Get query results with chunk details
        results_query = """
        SELECT qr.score, c.text, c.chunk_index, d.title, d.url
        FROM query_results qr
        JOIN chunks c ON qr.chunk_id = c.id
        JOIN documents d ON c.document_id = d.id
        WHERE qr.query_id = %s
        ORDER BY qr.score DESC
        """
        
        # For now, we'll use a simpler approach with Supabase
        results_result = db_client.table('query_results').select(
            'score, chunks!inner(text, chunk_index, documents!inner(title, url))'
        ).eq('query_id', query_id).order('score', desc=True).execute()
        
        results = []
        for result in results_result.data:
            chunk_data = result['chunks']
            doc_data = chunk_data['documents']
            results.append({
                'score': result['score'],
                'text': chunk_data['text'],
                'chunk_index': chunk_data['chunk_index'],
                'document_title': doc_data['title'],
                'document_url': doc_data['url']
            })
        
        return {
            "query": query_info,
            "results": results,
            "total_results": len(results)
        }
        
    except Exception as e:
        logger.error(f"Failed to get query results: {e}")
        return {"error": str(e)}



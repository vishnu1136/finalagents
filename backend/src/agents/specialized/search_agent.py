"""
Search Agent - Direct Google Drive Integration
=============================================
Specialized agent for direct Google Drive search without database storage.
"""

import time
from typing import Any, Dict, List, Optional
import logging

from ..core.base_agent import BaseAgent
from ..core.agent_communication import (
    AgentMessage, MessageType, AgentType,
    SearchRequest, SearchResponse, create_message
)
from integrations.mcp_client import GDriveMCPClient


class SearchAgent(BaseAgent):
    """Agent specialized in direct Google Drive search without file downloads."""
    
    def __init__(self):
        super().__init__(
            agent_type=AgentType.HYBRID_SEARCH_AGENT,
            name="SearchAgent",
            max_concurrent_tasks=5,
            timeout_seconds=30  # Reduced timeout since we're not downloading files
        )
        
        # Initialize Google Drive client
        self.gdrive_client = GDriveMCPClient()
        
        # Register message handlers
        self.register_handler(MessageType.SEARCH_REQUEST, self._handle_search_request)
        self.register_handler(MessageType.HEARTBEAT, self._handle_heartbeat)
    
    async def _send_message_to_orchestrator(self, message: AgentMessage) -> None:
        """Send message to orchestrator."""
        if hasattr(self, 'orchestrator_callback'):
            await self.orchestrator_callback(message)
    
    async def process_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a search task."""
        try:
            search_request = SearchRequest(**task_data)
            return await self._perform_direct_search(search_request)
        except Exception as e:
            self.logger.error(f"Error processing search task: {e}")
            raise
    
    async def _handle_search_request(self, message: AgentMessage) -> None:
        """Handle search request messages."""
        try:
            search_request = SearchRequest(**message.payload)
            search_response = await self._perform_direct_search(search_request)
            
            # Send response back
            response = create_message(
                sender=self.agent_type,
                recipient=message.sender,
                message_type=MessageType.SEARCH_RESPONSE,
                payload=search_response,
                correlation_id=message.id
            )
            await self._send_message_to_orchestrator(response)
            
        except Exception as e:
            self.logger.error(f"Error handling search request: {e}")
            await self._send_error_response(message, str(e))
    
    async def _handle_heartbeat(self, message: AgentMessage) -> None:
        """Handle heartbeat messages."""
        self.logger.debug("Received heartbeat")
    
    async def _perform_direct_search(self, search_request: SearchRequest) -> Dict[str, Any]:
        """Perform direct Google Drive search without downloading files."""
        start_time = time.time()
        
        try:
            query = search_request.normalized_query or search_request.query
            if not query:
                return {"results": [], "total_found": 0, "search_time": 0, "sources_used": []}
            
            self.logger.info(f"Performing direct Google Drive search for: '{query}'")
            
            # Use Google Drive's built-in fullText search (no downloads needed)
            files = await self.gdrive_client.list_files(query=query)
            
            self.logger.info(f"Google Drive returned {len(files)} relevant files")
            
            # Convert to search results format without downloading any content
            results = []
            for file_info in files:
                results.append({
                    "chunk_id": f"gdrive_{file_info['id']}",  # Virtual chunk ID
                    "title": file_info.get("name", "Unknown"),
                    "url": file_info.get("webViewLink", ""),
                    "snippet": f"Found in: {file_info.get('name', 'Unknown')}",
                    "score": 0.8,  # Google Drive's built-in relevance score
                    "file_id": file_info.get("id"),
                    "mime_type": file_info.get("mimeType", ""),
                    "source": "google_drive_direct"
                })
            
            # Sort by score (Google Drive already provides relevance ordering)
            results.sort(key=lambda x: x["score"], reverse=True)
            
            # Limit results based on request
            final_results = results[:search_request.max_results]
            
            search_time = time.time() - start_time
            
            self.logger.info(f"Returning {len(final_results)} direct search results in {search_time:.2f}s")
            
            # Create response
            search_response = SearchResponse(
                results=final_results,
                total_found=len(results),
                search_time=search_time,
                sources_used=["google_drive_direct"]
            )
            
            return {
                "results": final_results,
                "total_found": len(results),
                "search_time": search_time,
                "sources_used": search_response.sources_used,
                "search_method": "direct_gdrive"
            }
            
        except Exception as e:
            self.logger.error(f"Error performing direct search: {e}")
            raise
    
    async def _send_error_response(self, original_message: AgentMessage, error: str) -> None:
        """Send error response back to sender."""
        try:
            error_response = create_message(
                sender=self.agent_type,
                recipient=original_message.sender,
                message_type=MessageType.ERROR,
                payload={"error": error},
                correlation_id=original_message.id
            )
            await self._send_message_to_orchestrator(error_response)
        except Exception as e:
            self.logger.error(f"Failed to send error response: {e}")


# For backward compatibility, alias the old class name
HybridSearchAgent = SearchAgent
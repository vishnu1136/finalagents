"""
Source Linking Agent
====================
Specialized agent for providing links to source documents for further reading.
"""

import asyncio
import time
from typing import Any, Dict, List, Optional
import logging
from collections import defaultdict

from ..core.base_agent import BaseAgent
from ..core.agent_communication import (
    AgentMessage, MessageType, AgentType,
    SourceLinkingRequest, SourceLinkingResponse, create_message
)


class SourceLinkingAgent(BaseAgent):
    """Agent specialized in linking and organizing source documents."""
    
    def __init__(self):
        super().__init__(
            agent_type=AgentType.SOURCE_LINKING_AGENT,
            name="SourceLinkingAgent",
            max_concurrent_tasks=5,
            timeout_seconds=30
        )
        
        # Register message handlers
        self.register_handler(MessageType.SOURCE_LINKING_REQUEST, self._handle_source_linking_request)
        self.register_handler(MessageType.HEARTBEAT, self._handle_heartbeat)
    
    async def _send_message_to_orchestrator(self, message: AgentMessage) -> None:
        """Send message to orchestrator."""
        if hasattr(self, 'orchestrator_callback'):
            await self.orchestrator_callback(message)
    
    async def process_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a source linking task."""
        try:
            source_linking_request = SourceLinkingRequest(**task_data)
            return await self._link_sources(source_linking_request)
        except Exception as e:
            self.logger.error(f"Error processing source linking task: {e}")
            raise
    
    async def _handle_source_linking_request(self, message: AgentMessage) -> None:
        """Handle source linking request messages."""
        try:
            source_linking_request = SourceLinkingRequest(**message.payload)
            response = await self._link_sources(source_linking_request)
            
            # Send response back
            response_message = create_message(
                sender=self.agent_type,
                recipient=message.sender,
                message_type=MessageType.SOURCE_LINKING_RESPONSE,
                payload=response,
                correlation_id=message.id
            )
            await self._send_message_to_orchestrator(response_message)
            
        except Exception as e:
            self.logger.error(f"Error handling source linking request: {e}")
            await self._send_error_response(message, str(e))
    
    async def _handle_heartbeat(self, message: AgentMessage) -> None:
        """Handle heartbeat messages."""
        self.logger.debug("Received heartbeat")
    
    async def _link_sources(self, request: SourceLinkingRequest) -> Dict[str, Any]:
        """Link and organize source documents."""
        start_time = time.time()
        
        try:
            documents = request.documents or []
            query = request.query or ""
            
            self.logger.info(f"Linking sources for query: '{query}' with {len(documents)} documents")
            
            if not documents:
                return {
                    "sources": [],
                    "grouped_sources": {},
                    "source_categories": [],
                    "processing_time": time.time() - start_time
                }
            
            # Process and categorize sources
            processed_sources = self._process_sources(documents)
            grouped_sources = self._group_sources(processed_sources, query)
            source_categories = self._categorize_sources(processed_sources)
            
            processing_time = time.time() - start_time
            
            self.logger.info(f"Source linking complete: {len(processed_sources)} sources, {len(grouped_sources)} groups")
            
            return {
                "sources": processed_sources,
                "grouped_sources": grouped_sources,
                "source_categories": source_categories,
                "processing_time": processing_time
            }
            
        except Exception as e:
            self.logger.error(f"Error linking sources: {e}")
            raise
    
    def _process_sources(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process and clean source documents."""
        processed = []
        
        for doc in documents:
            # Extract and clean source information
            source = {
                "title": doc.get("title", "Unknown Document"),
                "url": doc.get("url", ""),
                "snippet": doc.get("snippet", ""),
                "score": doc.get("score", 0.0),
                "file_id": doc.get("file_id", ""),
                "mime_type": doc.get("mime_type", ""),
                "source_type": self._determine_source_type(doc),
                "relevance": self._calculate_relevance(doc),
                "accessibility": self._check_accessibility(doc)
            }
            
            # Only include sources with valid URLs or file IDs
            if source["url"] or source["file_id"]:
                processed.append(source)
        
        # Sort by relevance score
        processed.sort(key=lambda x: x["relevance"], reverse=True)
        
        return processed
    
    def _determine_source_type(self, doc: Dict[str, Any]) -> str:
        """Determine the type of source document."""
        mime_type = doc.get("mime_type", "").lower()
        title = doc.get("title", "").lower()
        
        # Google Docs
        if "document" in mime_type or "google" in mime_type:
            return "document"
        
        # PDFs
        if "pdf" in mime_type:
            return "pdf"
        
        # Spreadsheets
        if "sheet" in mime_type or "spreadsheet" in mime_type:
            return "spreadsheet"
        
        # Presentations
        if "presentation" in mime_type or "slides" in mime_type:
            return "presentation"
        
        # Check title for hints
        if any(word in title for word in ["policy", "procedure", "guideline"]):
            return "policy"
        elif any(word in title for word in ["meeting", "notes", "minutes"]):
            return "meeting_notes"
        elif any(word in title for word in ["training", "guide", "manual"]):
            return "training"
        elif any(word in title for word in ["form", "template", "checklist"]):
            return "form"
        
        return "document"
    
    def _calculate_relevance(self, doc: Dict[str, Any]) -> float:
        """Calculate relevance score for the document."""
        score = doc.get("score", 0.0)
        title = doc.get("title", "").lower()
        snippet = doc.get("snippet", "").lower()
        
        # Boost score for certain document types
        if any(word in title for word in ["policy", "procedure", "official"]):
            score += 0.2
        
        # Boost score for recent documents (if we had date info)
        # This would require additional metadata
        
        # Boost score for documents with longer, more descriptive snippets
        if len(snippet) > 100:
            score += 0.1
        
        return min(score, 1.0)
    
    def _check_accessibility(self, doc: Dict[str, Any]) -> str:
        """Check if the document is accessible."""
        url = doc.get("url", "")
        file_id = doc.get("file_id", "")
        
        if url and "drive.google.com" in url:
            return "accessible"
        elif file_id:
            return "file_id_available"
        else:
            return "limited"
    
    def _group_sources(self, sources: List[Dict[str, Any]], query: str) -> Dict[str, List[Dict[str, Any]]]:
        """Group sources by category and relevance."""
        grouped = defaultdict(list)
        
        for source in sources:
            source_type = source["source_type"]
            grouped[source_type].append(source)
        
        # Sort each group by relevance
        for group in grouped.values():
            group.sort(key=lambda x: x["relevance"], reverse=True)
        
        # Add a "most_relevant" group with top sources
        most_relevant = sources[:5]  # Top 5 most relevant
        if most_relevant:
            grouped["most_relevant"] = most_relevant
        
        return dict(grouped)
    
    def _categorize_sources(self, sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create categories for the sources."""
        categories = []
        
        # Count source types
        type_counts = defaultdict(int)
        for source in sources:
            type_counts[source["source_type"]] += 1
        
        # Create category information
        for source_type, count in type_counts.items():
            category = {
                "name": source_type.replace("_", " ").title(),
                "count": count,
                "type": source_type,
                "description": self._get_category_description(source_type)
            }
            categories.append(category)
        
        # Sort by count (most common first)
        categories.sort(key=lambda x: x["count"], reverse=True)
        
        return categories
    
    def _get_category_description(self, source_type: str) -> str:
        """Get description for source category."""
        descriptions = {
            "document": "Text documents and articles",
            "pdf": "PDF documents and reports",
            "spreadsheet": "Data sheets and spreadsheets",
            "presentation": "Slides and presentations",
            "policy": "Official policies and procedures",
            "meeting_notes": "Meeting notes and minutes",
            "training": "Training materials and guides",
            "form": "Forms and templates",
            "most_relevant": "Most relevant sources for your query"
        }
        
        return descriptions.get(source_type, "Document sources")

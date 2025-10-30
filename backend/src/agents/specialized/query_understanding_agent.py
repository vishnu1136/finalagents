"""
Query Understanding Agent
=========================
Specialized agent for parsing employee questions and determining intent.
"""

import asyncio
import time
from typing import Any, Dict, List, Optional
import logging
import re
from collections import Counter

from ..core.base_agent import BaseAgent
from ..core.agent_communication import (
    AgentMessage, MessageType, AgentType,
    QueryUnderstandingRequest, QueryUnderstandingResponse, create_message
)


class QueryUnderstandingAgent(BaseAgent):
    """Agent specialized in understanding and analyzing user queries."""
    
    def __init__(self):
        super().__init__(
            agent_type=AgentType.QUERY_UNDERSTANDER,
            name="QueryUnderstandingAgent",
            max_concurrent_tasks=5,
            timeout_seconds=30
        )
        
        # Register message handlers
        self.register_handler(MessageType.QUERY_UNDERSTANDING_REQUEST, self._handle_query_understanding_request)
        self.register_handler(MessageType.HEARTBEAT, self._handle_heartbeat)
    
    async def _send_message_to_orchestrator(self, message: AgentMessage) -> None:
        """Send message to orchestrator."""
        if hasattr(self, 'orchestrator_callback'):
            await self.orchestrator_callback(message)
    
    async def process_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a query understanding task."""
        try:
            query_understanding_request = QueryUnderstandingRequest(**task_data)
            return await self._analyze_query(query_understanding_request)
        except Exception as e:
            self.logger.error(f"Error processing query understanding task: {e}")
            raise
    
    async def _handle_query_understanding_request(self, message: AgentMessage) -> None:
        """Handle query understanding request messages."""
        try:
            query_understanding_request = QueryUnderstandingRequest(**message.payload)
            response = await self._analyze_query(query_understanding_request)
            
            # Send response back
            response_message = create_message(
                sender=self.agent_type,
                recipient=message.sender,
                message_type=MessageType.QUERY_UNDERSTANDING_RESPONSE,
                payload=response,
                correlation_id=message.id
            )
            await self._send_message_to_orchestrator(response_message)
            
        except Exception as e:
            self.logger.error(f"Error handling query understanding request: {e}")
            await self._send_error_response(message, str(e))
    
    async def _handle_heartbeat(self, message: AgentMessage) -> None:
        """Handle heartbeat messages."""
        self.logger.debug("Received heartbeat")
    
    async def _analyze_query(self, request: QueryUnderstandingRequest) -> Dict[str, Any]:
        """Analyze and understand the user query."""
        start_time = time.time()
        
        try:
            query = request.query.strip()
            if not query:
                return {
                    "normalized_query": "",
                    "expanded_keywords": [],
                    "is_broad_subject": True,
                    "intent": "general",
                    "confidence": 0.0,
                    "processing_time": 0.0
                }
            
            self.logger.info(f"Analyzing query: '{query}'")
            
            # Normalize the query
            normalized_query = self._normalize_query(query)
            
            # Extract keywords
            expanded_keywords = self._extract_keywords(query)
            
            # Determine if it's a broad subject
            is_broad_subject = self._is_broad_subject(query, expanded_keywords)
            
            # Determine intent
            intent = self._determine_intent(query, expanded_keywords)
            
            # Calculate confidence
            confidence = self._calculate_confidence(query, expanded_keywords, intent)
            
            processing_time = time.time() - start_time
            
            self.logger.info(f"Query analysis complete: intent={intent}, broad={is_broad_subject}, keywords={len(expanded_keywords)}")
            
            return {
                "normalized_query": normalized_query,
                "expanded_keywords": expanded_keywords,
                "is_broad_subject": is_broad_subject,
                "intent": intent,
                "confidence": confidence,
                "processing_time": processing_time
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing query: {e}")
            raise
    
    def _normalize_query(self, query: str) -> str:
        """Normalize the query for better search results."""
        # Convert to lowercase
        normalized = query.lower()
        
        # Remove extra whitespace
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        # Remove common stop words but keep important ones
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        words = normalized.split()
        filtered_words = [word for word in words if word not in stop_words or len(word) > 3]
        
        return ' '.join(filtered_words) if filtered_words else normalized
    
    def _extract_keywords(self, query: str) -> List[str]:
        """Extract and expand keywords from the query."""
        # Basic keyword extraction
        words = re.findall(r'\b\w+\b', query.lower())
        
        # Remove very short words
        keywords = [word for word in words if len(word) > 2]
        
        # Add common variations and synonyms
        expanded = set(keywords)
        
        # Add common business term variations
        business_terms = {
            'pto': ['vacation', 'time off', 'leave', 'holiday'],
            'hr': ['human resources', 'personnel'],
            'payroll': ['salary', 'wages', 'compensation'],
            'benefits': ['insurance', 'health', 'dental', 'vision'],
            'policy': ['policies', 'guidelines', 'procedures'],
            'training': ['education', 'learning', 'development'],
            'meeting': ['standup', 'stand-up', 'daily', 'scrum'],
            'project': ['initiative', 'task', 'work'],
            'provider': ['vendor', 'supplier', 'partner']
        }
        
        for keyword in keywords:
            if keyword in business_terms:
                expanded.update(business_terms[keyword])
        
        return list(expanded)
    
    def _is_broad_subject(self, query: str, keywords: List[str]) -> bool:
        """Determine if the query is about a broad subject."""
        # Broad subject indicators
        broad_indicators = [
            'what is', 'tell me about', 'overview', 'introduction',
            'how does', 'explain', 'describe', 'all about'
        ]
        
        query_lower = query.lower()
        
        # Check for broad indicators
        for indicator in broad_indicators:
            if indicator in query_lower:
                return True
        
        # Check query length (very short queries are often broad)
        if len(query.split()) <= 2:
            return True
        
        # Check if it's asking for general information
        general_questions = ['what', 'how', 'why', 'when', 'where', 'who']
        if any(query_lower.startswith(q) for q in general_questions):
            return True
        
        return False
    
    def _determine_intent(self, query: str, keywords: List[str]) -> str:
        """Determine the user's intent."""
        query_lower = query.lower()
        
        # Intent patterns
        intents = {
            'search': ['find', 'search', 'look for', 'locate', 'where is'],
            'how_to': ['how to', 'how do i', 'steps', 'process', 'procedure'],
            'policy': ['policy', 'rule', 'guideline', 'procedure', 'process'],
            'contact': ['contact', 'who', 'email', 'phone', 'reach'],
            'schedule': ['schedule', 'meeting', 'calendar', 'time', 'when'],
            'benefits': ['benefit', 'insurance', 'pto', 'vacation', 'leave'],
            'technical': ['error', 'bug', 'issue', 'problem', 'fix', 'troubleshoot'],
            'general': ['what', 'explain', 'tell me', 'describe']
        }
        
        # Score each intent
        intent_scores = {}
        for intent, patterns in intents.items():
            score = 0
            for pattern in patterns:
                if pattern in query_lower:
                    score += 1
            intent_scores[intent] = score
        
        # Return the intent with highest score, default to 'general'
        if intent_scores:
            return max(intent_scores, key=intent_scores.get)
        
        return 'general'
    
    def _calculate_confidence(self, query: str, keywords: List[str], intent: str) -> float:
        """Calculate confidence in the query analysis."""
        confidence = 0.5  # Base confidence
        
        # Longer queries with more keywords are more confident
        if len(keywords) > 3:
            confidence += 0.2
        
        # Specific intents are more confident
        if intent in ['how_to', 'policy', 'contact', 'technical']:
            confidence += 0.2
        
        # Queries with clear question words are more confident
        question_words = ['what', 'how', 'why', 'when', 'where', 'who']
        if any(query.lower().startswith(q) for q in question_words):
            confidence += 0.1
        
        return min(confidence, 1.0)

"""
Analysis Agent
=============
Specialized agent for document analysis and insights generation.
"""

import asyncio
import time
from typing import Any, Dict, List, Optional
import logging
import openai
import os

from ..base_agent import BaseAgent
from ..protocol.agent_communication import (
    AgentMessage, MessageType, AgentType,
    AnalysisRequest, AnalysisResponse, create_message
)


class QueryUnderstandingAgent(BaseAgent):
    """Agent specialized in query understanding and analysis."""
    
    def __init__(self):
        super().__init__(
            agent_type=AgentType.QUERY_UNDERSTANDER,
            name="QueryUnderstandingAgent",
            max_concurrent_tasks=10,
            timeout_seconds=30
        )
        
        # Initialize OpenAI client
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            self.logger.warning("OPENAI_API_KEY not found in environment variables")
            self.openai_client = None
        else:
            try:
                # Initialize with minimal configuration to avoid proxies issue
                self.openai_client = openai.AsyncOpenAI(
                    api_key=api_key,
                    timeout=30.0,
                    max_retries=2
                )
            except Exception as e:
                self.logger.error(f"Failed to initialize OpenAI client: {e}")
                self.openai_client = None
        
        # Register message handlers
        self.register_handler(MessageType.ANALYSIS_REQUEST, self._handle_analysis_request)
        self.register_handler(MessageType.HEARTBEAT, self._handle_heartbeat)
    
    async def _send_message_to_orchestrator(self, message: AgentMessage) -> None:
        """Send message to orchestrator."""
        if hasattr(self, 'orchestrator_callback'):
            await self.orchestrator_callback(message)
    
    async def process_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a query understanding task using the proven logic."""
        try:
            # Use the exact logic from the old query_understanding_node
            return await self._understand_query(task_data)
        except Exception as e:
            self.logger.error(f"Error processing query understanding task: {e}")
            raise
    
    async def _handle_analysis_request(self, message: AgentMessage) -> None:
        """Handle analysis request messages."""
        try:
            analysis_request = AnalysisRequest(**message.payload)
            analysis_response = await self._perform_analysis(analysis_request)
            
            # Send response back
            response = create_message(
                sender=self.agent_type,
                recipient=message.sender,
                message_type=MessageType.ANALYSIS_RESPONSE,
                payload=analysis_response,
                correlation_id=message.id
            )
            await self._send_message_to_orchestrator(response)
            
        except Exception as e:
            self.logger.error(f"Error handling analysis request: {e}")
            await self._send_error_response(message, str(e))
    
    async def _handle_heartbeat(self, message: AgentMessage) -> None:
        """Handle heartbeat messages."""
        self.logger.debug("Received heartbeat")
    
    async def _understand_query(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Understand query using the exact logic from the old query_understanding_node."""
        query = inputs.get("query", "").strip()
        
        # Extract meaningful keywords from the query
        # Remove common question words and phrases
        stop_words = {
            "can", "you", "please", "list", "all", "the", "files", "related", "to",
            "show", "me", "find", "search", "for", "about", "what", "is", "are",
            "how", "do", "does", "will", "would", "could", "should", "may", "might",
            "tell", "give", "get", "help", "assist", "with", "regarding", "concerning",
            "information", "resources", "documents", "data", "content"
        }
        
        # Convert to lowercase and split into words
        import re
        words = re.findall(r'\b\w+\b', query.lower())
        
        # Filter out stop words and keep only meaningful terms
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        
        # Subject expansion for better search coverage
        subject_expansions = {
            "health": ["healthcare", "medical", "clinical", "patient", "hospital"],
            "healthcare": ["health", "medical", "clinical", "patient", "hospital"],
            "medical": ["health", "healthcare", "clinical", "patient", "hospital"],
            "clinical": ["health", "healthcare", "medical", "patient", "hospital"],
            "ai": ["artificial intelligence", "machine learning", "ml", "automation"],
            "artificial": ["ai", "intelligence", "machine learning", "ml"],
            "intelligence": ["ai", "artificial", "machine learning", "ml"],
            "data": ["analytics", "analysis", "insights", "metrics"],
            "analytics": ["data", "analysis", "insights", "metrics"],
            "business": ["enterprise", "corporate", "organization", "company"],
            "technology": ["tech", "technical", "system", "platform"],
            "system": ["platform", "technology", "tech", "solution"]
        }
        
        # Expand keywords with related terms
        expanded_keywords = set(keywords)
        for keyword in keywords:
            if keyword in subject_expansions:
                expanded_keywords.update(subject_expansions[keyword])
        
        # If no keywords found, use the original query
        if not keywords:
            normalized_query = query
        else:
            # Join expanded keywords with spaces for better search coverage
            normalized_query = " ".join(sorted(expanded_keywords))
        
        # Determine intent based on query patterns
        intent = "qa"
        if any(word in query.lower() for word in ["list", "show", "find", "search"]):
            intent = "search"
        elif any(word in query.lower() for word in ["what", "how", "why", "when", "where"]):
            intent = "qa"
        
        # Detect if this is a broad subject query (asking for overview)
        is_broad_subject = (
            len(keywords) <= 2 and 
            any(word in query.lower() for word in ["what", "show", "list", "find"]) and
            not any(specific in query.lower() for specific in ["cdss", "implementation", "guide", "manual", "document"])
        )
        
        return {
            "intent": intent, 
            "normalized_query": normalized_query,
            "original_query": query,
            "is_broad_subject": is_broad_subject,
            "expanded_keywords": list(expanded_keywords)
        }
    
    async def _perform_analysis(self, analysis_request: AnalysisRequest) -> Dict[str, Any]:
        """Perform the actual analysis operation."""
        start_time = time.time()
        
        try:
            # Prepare document content for analysis
            document_texts = []
            for doc in analysis_request.documents:
                title = doc.get("title", "Unknown Document")
                snippet = doc.get("snippet", "")
                document_texts.append(f"Title: {title}\nContent: {snippet}\n")
            
            combined_content = "\n".join(document_texts)
            
            # Perform analysis based on type
            if analysis_request.analysis_type == "content":
                analysis_result = await self._analyze_content(combined_content, analysis_request.query)
            elif analysis_request.analysis_type == "relevance":
                analysis_result = await self._analyze_relevance(analysis_request.documents, analysis_request.query)
            elif analysis_request.analysis_type == "categorization":
                analysis_result = await self._analyze_categorization(analysis_request.documents)
            else:
                analysis_result = await self._analyze_general(combined_content, analysis_request.query)
            
            analysis_time = time.time() - start_time
            
            # Create response
            analysis_response = AnalysisResponse(
                analysis=analysis_result,
                confidence_score=analysis_result.get("confidence", 0.8),
                insights=analysis_result.get("insights", []),
                recommendations=analysis_result.get("recommendations", [])
            )
            
            return {
                "analysis": analysis_result,
                "confidence_score": analysis_response.confidence_score,
                "insights": analysis_response.insights,
                "recommendations": analysis_response.recommendations,
                "analysis_time": analysis_time
            }
            
        except Exception as e:
            self.logger.error(f"Error performing analysis: {e}")
            raise
    
    async def _analyze_content(self, content: str, query: str) -> Dict[str, Any]:
        """Analyze document content for insights."""
        try:
            if not self.openai_client:
                self.logger.warning("OpenAI client not available, using fallback analysis")
                return {
                    "content_analysis": f"Analysis for query '{query}' - OpenAI client not available",
                    "insights": ["OpenAI client not configured"],
                    "confidence": 0.1,
                    "themes": ["Configuration issue"]
                }
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert document analyst. Analyze the provided content and extract key insights, themes, and patterns."
                    },
                    {
                        "role": "user",
                        "content": f"Query: {query}\n\nContent to analyze:\n{content}\n\nProvide analysis with:\n1. Key themes\n2. Important insights\n3. Patterns or trends\n4. Confidence score (0-1)"
                    }
                ],
                max_tokens=1000,
                temperature=0.3
            )
            
            analysis_text = response.choices[0].message.content
            
            # Parse the analysis
            insights = self._extract_insights(analysis_text)
            confidence = self._extract_confidence(analysis_text)
            
            return {
                "content_analysis": analysis_text,
                "insights": insights,
                "confidence": confidence,
                "themes": self._extract_themes(analysis_text)
            }
            
        except Exception as e:
            self.logger.error(f"Error in content analysis: {e}")
            return {
                "content_analysis": "Analysis failed due to error",
                "insights": [],
                "confidence": 0.1,
                "themes": []
            }
    
    async def _analyze_relevance(self, documents: List[Dict[str, Any]], query: str) -> Dict[str, Any]:
        """Analyze relevance of documents to the query."""
        try:
            if not self.openai_client:
                self.logger.warning("OpenAI client not available, using fallback relevance analysis")
                return {
                    "relevance_analysis": f"Relevance analysis for query '{query}' - OpenAI client not available",
                    "relevance_scores": [5.0] * len(documents),
                    "average_relevance": 5.0,
                    "confidence": 0.1
                }
            
            # Prepare document summaries
            doc_summaries = []
            for i, doc in enumerate(documents):
                title = doc.get("title", "Unknown")
                snippet = doc.get("snippet", "")
                doc_summaries.append(f"Document {i+1}: {title}\nSnippet: {snippet}")
            
            combined_docs = "\n\n".join(doc_summaries)
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at analyzing document relevance. Rate how relevant each document is to the given query."
                    },
                    {
                        "role": "user",
                        "content": f"Query: {query}\n\nDocuments:\n{combined_docs}\n\nRate each document's relevance (1-10) and explain why."
                    }
                ],
                max_tokens=800,
                temperature=0.2
            )
            
            relevance_analysis = response.choices[0].message.content
            
            # Extract relevance scores
            relevance_scores = self._extract_relevance_scores(relevance_analysis)
            
            return {
                "relevance_analysis": relevance_analysis,
                "relevance_scores": relevance_scores,
                "average_relevance": sum(relevance_scores) / len(relevance_scores) if relevance_scores else 0,
                "confidence": 0.8
            }
            
        except Exception as e:
            self.logger.error(f"Error in relevance analysis: {e}")
            return {
                "relevance_analysis": "Relevance analysis failed",
                "relevance_scores": [5] * len(documents),
                "average_relevance": 5.0,
                "confidence": 0.1
            }
    
    async def _analyze_categorization(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze documents for categorization."""
        try:
            if not self.openai_client:
                self.logger.warning("OpenAI client not available, using fallback categorization")
                return {
                    "categorization": "Categorization analysis - OpenAI client not available",
                    "suggested_categories": ["General"],
                    "confidence": 0.1
                }
            
            # Prepare document information
            doc_info = []
            for doc in documents:
                title = doc.get("title", "Unknown")
                snippet = doc.get("snippet", "")
                doc_info.append(f"Title: {title}\nContent: {snippet[:200]}...")
            
            combined_info = "\n\n".join(doc_info)
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at categorizing documents. Analyze the provided documents and suggest appropriate categories."
                    },
                    {
                        "role": "user",
                        "content": f"Documents to categorize:\n{combined_info}\n\nSuggest categories and explain the reasoning."
                    }
                ],
                max_tokens=600,
                temperature=0.3
            )
            
            categorization = response.choices[0].message.content
            
            # Extract categories
            categories = self._extract_categories(categorization)
            
            return {
                "categorization": categorization,
                "suggested_categories": categories,
                "confidence": 0.8
            }
            
        except Exception as e:
            self.logger.error(f"Error in categorization analysis: {e}")
            return {
                "categorization": "Categorization analysis failed",
                "suggested_categories": ["General"],
                "confidence": 0.1
            }
    
    async def _analyze_general(self, content: str, query: str) -> Dict[str, Any]:
        """Perform general analysis."""
        try:
            if not self.openai_client:
                self.logger.warning("OpenAI client not available, using fallback general analysis")
                return {
                    "general_analysis": f"General analysis for query '{query}' - OpenAI client not available",
                    "insights": ["OpenAI client not configured"],
                    "confidence": 0.1
                }
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert analyst. Provide comprehensive analysis of the given content in relation to the query."
                    },
                    {
                        "role": "user",
                        "content": f"Query: {query}\n\nContent:\n{content}\n\nProvide detailed analysis."
                    }
                ],
                max_tokens=1200,
                temperature=0.4
            )
            
            analysis = response.choices[0].message.content
            
            return {
                "general_analysis": analysis,
                "insights": self._extract_insights(analysis),
                "confidence": 0.7
            }
            
        except Exception as e:
            self.logger.error(f"Error in general analysis: {e}")
            return {
                "general_analysis": "Analysis failed due to error",
                "insights": [],
                "confidence": 0.1
            }
    
    def _extract_insights(self, text: str) -> List[str]:
        """Extract insights from analysis text."""
        # Simple extraction - look for numbered lists or bullet points
        insights = []
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if line and (line.startswith('-') or line.startswith('•') or 
                        (line[0].isdigit() and '.' in line[:3])):
                insights.append(line)
        return insights[:5]  # Limit to top 5 insights
    
    def _extract_confidence(self, text: str) -> float:
        """Extract confidence score from analysis text."""
        # Look for confidence mentions
        text_lower = text.lower()
        if "confidence" in text_lower:
            import re
            match = re.search(r'confidence[:\s]*(\d+\.?\d*)', text_lower)
            if match:
                return float(match.group(1))
        return 0.8  # Default confidence
    
    def _extract_themes(self, text: str) -> List[str]:
        """Extract themes from analysis text."""
        # Simple theme extraction
        themes = []
        lines = text.split('\n')
        for line in lines:
            if "theme" in line.lower() or "topic" in line.lower():
                themes.append(line.strip())
        return themes[:3]  # Limit to top 3 themes
    
    def _extract_relevance_scores(self, text: str) -> List[float]:
        """Extract relevance scores from analysis text."""
        import re
        scores = []
        # Look for numbers that could be scores
        numbers = re.findall(r'\b(\d+\.?\d*)\b', text)
        for num in numbers:
            score = float(num)
            if 1 <= score <= 10:  # Valid relevance score range
                scores.append(score)
        return scores
    
    def _extract_categories(self, text: str) -> List[str]:
        """Extract categories from categorization text."""
        categories = []
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if line and not line.startswith('Document'):
                # Look for category-like text
                if any(word in line.lower() for word in ['category', 'type', 'class', 'group']):
                    categories.append(line)
        return categories[:5]  # Limit to top 5 categories

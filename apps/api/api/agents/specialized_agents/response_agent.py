"""
Response Agent
=============
Specialized agent for generating user responses and formatting output.
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
    ResponseRequest, ResponseResponse, create_message
)


class AnswerGenerationAgent(BaseAgent):
    """Agent specialized in generating user responses and formatting output."""
    
    def __init__(self):
        super().__init__(
            agent_type=AgentType.ANSWER_GENERATION_AGENT,
            name="AnswerGenerationAgent",
            max_concurrent_tasks=5,
            timeout_seconds=90
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
        self.register_handler(MessageType.RESPONSE_REQUEST, self._handle_response_request)
        self.register_handler(MessageType.HEARTBEAT, self._handle_heartbeat)
    
    async def _send_message_to_orchestrator(self, message: AgentMessage) -> None:
        """Send message to orchestrator."""
        if hasattr(self, 'orchestrator_callback'):
            await self.orchestrator_callback(message)
    
    async def process_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a response generation task using the proven logic."""
        try:
            # Use the exact logic from the old answer_generation_node
            return await self._generate_answer(task_data)
        except Exception as e:
            self.logger.error(f"Error processing response task: {e}")
            raise
    
    async def _handle_response_request(self, message: AgentMessage) -> None:
        """Handle response request messages."""
        try:
            response_request = ResponseRequest(**message.payload)
            response_response = await self._generate_response(response_request)
            
            # Send response back
            response = create_message(
                sender=self.agent_type,
                recipient=message.sender,
                message_type=MessageType.RESPONSE_RESPONSE,
                payload=response_response,
                correlation_id=message.id
            )
            await self._send_message_to_orchestrator(response)
            
        except Exception as e:
            self.logger.error(f"Error handling response request: {e}")
            await self._send_error_response(message, str(e))
    
    async def _handle_heartbeat(self, message: AgentMessage) -> None:
        """Handle heartbeat messages."""
        self.logger.debug("Received heartbeat")
    
    async def _generate_answer(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Generate answer using the exact logic from the old answer_generation_node."""
        results = inputs.get("search_results", inputs.get("results", []))
        query = inputs.get("normalized_query", inputs.get("query", ""))
        is_broad_subject = inputs.get("is_broad_subject", False)
        expanded_keywords = inputs.get("expanded_keywords", [])
        
        # Debug logging
        self.logger.info(f"Answer generation - Query: {query}")
        self.logger.info(f"Answer generation - Results count: {len(results) if results else 0}")
        if results and len(results) > 0:
            self.logger.info(f"Answer generation - First result keys: {list(results[0].keys()) if results[0] else 'None'}")
            self.logger.info(f"Answer generation - First result title: {results[0].get('title', 'No title')}")
        
        if not results:
            self.logger.warning("No search results provided to answer generation")
            return {"answer": "I couldn't find relevant information.", "sources": [], "grouped_sources": {}}
        
        # Prepare context from search results with URLs (limit to top 20 to avoid token limits)
        context_parts = []
        top_results = results[:20]  # Limit to top 20 results to avoid context length issues
        
        for i, result in enumerate(top_results, 1):
            title = result.get("title", "Unknown Document")
            snippet = result.get("snippet", "")
            url = result.get("url", "")
            
            # Format as markdown link if URL exists
            if url:
                context_parts.append(f"Source {i}: [{title}]({url})\n{snippet}\n")
            else:
                context_parts.append(f"Source {i}: {title}\n{snippet}\n")
        
        context = "\n".join(context_parts)
        
        # Add summary of remaining results
        if len(results) > 20:
            context += f"\n\nNote: {len(results) - 20} additional relevant documents were found but not included in this response due to length constraints."
        
        # Generate a comprehensive answer using OpenAI
        try:
            if not self.openai_client:
                self.logger.warning("OpenAI client not available, using fallback response generation")
                # Fallback to simple concatenation with URLs
                answer_parts = []
                answer_parts.append(f"I found {len(results)} relevant documents for your query: '{query}'")
                
                if results:
                    answer_parts.append("\nHere are the relevant sources:\n")
                    for i, result in enumerate(results[:10], 1):  # Limit to top 10
                        title = result.get("title", "Unknown Document")
                        url = result.get("url", "")
                        snippet = result.get("snippet", "")
                        
                        if url:
                            answer_parts.append(f"{i}. [{title}]({url})")
                        else:
                            answer_parts.append(f"{i}. {title}")
                        
                        if snippet:
                            answer_parts.append(f"   {snippet[:100]}...")
                        answer_parts.append("")
                
                return {
                    "answer": "\n".join(answer_parts),
                    "sources": sources,
                    "grouped_sources": grouped_sources
                }
            
            # Customize system prompt based on query type
            if is_broad_subject:
                system_prompt = f"""You are a helpful assistant that provides comprehensive overviews of subjects based on available documents. 
                
                The user is asking about a broad subject: "{query}". They want to understand what information is available about this topic.
                
                Based on the provided documents, give them:
                1. A brief overview of what this subject covers
                2. The main categories/types of information available
                3. Key topics and areas covered
                4. A summary of the available resources
                
                IMPORTANT: Include clickable links in your response using markdown format [text](url) when referencing specific documents. This helps users access the original sources.
                
                Be informative but concise. Help them understand the scope and depth of information available."""
            else:
                system_prompt = """You are a helpful assistant that provides comprehensive explanations based on the provided context. 

When given search results with markdown links, synthesize the information into a clear, well-structured answer that directly addresses the user's query.

IMPORTANT: Include clickable links in your response using markdown format [text](url) when referencing sources. This helps users access the original documents."""
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system", 
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": f"Query: {query}\n\nContext from documents:\n{context}\n\nPlease provide a comprehensive explanation based on the above context. Structure your answer clearly and cite the sources when relevant."
                    }
                ],
                max_tokens=1500,  # Increased for broader subject queries
                temperature=0.7
            )
            
            answer = response.choices[0].message.content
        except Exception as e:
            self.logger.error(f"Error generating answer with LLM: {e}")
            # Fallback to simple concatenation with URLs (limit to top 20)
            snippets = []
            top_results = results[:20]  # Limit to avoid overwhelming response
            
            for i, r in enumerate(top_results, 1):
                title = r.get("title", "Unknown Document")
                snippet = r.get("snippet", "")
                url = r.get("url", "")
                
                if url:
                    snippets.append(f"**Source {i}:** [{title}]({url})\n{snippet}")
                else:
                    snippets.append(f"**Source {i}:** {title}\n{snippet}")
            
            answer = f"I found {len(results)} relevant documents for your query, organized by category:\n\n" + "\n\n".join(snippets)
            
            # Add note about additional results
            if len(results) > 20:
                answer += f"\n\n*Note: {len(results) - 20} additional relevant documents were found.*"
        
        # Prepare sources
        sources = []
        for result in results:
            sources.append({
                "title": result.get("title", "Unknown Document"),
                "url": result.get("url", ""),
                "snippet": result.get("snippet", "")
            })
        
        # Group sources
        grouped_sources = self._group_sources(sources)
        
        return {
            "answer": answer, 
            "sources": sources,
            "grouped_sources": grouped_sources
        }
    
    async def _generate_response(self, response_request: ResponseRequest) -> Dict[str, Any]:
        """Generate the actual response."""
        start_time = time.time()
        
        try:
            # Prepare context from search results with URLs (limit to top 15)
            context_parts = []
            top_results = response_request.search_results[:15]  # Limit to avoid token issues
            
            for i, result in enumerate(top_results, 1):
                title = result.get("title", "Unknown Document")
                snippet = result.get("snippet", "")
                url = result.get("url", "")
                
                # Format as markdown link if URL exists
                if url:
                    context_parts.append(f"Source {i}: [{title}]({url})\n{snippet}\n")
                else:
                    context_parts.append(f"Source {i}: {title}\n{snippet}\n")
            
            context = "\n".join(context_parts)
            
            # Add summary of remaining results
            if len(response_request.search_results) > 15:
                context += f"\n\nNote: {len(response_request.search_results) - 15} additional relevant documents were found."
            
            # Determine response strategy based on type
            if response_request.response_type == "brief":
                answer = await self._generate_brief_response(response_request.query, context)
            elif response_request.response_type == "detailed":
                answer = await self._generate_detailed_response(response_request.query, context, response_request.analysis)
            else:  # comprehensive
                answer = await self._generate_comprehensive_response(response_request.query, context, response_request.analysis)
            
            # Generate sources with grouping
            sources = self._prepare_sources(response_request.search_results)
            grouped_sources = self._group_sources(sources)
            
            response_time = time.time() - start_time
            
            # Create response
            response_response = ResponseResponse(
                answer=answer,
                sources=sources,
                grouped_sources=grouped_sources,
                confidence=0.9
            )
            
            return {
                "answer": answer,
                "sources": sources,
                "grouped_sources": grouped_sources,
                "confidence": response_response.confidence,
                "response_time": response_time
            }
            
        except Exception as e:
            self.logger.error(f"Error generating response: {e}")
            # Fallback response with URLs
            snippets = []
            top_results = response_request.search_results[:20]  # Limit to avoid overwhelming response
            
            for i, result in enumerate(top_results, 1):
                title = result.get("title", "Unknown Document")
                snippet = result.get("snippet", "")
                url = result.get("url", "")
                
                if url:
                    snippets.append(f"**Source {i}:** [{title}]({url})\n{snippet}")
                else:
                    snippets.append(f"**Source {i}:** {title}\n{snippet}")
            
            answer = f"I found {len(response_request.search_results)} relevant documents for your query, organized by category:\n\n" + "\n\n".join(snippets)
            
            if len(response_request.search_results) > 20:
                answer += f"\n\n*Note: {len(response_request.search_results) - 20} additional relevant documents were found.*"
            
            return {
                "answer": answer,
                "sources": self._prepare_sources(response_request.search_results),
                "grouped_sources": {},
                "confidence": 0.3,
                "response_time": time.time() - start_time
            }
    
    async def _generate_brief_response(self, query: str, context: str) -> str:
        """Generate a brief response."""
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant. Provide a brief, concise answer based on the provided context. Keep it under 100 words. IMPORTANT: Include clickable links using markdown format [text](url) when referencing sources."
                    },
                    {
                        "role": "user",
                        "content": f"Query: {query}\n\nContext:\n{context}\n\nProvide a brief answer:"
                    }
                ],
                max_tokens=150,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            self.logger.error(f"Error generating brief response: {e}")
            return f"Based on the search results for '{query}', I found relevant information but encountered an error generating a response."
    
    async def _generate_detailed_response(self, query: str, context: str, analysis: Optional[Dict[str, Any]]) -> str:
        """Generate a detailed response."""
        try:
            analysis_context = ""
            if analysis:
                analysis_context = f"\n\nAnalysis insights:\n{analysis.get('general_analysis', '')}"
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert assistant. Provide a detailed, comprehensive answer based on the provided context and analysis. Structure your response clearly with headings and bullet points. IMPORTANT: Include clickable links using markdown format [text](url) when referencing sources."
                    },
                    {
                        "role": "user",
                        "content": f"Query: {query}\n\nContext:\n{context}{analysis_context}\n\nProvide a detailed response:"
                    }
                ],
                max_tokens=2000,
                temperature=0.6
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            self.logger.error(f"Error generating detailed response: {e}")
            return f"Based on the search results for '{query}', I found relevant information but encountered an error generating a detailed response."
    
    async def _generate_comprehensive_response(self, query: str, context: str, analysis: Optional[Dict[str, Any]]) -> str:
        """Generate a comprehensive response with overview and insights."""
        try:
            analysis_context = ""
            if analysis:
                insights = analysis.get('insights', [])
                recommendations = analysis.get('recommendations', [])
                analysis_context = f"\n\nKey Insights:\n" + "\n".join(f"• {insight}" for insight in insights)
                if recommendations:
                    analysis_context += f"\n\nRecommendations:\n" + "\n".join(f"• {rec}" for rec in recommendations)
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert knowledge assistant. Provide a comprehensive response that includes:
1. A brief overview of what information is available
2. Key findings and insights
3. Detailed explanations based on the sources
4. Practical recommendations
5. Clear structure with headings and formatting

IMPORTANT: Include clickable links using markdown format [text](url) when referencing sources."""
                    },
                    {
                        "role": "user",
                        "content": f"Query: {query}\n\nContext from documents:\n{context}{analysis_context}\n\nProvide a comprehensive response:"
                    }
                ],
                max_tokens=2500,
                temperature=0.5
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            self.logger.error(f"Error generating comprehensive response: {e}")
            return f"Based on the search results for '{query}', I found relevant information but encountered an error generating a comprehensive response."
    
    def _prepare_sources(self, search_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prepare sources for display."""
        sources = []
        for result in search_results:
            sources.append({
                "title": result.get("title", "Unknown Document"),
                "url": result.get("url", ""),
                "snippet": result.get("snippet", "")
            })
        return sources
    
    def _group_sources(self, sources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Group sources by category."""
        from collections import defaultdict
        
        # Simple categorization based on title keywords
        categories = {
            "Implementation Guides": ["implementation", "setup", "install", "guide", "tutorial"],
            "Best Practices": ["best practice", "recommendation", "guideline", "standard"],
            "Evaluation & Metrics": ["evaluation", "assessment", "metrics", "measurement"],
            "Use Cases": ["use case", "scenario", "example", "case study"],
            "Technical Documentation": ["api", "technical", "specification", "architecture"],
            "Research & Studies": ["research", "study", "paper", "analysis"],
            "Training & Education": ["training", "education", "learning", "course"],
            "Policies & Compliance": ["policy", "compliance", "regulation", "standard"]
        }
        
        grouped = defaultdict(list)
        
        for source in sources:
            title_lower = source["title"].lower()
            snippet_lower = source.get("snippet", "").lower()
            content = f"{title_lower} {snippet_lower}"
            
            # Find best matching category
            best_category = "General Documents"
            best_score = 0
            
            for category, keywords in categories.items():
                score = sum(1 for keyword in keywords if keyword in content)
                if score > best_score:
                    best_score = score
                    best_category = category
            
            grouped[best_category].append(source)
        
        # Convert to the expected format
        grouped_sources = {}
        for category, docs in grouped.items():
            grouped_sources[category] = {
                "count": len(docs),
                "documents": docs
            }
        
        return grouped_sources

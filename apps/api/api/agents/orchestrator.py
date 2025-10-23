"""
Agent Orchestrator
=================
Coordinates multiple agents in the A2A architecture.
"""

import asyncio
import time
from typing import Any, Dict, List, Optional, Set
import logging
from datetime import datetime, timedelta
import uuid

from .protocol.agent_communication import (
    AgentMessage, MessageType, AgentType,
    create_search_request, create_analysis_request, 
    create_response_request, create_categorization_request
)
from .specialized_agents.search_agent import HybridSearchAgent
from .specialized_agents.analysis_agent import QueryUnderstandingAgent
from .specialized_agents.response_agent import AnswerGenerationAgent
from .specialized_agents.categorization_agent import SourceLinkingAgent
from .nodes.query_understanding_node import run_node as understand_query


class AgentOrchestrator:
    """Orchestrates multiple agents in the A2A architecture."""
    
    def __init__(self):
        self.logger = logging.getLogger("orchestrator")
        self.agents: Dict[AgentType, Any] = {}
        self.message_routing: Dict[str, asyncio.Queue] = {}
        self.active_requests: Dict[str, Dict[str, Any]] = {}
        self.agent_status: Dict[AgentType, Dict[str, Any]] = {}
        self.is_running = False
        
        # Initialize agents
        self._initialize_agents()
    
    def _initialize_agents(self):
        """Initialize all specialized agents."""
        try:
            # Create agents
            self.agents[AgentType.HYBRID_SEARCH_AGENT] = HybridSearchAgent()
            self.agents[AgentType.QUERY_UNDERSTANDER] = QueryUnderstandingAgent()
            self.agents[AgentType.ANSWER_GENERATION_AGENT] = AnswerGenerationAgent()
            self.agents[AgentType.SOURCE_LINKING_AGENT] = SourceLinkingAgent()
            
            # Set up agent callbacks
            for agent in self.agents.values():
                agent.orchestrator_callback = self._route_message
            
            # Initialize message routing
            for agent_type in AgentType:
                self.message_routing[agent_type.value] = asyncio.Queue()
            
            self.logger.info("All agents initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Error initializing agents: {e}")
            raise
    
    async def start(self) -> None:
        """Start the orchestrator and all agents."""
        try:
            self.logger.info("Starting Agent Orchestrator")
            self.is_running = True
            
            # Start all agents
            for agent in self.agents.values():
                await agent.start()
            
            # Start message routing
            asyncio.create_task(self._message_routing_loop())
            
            # Start health monitoring
            asyncio.create_task(self._health_monitoring_loop())
            
            self.logger.info("Agent Orchestrator started successfully")
            
        except Exception as e:
            self.logger.error(f"Error starting orchestrator: {e}")
            raise
    
    async def stop(self) -> None:
        """Stop the orchestrator and all agents."""
        try:
            self.logger.info("Stopping Agent Orchestrator")
            self.is_running = False
            
            # Stop all agents
            for agent in self.agents.values():
                await agent.stop()
            
            self.logger.info("Agent Orchestrator stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping orchestrator: {e}")
    
    async def process_query(self, query: str) -> Dict[str, Any]:
        """Process a user query through the agent pipeline."""
        request_id = str(uuid.uuid4())
        start_time = time.time()
        
        try:
            self.logger.info(f"Processing query: {query[:100]}...")
            
            # Step 1: Query Understanding
            query_analysis = await understand_query({"query": query})
            self.logger.debug(f"Query analysis: {query_analysis}")
            
            # Step 2: Determine processing strategy
            processing_strategy = self._determine_processing_strategy(query_analysis)
            self.logger.debug(f"Processing strategy: {processing_strategy}")
            
            # Step 3: Execute processing strategy
            if processing_strategy == "parallel":
                result = await self._parallel_processing(query, query_analysis, request_id)
            elif processing_strategy == "sequential":
                result = await self._sequential_processing(query, query_analysis, request_id)
            else:  # hybrid
                result = await self._hybrid_processing(query, query_analysis, request_id)
            
            processing_time = time.time() - start_time
            result["processing_time"] = processing_time
            result["request_id"] = request_id
            
            self.logger.info(f"Query processed successfully in {processing_time:.2f}s")
            return result
            
        except Exception as e:
            self.logger.error(f"Error processing query: {e}")
            return {
                "answer": "I encountered an error while processing your query. Please try again.",
                "sources": [],
                "grouped_sources": {},
                "error": str(e),
                "processing_time": time.time() - start_time,
                "request_id": request_id
            }
        finally:
            # Clean up request tracking
            self.active_requests.pop(request_id, None)
    
    def _determine_processing_strategy(self, query_analysis: Dict[str, Any]) -> str:
        """Determine the best processing strategy based on query analysis."""
        is_broad_subject = query_analysis.get("is_broad_subject", False)
        expanded_keywords = query_analysis.get("expanded_keywords", [])
        
        if is_broad_subject and len(expanded_keywords) > 3:
            return "parallel"  # Use parallel processing for broad subjects
        elif len(expanded_keywords) <= 2:
            return "sequential"  # Use sequential for specific queries
        else:
            return "hybrid"  # Use hybrid approach
    
    async def _parallel_processing(
        self, 
        query: str, 
        query_analysis: Dict[str, Any], 
        request_id: str
    ) -> Dict[str, Any]:
        """Process query using parallel agent execution."""
        try:
            # Start all agents in parallel
            search_task = asyncio.create_task(
                self._execute_search_agent(query, query_analysis, request_id)
            )
            categorization_task = asyncio.create_task(
                self._execute_categorization_agent(query, query_analysis, request_id)
            )
            
            # Wait for both to complete
            search_result, categorization_result = await asyncio.gather(
                search_task, categorization_task, return_exceptions=True
            )
            
            # Handle any exceptions
            if isinstance(search_result, Exception):
                self.logger.error(f"Search agent error: {search_result}")
                search_result = {"results": [], "total_found": 0}
            
            if isinstance(categorization_result, Exception):
                self.logger.error(f"Categorization agent error: {categorization_result}")
                categorization_result = {"categories": {}}
            
            # Execute analysis and response agents
            analysis_task = asyncio.create_task(
                self._execute_analysis_agent(query, search_result.get("results", []), request_id)
            )
            response_task = asyncio.create_task(
                self._execute_response_agent(query, search_result.get("results", []), request_id)
            )
            
            analysis_result, response_result = await asyncio.gather(
                analysis_task, response_task, return_exceptions=True
            )
            
            # Handle exceptions
            if isinstance(analysis_result, Exception):
                self.logger.error(f"Analysis agent error: {analysis_result}")
                analysis_result = {"analysis": {}, "confidence": 0.1}
            
            if isinstance(response_result, Exception):
                self.logger.error(f"Response agent error: {response_result}")
                response_result = {
                    "answer": "I found relevant information but encountered an error generating a response.",
                    "sources": [],
                    "grouped_sources": {}
                }
            
            # Combine results
            return {
                "answer": response_result.get("answer", ""),
                "sources": response_result.get("sources", []),
                "grouped_sources": response_result.get("grouped_sources", {}),
                "analysis": analysis_result.get("analysis", {}),
                "confidence": analysis_result.get("confidence", 0.8),
                "search_metadata": {
                    "total_found": search_result.get("total_found", 0),
                    "sources_used": search_result.get("sources_used", [])
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error in parallel processing: {e}")
            raise
    
    async def _sequential_processing(
        self, 
        query: str, 
        query_analysis: Dict[str, Any], 
        request_id: str
    ) -> Dict[str, Any]:
        """Process query using sequential agent execution."""
        try:
            # Step 1: Search
            search_result = await self._execute_search_agent(query, query_analysis, request_id)
            
            # Step 2: Analysis
            analysis_result = await self._execute_analysis_agent(
                query, search_result.get("results", []), request_id
            )
            
            # Step 3: Categorization
            categorization_result = await self._execute_categorization_agent(
                query, query_analysis, request_id
            )
            
            # Step 4: Response generation
            response_result = await self._execute_response_agent(
                query, search_result.get("results", []), request_id, analysis_result
            )
            
            return {
                "answer": response_result.get("answer", ""),
                "sources": response_result.get("sources", []),
                "grouped_sources": response_result.get("grouped_sources", {}),
                "analysis": analysis_result.get("analysis", {}),
                "confidence": analysis_result.get("confidence", 0.8),
                "search_metadata": {
                    "total_found": search_result.get("total_found", 0),
                    "sources_used": search_result.get("sources_used", [])
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error in sequential processing: {e}")
            raise
    
    async def _hybrid_processing(
        self, 
        query: str, 
        query_analysis: Dict[str, Any], 
        request_id: str
    ) -> Dict[str, Any]:
        """Process query using hybrid approach (some parallel, some sequential)."""
        try:
            # Start search and categorization in parallel
            search_task = asyncio.create_task(
                self._execute_search_agent(query, query_analysis, request_id)
            )
            categorization_task = asyncio.create_task(
                self._execute_categorization_agent(query, query_analysis, request_id)
            )
            
            search_result, categorization_result = await asyncio.gather(
                search_task, categorization_task, return_exceptions=True
            )
            
            # Then do analysis and response sequentially
            analysis_result = await self._execute_analysis_agent(
                query, search_result.get("results", []), request_id
            )
            response_result = await self._execute_response_agent(
                query, search_result.get("results", []), request_id, analysis_result
            )
            
            return {
                "answer": response_result.get("answer", ""),
                "sources": response_result.get("sources", []),
                "grouped_sources": response_result.get("grouped_sources", {}),
                "analysis": analysis_result.get("analysis", {}),
                "confidence": analysis_result.get("confidence", 0.8),
                "search_metadata": {
                    "total_found": search_result.get("total_found", 0),
                    "sources_used": search_result.get("sources_used", [])
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error in hybrid processing: {e}")
            raise
    
    async def _execute_search_agent(
        self, 
        query: str, 
        query_analysis: Dict[str, Any], 
        request_id: str
    ) -> Dict[str, Any]:
        """Execute search agent."""
        try:
            search_agent = self.agents[AgentType.SEARCH_AGENT]
            
            search_request = create_search_request(
                query=query,
                normalized_query=query_analysis.get("normalized_query", query),
                expanded_keywords=query_analysis.get("expanded_keywords", []),
                is_broad_subject=query_analysis.get("is_broad_subject", False)
            )
            
            # Send message and wait for response
            response = await search_agent.send_message(
                recipient=AgentType.SEARCH_AGENT,
                message_type=MessageType.SEARCH_REQUEST,
                payload=search_request.payload,
                correlation_id=request_id
            )
            
            return response.payload
            
        except Exception as e:
            self.logger.error(f"Error executing search agent: {e}")
            return {"results": [], "total_found": 0, "sources_used": []}
    
    async def _execute_analysis_agent(
        self, 
        query: str, 
        documents: List[Dict[str, Any]], 
        request_id: str
    ) -> Dict[str, Any]:
        """Execute analysis agent."""
        try:
            analysis_agent = self.agents[AgentType.ANALYSIS_AGENT]
            
            analysis_request = create_analysis_request(
                documents=documents,
                query=query,
                analysis_type="content"
            )
            
            response = await analysis_agent.send_message(
                recipient=AgentType.ANALYSIS_AGENT,
                message_type=MessageType.ANALYSIS_REQUEST,
                payload=analysis_request.payload,
                correlation_id=request_id
            )
            
            return response.payload
            
        except Exception as e:
            self.logger.error(f"Error executing analysis agent: {e}")
            return {"analysis": {}, "confidence": 0.1}
    
    async def _execute_response_agent(
        self, 
        query: str, 
        documents: List[Dict[str, Any]], 
        request_id: str,
        analysis: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute response agent."""
        try:
            response_agent = self.agents[AgentType.RESPONSE_AGENT]
            
            response_request = create_response_request(
                query=query,
                search_results=documents,
                analysis=analysis
            )
            
            response = await response_agent.send_message(
                recipient=AgentType.RESPONSE_AGENT,
                message_type=MessageType.RESPONSE_REQUEST,
                payload=response_request.payload,
                correlation_id=request_id
            )
            
            return response.payload
            
        except Exception as e:
            self.logger.error(f"Error executing response agent: {e}")
            return {
                "answer": "I found relevant information but encountered an error generating a response.",
                "sources": [],
                "grouped_sources": {}
            }
    
    async def _execute_categorization_agent(
        self, 
        query: str, 
        query_analysis: Dict[str, Any], 
        request_id: str
    ) -> Dict[str, Any]:
        """Execute categorization agent."""
        try:
            categorization_agent = self.agents[AgentType.CATEGORIZATION_AGENT]
            
            # For now, we'll use empty documents since categorization happens after search
            categorization_request = create_categorization_request(
                documents=[],
                categorization_type="smart"
            )
            
            response = await categorization_agent.send_message(
                recipient=AgentType.CATEGORIZATION_AGENT,
                message_type=MessageType.CATEGORIZATION_REQUEST,
                payload=categorization_request.payload,
                correlation_id=request_id
            )
            
            return response.payload
            
        except Exception as e:
            self.logger.error(f"Error executing categorization agent: {e}")
            return {"categories": {}}
    
    async def _route_message(self, message: AgentMessage) -> None:
        """Route messages between agents."""
        try:
            # Add message to recipient's queue
            recipient_queue = self.message_routing.get(message.recipient.value)
            if recipient_queue:
                await recipient_queue.put(message)
            else:
                self.logger.warning(f"No queue found for recipient: {message.recipient.value}")
                
        except Exception as e:
            self.logger.error(f"Error routing message: {e}")
    
    async def _message_routing_loop(self) -> None:
        """Main message routing loop."""
        while self.is_running:
            try:
                # Process messages for each agent
                for agent_type, agent in self.agents.items():
                    queue = self.message_routing.get(agent_type.value)
                    if queue:
                        try:
                            message = await asyncio.wait_for(queue.get(), timeout=0.1)
                            await agent.receive_message(message)
                        except asyncio.TimeoutError:
                            continue
                        except Exception as e:
                            self.logger.error(f"Error processing message for {agent_type.value}: {e}")
                
                await asyncio.sleep(0.01)  # Small delay to prevent busy waiting
                
            except Exception as e:
                self.logger.error(f"Error in message routing loop: {e}")
                await asyncio.sleep(1)
    
    async def _health_monitoring_loop(self) -> None:
        """Monitor agent health and status."""
        while self.is_running:
            try:
                # Check agent status
                for agent_type, agent in self.agents.items():
                    status = agent.get_status()
                    self.agent_status[agent_type] = status
                    
                    # Log any issues
                    if not status.get("is_running", False):
                        self.logger.warning(f"Agent {agent_type.value} is not running")
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                self.logger.error(f"Error in health monitoring: {e}")
                await asyncio.sleep(10)
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status."""
        return {
            "orchestrator_running": self.is_running,
            "agent_count": len(self.agents),
            "agent_status": self.agent_status,
            "active_requests": len(self.active_requests),
            "timestamp": datetime.now().isoformat()
        }

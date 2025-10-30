"""
LangGraph + A2A Integration
==========================
Combines LangGraph state management with A2A agent architecture.
"""

from typing import Any, Dict, List, Optional, TypedDict
import asyncio
import logging
from datetime import datetime

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from ..specialized.query_understanding_agent import QueryUnderstandingAgent
from ..specialized.search_agent import SearchAgent
from ..specialized.answer_generation_agent import AnswerGenerationAgent
from ..specialized.source_linking_agent import SourceLinkingAgent
from .agent_communication import AgentType, MessageType, AgentMessage


class LangGraphA2AState(TypedDict, total=False):
    """Enhanced state for LangGraph + A2A integration."""
    # Query information
    query: str
    original_query: str
    normalized_query: str
    expanded_keywords: List[str]
    is_broad_subject: bool
    intent: str
    
    # Processing metadata
    processing_strategy: str  # "parallel", "sequential", "hybrid"
    request_id: str
    start_time: float
    
    # Agent results
    search_results: List[Dict[str, Any]]
    analysis_results: Dict[str, Any]
    categorization_results: Dict[str, Any]
    response_results: Dict[str, Any]
    
    # Final outputs
    answer: str
    sources: List[Dict[str, Any]]
    grouped_sources: Dict[str, Any]
    
    # Error handling
    errors: List[str]
    retry_count: int
    max_retries: int
    
    # Performance metrics
    processing_time: float
    agent_times: Dict[str, float]


class LangGraphA2AOrchestrator:
    """LangGraph-based orchestrator with A2A agent integration."""
    
    def __init__(self):
        self.logger = logging.getLogger("langgraph_a2a")
        self.memory = MemorySaver()
        self.graph = self._build_graph()
        self.is_running = False
        
        # Initialize all 4 agents
        self.query_understanding_agent = QueryUnderstandingAgent()
        self.search_agent = SearchAgent()
        self.response_agent = AnswerGenerationAgent()
        self.source_linking_agent = SourceLinkingAgent()
        
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph with A2A agent integration."""
        
        # Create the state graph
        builder = StateGraph(LangGraphA2AState)
        
        # Add nodes
        builder.add_node("query_understanding", self._query_understanding_node)
        builder.add_node("strategy_decision", self._strategy_decision_node)
        builder.add_node("parallel_processing", self._parallel_processing_node)
        builder.add_node("sequential_processing", self._sequential_processing_node)
        builder.add_node("hybrid_processing", self._hybrid_processing_node)
        builder.add_node("response_generation", self._response_generation_node)
        builder.add_node("error_handling", self._error_handling_node)
        builder.add_node("finalization", self._finalization_node)
        
        # Add edges
        builder.add_edge(START, "query_understanding")
        builder.add_edge("query_understanding", "strategy_decision")
        
        # Conditional routing based on strategy
        builder.add_conditional_edges(
            "strategy_decision",
            self._route_strategy,
            {
                "parallel": "parallel_processing",
                "sequential": "sequential_processing", 
                "hybrid": "hybrid_processing",
                "error": "error_handling"
            }
        )
        
        # All processing paths lead to response generation
        builder.add_edge("parallel_processing", "response_generation")
        builder.add_edge("sequential_processing", "response_generation")
        builder.add_edge("hybrid_processing", "response_generation")
        
        # Response generation to finalization
        builder.add_edge("response_generation", "finalization")
        builder.add_edge("finalization", END)
        
        # Error handling
        builder.add_edge("error_handling", "finalization")
        
        # Compile with memory
        return builder.compile(checkpointer=self.memory, interrupt_before=[], interrupt_after=[])
    
    async def start(self) -> None:
        """Start the LangGraph A2A orchestrator."""
        try:
            self.logger.info("Starting LangGraph A2A Orchestrator")
            
            self.is_running = True
            self.logger.info("LangGraph A2A Orchestrator started successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to start LangGraph A2A Orchestrator: {e}")
            raise
    
    async def stop(self) -> None:
        """Stop the LangGraph A2A orchestrator."""
        try:
            self.logger.info("Stopping LangGraph A2A Orchestrator")
            
            self.is_running = False
            self.logger.info("LangGraph A2A Orchestrator stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping LangGraph A2A Orchestrator: {e}")
    
    async def process_query(self, query: str, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process a query through the LangGraph A2A pipeline."""
        try:
            # Create initial state
            initial_state: LangGraphA2AState = {
                "query": query,
                "original_query": query,
                "request_id": f"req_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
                "start_time": asyncio.get_event_loop().time(),
                "retry_count": 0,
                "max_retries": 3,
                "errors": [],
                "agent_times": {}
            }
            
            # Process through LangGraph
            config = config or {"configurable": {"thread_id": initial_state["request_id"]}}
            final_state = await self.graph.ainvoke(initial_state, config=config)
            
            # Extract results
            return {
                "answer": final_state.get("answer", ""),
                "sources": final_state.get("sources", []),
                "grouped_sources": final_state.get("grouped_sources", {}),
                "processing_time": final_state.get("processing_time", 0.0),
                "request_id": final_state.get("request_id", ""),
                "agent_times": final_state.get("agent_times", {}),
                "errors": final_state.get("errors", [])
            }
            
        except Exception as e:
            self.logger.error(f"Error processing query: {e}")
            return {
                "answer": "I encountered an error while processing your query. Please try again.",
                "sources": [],
                "grouped_sources": {},
                "processing_time": 0.0,
                "request_id": "",
                "agent_times": {},
                "errors": [str(e)]
            }
    
    async def _query_understanding_node(self, state: LangGraphA2AState) -> LangGraphA2AState:
        """Query understanding node using A2A agent."""
        try:
            self.logger.debug("Processing query understanding")
            start_time = asyncio.get_event_loop().time()
            
            # Use the query understanding agent
            query_agent = self.query_understanding_agent
            
            # Process query understanding
            result = await query_agent.process_task({
                "query": state["query"],
                "context": {}
            })
            
            # Update state
            state.update({
                "normalized_query": result.get("normalized_query", state["query"]),
                "expanded_keywords": result.get("expanded_keywords", []),
                "is_broad_subject": result.get("is_broad_subject", False),
                "intent": result.get("intent", "qa")
            })
            
            # Record timing
            processing_time = asyncio.get_event_loop().time() - start_time
            state["agent_times"]["query_understanding"] = processing_time
            
            self.logger.debug(f"Query understanding completed in {processing_time:.2f}s")
            return state
            
        except Exception as e:
            self.logger.error(f"Error in query understanding: {e}")
            state["errors"].append(f"Query understanding error: {e}")
            return state
    
    async def _strategy_decision_node(self, state: LangGraphA2AState) -> LangGraphA2AState:
        """Strategy decision node."""
        try:
            self.logger.debug("Making strategy decision")
            
            # Determine processing strategy
            is_broad_subject = state.get("is_broad_subject", False)
            expanded_keywords = state.get("expanded_keywords", [])
            
            if is_broad_subject and len(expanded_keywords) > 3:
                strategy = "parallel"
            elif len(expanded_keywords) <= 2:
                strategy = "sequential"
            else:
                strategy = "hybrid"
            
            state["processing_strategy"] = strategy
            self.logger.debug(f"Selected strategy: {strategy}")
            
            return state
            
        except Exception as e:
            self.logger.error(f"Error in strategy decision: {e}")
            state["errors"].append(f"Strategy decision error: {e}")
            state["processing_strategy"] = "error"
            return state
    
    def _route_strategy(self, state: LangGraphA2AState) -> str:
        """Route based on processing strategy."""
        return state.get("processing_strategy", "sequential")
    
    async def _parallel_processing_node(self, state: LangGraphA2AState) -> LangGraphA2AState:
        """Parallel processing node using A2A agents."""
        try:
            self.logger.debug("Starting parallel processing")
            start_time = asyncio.get_event_loop().time()
            
            # Start search and categorization in parallel
            search_task = asyncio.create_task(
                self._execute_search_agent(state)
            )
            categorization_task = asyncio.create_task(
                self._execute_categorization_agent(state)
            )
            
            # Wait for both to complete
            search_results, categorization_results = await asyncio.gather(
                search_task, categorization_task, return_exceptions=True
            )
            
            # Handle results
            if isinstance(search_results, Exception):
                self.logger.error(f"Search agent error: {search_results}")
                state["errors"].append(f"Search error: {search_results}")
                search_results = {"results": [], "total_found": 0}
            
            if isinstance(categorization_results, Exception):
                self.logger.error(f"Categorization agent error: {categorization_results}")
                state["errors"].append(f"Categorization error: {categorization_results}")
                categorization_results = {"categories": {}}
            
            # Update state
            search_results_list = search_results.get("results", [])
            self.logger.info(f"Parallel processing - Storing {len(search_results_list)} search results in state")
            if search_results_list and len(search_results_list) > 0:
                self.logger.info(f"Parallel processing - First result keys: {list(search_results_list[0].keys()) if search_results_list[0] else 'None'}")
            
            state.update({
                "search_results": search_results_list,
                "categorization_results": categorization_results
            })
            
            # Record timing
            processing_time = asyncio.get_event_loop().time() - start_time
            state["agent_times"]["parallel_processing"] = processing_time
            
            self.logger.debug(f"Parallel processing completed in {processing_time:.2f}s")
            return state
            
        except Exception as e:
            self.logger.error(f"Error in parallel processing: {e}")
            state["errors"].append(f"Parallel processing error: {e}")
            return state
    
    async def _sequential_processing_node(self, state: LangGraphA2AState) -> LangGraphA2AState:
        """Sequential processing node using A2A agents."""
        try:
            self.logger.debug("Starting sequential processing")
            start_time = asyncio.get_event_loop().time()
            
            # Step 1: Search
            search_results = await self._execute_search_agent(state)
            state["search_results"] = search_results.get("results", [])
            
            # Step 2: Analysis
            analysis_results = await self._execute_analysis_agent(state)
            state["analysis_results"] = analysis_results
            
            # Step 3: Categorization
            categorization_results = await self._execute_categorization_agent(state)
            state["categorization_results"] = categorization_results
            
            # Record timing
            processing_time = asyncio.get_event_loop().time() - start_time
            state["agent_times"]["sequential_processing"] = processing_time
            
            self.logger.debug(f"Sequential processing completed in {processing_time:.2f}s")
            return state
            
        except Exception as e:
            self.logger.error(f"Error in sequential processing: {e}")
            state["errors"].append(f"Sequential processing error: {e}")
            return state
    
    async def _hybrid_processing_node(self, state: LangGraphA2AState) -> LangGraphA2AState:
        """Hybrid processing node using A2A agents."""
        try:
            self.logger.debug("Starting hybrid processing")
            start_time = asyncio.get_event_loop().time()
            
            # Start search and categorization in parallel
            search_task = asyncio.create_task(
                self._execute_search_agent(state)
            )
            categorization_task = asyncio.create_task(
                self._execute_categorization_agent(state)
            )
            
            search_results, categorization_results = await asyncio.gather(
                search_task, categorization_task, return_exceptions=True
            )
            
            # Handle results
            if isinstance(search_results, Exception):
                self.logger.error(f"Search agent error: {search_results}")
                state["errors"].append(f"Search error: {search_results}")
                search_results = {"results": [], "total_found": 0}
            
            if isinstance(categorization_results, Exception):
                self.logger.error(f"Categorization agent error: {categorization_results}")
                state["errors"].append(f"Categorization error: {categorization_results}")
                categorization_results = {"categories": {}}
            
            # Then do analysis sequentially
            analysis_results = await self._execute_analysis_agent(state)
            
            # Update state
            state.update({
                "search_results": search_results.get("results", []),
                "analysis_results": analysis_results,
                "categorization_results": categorization_results
            })
            
            # Record timing
            processing_time = asyncio.get_event_loop().time() - start_time
            state["agent_times"]["hybrid_processing"] = processing_time
            
            self.logger.debug(f"Hybrid processing completed in {processing_time:.2f}s")
            return state
            
        except Exception as e:
            self.logger.error(f"Error in hybrid processing: {e}")
            state["errors"].append(f"Hybrid processing error: {e}")
            return state
    
    async def _response_generation_node(self, state: LangGraphA2AState) -> LangGraphA2AState:
        """Response generation node using A2A agent."""
        try:
            self.logger.debug("Generating response")
            start_time = asyncio.get_event_loop().time()
            
            # Debug logging
            search_results = state.get("search_results", [])
            self.logger.info(f"Response generation - Search results count: {len(search_results)}")
            if search_results and len(search_results) > 0:
                self.logger.info(f"Response generation - First result keys: {list(search_results[0].keys()) if search_results[0] else 'None'}")
            
            # Use response generation agent
            # Execute response agent directly
            response_agent = self.response_agent
            
            # Prepare request
            request_data = {
                "query": state["query"],
                "normalized_query": state.get("normalized_query", state["query"]),
                "expanded_keywords": state.get("expanded_keywords", []),
                "is_broad_subject": state.get("is_broad_subject", False),
                "search_results": state.get("search_results", [])
            }
            
            # Generate response
            result = await response_agent.process_task(request_data)
            
            # Update state
            state.update({
                "answer": result.get("answer", ""),
                "sources": result.get("sources", []),
                "grouped_sources": result.get("grouped_sources", {}),
                "response_results": result
            })
            
            # Record timing
            processing_time = asyncio.get_event_loop().time() - start_time
            state["agent_times"]["response_generation"] = processing_time
            
            self.logger.debug(f"Response generation completed in {processing_time:.2f}s")
            return state
            
        except Exception as e:
            self.logger.error(f"Error in response generation: {e}")
            state["errors"].append(f"Response generation error: {e}")
            return state
    
    async def _error_handling_node(self, state: LangGraphA2AState) -> LangGraphA2AState:
        """Error handling node."""
        try:
            self.logger.debug("Handling errors")
            
            # Check if we should retry
            retry_count = state.get("retry_count", 0)
            max_retries = state.get("max_retries", 3)
            
            if retry_count < max_retries:
                # Retry with exponential backoff
                retry_count += 1
                state["retry_count"] = retry_count
                
                # Wait before retry
                wait_time = 2 ** retry_count
                await asyncio.sleep(wait_time)
                
                # Reset errors and try again
                state["errors"] = []
                state["processing_strategy"] = "sequential"  # Use safe strategy
                
                self.logger.info(f"Retrying request (attempt {retry_count}/{max_retries})")
                return state
            else:
                # Max retries reached, return error response
                state["answer"] = "I encountered multiple errors while processing your query. Please try again later."
                state["sources"] = []
                state["grouped_sources"] = {}
                
                self.logger.error(f"Max retries reached. Errors: {state.get('errors', [])}")
                return state
                
        except Exception as e:
            self.logger.error(f"Error in error handling: {e}")
            state["answer"] = "I encountered an error while processing your query. Please try again."
            state["sources"] = []
            state["grouped_sources"] = {}
            return state
    
    async def _finalization_node(self, state: LangGraphA2AState) -> LangGraphA2AState:
        """Finalization node."""
        try:
            self.logger.debug("Finalizing results")
            
            # Calculate total processing time
            start_time = state.get("start_time", asyncio.get_event_loop().time())
            total_time = asyncio.get_event_loop().time() - start_time
            state["processing_time"] = total_time
            
            # Ensure we have required fields
            if not state.get("answer"):
                state["answer"] = "I couldn't find relevant information for your query."
            
            if not state.get("sources"):
                state["sources"] = []
            
            if not state.get("grouped_sources"):
                state["grouped_sources"] = {}
            
            self.logger.info(f"Query processed in {total_time:.2f}s")
            return state
            
        except Exception as e:
            self.logger.error(f"Error in finalization: {e}")
            return state
    
    async def _execute_search_agent(self, state: LangGraphA2AState) -> Dict[str, Any]:
        """Execute search agent."""
        try:
            # Execute search agent directly
            search_agent = self.search_agent
            
            request_data = {
                "query": state["query"],
                "normalized_query": state.get("normalized_query", state["query"]),
                "expanded_keywords": state.get("expanded_keywords", []),
                "is_broad_subject": state.get("is_broad_subject", False)
            }
            
            return await search_agent.process_task(request_data)
            
        except Exception as e:
            self.logger.error(f"Error executing search agent: {e}")
            return {"results": [], "total_found": 0}
    
    async def _execute_analysis_agent(self, state: LangGraphA2AState) -> Dict[str, Any]:
        """Execute analysis agent."""
        try:
            # Execute analysis agent directly
            analysis_agent = self.source_linking_agent  # Use source linking for analysis
            
            request_data = {
                "documents": state.get("search_results", []),
                "query": state["query"],
                "context": {
                    "normalized_query": state.get("normalized_query", state["query"]),
                    "expanded_keywords": state.get("expanded_keywords", []),
                    "is_broad_subject": state.get("is_broad_subject", False),
                    "intent": state.get("intent", "qa"),
                    "confidence": state.get("confidence", 0.8),
                    "processing_time": state.get("agent_times", {}).get("query_understanding", 0.0)
                }
            }
            
            return await analysis_agent.process_task(request_data)
            
        except Exception as e:
            self.logger.error(f"Error executing analysis agent: {e}")
            return {"analysis": {}, "confidence": 0.1}
    
    async def _execute_categorization_agent(self, state: LangGraphA2AState) -> Dict[str, Any]:
        """Execute categorization agent."""
        try:
            # Execute categorization agent directly
            categorization_agent = self.source_linking_agent  # Use source linking for categorization
            
            request_data = {
                "documents": state.get("search_results", []),
                "query": state["query"],
                "context": {
                    "normalized_query": state.get("normalized_query", state["query"]),
                    "expanded_keywords": state.get("expanded_keywords", []),
                    "is_broad_subject": state.get("is_broad_subject", False),
                    "intent": state.get("intent", "qa"),
                    "confidence": state.get("confidence", 0.8),
                    "processing_time": state.get("agent_times", {}).get("query_understanding", 0.0)
                }
            }
            
            return await categorization_agent.process_task(request_data)
            
        except Exception as e:
            self.logger.error(f"Error executing categorization agent: {e}")
            return {"categories": {}}
    
    def get_status(self) -> Dict[str, Any]:
        """Get system status."""
        return {
            "langgraph_a2a_running": self.is_running,
            "agent_orchestrator_status": {
                "agent_count": 4,
                "agent_status": {
                    "QueryUnderstandingAgent": "running",
                    "SearchAgent": "running", 
                    "AnswerGenerationAgent": "running",
                    "SourceLinkingAgent": "running"
                },
                "active_requests": 0,
                "timestamp": datetime.now().isoformat()
            },
            "memory_checkpoints": len(self.memory.storage) if hasattr(self.memory, 'storage') else 0
        }

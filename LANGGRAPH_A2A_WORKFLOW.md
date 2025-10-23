# LangGraph + A2A Architecture Workflow

## Complete Step-by-Step Process: LangGraph and A2A Integration

This document traces exactly how LangGraph and Agent-to-Agent (A2A) communication is used throughout the application, including which files and code sections implement each component.

---

## **Architecture Overview**

### **LangGraph Components**
- **State Management**: `LangGraphA2AState` with persistent memory
- **Graph Nodes**: Query understanding, strategy decision, processing, response generation
- **Conditional Routing**: Based on processing strategy
- **Memory Checkpointing**: Thread-based state persistence

### **A2A Components**
- **Agent Communication Protocol**: Message routing between specialized agents
- **Agent Types**: Search, Analysis, Response, Categorization agents
- **Message Types**: Requests, responses, heartbeats
- **Orchestrator**: Coordinates agent interactions

---

## **Step 1: LangGraph Graph Construction**

### **File**: `apps/api/api/agents/langgraph_a2a.py`
### **Code Section**: Lines 65-110

```python
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
    
    # Compile with memory
    return builder.compile(checkpointer=self.memory, interrupt_before=[], interrupt_after=[])
```

**LangGraph Features Used**:
- **StateGraph**: Main graph structure
- **Nodes**: Individual processing steps
- **Edges**: Sequential flow between nodes
- **Conditional Edges**: Dynamic routing based on state
- **Memory Checkpointer**: Persistent state across requests

---

## **Step 2: LangGraph State Definition**

### **File**: `apps/api/api/agents/langgraph_a2a.py`
### **Code Section**: Lines 19-53

```python
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
```

**LangGraph State Features**:
- **TypedDict**: Type-safe state definition
- **total=False**: Optional fields
- **Persistent State**: Maintained across graph execution
- **Rich Metadata**: Query analysis, timing, errors

---

## **Step 3: A2A Agent Orchestrator Initialization**

### **File**: `apps/api/api/agents/orchestrator.py`
### **Code Section**: Lines 26-61

```python
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
```

**A2A Features Used**:
- **Agent Registry**: Dictionary of agent types to instances
- **Message Routing**: Queue-based communication
- **Callback System**: Agents can send messages back to orchestrator
- **Agent Status Tracking**: Health monitoring

---

## **Step 4: A2A Message Protocol**

### **File**: `apps/api/api/agents/protocol/agent_communication.py`
### **Code Section**: Lines 1-50

```python
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from datetime import datetime

class AgentType(Enum):
    """Types of agents in the system."""
    HYBRID_SEARCH_AGENT = "hybrid_search_agent"
    QUERY_UNDERSTANDER = "query_understander"
    ANSWER_GENERATION_AGENT = "answer_generation_agent"
    SOURCE_LINKING_AGENT = "source_linking_agent"

class MessageType(Enum):
    """Types of messages between agents."""
    SEARCH_REQUEST = "search_request"
    ANALYSIS_REQUEST = "analysis_request"
    RESPONSE_REQUEST = "response_request"
    CATEGORIZATION_REQUEST = "categorization_request"
    HEARTBEAT = "heartbeat"

class AgentMessage(BaseModel):
    """Message envelope for A2A communication."""
    message_id: str
    sender: AgentType
    recipient: AgentType
    message_type: MessageType
    payload: Dict[str, Any]
    correlation_id: Optional[str] = None
    timestamp: datetime = datetime.now()
```

**A2A Protocol Features**:
- **Standardized Messages**: Consistent message format
- **Agent Types**: Enum-based agent identification
- **Message Types**: Categorized message types
- **Correlation IDs**: Request tracking
- **Timestamps**: Message ordering

---

## **Step 5: LangGraph Query Understanding Node**

### **File**: `apps/api/api/agents/langgraph_a2a.py`
### **Code Section**: Lines 183-215

```python
async def _query_understanding_node(self, state: LangGraphA2AState) -> LangGraphA2AState:
    """Query understanding node using A2A agent."""
    try:
        self.logger.debug("Processing query understanding")
        start_time = asyncio.get_event_loop().time()
        
        # Use the query understanding agent
        query_agent = self.agent_orchestrator.agents[AgentType.QUERY_UNDERSTANDER]
        
        # Process query understanding
        result = await query_agent.process_task({
            "query": state["query"]
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
        
        return state
```

**LangGraph + A2A Integration**:
- **Node Function**: LangGraph node that processes state
- **A2A Agent Call**: Direct call to specialized agent
- **State Update**: LangGraph state modification
- **Timing Tracking**: Performance metrics

---

## **Step 6: LangGraph Conditional Routing**

### **File**: `apps/api/api/agents/langgraph_a2a.py`
### **Code Section**: Lines 217-246

```python
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

def _route_strategy(self, state: LangGraphA2AState) -> str:
    """Route based on processing strategy."""
    return state.get("processing_strategy", "sequential")
```

**LangGraph Routing Features**:
- **Conditional Edges**: Dynamic path selection
- **State-Based Routing**: Decision based on state content
- **Multiple Paths**: Parallel, sequential, hybrid processing
- **Fallback Routing**: Default to sequential

---

## **Step 7: LangGraph Parallel Processing with A2A**

### **File**: `apps/api/api/agents/langgraph_a2a.py`
### **Code Section**: Lines 248-294

```python
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
        
        # Update state
        state.update({
            "search_results": search_results.get("results", []),
            "categorization_results": categorization_results
        })
        
        # Record timing
        processing_time = asyncio.get_event_loop().time() - start_time
        state["agent_times"]["parallel_processing"] = processing_time
        
        return state
```

**LangGraph + A2A Parallel Features**:
- **Async Tasks**: Concurrent agent execution
- **Error Handling**: Exception management
- **State Updates**: Parallel result integration
- **Timing Metrics**: Performance tracking

---

## **Step 8: A2A Agent Execution**

### **File**: `apps/api/api/agents/langgraph_a2a.py`
### **Code Section**: Lines 494-510

```python
async def _execute_search_agent(self, state: LangGraphA2AState) -> Dict[str, Any]:
    """Execute search agent."""
    try:
        search_agent = self.agent_orchestrator.agents[AgentType.HYBRID_SEARCH_AGENT]
        
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
```

**A2A Agent Execution**:
- **Agent Lookup**: Get agent by type from orchestrator
- **Task Processing**: Direct method call to agent
- **Data Preparation**: State to task data conversion
- **Error Handling**: Graceful failure management

---

## **Step 9: A2A Base Agent Implementation**

### **File**: `apps/api/api/agents/base_agent.py`
### **Code Section**: Lines 1-50

```python
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Callable
import asyncio
import logging
from datetime import datetime

from .protocol.agent_communication import AgentMessage, MessageType, AgentType

class BaseAgent(ABC):
    """Base class for all A2A agents."""
    
    def __init__(
        self,
        agent_type: AgentType,
        name: str,
        max_concurrent_tasks: int = 3,
        timeout_seconds: int = 30
    ):
        self.agent_type = agent_type
        self.name = name
        self.max_concurrent_tasks = max_concurrent_tasks
        self.timeout_seconds = timeout_seconds
        self.logger = logging.getLogger(f"agent.{name}")
        
        # Message handling
        self.message_handlers: Dict[MessageType, Callable] = {}
        self.is_running = False
        
        # Task management
        self.active_tasks: Dict[str, asyncio.Task] = {}
        self.task_semaphore = asyncio.Semaphore(max_concurrent_tasks)
    
    @abstractmethod
    async def process_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a task. Must be implemented by subclasses."""
        pass
    
    def register_handler(self, message_type: MessageType, handler: Callable):
        """Register a message handler."""
        self.message_handlers[message_type] = handler
    
    async def receive_message(self, message: AgentMessage):
        """Receive and process a message."""
        handler = self.message_handlers.get(message.message_type)
        if handler:
            await handler(message)
```

**A2A Base Agent Features**:
- **Abstract Base Class**: Common agent interface
- **Message Handling**: Handler registration and processing
- **Task Management**: Concurrent task limits
- **Logging**: Structured logging per agent

---

## **Step 10: A2A Message Routing**

### **File**: `apps/api/api/agents/orchestrator.py`
### **Code Section**: Lines 438-471

```python
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
```

**A2A Message Routing Features**:
- **Queue-Based Routing**: Async queues for each agent
- **Message Loop**: Continuous message processing
- **Error Handling**: Graceful error management
- **Timeout Handling**: Non-blocking message retrieval

---

## **Step 11: LangGraph Memory Management**

### **File**: `apps/api/api/agents/langgraph_a2a.py`
### **Code Section**: Lines 58-64

```python
def __init__(self):
    self.logger = logging.getLogger("langgraph_a2a")
    self.agent_orchestrator = AgentOrchestrator()
    self.memory = MemorySaver()
    self.graph = self._build_graph()
    self.is_running = False
```

### **File**: `apps/api/api/agents/langgraph_a2a.py`
### **Code Section**: Lines 156-158

```python
# Process through LangGraph
config = config or {"configurable": {"thread_id": initial_state["request_id"]}}
final_state = await self.graph.ainvoke(initial_state, config=config)
```

**LangGraph Memory Features**:
- **MemorySaver**: Persistent state storage
- **Thread IDs**: Request-based state isolation
- **Configurable**: Memory configuration options
- **State Persistence**: Cross-request state maintenance

---

## **Step 12: A2A Agent Health Monitoring**

### **File**: `apps/api/api/agents/orchestrator.py`
### **Code Section**: Lines 473-490

```python
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
```

**A2A Health Monitoring Features**:
- **Status Checking**: Regular agent health checks
- **Status Reporting**: System-wide status information
- **Error Detection**: Agent failure detection
- **Monitoring Loop**: Continuous health monitoring

---

## **Step 13: LangGraph Error Handling**

### **File**: `apps/api/api/agents/langgraph_a2a.py`
### **Code Section**: Lines 427-465

```python
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
```

**LangGraph Error Handling Features**:
- **Retry Logic**: Exponential backoff retry
- **State Recovery**: Error state management
- **Fallback Strategy**: Safe processing mode
- **Error Logging**: Comprehensive error tracking

---

## **Step 14: LangGraph Finalization**

### **File**: `apps/api/api/agents/langgraph_a2a.py`
### **Code Section**: Lines 467-492

```python
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
```

**LangGraph Finalization Features**:
- **Time Calculation**: Total processing time
- **Data Validation**: Required field checking
- **State Cleanup**: Final state preparation
- **Logging**: Completion metrics

---

## **Summary of LangGraph + A2A Integration**

### **LangGraph Components Used**

| Component | File | Purpose |
|-----------|------|---------|
| **StateGraph** | `langgraph_a2a.py:69` | Main graph structure |
| **Nodes** | `langgraph_a2a.py:72-78` | Processing steps |
| **Edges** | `langgraph_a2a.py:82-84` | Sequential flow |
| **Conditional Edges** | `langgraph_a2a.py:86-95` | Dynamic routing |
| **Memory Checkpointer** | `langgraph_a2a.py:61` | State persistence |
| **State Management** | `langgraph_a2a.py:19-53` | TypedDict state |

### **A2A Components Used**

| Component | File | Purpose |
|-----------|------|---------|
| **Agent Orchestrator** | `orchestrator.py:26` | Agent coordination |
| **Message Protocol** | `agent_communication.py` | Communication format |
| **Base Agent** | `base_agent.py` | Agent interface |
| **Message Routing** | `orchestrator.py:438-471` | Inter-agent communication |
| **Health Monitoring** | `orchestrator.py:473-490` | Agent status tracking |
| **Specialized Agents** | `specialized_agents/` | Task-specific agents |

### **Integration Points**

1. **LangGraph Nodes → A2A Agents**: Each LangGraph node calls A2A agents
2. **A2A State → LangGraph State**: Agent results update LangGraph state
3. **LangGraph Memory → A2A Requests**: Thread IDs for request tracking
4. **A2A Errors → LangGraph Errors**: Agent errors flow to LangGraph error handling
5. **LangGraph Timing → A2A Metrics**: Performance tracking across both systems

### **Key Benefits**

- **LangGraph**: State management, conditional routing, memory persistence
- **A2A**: Agent specialization, message routing, health monitoring
- **Combined**: Robust, scalable, maintainable agent architecture

This architecture provides the best of both worlds: LangGraph's powerful state management and conditional routing with A2A's flexible agent communication and specialization!

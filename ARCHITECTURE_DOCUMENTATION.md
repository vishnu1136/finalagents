# IKB Navigator Architecture Documentation

## Overview

The IKB Navigator is built using a **hybrid architecture** that combines **LangGraph** (for state management and workflow orchestration) with **Agent-to-Agent (A2A)** communication patterns. This creates a robust, scalable system for intelligent document search and knowledge retrieval.

## Architecture Components

### 1. LangGraph Architecture (State Management & Workflow)

LangGraph provides the **workflow orchestration** and **state management** layer. It defines the processing pipeline and manages the flow of data between different processing stages.

#### Key Components:

**State Definition:**
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

**Graph Construction:**
```python
def _build_graph(self) -> StateGraph:
    """Build the LangGraph with A2A agent integration."""
    
    # Create the state graph
    builder = StateGraph(LangGraphA2AState)
    
    # Add nodes (processing steps)
    builder.add_node("query_understanding", self._query_understanding_node)
    builder.add_node("strategy_decision", self._strategy_decision_node)
    builder.add_node("parallel_processing", self._parallel_processing_node)
    builder.add_node("sequential_processing", self._sequential_processing_node)
    builder.add_node("hybrid_processing", self._hybrid_processing_node)
    builder.add_node("response_generation", self._response_generation_node)
    builder.add_node("error_handling", self._error_handling_node)
    builder.add_node("finalization", self._finalization_node)
    
    # Add edges (workflow connections)
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
```

**Processing Flow:**
```
START → Query Understanding → Strategy Decision → [Parallel/Sequential/Hybrid Processing] → Response Generation → Finalization → END
                                                                                    ↓
                                                                              Error Handling
```

### 2. Agent-to-Agent (A2A) Architecture (Communication & Coordination)

The A2A architecture provides **decentralized communication** between specialized agents. Each agent is responsible for a specific domain and communicates through standardized messages.

#### Key Components:

**Message Protocol:**
```python
class MessageType(Enum):
    """Types of messages that can be sent between agents."""
    SEARCH_REQUEST = "search_request"
    SEARCH_RESPONSE = "search_response"
    ANALYSIS_REQUEST = "analysis_request"
    ANALYSIS_RESPONSE = "analysis_response"
    RESPONSE_REQUEST = "response_request"
    RESPONSE_RESPONSE = "response_response"
    CATEGORIZATION_REQUEST = "categorization_request"
    CATEGORIZATION_RESPONSE = "categorization_response"
    ERROR = "error"
    HEARTBEAT = "heartbeat"
    COORDINATION = "coordination"

class AgentType(Enum):
    """Types of agents in the system."""
    QUERY_UNDERSTANDER = "query_understander"
    HYBRID_SEARCH_AGENT = "hybrid_search_agent"
    ANSWER_GENERATION_AGENT = "answer_generation_agent"
    SOURCE_LINKING_AGENT = "source_linking_agent"
    ORCHESTRATOR = "orchestrator"

@dataclass
class AgentMessage:
    """Standard message format for agent-to-agent communication."""
    id: str
    sender: AgentType
    recipient: AgentType
    message_type: MessageType
    payload: Dict[str, Any]
    timestamp: datetime
    correlation_id: Optional[str] = None
    priority: int = 1  # 1=low, 5=high
    retry_count: int = 0
```

**Base Agent Class:**
```python
class BaseAgent(ABC):
    """Base class for all agents in the A2A system."""
    
    def __init__(
        self,
        agent_type: AgentType,
        name: str,
        max_concurrent_tasks: int = 10,
        timeout_seconds: int = 30
    ):
        self.agent_type = agent_type
        self.name = name
        self.max_concurrent_tasks = max_concurrent_tasks
        self.timeout_seconds = timeout_seconds
        self.logger = logging.getLogger(f"agent.{name}")
        self.is_running = False
        self.message_handlers: Dict[MessageType, Callable] = {}
        self.pending_messages: Dict[str, asyncio.Future] = {}
        self.message_queue: asyncio.Queue = asyncio.Queue()
        self.task_semaphore = asyncio.Semaphore(max_concurrent_tasks)
    
    async def start(self) -> None:
        """Start the agent."""
        self.logger.info(f"Starting agent {self.name}")
        self.is_running = True
        
        # Start message processing loop
        asyncio.create_task(self._message_processing_loop())
        
        # Start heartbeat
        asyncio.create_task(self._heartbeat_loop())
    
    def register_handler(self, message_type: MessageType, handler: Callable):
        """Register a message handler."""
        self.message_handlers[message_type] = handler
    
    async def send_message(self, recipient: AgentType, message_type: MessageType, payload: Dict[str, Any]) -> AgentMessage:
        """Send a message to another agent."""
        message = AgentMessage(
            id=str(uuid.uuid4()),
            sender=self.agent_type,
            recipient=recipient,
            message_type=message_type,
            payload=payload,
            timestamp=datetime.now()
        )
        
        # Send through orchestrator
        await self._send_message_to_orchestrator(message)
        return message
```

**Agent Orchestrator:**
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
```

### 3. Specialized Agents

Each agent specializes in a specific domain and implements the BaseAgent interface:

#### HybridSearchAgent
- **Purpose**: Document search and retrieval
- **Capabilities**: 
  - Database search with vector embeddings
  - Google Drive integration
  - Hybrid search (combines multiple sources)
  - Real-time file processing

```python
class HybridSearchAgent(BaseAgent):
    """Agent specialized in hybrid document search and retrieval."""
    
    def __init__(self):
        super().__init__(
            agent_type=AgentType.HYBRID_SEARCH_AGENT,
            name="HybridSearchAgent",
            max_concurrent_tasks=5,
            timeout_seconds=60
        )
        
        # Initialize search components
        self.gdrive_client = GDriveMCPClient()
        self.db_client = get_supabase_client()
        
        # Register message handlers
        self.register_handler(MessageType.SEARCH_REQUEST, self._handle_search_request)
        self.register_handler(MessageType.HEARTBEAT, self._handle_heartbeat)
```

#### QueryUnderstandingAgent
- **Purpose**: Query analysis and understanding
- **Capabilities**:
  - Query normalization
  - Intent detection
  - Keyword expansion
  - Broad subject detection

#### AnswerGenerationAgent
- **Purpose**: Response generation
- **Capabilities**:
  - AI-powered answer generation
  - Source linking with URLs
  - Multiple response types (brief, detailed, comprehensive)
  - Context management

#### SourceLinkingAgent
- **Purpose**: Document categorization and source linking
- **Capabilities**:
  - Document categorization
  - Source grouping
  - URL formatting
  - Metadata management

## How It All Works Together

### 1. Request Processing Flow

```
User Query → FastAPI → LangGraph A2A Orchestrator → Agent Orchestrator → Specialized Agents
```

### 2. Detailed Processing Steps

1. **Query Understanding** (LangGraph Node)
   - Normalizes the query
   - Detects intent and broad subjects
   - Expands keywords
   - Updates state with query metadata

2. **Strategy Decision** (LangGraph Node)
   - Analyzes query complexity
   - Determines processing strategy (parallel/sequential/hybrid)
   - Routes to appropriate processing path

3. **Parallel Processing** (LangGraph Node + A2A Agents)
   - Sends search requests to HybridSearchAgent
   - Sends analysis requests to QueryUnderstandingAgent
   - Processes multiple tasks concurrently
   - Aggregates results in state

4. **Response Generation** (LangGraph Node + A2A Agents)
   - Sends response request to AnswerGenerationAgent
   - Generates AI-powered answers with source links
   - Formats URLs as clickable markdown links
   - Manages context length to avoid token limits

5. **Finalization** (LangGraph Node)
   - Compiles final response
   - Calculates performance metrics
   - Logs query and results to database
   - Returns structured response

### 3. Communication Patterns

**Synchronous Communication:**
- Direct method calls within LangGraph nodes
- Immediate response handling

**Asynchronous Communication:**
- Message queues between agents
- Non-blocking operations
- Concurrent processing

**Error Handling:**
- Retry mechanisms
- Fallback responses
- Graceful degradation

## Key Benefits

### LangGraph Benefits:
- **State Management**: Centralized state tracking across the entire workflow
- **Workflow Orchestration**: Clear, visual workflow definition
- **Memory & Checkpointing**: Persistent state across requests
- **Conditional Routing**: Dynamic workflow paths based on conditions
- **Error Recovery**: Built-in error handling and retry mechanisms

### A2A Benefits:
- **Modularity**: Each agent has a single responsibility
- **Scalability**: Agents can be scaled independently
- **Fault Tolerance**: Failure of one agent doesn't crash the system
- **Extensibility**: Easy to add new agents or modify existing ones
- **Concurrency**: Multiple agents can work in parallel

### Combined Benefits:
- **Best of Both Worlds**: LangGraph's workflow management + A2A's modularity
- **Robust Processing**: Multiple layers of error handling and recovery
- **Performance**: Parallel processing where possible, sequential where needed
- **Maintainability**: Clear separation of concerns and responsibilities

## Data Flow Example

```
1. User Query: "What is BRD?"
   ↓
2. LangGraph State: {query: "What is BRD?", original_query: "What is BRD?", ...}
   ↓
3. Query Understanding Node: {normalized_query: "brd", is_broad_subject: true, ...}
   ↓
4. Strategy Decision Node: {processing_strategy: "parallel", ...}
   ↓
5. Parallel Processing Node:
   - Send SEARCH_REQUEST to HybridSearchAgent
   - Send ANALYSIS_REQUEST to QueryUnderstandingAgent
   - Wait for responses
   ↓
6. Response Generation Node:
   - Send RESPONSE_REQUEST to AnswerGenerationAgent
   - Generate answer with clickable links
   ↓
7. Finalization Node:
   - Compile final response
   - Log to database
   - Return to user
```

This architecture provides a robust, scalable, and maintainable system for intelligent document search and knowledge retrieval.

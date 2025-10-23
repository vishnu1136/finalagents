# IKB Navigator Architecture Diagram

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                USER INTERFACE                                   │
│                              (React Frontend)                                  │
└─────────────────────┬───────────────────────────────────────────────────────────┘
                      │ HTTP Requests
                      ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              FASTAPI SERVER                                     │
│                         (main_langgraph_a2a.py)                                │
└─────────────────────┬───────────────────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        LANGGRAPH A2A ORCHESTRATOR                               │
│                           (langgraph_a2a.py)                                    │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                        LANGGRAPH WORKFLOW                               │   │
│  │                                                                         │   │
│  │  START → Query Understanding → Strategy Decision → Processing →        │   │
│  │              ↓                    ↓              ↓                     │   │
│  │         [Normalize]         [Parallel/Seq]   [Response Gen]            │   │
│  │         [Detect Intent]      [Hybrid]         [Finalization]            │   │
│  │         [Expand Keywords]    ↓              ↓                          │   │
│  │                              END ←──────────┘                          │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────┬───────────────────────────────────────────────────────────┘
                      │ Agent Communication
                      ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           AGENT ORCHESTRATOR                                    │
│                            (orchestrator.py)                                    │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                        A2A COMMUNICATION                                │   │
│  │                                                                         │   │
│  │  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐ │   │
│  │  │   Query     │    │   Hybrid    │    │   Answer    │    │   Source    │ │   │
│  │  │Understander │◄──►│   Search    │◄──►│ Generation │◄──►│   Linking   │ │   │
│  │  │   Agent     │    │   Agent     │    │   Agent     │    │   Agent     │ │   │
│  │  └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘ │   │
│  │                                                                         │   │
│  │  Message Types: SEARCH_REQUEST, ANALYSIS_REQUEST, RESPONSE_REQUEST     │   │
│  │  Communication: Async queues, Message routing, Error handling          │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────┬───────────────────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              DATA LAYER                                         │
│                                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐            │
│  │   SUPABASE      │    │   GOOGLE DRIVE  │    │   OPENAI API     │            │
│  │   DATABASE      │    │   INTEGRATION   │    │   EMBEDDINGS     │            │
│  │                 │    │                 │    │                 │            │
│  │ • Documents     │    │ • File Search   │    │ • Text Embedding│            │
│  │ • Chunks        │    │ • Content Fetch │    │ • Answer Gen     │            │
│  │ • Embeddings    │    │ • Real-time     │    │ • Query Analysis│            │
│  │ • Queries       │    │   Processing    │    │                 │            │
│  │ • Query Results │    │                 │    │                 │            │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘            │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Detailed Component Interaction

### 1. LangGraph Workflow (State Management)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              LANGGRAPH STATE                                   │
│                                                                                 │
│  State: {                                                                       │
│    query: "What is BRD?",                                                      │
│    normalized_query: "brd",                                                    │
│    is_broad_subject: true,                                                      │
│    processing_strategy: "parallel",                                             │
│    search_results: [...],                                                        │
│    answer: "I found 100 relevant documents...",                                 │
│    sources: [...],                                                              │
│    grouped_sources: {...},                                                      │
│    errors: [],                                                                  │
│    processing_time: 159.98                                                      │
│  }                                                                              │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 2. Agent Communication Flow

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           A2A MESSAGE FLOW                                     │
│                                                                                 │
│  Orchestrator → HybridSearchAgent:                                             │
│  {                                                                              │
│    "message_type": "SEARCH_REQUEST",                                           │
│    "payload": {                                                                 │
│      "query": "brd",                                                            │
│      "config": {}                                                               │
│    }                                                                            │
│  }                                                                              │
│                                                                                 │
│  HybridSearchAgent → Orchestrator:                                             │
│  {                                                                              │
│    "message_type": "SEARCH_RESPONSE",                                          │
│    "payload": {                                                                 │
│      "results": [                                                               │
│        {                                                                        │
│          "title": "BRD Analysis & Issue Generation Feature",                   │
│          "url": "https://drive.google.com/...",                                │
│          "snippet": "This feature will be powered by...",                      │
│          "score": 0.358                                                        │
│        }                                                                        │
│      ]                                                                          │
│    }                                                                            │
│  }                                                                              │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 3. Processing Pipeline

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           PROCESSING PIPELINE                                   │
│                                                                                 │
│  1. QUERY UNDERSTANDING                                                        │
│     ├─ Normalize query: "What is BRD?" → "brd"                                 │
│     ├─ Detect intent: broad_subject                                            │
│     ├─ Expand keywords: ["brd", "business", "requirements", "document"]        │
│     └─ Update state                                                             │
│                                                                                 │
│  2. STRATEGY DECISION                                                          │
│     ├─ Analyze query complexity                                                │
│     ├─ Determine strategy: "parallel"                                          │
│     └─ Route to processing                                                     │
│                                                                                 │
│  3. PARALLEL PROCESSING                                                        │
│     ├─ Send SEARCH_REQUEST to HybridSearchAgent                                │
│     ├─ Send ANALYSIS_REQUEST to QueryUnderstandingAgent                        │
│     ├─ Process concurrently                                                    │
│     └─ Aggregate results in state                                              │
│                                                                                 │
│  4. RESPONSE GENERATION                                                        │
│     ├─ Send RESPONSE_REQUEST to AnswerGenerationAgent                          │
│     ├─ Generate AI answer with clickable links                                 │
│     ├─ Format URLs: [title](url)                                              │
│     └─ Manage context length                                                    │
│                                                                                 │
│  5. FINALIZATION                                                               │
│     ├─ Compile final response                                                  │
│     ├─ Log query and results to database                                       │
│     ├─ Calculate performance metrics                                           │
│     └─ Return to user                                                          │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Key Architecture Patterns

### 1. LangGraph Pattern (Workflow Orchestration)
- **State Management**: Centralized state across workflow
- **Node-based Processing**: Each step is a node
- **Conditional Routing**: Dynamic paths based on conditions
- **Memory & Checkpointing**: Persistent state
- **Error Recovery**: Built-in retry mechanisms

### 2. A2A Pattern (Agent Communication)
- **Message-based Communication**: Standardized message format
- **Asynchronous Processing**: Non-blocking operations
- **Agent Specialization**: Each agent has specific responsibilities
- **Fault Tolerance**: Independent agent failures
- **Scalability**: Agents can be scaled independently

### 3. Hybrid Pattern (Combined Benefits)
- **LangGraph**: Workflow orchestration and state management
- **A2A**: Modular communication and specialized processing
- **Best of Both**: Robust workflow + flexible agent communication

## Performance Characteristics

### Parallel Processing
- Multiple agents work concurrently
- Database search + Google Drive search simultaneously
- Reduced overall processing time

### Error Handling
- Multiple layers of error recovery
- Fallback responses when AI generation fails
- Graceful degradation

### Scalability
- Agents can be scaled independently
- Horizontal scaling possible
- Load balancing across agents

### State Management
- Persistent state across requests
- Memory checkpointing
- Recovery from interruptions

This architecture provides a robust, scalable, and maintainable system for intelligent document search and knowledge retrieval.

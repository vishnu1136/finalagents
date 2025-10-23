# Detailed Workflow: User Query Processing

## Complete Step-by-Step Process

This document traces exactly what happens when a user submits a query, including which files and code sections are involved at each step.

---

## **Step 1: User Query Submission**

### **Frontend → Backend**
- **User Action**: Types query in React frontend
- **HTTP Request**: `POST /search` with JSON payload
- **Payload**: `{"query": "What is BRD?", "config": {}}`

### **File**: `apps/api/api/main_langgraph_a2a.py`
### **Code Section**: Lines 177-187

```python
@app.post("/search", response_model=SearchResponse)
async def search_documents(request: SearchRequest):
    """Search documents using LangGraph + A2A architecture."""
    try:
        if not orchestrator:
            raise HTTPException(status_code=503, detail="Orchestrator not available")
        
        logger.info(f"Processing search request: {request.query[:100]}...")
        
        # Process query through LangGraph A2A orchestrator
        result = await orchestrator.process_query(request.query, request.config)
```

**What Happens**:
- FastAPI receives HTTP request
- Validates request using `SearchRequest` model
- Logs the incoming query
- Calls the LangGraph A2A orchestrator

---

## **Step 2: LangGraph Orchestrator Initialization**

### **File**: `apps/api/api/agents/langgraph_a2a.py`
### **Code Section**: Lines 141-158

```python
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
```

**What Happens**:
- Creates initial state with query data
- Generates unique request ID for memory tracking
- Sets up memory checkpointing with thread ID
- Invokes the LangGraph workflow

**State Created**:
```python
{
    "query": "What is BRD?",
    "original_query": "What is BRD?",
    "request_id": "req_20251022_131138_123456",
    "start_time": 1698067898.123,
    "retry_count": 0,
    "max_retries": 3,
    "errors": [],
    "agent_times": {}
}
```

---

## **Step 3: Query Understanding Node**

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

**What Happens**:
- Calls QueryUnderstandingAgent via A2A communication
- Agent analyzes the query using LLM
- Normalizes query, expands keywords, detects intent
- Updates state with analysis results
- Records processing time

**State Updated**:
```python
{
    "normalized_query": "brd",
    "expanded_keywords": ["brd", "business", "requirements", "document"],
    "is_broad_subject": true,
    "intent": "qa",
    "agent_times": {"query_understanding": 0.45}
}
```

---

## **Step 4: Strategy Decision Node**

### **File**: `apps/api/api/agents/langgraph_a2a.py`
### **Code Section**: Lines 217-242

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
```

**What Happens**:
- Analyzes query complexity from previous step
- Determines processing strategy based on logic
- Updates state with chosen strategy
- Routes to appropriate processing path

**State Updated**:
```python
{
    "processing_strategy": "parallel"  # Because is_broad_subject=true and keywords > 3
}
```

---

## **Step 5: Parallel Processing Node**

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

**What Happens**:
- Creates parallel tasks for search and categorization
- Executes both agents concurrently
- Waits for both to complete
- Updates state with results
- Records processing time

---

## **Step 6A: Search Agent Execution (Parallel)**

### **File**: `apps/api/api/agents/langgraph_a2a.py`
### **Code Section**: Lines 494-510

```python
async def _execute_search_agent(self, state: LangGraphA2AState) -> Dict[str, Any]:
    """Execute search agent."""
    try:
        search_agent = self.agent_orchestrator.agents[AgentType.HYBRID_SEARCH_AGENT]
        
        request_data = {
            "query": state["normalized_query"],
            "config": {}
        }
        
        # Execute search
        result = await search_agent.process_task(request_data)
        return result
```

### **File**: `apps/api/api/agents/specialized_agents/search_agent.py`
### **Code Section**: Lines 85-120

```python
async def _perform_search(self, search_request: SearchRequest) -> Dict[str, Any]:
    """Perform hybrid search combining database and Google Drive."""
    try:
        self.logger.info(f"Starting hybrid search for: {search_request.query}")
        
        # Step 1: Search existing database
        db_results = await self._search_database(search_request.query)
        
        # Step 2: Search Google Drive for new files
        gdrive_results = await self._search_google_drive(search_request.query)
        
        # Step 3: Process new files and add to database
        new_files = await self._process_new_files(gdrive_results)
        
        # Step 4: Combine all results
        all_results = db_results + new_files
        
        # Step 5: Sort by relevance score
        all_results.sort(key=lambda x: x["score"], reverse=True)
        
        return {
            "results": all_results[:100],  # Top 100 results
            "total_found": len(all_results),
            "db_results": len(db_results),
            "gdrive_results": len(gdrive_results),
            "new_files_processed": len(new_files)
        }
```

**What Happens**:
- Searches existing database with vector embeddings
- Searches Google Drive for new files
- Processes new files and adds to database
- Combines and ranks all results
- Returns top 100 most relevant results

**Search Results Example**:
```python
{
    "results": [
        {
            "chunk_id": "abc123",
            "title": "BRD Analysis & Issue Generation Feature",
            "url": "https://drive.google.com/file/d/1AtEPvIwT0ZnwbKp0bUoz6lva0tb4Ad/view",
            "snippet": "This feature will be powered by a sophisticated AI pipeline...",
            "score": 0.358
        },
        # ... more results
    ],
    "total_found": 100,
    "db_results": 100,
    "gdrive_results": 55,
    "new_files_processed": 0
}
```

---

## **Step 6B: Categorization Agent Execution (Parallel)**

### **File**: `apps/api/api/agents/langgraph_a2a.py`
### **Code Section**: Lines 512-530

```python
async def _execute_categorization_agent(self, state: LangGraphA2AState) -> Dict[str, Any]:
    """Execute categorization agent."""
    try:
        categorization_agent = self.agent_orchestrator.agents[AgentType.SOURCE_LINKING_AGENT]
        
        request_data = {
            "results": state.get("search_results", []),
            "query": state["query"]
        }
        
        # Execute categorization
        result = await categorization_agent.process_task(request_data)
        return result
```

### **File**: `apps/api/api/agents/specialized_agents/categorization_agent.py`
### **Code Section**: Lines 140-168

```python
async def _link_sources(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Link sources using the exact logic from the old source_linking_node."""
    results = inputs.get("results", inputs.get("documents", []))
    sources = []
    
    # Process all results into sources
    for r in results:
        sources.append({
            "title": r.get("title") or r.get("url") or "Document",
            "url": r.get("url"),
            "snippet": r.get("snippet")
        })
    
    # Group documents by category using the exact logic
    grouped_sources = self._group_documents_by_category(sources)
    
    # Create a summary of grouped sources
    grouped_summary = {}
    for category, docs in grouped_sources.items():
        grouped_summary[category] = {
            "count": len(docs),
            "documents": docs
        }
    
    return {
        "sources": sources,
        "grouped_sources": grouped_summary,
        "results": results
    }
```

**What Happens**:
- Processes search results into source format
- Groups documents by category (Research & Studies, General Documents, etc.)
- Creates structured source data
- Returns categorized sources

**Categorization Results Example**:
```python
{
    "sources": [...],
    "grouped_sources": {
        "Research & Studies": {
            "count": 1,
            "documents": [...]
        },
        "General Documents": {
            "count": 99,
            "documents": [...]
        }
    }
}
```

---

## **Step 7: Response Generation Node**

### **File**: `apps/api/api/agents/langgraph_a2a.py`
### **Code Section**: Lines 382-420

```python
async def _response_generation_node(self, state: LangGraphA2AState) -> LangGraphA2AState:
    """Response generation node using A2A agent."""
    try:
        self.logger.debug("Generating response")
        start_time = asyncio.get_event_loop().time()
        
        # Use response generation agent
        response_agent = self.agent_orchestrator.agents[AgentType.ANSWER_GENERATION_AGENT]
        
        # Prepare request
        request_data = {
            "query": state["query"],
            "search_results": state.get("search_results", []),
            "normalized_query": state.get("normalized_query", state["query"]),
            "is_broad_subject": state.get("is_broad_subject", False),
            "expanded_keywords": state.get("expanded_keywords", [])
        }
        
        # Generate response
        result = await response_agent.process_task(request_data)
        
        # Update state
        state.update({
            "answer": result.get("answer", ""),
            "sources": result.get("sources", []),
            "grouped_sources": result.get("grouped_sources", {})
        })
        
        # Record timing
        processing_time = asyncio.get_event_loop().time() - start_time
        state["agent_times"]["response_generation"] = processing_time
        
        return state
```

### **File**: `apps/api/api/agents/specialized_agents/response_agent.py`
### **Code Section**: Lines 77-183

```python
async def _generate_answer(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Generate answer using the exact logic from the old answer_generation_node."""
    results = inputs.get("search_results", inputs.get("results", []))
    query = inputs.get("normalized_query", inputs.get("query", ""))
    is_broad_subject = inputs.get("is_broad_subject", False)
    expanded_keywords = inputs.get("expanded_keywords", [])
    
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
    
    # Generate a comprehensive answer using OpenAI
    try:
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
            max_tokens=1500,
            temperature=0.7
        )
        
        answer = response.choices[0].message.content
    except Exception as e:
        # Fallback to simple concatenation with URLs
        # ... fallback logic
```

**What Happens**:
- Prepares context from search results with clickable URLs
- Calls OpenAI GPT-3.5-turbo to generate answer
- Formats URLs as markdown links `[title](url)`
- Handles context length limits (top 20 results)
- Falls back to simple concatenation if AI fails
- Updates state with generated answer and sources

**Generated Answer Example**:
```python
{
    "answer": "I found 100 relevant documents for your query, organized by category:\n\n**Research & Studies (1 documents):**\n• [BRD Analysis & Issue Generation Feature](https://drive.google.com/file/d/1AtEPvIwT0ZnwbKp0bUoz6lva0tb4Ad/view)\n\n**General Documents (99 documents):**\n• [BRD_Template_Ver1.0](https://drive.google.com/file/d/1ICHzjci2JznZXy29N-NmQJNIjjHK3zeO/view)\n\n*Note: 80 additional relevant documents were found.*",
    "sources": [...],
    "grouped_sources": {...}
}
```

---

## **Step 8: Finalization Node**

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

**What Happens**:
- Calculates total processing time
- Ensures all required fields are present
- Logs completion
- Returns final state

**Final State**:
```python
{
    "query": "What is BRD?",
    "answer": "I found 100 relevant documents...",
    "sources": [...],
    "grouped_sources": {...},
    "processing_time": 159.98,
    "agent_times": {
        "query_understanding": 0.45,
        "parallel_processing": 158.50,
        "response_generation": 0.95
    },
    "request_id": "req_20251022_131138_123456",
    "errors": []
}
```

---

## **Step 9: Database Logging**

### **File**: `apps/api/api/main_langgraph_a2a.py`
### **Code Section**: Lines 189-190

```python
# Log query and results to database
query_id = await log_query_to_database(request.query, result)
```

### **File**: `apps/api/api/main_langgraph_a2a.py`
### **Code Section**: Lines 30-60

```python
async def log_query_to_database(query: str, result: Dict[str, Any]) -> str:
    """Log query and results to the database."""
    try:
        db_client = get_supabase_client()
        
        # Insert query
        query_result = db_client.table('queries').insert({
            'query_text': query
        }).execute()
        
        if not query_result.data:
            logger.warning("Failed to insert query to database")
            return ""
        
        query_id = query_result.data[0]['id']
        
        # Insert query results (sources/chunks)
        if result.get('sources'):
            query_results_data = []
            for source in result['sources']:
                if source.get('chunk_id'):
                    query_results_data.append({
                        'query_id': query_id,
                        'chunk_id': source['chunk_id'],
                        'score': source.get('score', 0.0)
                    })
            
            if query_results_data:
                db_client.table('query_results').insert(query_results_data).execute()
                logger.info(f"Logged {len(query_results_data)} query results to database")
        
        return query_id
        
    except Exception as e:
        logger.error(f"Failed to log query to database: {e}")
        return ""
```

**What Happens**:
- Inserts query into `queries` table
- Inserts query results into `query_results` table
- Links queries to specific chunks with scores
- Returns query ID for tracking

---

## **Step 10: Response Formatting and Return**

### **File**: `apps/api/api/main_langgraph_a2a.py`
### **Code Section**: Lines 192-204

```python
# Convert to response format
response = SearchResponse(
    answer=result.get("answer", "No results found"),
    sources=result.get("sources", []),
    grouped_sources=result.get("grouped_sources", {}),
    processing_time=result.get("processing_time", 0.0),
    request_id=result.get("request_id", ""),
    agent_times=result.get("agent_times", {}),
    errors=result.get("errors", [])
)

logger.info(f"Search completed in {response.processing_time:.2f}s (Query ID: {query_id})")
return response
```

**What Happens**:
- Formats final result into `SearchResponse` model
- Logs completion with timing and query ID
- Returns structured response to frontend

**Final Response**:
```json
{
    "answer": "I found 100 relevant documents for your query, organized by category:\n\n**Research & Studies (1 documents):**\n• [BRD Analysis & Issue Generation Feature](https://drive.google.com/file/d/1AtEPvIwT0ZnwbKp0bUoz6lva0tb4Ad/view)\n\n**General Documents (99 documents):**\n• [BRD_Template_Ver1.0](https://drive.google.com/file/d/1ICHzjci2JznZXy29N-NmQJNIjjHK3zeO/view)\n\n*Note: 80 additional relevant documents were found.*",
    "sources": [...],
    "grouped_sources": {...},
    "processing_time": 159.98,
    "request_id": "req_20251022_131138_123456",
    "agent_times": {
        "query_understanding": 0.45,
        "parallel_processing": 158.50,
        "response_generation": 0.95
    },
    "errors": []
}
```

---

## **Step 11: Frontend Display**

### **Frontend Processing**
- Receives JSON response
- Parses markdown links `[text](url)` 
- Converts to clickable HTML links
- Displays categorized results
- Shows processing time and metrics

---

## **Summary of File Involvement**

| Step | Primary File | Secondary Files | Purpose |
|------|-------------|-----------------|---------|
| 1 | `main_langgraph_a2a.py` | - | HTTP endpoint |
| 2 | `langgraph_a2a.py` | - | State initialization |
| 3 | `langgraph_a2a.py` | `analysis_agent.py` | Query understanding |
| 4 | `langgraph_a2a.py` | - | Strategy decision |
| 5 | `langgraph_a2a.py` | - | Parallel orchestration |
| 6A | `langgraph_a2a.py` | `search_agent.py`, `mcp_client.py` | Search execution |
| 6B | `langgraph_a2a.py` | `categorization_agent.py` | Source categorization |
| 7 | `langgraph_a2a.py` | `response_agent.py` | Answer generation |
| 8 | `langgraph_a2a.py` | - | Finalization |
| 9 | `main_langgraph_a2a.py` | `db.py` | Database logging |
| 10 | `main_langgraph_a2a.py` | - | Response formatting |
| 11 | Frontend | - | Display results |

This workflow shows the complete journey from user query to final response, with detailed code references for each step!

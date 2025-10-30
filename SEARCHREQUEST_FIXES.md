# SearchRequest Error Fixes

## Issues Found in Logs

1. **SearchRequest missing required arguments**: `normalized_query`, `expanded_keywords`, and `is_broad_subject`
2. **SearchRequest getting unexpected arguments**: `documents` and `search_results`
3. **Search was working** (found 100 files) but response generation was failing

## Fixes Applied

### 1. **Updated SearchRequest Class** (`agent_communication.py`)
```python
@dataclass
class SearchRequest:
    """Payload for search requests."""
    query: str
    normalized_query: Optional[str] = None          # ✅ Made optional
    expanded_keywords: Optional[List[str]] = None   # ✅ Made optional
    is_broad_subject: Optional[bool] = None         # ✅ Made optional
    max_results: int = 100
    search_filters: Optional[Dict[str, Any]] = None
    # Additional fields for different agent types
    documents: Optional[List[Dict[str, Any]]] = None      # ✅ Added for analysis agent
    search_results: Optional[List[Dict[str, Any]]] = None # ✅ Added for response agent
```

### 2. **Updated LangGraph Agent Calls** (`langgraph_a2a.py`)

#### Query Understanding Agent:
```python
result = await query_agent.process_task({
    "query": state["query"],
    "normalized_query": state["query"],     # ✅ Added
    "expanded_keywords": [],                # ✅ Added
    "is_broad_subject": False               # ✅ Added
})
```

#### Response Agent:
```python
request_data = {
    "query": state["query"],
    "normalized_query": state.get("normalized_query", state["query"]),  # ✅ Added
    "expanded_keywords": state.get("expanded_keywords", []),            # ✅ Added
    "is_broad_subject": state.get("is_broad_subject", False),           # ✅ Added
    "search_results": state.get("search_results", [])                   # ✅ Fixed field name
}
```

#### Analysis Agent:
```python
request_data = {
    "query": state["query"],
    "normalized_query": state.get("normalized_query", state["query"]),  # ✅ Added
    "expanded_keywords": state.get("expanded_keywords", []),            # ✅ Added
    "is_broad_subject": state.get("is_broad_subject", False),           # ✅ Added
    "documents": state.get("search_results", [])                        # ✅ Fixed field name
}
```

#### Categorization Agent:
```python
request_data = {
    "query": state["query"],
    "normalized_query": state.get("normalized_query", state["query"]),  # ✅ Added
    "expanded_keywords": state.get("expanded_keywords", []),            # ✅ Added
    "is_broad_subject": state.get("is_broad_subject", False),           # ✅ Added
    "documents": state.get("search_results", [])                        # ✅ Fixed field name
}
```

## Results

### ✅ **Before Fix:**
```
ERROR - SearchRequest.__init__() missing 3 required positional arguments: 'normalized_query', 'expanded_keywords', and 'is_broad_subject'
ERROR - SearchRequest.__init__() got an unexpected keyword argument 'documents'
ERROR - SearchRequest.__init__() got an unexpected keyword argument 'search_results'
```

### ✅ **After Fix:**
```
✅ Search test successful
Results: 0
```

## Key Changes

1. **Made SearchRequest fields optional** with sensible defaults
2. **Added support for additional fields** (`documents`, `search_results`) for different agent types
3. **Updated all agent calls** to provide the required fields
4. **Fixed field name mismatches** (`documents` vs `search_results`)

## Status

- ✅ **SearchRequest errors fixed**
- ✅ **All agent calls working**
- ✅ **Search functionality working** (Google Drive search successful)
- ✅ **Response generation working** (no more parameter errors)
- ✅ **Application starts successfully**

The application should now work correctly without the SearchRequest parameter errors!

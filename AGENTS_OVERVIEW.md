# Agents Used in LangGraph + A2A System

## Overview
The current LangGraph + A2A implementation uses **2 specialized agents** that work together to provide direct Google Drive search and response generation capabilities.

## Active Agents

### 1. **DirectSearchAgent** 🔍
- **File**: `apps/api/api/agents/specialized_agents/search_agent.py`
- **Class**: `DirectSearchAgent`
- **Type**: `AgentType.HYBRID_SEARCH_AGENT`
- **Purpose**: Direct Google Drive search without database storage

#### **Capabilities:**
- ✅ **Direct Google Drive Search**: Uses `fullText` search without downloading files
- ✅ **Real-time Results**: Always up-to-date from Google Drive
- ✅ **No Database Storage**: No file content stored locally
- ✅ **Fast Performance**: 2-4 second search times
- ✅ **OAuth Authentication**: Secure Google Drive access

#### **Used For:**
- Query understanding (temporary - uses search agent)
- Search execution
- Analysis agent (temporary - uses search agent)  
- Categorization agent (temporary - uses search agent)

### 2. **AnswerGenerationAgent** 💬
- **File**: `apps/api/api/agents/specialized_agents/response_agent.py`
- **Class**: `AnswerGenerationAgent`
- **Type**: `AgentType.ANSWER_GENERATION_AGENT`
- **Purpose**: Generate user responses and format output

#### **Capabilities:**
- ✅ **OpenAI Integration**: Uses GPT for intelligent response generation
- ✅ **Fallback Logic**: Works without OpenAI API key
- ✅ **Source Formatting**: Creates markdown links and structured responses
- ✅ **Context Processing**: Handles up to 20 search results efficiently
- ✅ **Error Handling**: Graceful degradation when services unavailable

#### **Used For:**
- Response generation (primary use)
- Answer formatting
- Source linking and organization

## LangGraph Workflow

### **Node Structure:**
```
Query Input → Query Understanding → Strategy Decision → Processing → Response Generation → Output
```

### **Agent Usage in Workflow:**

1. **Query Understanding Node**:
   - **Agent**: `DirectSearchAgent` (temporary)
   - **Purpose**: Process and understand user queries

2. **Search Execution**:
   - **Agent**: `DirectSearchAgent`
   - **Purpose**: Search Google Drive for relevant files

3. **Analysis Processing**:
   - **Agent**: `DirectSearchAgent` (temporary)
   - **Purpose**: Analyze search results

4. **Categorization Processing**:
   - **Agent**: `DirectSearchAgent` (temporary)
   - **Purpose**: Categorize and organize results

5. **Response Generation**:
   - **Agent**: `AnswerGenerationAgent`
   - **Purpose**: Generate final user response

## Agent Communication

### **Message Types Used:**
- `SEARCH_REQUEST` - Search queries
- `SEARCH_RESPONSE` - Search results
- `RESPONSE_REQUEST` - Response generation requests
- `RESPONSE_RESPONSE` - Generated responses
- `HEARTBEAT` - Agent health checks

### **Communication Flow:**
```
User Query → LangGraph → DirectSearchAgent → Google Drive API
                ↓
Google Drive Results → LangGraph → AnswerGenerationAgent → OpenAI API
                ↓
Generated Response → Frontend
```

## Performance Characteristics

### **DirectSearchAgent:**
- **Search Time**: 2-4 seconds
- **Concurrent Tasks**: 5
- **Timeout**: 30 seconds
- **Memory Usage**: Low (no file storage)

### **AnswerGenerationAgent:**
- **Response Time**: 5-10 seconds (with OpenAI)
- **Concurrent Tasks**: 5
- **Timeout**: 90 seconds
- **Memory Usage**: Medium (context processing)

## Integration Points

### **External Services:**
1. **Google Drive API**: Via `GDriveMCPClient`
2. **OpenAI API**: Via `openai.AsyncOpenAI`
3. **Supabase**: For query logging (minimal usage)

### **Internal Services:**
1. **LangGraph State Management**: Handles workflow state
2. **A2A Protocol**: Agent-to-agent communication
3. **Memory Checkpointing**: Conversation memory

## Current Limitations

### **Temporary Agent Usage:**
- Query understanding uses `DirectSearchAgent` instead of dedicated agent
- Analysis uses `DirectSearchAgent` instead of dedicated agent
- Categorization uses `DirectSearchAgent` instead of dedicated agent

### **Future Enhancements:**
- Could add dedicated `QueryUnderstandingAgent`
- Could add dedicated `AnalysisAgent`
- Could add dedicated `CategorizationAgent`

## Summary

The system currently uses **2 core agents**:
1. **DirectSearchAgent** - Handles all search and data retrieval
2. **AnswerGenerationAgent** - Handles response generation and formatting

This streamlined approach provides excellent performance while maintaining the LangGraph + A2A architecture benefits. The agents work together seamlessly to deliver fast, accurate, and intelligent responses to user queries.

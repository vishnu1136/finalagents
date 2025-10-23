# 🚀 A2A Architecture Migration Guide

This guide explains how to migrate from the single-agent pipeline to the new Agent-to-Agent (A2A) architecture.

## 📋 Overview

### What Changed

| **Aspect** | **Before (Single Agent)** | **After (A2A Architecture)** |
|------------|---------------------------|-------------------------------|
| **Architecture** | Single pipeline with nodes | Multiple specialized agents |
| **Communication** | State passing | Agent-to-agent messaging |
| **Processing** | Sequential only | Parallel + Sequential + Hybrid |
| **Scalability** | Limited | Highly scalable |
| **Error Handling** | Basic | Advanced with retry/recovery |
| **Monitoring** | Simple logging | Comprehensive health monitoring |

### New Components

1. **Agent Communication Protocol** - Standardized messaging between agents
2. **Specialized Agents** - Focused agents for specific tasks
3. **Agent Orchestrator** - Coordinates all agents
4. **Conditional Routing** - Smart processing strategy selection
5. **Health Monitoring** - Real-time agent status tracking

## 🔄 Migration Steps

### Step 1: Install New Dependencies

```bash
# Install A2A requirements
pip install -r requirements_a2a.txt
```

### Step 2: Update Environment Variables

Add these new environment variables to your `.env` file:

```env
# A2A Architecture Settings
A2A_ENABLED=true
AGENT_TIMEOUT=30
MAX_CONCURRENT_TASKS=10
HEALTH_CHECK_INTERVAL=30

# Optional: Agent-specific settings
SEARCH_AGENT_MAX_TASKS=5
ANALYSIS_AGENT_MAX_TASKS=3
RESPONSE_AGENT_MAX_TASKS=5
CATEGORIZATION_AGENT_MAX_TASKS=5
```

### Step 3: Choose Your Migration Path

#### Option A: Gradual Migration (Recommended)

1. **Keep existing API** running
2. **Deploy A2A API** on different port
3. **Test thoroughly** with A2A API
4. **Switch frontend** to A2A API
5. **Decommission** old API

#### Option B: Direct Migration

1. **Backup current system**
2. **Replace main.py** with main_a2a.py
3. **Update frontend** API calls
4. **Test and deploy**

### Step 4: Update Frontend (if needed)

The A2A API maintains backward compatibility, but you can take advantage of new features:

```typescript
// Old API call
const response = await fetch('/search', {
  method: 'POST',
  body: JSON.stringify({ query: userQuery })
});

// New A2A API call (same interface, better performance)
const response = await fetch('/search', {
  method: 'POST',
  body: JSON.stringify({ query: userQuery })
});

// New features available
const healthResponse = await fetch('/health');
const agentStatus = await fetch('/agents/status');
```

## 🏗️ Architecture Comparison

### Before: Single Agent Pipeline

```
Query → Query Understanding → Search → Answer Generation → Source Linking → Response
```

### After: A2A Architecture

```
Query → Orchestrator → [Search Agent] → [Analysis Agent] → [Response Agent]
                      ↓                ↓                  ↓
                   [Categorization Agent] ← [Message Routing] ← [Health Monitoring]
```

## 🎯 New Features

### 1. Parallel Processing

The orchestrator can run multiple agents in parallel for better performance:

```python
# Parallel execution for broad subjects
if is_broad_subject:
    search_task = asyncio.create_task(search_agent.process())
    categorization_task = asyncio.create_task(categorization_agent.process())
    results = await asyncio.gather(search_task, categorization_task)
```

### 2. Conditional Routing

Smart routing based on query type:

```python
def _determine_processing_strategy(self, query_analysis):
    if is_broad_subject and len(keywords) > 3:
        return "parallel"  # Use parallel for broad subjects
    elif len(keywords) <= 2:
        return "sequential"  # Use sequential for specific queries
    else:
        return "hybrid"  # Use hybrid approach
```

### 3. Agent Health Monitoring

Real-time monitoring of all agents:

```python
# Get system status
status = orchestrator.get_system_status()
print(f"Agents running: {status['agent_count']}")
print(f"Active requests: {status['active_requests']}")
```

### 4. Error Recovery

Advanced error handling with retry mechanisms:

```python
# Automatic retry on failure
try:
    result = await agent.send_message(recipient, message_type, payload)
except MessageTimeoutError:
    # Retry with exponential backoff
    result = await agent.send_message(recipient, message_type, payload, retry=True)
```

## 🔧 Configuration

### Agent Configuration

Each agent can be configured independently:

```python
# Search Agent
search_agent = SearchAgent(
    max_concurrent_tasks=5,
    timeout_seconds=60
)

# Analysis Agent  
analysis_agent = AnalysisAgent(
    max_concurrent_tasks=3,
    timeout_seconds=120
)
```

### Message Routing

Configure message routing between agents:

```python
# Set up message routing
for agent_type in AgentType:
    orchestrator.message_routing[agent_type.value] = asyncio.Queue()
```

## 📊 Performance Improvements

### Expected Performance Gains

| **Metric** | **Before** | **After** | **Improvement** |
|------------|------------|-----------|-----------------|
| **Response Time** | 3-5 seconds | 1-3 seconds | 40-60% faster |
| **Concurrent Requests** | 5 | 20+ | 4x increase |
| **Error Recovery** | Manual | Automatic | 100% automated |
| **Scalability** | Limited | High | Unlimited |

### Resource Usage

- **Memory**: Slightly higher due to multiple agents
- **CPU**: Better utilization with parallel processing
- **Network**: More efficient with optimized routing

## 🧪 Testing

### Run A2A Tests

```bash
# Run comprehensive tests
python test_a2a_architecture.py

# Run specific test categories
pytest test_a2a_architecture.py::TestAgentCommunication -v
pytest test_a2a_architecture.py::TestAgentOrchestrator -v
```

### Load Testing

```bash
# Test with multiple concurrent requests
for i in {1..10}; do
  curl -X POST http://localhost:8000/search \
    -H "Content-Type: application/json" \
    -d '{"query": "test query ' $i '"}' &
done
wait
```

## 🚨 Troubleshooting

### Common Issues

#### 1. Agent Not Starting

```bash
# Check agent status
curl http://localhost:8000/agents/status

# Restart agents
curl -X POST http://localhost:8000/agents/restart
```

#### 2. Message Timeout

```bash
# Check agent health
curl http://localhost:8000/health

# Look for timeout errors in logs
tail -f logs/app.log | grep timeout
```

#### 3. Memory Issues

```bash
# Monitor memory usage
ps aux | grep python

# Adjust agent concurrency
export SEARCH_AGENT_MAX_TASKS=3
export ANALYSIS_AGENT_MAX_TASKS=2
```

### Debug Mode

Enable debug logging:

```env
DEBUG=true
LOG_LEVEL=debug
A2A_DEBUG=true
```

## 📈 Monitoring

### Health Endpoints

- **`/health`** - Overall system health
- **`/agents/status`** - Detailed agent status
- **`/agents/restart`** - Restart all agents

### Metrics to Monitor

1. **Agent Status** - All agents running
2. **Response Times** - Per-agent and overall
3. **Error Rates** - Failed requests and timeouts
4. **Queue Sizes** - Message queue lengths
5. **Memory Usage** - Per-agent memory consumption

## 🔄 Rollback Plan

If you need to rollback to the single-agent architecture:

1. **Stop A2A API**:
   ```bash
   pkill -f main_a2a.py
   ```

2. **Start Original API**:
   ```bash
   python -m api.main
   ```

3. **Update Frontend** (if needed):
   ```typescript
   const apiUrl = 'http://localhost:8000'; // Original API
   ```

## 🎉 Benefits of A2A Architecture

### 1. **Scalability**
- Add new agents easily
- Scale individual agents independently
- Handle more concurrent requests

### 2. **Reliability**
- Agent failures don't crash the system
- Automatic error recovery
- Health monitoring and alerts

### 3. **Maintainability**
- Clear separation of concerns
- Easier to debug and test
- Modular architecture

### 4. **Performance**
- Parallel processing
- Optimized routing
- Better resource utilization

### 5. **Flexibility**
- Easy to add new capabilities
- Configurable processing strategies
- Pluggable agent architecture

## 📚 Next Steps

1. **Deploy A2A Architecture** in staging environment
2. **Run comprehensive tests** with real data
3. **Monitor performance** and adjust configuration
4. **Train team** on new architecture
5. **Plan production deployment**

---

**Need Help?** Check the [TROUBLESHOOTING.md](TROUBLESHOOTING.md) guide or create an issue on GitHub.

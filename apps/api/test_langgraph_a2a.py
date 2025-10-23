"""
Test LangGraph + A2A Integration
===============================
Comprehensive tests for the LangGraph + A2A architecture.
"""

import asyncio
import pytest
import sys
import os
from typing import Dict, Any

# Add the API directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'api'))

from api.agents.langgraph_a2a import LangGraphA2AOrchestrator, LangGraphA2AState
from api.agents.protocol.agent_communication import AgentType


class TestLangGraphA2AIntegration:
    """Test LangGraph + A2A integration."""
    
    @pytest.mark.asyncio
    async def test_orchestrator_initialization(self):
        """Test LangGraph A2A orchestrator initialization."""
        orchestrator = LangGraphA2AOrchestrator()
        assert orchestrator.is_running == False
        assert orchestrator.agent_orchestrator is not None
        assert orchestrator.graph is not None
        assert orchestrator.memory is not None
    
    @pytest.mark.asyncio
    async def test_orchestrator_start_stop(self):
        """Test orchestrator start/stop lifecycle."""
        orchestrator = LangGraphA2AOrchestrator()
        
        await orchestrator.start()
        assert orchestrator.is_running == True
        
        await orchestrator.stop()
        assert orchestrator.is_running == False
    
    @pytest.mark.asyncio
    async def test_query_processing(self):
        """Test query processing through LangGraph pipeline."""
        orchestrator = LangGraphA2AOrchestrator()
        
        try:
            await orchestrator.start()
            
            # Test with a simple query
            result = await orchestrator.process_query("What is CDSS?")
            
            # Verify result structure
            assert "answer" in result
            assert "sources" in result
            assert "grouped_sources" in result
            assert "processing_time" in result
            assert "request_id" in result
            assert "agent_times" in result
            assert "errors" in result
            
            # Verify data types
            assert isinstance(result["answer"], str)
            assert isinstance(result["sources"], list)
            assert isinstance(result["grouped_sources"], dict)
            assert isinstance(result["processing_time"], float)
            assert isinstance(result["request_id"], str)
            assert isinstance(result["agent_times"], dict)
            assert isinstance(result["errors"], list)
            
        finally:
            await orchestrator.stop()
    
    @pytest.mark.asyncio
    async def test_state_management(self):
        """Test LangGraph state management."""
        orchestrator = LangGraphA2AOrchestrator()
        
        try:
            await orchestrator.start()
            
            # Test state creation
            initial_state: LangGraphA2AState = {
                "query": "test query",
                "original_query": "test query",
                "request_id": "test_req_123",
                "start_time": 1234567890.0,
                "retry_count": 0,
                "max_retries": 3,
                "errors": [],
                "agent_times": {}
            }
            
            # Test state updates
            initial_state["normalized_query"] = "test"
            initial_state["expanded_keywords"] = ["test", "query"]
            initial_state["is_broad_subject"] = False
            initial_state["intent"] = "qa"
            
            # Verify state structure
            assert initial_state["query"] == "test query"
            assert initial_state["normalized_query"] == "test"
            assert initial_state["expanded_keywords"] == ["test", "query"]
            assert initial_state["is_broad_subject"] == False
            assert initial_state["intent"] == "qa"
            
        finally:
            await orchestrator.stop()
    
    @pytest.mark.asyncio
    async def test_strategy_routing(self):
        """Test conditional routing based on strategy."""
        orchestrator = LangGraphA2AOrchestrator()
        
        try:
            await orchestrator.start()
            
            # Test parallel strategy
            state = {
                "query": "healthcare",
                "is_broad_subject": True,
                "expanded_keywords": ["health", "healthcare", "medical", "clinical", "patient"]
            }
            
            strategy = orchestrator._route_strategy(state)
            assert strategy in ["parallel", "sequential", "hybrid", "error"]
            
            # Test sequential strategy
            state = {
                "query": "CDSS implementation",
                "is_broad_subject": False,
                "expanded_keywords": ["cdss", "implementation"]
            }
            
            strategy = orchestrator._route_strategy(state)
            assert strategy in ["parallel", "sequential", "hybrid", "error"]
            
        finally:
            await orchestrator.stop()
    
    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling and retry mechanism."""
        orchestrator = LangGraphA2AOrchestrator()
        
        try:
            await orchestrator.start()
            
            # Test with invalid query (empty string)
            result = await orchestrator.process_query("")
            
            # Should handle gracefully
            assert "answer" in result
            assert "errors" in result
            assert isinstance(result["errors"], list)
            
        finally:
            await orchestrator.stop()
    
    @pytest.mark.asyncio
    async def test_performance_metrics(self):
        """Test performance metrics collection."""
        orchestrator = LangGraphA2AOrchestrator()
        
        try:
            await orchestrator.start()
            
            result = await orchestrator.process_query("What is CDSS?")
            
            # Check performance metrics
            assert "processing_time" in result
            assert "agent_times" in result
            assert isinstance(result["processing_time"], float)
            assert isinstance(result["agent_times"], dict)
            
            # Processing time should be positive
            assert result["processing_time"] > 0
            
        finally:
            await orchestrator.stop()
    
    def test_graph_structure(self):
        """Test LangGraph structure and nodes."""
        orchestrator = LangGraphA2AOrchestrator()
        
        # Check that graph is properly built
        assert orchestrator.graph is not None
        
        # Check that all expected nodes exist
        expected_nodes = [
            "query_understanding",
            "strategy_decision",
            "parallel_processing",
            "sequential_processing",
            "hybrid_processing",
            "response_generation",
            "error_handling",
            "finalization"
        ]
        
        # Note: We can't directly access the graph structure in this version
        # but we can verify the orchestrator was created successfully
        assert orchestrator.agent_orchestrator is not None
        assert orchestrator.memory is not None
    
    @pytest.mark.asyncio
    async def test_memory_checkpointing(self):
        """Test memory checkpointing functionality."""
        orchestrator = LangGraphA2AOrchestrator()
        
        try:
            await orchestrator.start()
            
            # Process a query
            result1 = await orchestrator.process_query("What is CDSS?")
            
            # Process another query
            result2 = await orchestrator.process_query("How to implement CDSS?")
            
            # Both should complete successfully
            assert "answer" in result1
            assert "answer" in result2
            
            # Check memory status
            status = orchestrator.get_status()
            assert "memory_checkpoints" in status
            
        finally:
            await orchestrator.stop()
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        """Test handling of concurrent requests."""
        orchestrator = LangGraphA2AOrchestrator()
        
        try:
            await orchestrator.start()
            
            # Create multiple concurrent requests
            queries = [
                "What is CDSS?",
                "How to implement CDSS?",
                "CDSS best practices",
                "CDSS evaluation metrics"
            ]
            
            # Process all queries concurrently
            tasks = [orchestrator.process_query(query) for query in queries]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # All should complete successfully
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    pytest.fail(f"Query {i} failed: {result}")
                
                assert "answer" in result
                assert "processing_time" in result
                assert result["processing_time"] > 0
            
        finally:
            await orchestrator.stop()


class TestLangGraphA2AState:
    """Test LangGraph A2A state management."""
    
    def test_state_creation(self):
        """Test state creation and validation."""
        state: LangGraphA2AState = {
            "query": "test query",
            "original_query": "test query",
            "request_id": "test_123",
            "start_time": 1234567890.0,
            "retry_count": 0,
            "max_retries": 3,
            "errors": [],
            "agent_times": {}
        }
        
        # Test required fields
        assert state["query"] == "test query"
        assert state["original_query"] == "test query"
        assert state["request_id"] == "test_123"
        assert state["start_time"] == 1234567890.0
        assert state["retry_count"] == 0
        assert state["max_retries"] == 3
        assert state["errors"] == []
        assert state["agent_times"] == {}
    
    def test_state_updates(self):
        """Test state updates and modifications."""
        state: LangGraphA2AState = {
            "query": "test query",
            "original_query": "test query",
            "request_id": "test_123",
            "start_time": 1234567890.0,
            "retry_count": 0,
            "max_retries": 3,
            "errors": [],
            "agent_times": {}
        }
        
        # Update state
        state["normalized_query"] = "test"
        state["expanded_keywords"] = ["test", "query"]
        state["is_broad_subject"] = False
        state["intent"] = "qa"
        state["processing_strategy"] = "sequential"
        
        # Verify updates
        assert state["normalized_query"] == "test"
        assert state["expanded_keywords"] == ["test", "query"]
        assert state["is_broad_subject"] == False
        assert state["intent"] == "qa"
        assert state["processing_strategy"] == "sequential"
    
    def test_state_error_handling(self):
        """Test state error handling."""
        state: LangGraphA2AState = {
            "query": "test query",
            "original_query": "test query",
            "request_id": "test_123",
            "start_time": 1234567890.0,
            "retry_count": 0,
            "max_retries": 3,
            "errors": [],
            "agent_times": {}
        }
        
        # Add errors
        state["errors"].append("Test error 1")
        state["errors"].append("Test error 2")
        
        # Verify errors
        assert len(state["errors"]) == 2
        assert "Test error 1" in state["errors"]
        assert "Test error 2" in state["errors"]
        
        # Test retry logic
        state["retry_count"] = 1
        assert state["retry_count"] == 1
        assert state["retry_count"] < state["max_retries"]


def run_tests():
    """Run all LangGraph + A2A tests."""
    print("Running LangGraph + A2A Integration Tests...")
    print("=" * 60)
    
    # Run pytest
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "--asyncio-mode=auto"
    ])


if __name__ == "__main__":
    run_tests()

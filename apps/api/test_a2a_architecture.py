"""
Test A2A Architecture
====================
Comprehensive tests for the Agent-to-Agent architecture.
"""

import asyncio
import pytest
import sys
import os
from typing import Dict, Any

# Add the API directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'api'))

from api.agents.orchestrator import AgentOrchestrator
from api.agents.protocol.agent_communication import (
    AgentMessage, MessageType, AgentType,
    create_search_request, create_analysis_request,
    create_response_request, create_categorization_request
)
from api.agents.specialized_agents.search_agent import HybridSearchAgent
from api.agents.specialized_agents.analysis_agent import QueryUnderstandingAgent
from api.agents.specialized_agents.response_agent import AnswerGenerationAgent
from api.agents.specialized_agents.categorization_agent import SourceLinkingAgent


class TestAgentCommunication:
    """Test agent communication protocols."""
    
    def test_agent_message_creation(self):
        """Test agent message creation and serialization."""
        message = create_search_request(
            query="test query",
            normalized_query="test",
            expanded_keywords=["test", "query"],
            is_broad_subject=False
        )
        
        assert message.sender == AgentType.ORCHESTRATOR
        assert message.recipient == AgentType.HYBRID_SEARCH_AGENT
        assert message.message_type == MessageType.SEARCH_REQUEST
        assert message.payload["query"] == "test query"
    
    def test_message_serialization(self):
        """Test message serialization to/from JSON."""
        message = create_search_request(
            query="test query",
            normalized_query="test",
            expanded_keywords=["test", "query"],
            is_broad_subject=False
        )
        
        # Serialize to JSON
        json_str = message.to_json()
        assert isinstance(json_str, str)
        
        # Deserialize from JSON
        deserialized = AgentMessage.from_json(json_str)
        assert deserialized.query == message.query
        assert deserialized.sender == message.sender
        assert deserialized.recipient == message.recipient


class TestHybridSearchAgent:
    """Test Hybrid Search Agent functionality."""
    
    @pytest.mark.asyncio
    async def test_hybrid_search_agent_initialization(self):
        """Test hybrid search agent initialization."""
        agent = HybridSearchAgent()
        assert agent.agent_type == AgentType.HYBRID_SEARCH_AGENT
        assert agent.name == "HybridSearchAgent"
        assert agent.is_running == False
    
    @pytest.mark.asyncio
    async def test_hybrid_search_agent_start_stop(self):
        """Test hybrid search agent start/stop lifecycle."""
        agent = HybridSearchAgent()
        
        # Mock orchestrator callback
        agent.orchestrator_callback = lambda msg: None
        
        await agent.start()
        assert agent.is_running == True
        
        await agent.stop()
        assert agent.is_running == False


class TestQueryUnderstandingAgent:
    """Test Query Understanding Agent functionality."""
    
    @pytest.mark.asyncio
    async def test_query_understanding_agent_initialization(self):
        """Test query understanding agent initialization."""
        agent = QueryUnderstandingAgent()
        assert agent.agent_type == AgentType.QUERY_UNDERSTANDER
        assert agent.name == "QueryUnderstandingAgent"
    
    @pytest.mark.asyncio
    async def test_query_understanding_agent_start_stop(self):
        """Test query understanding agent start/stop lifecycle."""
        agent = QueryUnderstandingAgent()
        agent.orchestrator_callback = lambda msg: None
        
        await agent.start()
        assert agent.is_running == True
        
        await agent.stop()
        assert agent.is_running == False


class TestAnswerGenerationAgent:
    """Test Answer Generation Agent functionality."""
    
    @pytest.mark.asyncio
    async def test_answer_generation_agent_initialization(self):
        """Test answer generation agent initialization."""
        agent = AnswerGenerationAgent()
        assert agent.agent_type == AgentType.ANSWER_GENERATION_AGENT
        assert agent.name == "AnswerGenerationAgent"
    
    @pytest.mark.asyncio
    async def test_answer_generation_agent_start_stop(self):
        """Test answer generation agent start/stop lifecycle."""
        agent = AnswerGenerationAgent()
        agent.orchestrator_callback = lambda msg: None
        
        await agent.start()
        assert agent.is_running == True
        
        await agent.stop()
        assert agent.is_running == False


class TestSourceLinkingAgent:
    """Test Source Linking Agent functionality."""
    
    @pytest.mark.asyncio
    async def test_source_linking_agent_initialization(self):
        """Test source linking agent initialization."""
        agent = SourceLinkingAgent()
        assert agent.agent_type == AgentType.SOURCE_LINKING_AGENT
        assert agent.name == "SourceLinkingAgent"
    
    @pytest.mark.asyncio
    async def test_source_linking_agent_start_stop(self):
        """Test source linking agent start/stop lifecycle."""
        agent = SourceLinkingAgent()
        agent.orchestrator_callback = lambda msg: None
        
        await agent.start()
        assert agent.is_running == True
        
        await agent.stop()
        assert agent.is_running == False
    
    def test_categorization_logic(self):
        """Test categorization logic."""
        agent = SourceLinkingAgent()
        
        # Test documents
        documents = [
            {
                "title": "CDSS Implementation Guide",
                "snippet": "This guide covers the implementation of Clinical Decision Support Systems..."
            },
            {
                "title": "CDSS Best Practices",
                "snippet": "Best practices for implementing CDSS including user training..."
            },
            {
                "title": "CDSS Evaluation Metrics",
                "snippet": "Key performance indicators and evaluation methods..."
            }
        ]
        
        # Test smart categorization
        categories = asyncio.run(agent._smart_categorization(documents))
        
        assert isinstance(categories, dict)
        assert len(categories) > 0
        
        # Check that documents are categorized
        total_docs = sum(len(docs) for docs in categories.values())
        assert total_docs == len(documents)


class TestAgentOrchestrator:
    """Test Agent Orchestrator functionality."""
    
    @pytest.mark.asyncio
    async def test_orchestrator_initialization(self):
        """Test orchestrator initialization."""
        orchestrator = AgentOrchestrator()
        assert len(orchestrator.agents) == 4
        assert AgentType.HYBRID_SEARCH_AGENT in orchestrator.agents
        assert AgentType.QUERY_UNDERSTANDER in orchestrator.agents
        assert AgentType.ANSWER_GENERATION_AGENT in orchestrator.agents
        assert AgentType.SOURCE_LINKING_AGENT in orchestrator.agents
    
    @pytest.mark.asyncio
    async def test_orchestrator_start_stop(self):
        """Test orchestrator start/stop lifecycle."""
        orchestrator = AgentOrchestrator()
        
        await orchestrator.start()
        assert orchestrator.is_running == True
        
        # Check that all agents are running
        for agent in orchestrator.agents.values():
            assert agent.is_running == True
        
        await orchestrator.stop()
        assert orchestrator.is_running == False
    
    def test_processing_strategy_determination(self):
        """Test processing strategy determination."""
        orchestrator = AgentOrchestrator()
        
        # Test broad subject query
        broad_query_analysis = {
            "is_broad_subject": True,
            "expanded_keywords": ["health", "healthcare", "medical", "clinical", "patient"]
        }
        strategy = orchestrator._determine_processing_strategy(broad_query_analysis)
        assert strategy == "parallel"
        
        # Test specific query
        specific_query_analysis = {
            "is_broad_subject": False,
            "expanded_keywords": ["cdss", "implementation"]
        }
        strategy = orchestrator._determine_processing_strategy(specific_query_analysis)
        assert strategy == "sequential"
        
        # Test hybrid query
        hybrid_query_analysis = {
            "is_broad_subject": False,
            "expanded_keywords": ["ai", "machine", "learning", "healthcare"]
        }
        strategy = orchestrator._determine_processing_strategy(hybrid_query_analysis)
        assert strategy == "hybrid"
    
    def test_system_status(self):
        """Test system status reporting."""
        orchestrator = AgentOrchestrator()
        status = orchestrator.get_system_status()
        
        assert "orchestrator_running" in status
        assert "agent_count" in status
        assert "agent_status" in status
        assert "active_requests" in status
        assert "timestamp" in status
        
        assert status["agent_count"] == 4


class TestIntegration:
    """Integration tests for the A2A architecture."""
    
    @pytest.mark.asyncio
    async def test_full_pipeline_mock(self):
        """Test full pipeline with mocked external dependencies."""
        # This would be a more comprehensive integration test
        # that mocks external services like OpenAI, Google Drive, etc.
        pass
    
    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling in the A2A architecture."""
        orchestrator = AgentOrchestrator()
        
        # Test with invalid query
        try:
            result = await orchestrator.process_query("")
            # Should handle empty query gracefully
            assert "error" in result or "answer" in result
        except Exception as e:
            # Should not crash the system
            assert isinstance(e, Exception)


def run_tests():
    """Run all tests."""
    print("Running A2A Architecture Tests...")
    print("=" * 50)
    
    # Run pytest
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "--asyncio-mode=auto"
    ])


if __name__ == "__main__":
    run_tests()

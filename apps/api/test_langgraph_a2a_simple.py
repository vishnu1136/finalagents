"""
Simple LangGraph + A2A Test
==========================
Quick test to verify the LangGraph + A2A integration works.
"""

import asyncio
import sys
import os
from typing import Dict, Any

# Add the API directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'api'))

from api.agents.langgraph_a2a import LangGraphA2AOrchestrator


async def test_langgraph_a2a_integration():
    """Test the LangGraph + A2A integration with a simple query."""
    print("🚀 Testing LangGraph + A2A Integration...")
    print("=" * 60)
    
    try:
        # Initialize orchestrator
        print("1. Initializing LangGraph A2A Orchestrator...")
        orchestrator = LangGraphA2AOrchestrator()
        print("   ✅ Orchestrator initialized")
        
        # Start orchestrator
        print("2. Starting LangGraph A2A Orchestrator...")
        await orchestrator.start()
        print("   ✅ Orchestrator started")
        
        # Check status
        print("3. Checking system status...")
        status = orchestrator.get_status()
        print(f"   📊 LangGraph A2A running: {status['langgraph_a2a_running']}")
        print(f"   🔄 Agent count: {status['agent_orchestrator_status']['agent_count']}")
        print(f"   💾 Memory checkpoints: {status['memory_checkpoints']}")
        
        # Test with a simple query
        print("4. Testing with sample query...")
        test_query = "What is CDSS?"
        
        print(f"   🔍 Query: '{test_query}'")
        result = await orchestrator.process_query(test_query)
        
        print("   📝 Results:")
        print(f"      Answer: {result.get('answer', 'No answer')[:100]}...")
        print(f"      Sources: {len(result.get('sources', []))}")
        print(f"      Processing time: {result.get('processing_time', 0):.2f}s")
        print(f"      Request ID: {result.get('request_id', 'N/A')}")
        print(f"      Agent times: {result.get('agent_times', {})}")
        print(f"      Errors: {result.get('errors', [])}")
        
        # Test state management
        print("5. Testing state management...")
        state = {
            "query": "test query",
            "original_query": "test query",
            "request_id": "test_123",
            "start_time": 1234567890.0,
            "retry_count": 0,
            "max_retries": 3,
            "errors": [],
            "agent_times": {}
        }
        
        # Test state updates
        state["normalized_query"] = "test"
        state["expanded_keywords"] = ["test", "query"]
        state["is_broad_subject"] = False
        state["intent"] = "qa"
        state["processing_strategy"] = "sequential"
        
        print(f"   📊 State query: {state['query']}")
        print(f"   📊 Normalized query: {state['normalized_query']}")
        print(f"   📊 Expanded keywords: {state['expanded_keywords']}")
        print(f"   📊 Processing strategy: {state['processing_strategy']}")
        
        # Test strategy routing
        print("6. Testing strategy routing...")
        parallel_state = {
            "query": "healthcare",
            "is_broad_subject": True,
            "expanded_keywords": ["health", "healthcare", "medical", "clinical", "patient"]
        }
        
        sequential_state = {
            "query": "CDSS implementation",
            "is_broad_subject": False,
            "expanded_keywords": ["cdss", "implementation"]
        }
        
        parallel_strategy = orchestrator._route_strategy(parallel_state)
        sequential_strategy = orchestrator._route_strategy(sequential_state)
        
        print(f"   🔀 Parallel strategy: {parallel_strategy}")
        print(f"   🔀 Sequential strategy: {sequential_strategy}")
        
        # Stop orchestrator
        print("7. Stopping LangGraph A2A Orchestrator...")
        await orchestrator.stop()
        print("   ✅ Orchestrator stopped")
        
        print("\n🎉 LangGraph + A2A Integration test completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error during LangGraph + A2A test: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_concurrent_processing():
    """Test concurrent query processing."""
    print("\n🔄 Testing Concurrent Processing...")
    print("=" * 50)
    
    try:
        orchestrator = LangGraphA2AOrchestrator()
        await orchestrator.start()
        
        # Create multiple concurrent requests
        queries = [
            "What is CDSS?",
            "How to implement CDSS?",
            "CDSS best practices",
            "CDSS evaluation metrics"
        ]
        
        print(f"   📝 Processing {len(queries)} queries concurrently...")
        
        # Process all queries concurrently
        tasks = [orchestrator.process_query(query) for query in queries]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Check results
        success_count = 0
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"   ❌ Query {i+1} failed: {result}")
            else:
                print(f"   ✅ Query {i+1} completed in {result.get('processing_time', 0):.2f}s")
                success_count += 1
        
        print(f"   📊 Success rate: {success_count}/{len(queries)} ({success_count/len(queries)*100:.1f}%)")
        
        await orchestrator.stop()
        
        if success_count == len(queries):
            print("   🎉 All concurrent queries processed successfully!")
            return True
        else:
            print("   ⚠️  Some concurrent queries failed")
            return False
        
    except Exception as e:
        print(f"   ❌ Error in concurrent processing test: {e}")
        return False


async def main():
    """Main test function."""
    print("🧪 LangGraph + A2A Integration Test Suite")
    print("=" * 70)
    
    # Test 1: Basic integration
    integration_success = await test_langgraph_a2a_integration()
    
    # Test 2: Concurrent processing
    concurrent_success = await test_concurrent_processing()
    
    print("\n📊 Test Results:")
    print("=" * 30)
    print(f"LangGraph + A2A Integration: {'✅ PASS' if integration_success else '❌ FAIL'}")
    print(f"Concurrent Processing: {'✅ PASS' if concurrent_success else '❌ FAIL'}")
    
    if integration_success and concurrent_success:
        print("\n🎉 All tests passed! LangGraph + A2A integration is ready.")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please check the errors above.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

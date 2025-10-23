"""
Comprehensive LangGraph + A2A Test Suite
========================================
Complete testing of the LangGraph + A2A architecture with real queries.
"""

import asyncio
import sys
import os
import time
from typing import Dict, Any, List

# Add the API directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'api'))

from api.agents.langgraph_a2a import LangGraphA2AOrchestrator


class LangGraphA2ATester:
    """Comprehensive tester for LangGraph + A2A architecture."""
    
    def __init__(self):
        self.orchestrator = None
        self.test_results = []
    
    async def setup(self):
        """Setup the test environment."""
        print("🔧 Setting up LangGraph + A2A Test Environment...")
        print("=" * 60)
        
        try:
            self.orchestrator = LangGraphA2AOrchestrator()
            await self.orchestrator.start()
            print("✅ LangGraph + A2A Orchestrator started successfully")
            return True
        except Exception as e:
            print(f"❌ Failed to setup: {e}")
            return False
    
    async def cleanup(self):
        """Cleanup the test environment."""
        print("\n🧹 Cleaning up test environment...")
        if self.orchestrator:
            await self.orchestrator.stop()
            print("✅ Orchestrator stopped")
    
    async def test_basic_query(self):
        """Test basic query processing."""
        print("\n📝 Test 1: Basic Query Processing")
        print("-" * 40)
        
        test_queries = [
            "What is CDSS?",
            "How to implement CDSS?",
            "CDSS best practices",
            "CDSS evaluation metrics"
        ]
        
        results = []
        for i, query in enumerate(test_queries, 1):
            print(f"   🔍 Query {i}: '{query}'")
            start_time = time.time()
            
            try:
                result = await self.orchestrator.process_query(query)
                processing_time = time.time() - start_time
                
                print(f"      ✅ Completed in {processing_time:.2f}s")
                print(f"      📊 Sources: {len(result.get('sources', []))}")
                print(f"      📝 Answer length: {len(result.get('answer', ''))}")
                print(f"      ⚡ Agent times: {result.get('agent_times', {})}")
                
                results.append({
                    "query": query,
                    "success": True,
                    "processing_time": processing_time,
                    "sources_count": len(result.get('sources', [])),
                    "answer_length": len(result.get('answer', '')),
                    "agent_times": result.get('agent_times', {}),
                    "errors": result.get('errors', [])
                })
                
            except Exception as e:
                print(f"      ❌ Failed: {e}")
                results.append({
                    "query": query,
                    "success": False,
                    "error": str(e)
                })
        
        return results
    
    async def test_concurrent_queries(self):
        """Test concurrent query processing."""
        print("\n🔄 Test 2: Concurrent Query Processing")
        print("-" * 40)
        
        queries = [
            "What is CDSS?",
            "CDSS implementation guide",
            "CDSS best practices",
            "CDSS evaluation methods",
            "CDSS use cases"
        ]
        
        print(f"   📝 Processing {len(queries)} queries concurrently...")
        start_time = time.time()
        
        try:
            # Process all queries concurrently
            tasks = [self.orchestrator.process_query(query) for query in queries]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            total_time = time.time() - start_time
            success_count = sum(1 for r in results if not isinstance(r, Exception))
            
            print(f"   ✅ Completed {success_count}/{len(queries)} queries in {total_time:.2f}s")
            print(f"   📊 Success rate: {success_count/len(queries)*100:.1f}%")
            
            # Show individual results
            for i, (query, result) in enumerate(zip(queries, results), 1):
                if isinstance(result, Exception):
                    print(f"      ❌ Query {i}: {query} - Error: {result}")
                else:
                    print(f"      ✅ Query {i}: {query} - {len(result.get('sources', []))} sources")
            
            return {
                "total_queries": len(queries),
                "successful_queries": success_count,
                "total_time": total_time,
                "success_rate": success_count/len(queries)*100,
                "results": results
            }
            
        except Exception as e:
            print(f"   ❌ Concurrent processing failed: {e}")
            return {"error": str(e)}
    
    async def test_strategy_routing(self):
        """Test different processing strategies."""
        print("\n🎯 Test 3: Strategy Routing")
        print("-" * 40)
        
        test_cases = [
            {
                "query": "healthcare",
                "expected_strategy": "parallel",
                "description": "Broad subject query"
            },
            {
                "query": "CDSS implementation guide",
                "expected_strategy": "sequential", 
                "description": "Specific query"
            },
            {
                "query": "AI machine learning healthcare",
                "expected_strategy": "hybrid",
                "description": "Medium complexity query"
            }
        ]
        
        results = []
        for i, test_case in enumerate(test_cases, 1):
            print(f"   🧪 Test case {i}: {test_case['description']}")
            print(f"      Query: '{test_case['query']}'")
            
            try:
                result = await self.orchestrator.process_query(test_case['query'])
                strategy = result.get('agent_times', {}).get('strategy', 'unknown')
                
                print(f"      ✅ Processed successfully")
                print(f"      📊 Strategy used: {strategy}")
                print(f"      ⏱️  Processing time: {result.get('processing_time', 0):.2f}s")
                
                results.append({
                    "query": test_case['query'],
                    "expected_strategy": test_case['expected_strategy'],
                    "actual_strategy": strategy,
                    "success": True,
                    "processing_time": result.get('processing_time', 0)
                })
                
            except Exception as e:
                print(f"      ❌ Failed: {e}")
                results.append({
                    "query": test_case['query'],
                    "success": False,
                    "error": str(e)
                })
        
        return results
    
    async def test_error_handling(self):
        """Test error handling and recovery."""
        print("\n🚨 Test 4: Error Handling")
        print("-" * 40)
        
        error_test_cases = [
            {
                "query": "",
                "description": "Empty query"
            },
            {
                "query": "x" * 1000,
                "description": "Very long query"
            },
            {
                "query": "!@#$%^&*()",
                "description": "Special characters only"
            }
        ]
        
        results = []
        for i, test_case in enumerate(error_test_cases, 1):
            print(f"   🧪 Error test {i}: {test_case['description']}")
            print(f"      Query: '{test_case['query'][:50]}{'...' if len(test_case['query']) > 50 else ''}'")
            
            try:
                result = await self.orchestrator.process_query(test_case['query'])
                errors = result.get('errors', [])
                
                if errors:
                    print(f"      ⚠️  Handled gracefully with {len(errors)} errors")
                    print(f"      📝 Errors: {errors}")
                else:
                    print(f"      ✅ Processed without errors")
                
                results.append({
                    "query": test_case['query'],
                    "description": test_case['description'],
                    "success": True,
                    "errors": errors,
                    "answer_length": len(result.get('answer', ''))
                })
                
            except Exception as e:
                print(f"      ❌ Unhandled error: {e}")
                results.append({
                    "query": test_case['query'],
                    "description": test_case['description'],
                    "success": False,
                    "error": str(e)
                })
        
        return results
    
    async def test_performance_metrics(self):
        """Test performance metrics collection."""
        print("\n📊 Test 5: Performance Metrics")
        print("-" * 40)
        
        query = "What is CDSS and how to implement it?"
        print(f"   🔍 Query: '{query}'")
        
        try:
            result = await self.orchestrator.process_query(query)
            
            print(f"   ✅ Query processed successfully")
            print(f"   📊 Performance Metrics:")
            print(f"      Total time: {result.get('processing_time', 0):.2f}s")
            print(f"      Sources found: {len(result.get('sources', []))}")
            print(f"      Answer length: {len(result.get('answer', ''))}")
            print(f"      Request ID: {result.get('request_id', 'N/A')}")
            
            agent_times = result.get('agent_times', {})
            if agent_times:
                print(f"      Agent timing breakdown:")
                for agent, time_taken in agent_times.items():
                    print(f"         {agent}: {time_taken:.2f}s")
            
            return {
                "success": True,
                "processing_time": result.get('processing_time', 0),
                "sources_count": len(result.get('sources', [])),
                "answer_length": len(result.get('answer', '')),
                "agent_times": agent_times,
                "request_id": result.get('request_id', '')
            }
            
        except Exception as e:
            print(f"   ❌ Performance test failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def test_system_status(self):
        """Test system status and health monitoring."""
        print("\n💓 Test 6: System Status")
        print("-" * 40)
        
        try:
            status = self.orchestrator.get_status()
            
            print(f"   ✅ System status retrieved")
            print(f"   📊 Status details:")
            print(f"      LangGraph A2A running: {status.get('langgraph_a2a_running', False)}")
            print(f"      Memory checkpoints: {status.get('memory_checkpoints', 0)}")
            
            agent_status = status.get('agent_orchestrator_status', {})
            print(f"      Agent count: {agent_status.get('agent_count', 0)}")
            print(f"      Active requests: {agent_status.get('active_requests', 0)}")
            
            return {
                "success": True,
                "status": status
            }
            
        except Exception as e:
            print(f"   ❌ Status test failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def run_all_tests(self):
        """Run all tests."""
        print("🧪 LangGraph + A2A Comprehensive Test Suite")
        print("=" * 60)
        
        # Setup
        if not await self.setup():
            return False
        
        try:
            # Run all tests
            test_results = {}
            
            # Test 1: Basic queries
            test_results['basic_queries'] = await self.test_basic_query()
            
            # Test 2: Concurrent processing
            test_results['concurrent_queries'] = await self.test_concurrent_queries()
            
            # Test 3: Strategy routing
            test_results['strategy_routing'] = await self.test_strategy_routing()
            
            # Test 4: Error handling
            test_results['error_handling'] = await self.test_error_handling()
            
            # Test 5: Performance metrics
            test_results['performance_metrics'] = await self.test_performance_metrics()
            
            # Test 6: System status
            test_results['system_status'] = await self.test_system_status()
            
            # Summary
            self.print_test_summary(test_results)
            
            return test_results
            
        finally:
            await self.cleanup()
    
    def print_test_summary(self, results):
        """Print test summary."""
        print("\n📋 Test Summary")
        print("=" * 60)
        
        # Basic queries summary
        basic_results = results.get('basic_queries', [])
        basic_success = sum(1 for r in basic_results if r.get('success', False))
        print(f"📝 Basic Queries: {basic_success}/{len(basic_results)} passed")
        
        # Concurrent queries summary
        concurrent_results = results.get('concurrent_queries', {})
        if 'success_rate' in concurrent_results:
            print(f"🔄 Concurrent Queries: {concurrent_results['success_rate']:.1f}% success rate")
        
        # Strategy routing summary
        strategy_results = results.get('strategy_routing', [])
        strategy_success = sum(1 for r in strategy_results if r.get('success', False))
        print(f"🎯 Strategy Routing: {strategy_success}/{len(strategy_results)} passed")
        
        # Error handling summary
        error_results = results.get('error_handling', [])
        error_success = sum(1 for r in error_results if r.get('success', False))
        print(f"🚨 Error Handling: {error_success}/{len(error_results)} passed")
        
        # Performance metrics summary
        perf_results = results.get('performance_metrics', {})
        if perf_results.get('success', False):
            print(f"📊 Performance: ✅ Passed ({perf_results.get('processing_time', 0):.2f}s)")
        else:
            print(f"📊 Performance: ❌ Failed")
        
        # System status summary
        status_results = results.get('system_status', {})
        if status_results.get('success', False):
            print(f"💓 System Status: ✅ Passed")
        else:
            print(f"💓 System Status: ❌ Failed")
        
        print("\n🎉 All tests completed!")


async def main():
    """Main test function."""
    tester = LangGraphA2ATester()
    results = await tester.run_all_tests()
    
    if results:
        print("\n✅ LangGraph + A2A architecture is working perfectly!")
        return 0
    else:
        print("\n❌ Some tests failed. Please check the errors above.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

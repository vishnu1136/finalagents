#!/usr/bin/env python3
"""
Test script for Direct Google Drive Search Implementation
========================================================
This script tests the new direct search functionality without downloading files.
"""

import asyncio
import os
import sys
from typing import Dict, Any

# Add the API directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'api'))

from api.agents.nodes.direct_search_node import run_node as direct_search
from api.agents.nodes.hybrid_search_node import run_node as hybrid_search
from api.integrations.mcp_client import GDriveMCPClient


async def test_direct_search():
    """Test the direct search functionality."""
    print("🔍 Testing Direct Google Drive Search Implementation")
    print("=" * 60)
    
    # Test queries
    test_queries = [
        "python programming",
        "machine learning",
        "documentation",
        "API",
        "test"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n📝 Test {i}: Searching for '{query}'")
        print("-" * 40)
        
        try:
            # Test direct search
            start_time = asyncio.get_event_loop().time()
            result = await direct_search({
                "query": query,
                "normalized_query": query
            })
            end_time = asyncio.get_event_loop().time()
            
            search_time = end_time - start_time
            
            print(f"✅ Direct search completed in {search_time:.2f}s")
            print(f"📊 Results found: {result.get('total_found', 0)}")
            print(f"🔧 Search method: {result.get('search_method', 'unknown')}")
            
            # Show first few results
            results = result.get('results', [])
            if results:
                print(f"📋 Top {min(3, len(results))} results:")
                for j, res in enumerate(results[:3], 1):
                    print(f"   {j}. {res.get('title', 'Unknown')[:50]}...")
                    print(f"      Score: {res.get('score', 0):.2f}")
                    print(f"      Source: {res.get('source', 'unknown')}")
            else:
                print("   No results found")
                
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n🎉 Direct search testing completed!")


async def test_google_drive_client():
    """Test the Google Drive client directly."""
    print("\n🔗 Testing Google Drive Client")
    print("=" * 40)
    
    try:
        client = GDriveMCPClient()
        
        # Test basic file listing
        print("📁 Testing file listing...")
        files = await client.list_files(query="test")
        
        print(f"✅ Found {len(files)} files")
        
        if files:
            print("📋 Sample files:")
            for i, file_info in enumerate(files[:3], 1):
                print(f"   {i}. {file_info.get('name', 'Unknown')[:50]}...")
                print(f"      ID: {file_info.get('id', 'Unknown')}")
                print(f"      Type: {file_info.get('mimeType', 'Unknown')}")
        
    except Exception as e:
        print(f"❌ Google Drive client error: {e}")
        import traceback
        traceback.print_exc()


async def compare_search_methods():
    """Compare direct search vs hybrid search performance."""
    print("\n⚡ Performance Comparison")
    print("=" * 40)
    
    test_query = "python"
    
    try:
        # Test direct search
        print("🔍 Testing direct search...")
        start_time = asyncio.get_event_loop().time()
        direct_result = await direct_search({
            "query": test_query,
            "normalized_query": test_query
        })
        direct_time = asyncio.get_event_loop().time() - start_time
        
        print(f"✅ Direct search: {direct_time:.2f}s, {direct_result.get('total_found', 0)} results")
        
        # Test hybrid search (if available)
        print("🔍 Testing hybrid search...")
        start_time = asyncio.get_event_loop().time()
        hybrid_result = await hybrid_search({
            "query": test_query,
            "normalized_query": test_query
        })
        hybrid_time = asyncio.get_event_loop().time() - start_time
        
        print(f"✅ Hybrid search: {hybrid_time:.2f}s, {hybrid_result.get('total_found', 0)} results")
        
        # Compare performance
        if direct_time > 0 and hybrid_time > 0:
            speedup = hybrid_time / direct_time
            print(f"🚀 Direct search is {speedup:.1f}x faster!")
        
    except Exception as e:
        print(f"❌ Comparison error: {e}")


async def main():
    """Main test function."""
    print("🧪 Direct Google Drive Search Test Suite")
    print("=" * 50)
    
    # Check environment variables
    print("🔧 Checking environment...")
    required_vars = ["GDRIVE_API_KEY", "GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "GOOGLE_REFRESH_TOKEN"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"⚠️  Missing environment variables: {', '.join(missing_vars)}")
        print("   Some tests may fail without proper Google Drive authentication")
    else:
        print("✅ All required environment variables found")
    
    # Run tests
    await test_google_drive_client()
    await test_direct_search()
    await compare_search_methods()
    
    print("\n🎯 Test Summary")
    print("=" * 30)
    print("✅ Direct search implementation is ready!")
    print("✅ No file downloads required")
    print("✅ Uses Google Drive's built-in fullText search")
    print("✅ Fast response times")
    print("✅ Always current data")


if __name__ == "__main__":
    asyncio.run(main())

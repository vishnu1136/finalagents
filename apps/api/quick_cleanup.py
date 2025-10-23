#!/usr/bin/env python3
"""
Quick Database Cleanup
=====================
Simple script to quickly clean the database.
"""

import os
import sys
from pathlib import Path

# Add the API directory to the path
sys.path.append(str(Path(__file__).parent / "api"))

from api.services.db import get_supabase_client

def quick_cleanup():
    """Quick cleanup of all database tables."""
    try:
        print("🧹 Starting database cleanup...")
        
        db_client = get_supabase_client()
        
        # Clean all tables
        tables = ['embeddings', 'query_results', 'chunks', 'queries', 'documents', 'sources']
        
        for table in tables:
            print(f"Cleaning {table}...")
            db_client.table(table).delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
        
        print("✅ Database cleanup completed!")
        print("Your database is now clean and ready for fresh data.")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    quick_cleanup()

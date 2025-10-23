#!/usr/bin/env python3
"""
Database Cleanup Script
======================
Clears all data from the knowledge base database while preserving table structure.
This will give you a fresh start with the new improved limits.
"""

import os
import sys
from pathlib import Path

# Add the API directory to the path
sys.path.append(str(Path(__file__).parent / "api"))

from api.services.db import get_supabase_client
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def cleanup_database():
    """Clean all data from the database tables."""
    try:
        logger.info("Starting database cleanup...")
        
        # Get Supabase client
        db_client = get_supabase_client()
        
        # Tables to clean in order (respecting foreign key constraints)
        tables_to_clean = [
            'embeddings',      # Has foreign key to chunks
            'query_results',   # Has foreign key to queries and chunks
            'chunks',          # Has foreign key to documents
            'queries',         # Independent table
            'documents',       # Has foreign key to sources
            'sources'          # Independent table
        ]
        
        total_deleted = 0
        
        for table in tables_to_clean:
            try:
                logger.info(f"Cleaning table: {table}")
                
                # Get count before deletion
                count_result = db_client.table(table).select('*', count='exact').execute()
                count = count_result.count if hasattr(count_result, 'count') else len(count_result.data)
                
                if count > 0:
                    # Delete all records
                    delete_result = db_client.table(table).delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
                    logger.info(f"Deleted {count} records from {table}")
                    total_deleted += count
                else:
                    logger.info(f"Table {table} is already empty")
                    
            except Exception as e:
                logger.error(f"Error cleaning table {table}: {e}")
                # Continue with other tables even if one fails
        
        logger.info(f"Database cleanup completed! Total records deleted: {total_deleted}")
        
        # Verify cleanup
        logger.info("Verifying cleanup...")
        for table in tables_to_clean:
            try:
                count_result = db_client.table(table).select('*', count='exact').execute()
                count = count_result.count if hasattr(count_result, 'count') else len(count_result.data)
                logger.info(f"Table {table}: {count} records remaining")
            except Exception as e:
                logger.error(f"Error verifying table {table}: {e}")
        
        logger.info("Database cleanup verification completed!")
        
    except Exception as e:
        logger.error(f"Database cleanup failed: {e}")
        raise

def main():
    """Main function."""
    print("=" * 60)
    print("DATABASE CLEANUP SCRIPT")
    print("=" * 60)
    print("This script will DELETE ALL DATA from your knowledge base database.")
    print("Tables that will be cleaned:")
    print("- embeddings")
    print("- query_results") 
    print("- chunks")
    print("- queries")
    print("- documents")
    print("- sources")
    print("=" * 60)
    
    # Ask for confirmation
    response = input("Are you sure you want to proceed? Type 'YES' to confirm: ")
    
    if response != 'YES':
        print("Cleanup cancelled.")
        return
    
    try:
        cleanup_database()
        print("\n" + "=" * 60)
        print("✅ DATABASE CLEANUP COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print("Your database is now clean and ready for fresh data.")
        print("You can now restart your server and begin indexing files again.")
        print("The new limits (8MB files, 4MB text, 4000 chunks) will be applied.")
        
    except Exception as e:
        print(f"\n❌ Database cleanup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

import os
from typing import Any, Iterable, Sequence, Dict, List
from contextlib import contextmanager
from pathlib import Path
from dotenv import load_dotenv

from supabase import create_client, Client


def _load_env_if_needed():
    """Load environment variables if not already loaded"""
    if not os.getenv("SUPABASE_URL"):
        # Load from default locations
        load_dotenv()
        
        # Try multiple possible paths for the .env file
        possible_paths = [
            Path("apps/.env"),  # From project root
            Path(".env"),  # Current directory
            Path(__file__).resolve().parent.parent.parent.parent / ".env",  # From services -> api -> api -> apps
        ]
        
        for env_path in possible_paths:
            if env_path.exists():
                load_dotenv(dotenv_path=env_path, override=True)
                break


def get_supabase_client() -> Client:
    _load_env_if_needed()
    
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
    
    if not supabase_url or not supabase_key:
        raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set")
    return create_client(supabase_url, supabase_key)


class SupabaseConnection:
    """A wrapper to make Supabase client compatible with psycopg-style usage"""
    
    def __init__(self, client: Client):
        self.client = client
        self._cursor = None
    
    def cursor(self):
        if self._cursor is None:
            self._cursor = SupabaseCursor(self.client)
        return self._cursor
    
    def commit(self):
        # Supabase auto-commits, so this is a no-op
        pass
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


class SupabaseCursor:
    """A cursor-like interface for Supabase client"""
    
    def __init__(self, client: Client):
        self.client = client
        self._last_result = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
    
    def execute(self, sql: str, params: Sequence[Any] | None = None):
        # For now, we'll implement specific queries that are used in the codebase
        # This is a temporary solution - ideally we'd refactor to use Supabase API methods
        
        sql = sql.strip()
        
        if "insert into sources" in sql.lower() and "on conflict do nothing" in sql.lower():
            # Handle source insertion
            try:
                result = self.client.table('sources').insert({
                    'provider': 'gdrive',
                    'name': 'Google Drive'
                }).execute()
                self._last_result = result.data
            except Exception:
                # Ignore conflicts (source already exists)
                self._last_result = []
            return
        
        if "insert into sources" in sql.lower() and "returning id" in sql.lower():
            # Handle source insertion with return
            try:
                params = params or []
                if len(params) >= 2:
                    provider, name = params
                    result = self.client.table('sources').insert({
                        'provider': provider,
                        'name': name
                    }).execute()
                    self._last_result = result.data
                else:
                    self._last_result = []
            except Exception as e:
                print(f"Error inserting source: {e}")
                self._last_result = []
            return
        
        if "select e.chunk_id, e.embedding" in sql.lower() and "from embeddings e" in sql.lower():
            # Handle the search query from search_node.py
            try:
                result = self.client.table('embeddings') \
                    .select('chunk_id, embedding, chunks!inner(text, documents!inner(title, url))') \
                    .limit(2000) \
                    .execute()
                
                # Transform the result to match expected format
                transformed_rows = []
                for row in result.data:
                    chunks_data = row.get('chunks')
                    if chunks_data and chunks_data.get('documents'):
                        transformed_rows.append({
                            'chunk_id': row['chunk_id'],
                            'embedding': row['embedding'],
                            'text': chunks_data['text'],
                            'title': chunks_data['documents']['title'],
                            'url': chunks_data['documents']['url']
                        })
                self._last_result = transformed_rows
            except Exception as e:
                print(f"Error executing search query: {e}")
                # Return empty result if no data or on error
                self._last_result = []
            return
        
        if "insert into documents" in sql.lower() and "on conflict" in sql.lower():
            # Handle document insertion with upsert
            try:
                # Extract parameters from the SQL (this is a simplified approach)
                # In a real implementation, you'd parse the SQL properly
                params = params or []
                if len(params) >= 5:
                    title, mime_type, file_id, url, checksum = params
                    
                    # First, get the source_id
                    source_result = self.client.table('sources').select('id').eq('provider', 'gdrive').execute()
                    if source_result.data:
                        source_id = source_result.data[0]['id']
                        
                        # Upsert document
                        doc_data = {
                            'source_id': source_id,
                            'title': title,
                            'mime_type': mime_type,
                            'drive_file_id': file_id,
                            'url': url,
                            'checksum': checksum
                        }
                        
                        # Try to insert, if conflict then update
                        try:
                            result = self.client.table('documents').insert(doc_data).execute()
                            self._last_result = result.data
                        except Exception:
                            # If insert fails due to conflict, update instead
                            result = self.client.table('documents').update({
                                'title': title,
                                'mime_type': mime_type,
                                'url': url,
                                'checksum': checksum
                            }).eq('drive_file_id', file_id).execute()
                            self._last_result = result.data
                    else:
                        self._last_result = []
                else:
                    self._last_result = []
            except Exception as e:
                print(f"Error inserting document: {e}")
                self._last_result = []
            return
        
        if "delete from chunks where document_id" in sql.lower():
            # Handle chunk deletion
            try:
                params = params or []
                if params:
                    document_id = params[0]
                    result = self.client.table('chunks').delete().eq('document_id', document_id).execute()
                    self._last_result = result.data
                else:
                    self._last_result = []
            except Exception as e:
                print(f"Error deleting chunks: {e}")
                self._last_result = []
            return
        
        if "insert into chunks" in sql.lower() and "returning id" in sql.lower():
            # Handle chunk insertion
            try:
                params = params or []
                if len(params) >= 4:
                    document_id, chunk_index, text, token_count = params
                    chunk_data = {
                        'document_id': document_id,
                        'chunk_index': chunk_index,
                        'text': text,
                        'token_count': token_count
                    }
                    result = self.client.table('chunks').insert(chunk_data).execute()
                    self._last_result = result.data
                else:
                    self._last_result = []
            except Exception as e:
                print(f"Error inserting chunk: {e}")
                self._last_result = []
            return
        
        if "select id, text from chunks where document_id" in sql.lower():
            # Handle chunk selection
            try:
                params = params or []
                if params:
                    document_id = params[0]
                    result = self.client.table('chunks').select('id, text').eq('document_id', document_id).order('chunk_index').execute()
                    self._last_result = result.data
                else:
                    self._last_result = []
            except Exception as e:
                print(f"Error selecting chunks: {e}")
                self._last_result = []
            return
        
        if "delete from embeddings where chunk_id" in sql.lower():
            # Handle embedding deletion
            try:
                params = params or []
                if params:
                    chunk_ids = params[0] if isinstance(params[0], list) else [params[0]]
                    result = self.client.table('embeddings').delete().in_('chunk_id', chunk_ids).execute()
                    self._last_result = result.data
                else:
                    self._last_result = []
            except Exception as e:
                print(f"Error deleting embeddings: {e}")
                self._last_result = []
            return
        
        if "insert into embeddings" in sql.lower():
            # Handle embedding insertion
            try:
                params = params or []
                if len(params) >= 3:
                    chunk_id, embedding, model = params
                    embedding_data = {
                        'chunk_id': chunk_id,
                        'embedding': embedding,
                        'model': model
                    }
                    result = self.client.table('embeddings').insert(embedding_data).execute()
                    self._last_result = result.data
                else:
                    self._last_result = []
            except Exception as e:
                print(f"Error inserting embedding: {e}")
                self._last_result = []
            return
        
        if "select id from sources where provider" in sql.lower():
            # Handle source selection
            try:
                params = params or []
                if params:
                    provider = params[0]
                    result = self.client.table('sources').select('id').eq('provider', provider).limit(1).execute()
                    self._last_result = result.data
                else:
                    self._last_result = []
            except Exception as e:
                print(f"Error selecting source: {e}")
                self._last_result = []
            return
        
        if "insert into documents" in sql.lower() and "returning id" in sql.lower():
            # Handle document insertion with return
            try:
                params = params or []
                if len(params) >= 4:
                    source_id, title, url, checksum = params
                    doc_data = {
                        'source_id': source_id,
                        'title': title,
                        'url': url,
                        'checksum': checksum
                    }
                    result = self.client.table('documents').insert(doc_data).execute()
                    self._last_result = result.data
                else:
                    self._last_result = []
            except Exception as e:
                print(f"Error inserting document: {e}")
                self._last_result = []
            return
        
        if "select d.drive_file_id, d.title, d.url, d.updated_at from documents d where d.drive_file_id = any" in sql.lower():
            # Handle checking existing files
            try:
                params = params or []
                if params:
                    file_ids = params[0]
                    result = self.client.table('documents').select('drive_file_id, title, url, updated_at').in_('drive_file_id', file_ids).execute()
                    self._last_result = result.data
                else:
                    self._last_result = []
            except Exception as e:
                print(f"Error checking existing files: {e}")
                self._last_result = []
            return
        
        # For other queries, we'll need to implement them as needed
        print(f"Warning: SQL query not implemented: {sql[:100]}...")
        self._last_result = []
    
    def executemany(self, sql: str, params_seq: Iterable[Sequence[Any]]):
        raise NotImplementedError("executemany not yet implemented for Supabase")
    
    def fetchall(self):
        return self._last_result or []
    
    def fetchone(self):
        if self._last_result and len(self._last_result) > 0:
            return self._last_result[0]
        return None


def get_connection() -> SupabaseConnection:
    """Returns a connection-like wrapper around Supabase client"""
    client = get_supabase_client()
    return SupabaseConnection(client)


def executemany(sql: str, params_seq: Iterable[Sequence[Any]]) -> None:
    # Note: This function may need to be refactored based on specific use cases
    # Supabase client doesn't directly support executemany with raw SQL
    # Consider using individual insert operations or batch inserts via the API
    supabase = get_supabase_client()
    # Implementation depends on the specific SQL being executed
    raise NotImplementedError("executemany needs to be refactored for Supabase client usage")


def execute(sql: str, params: Sequence[Any] | None = None) -> None:
    # Note: This function may need to be refactored based on specific use cases
    # Supabase client doesn't directly support raw SQL execution
    # Consider using the Supabase API methods instead
    supabase = get_supabase_client()
    # Implementation depends on the specific SQL being executed
    raise NotImplementedError("execute needs to be refactored for Supabase client usage")



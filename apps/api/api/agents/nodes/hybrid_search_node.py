from typing import Any, Dict, List
import hashlib
import os
from api.services import db
from api.services.db import get_supabase_client
from api.services.embedding import embed_texts
from api.integrations.mcp_client import GDriveMCPClient
import numpy as np


TOP_K = 100


async def run_node(inputs: Dict[str, Any]) -> Dict[str, Any]:
    query = inputs.get("normalized_query") or inputs.get("query")
    if not query:
        return {"results": []}
    
    print(f"Searching with normalized query: '{query}'")
    
    # Step 1: First try to search the database for existing content
    db_results = await search_database(query)
    print(f"Found {len(db_results)} results in database")
    
    # Step 2: Search Google Drive for files matching the query (only if we have few DB results)
    drive_files = []
    if len(db_results) < 3:  # Only search Drive if we don't have enough DB results
        client = GDriveMCPClient()
        try:
            drive_files = await client.list_files(query=query)
            print(f"Found {len(drive_files)} files in Google Drive matching '{query}'")
        except Exception as e:
            print(f"Error searching Google Drive: {e}")
            drive_files = []
    
    if not drive_files and not db_results:
        return {"results": []}
    
    # Step 3: Process new/updated files from Google Drive (if any)
    new_files = []
    if drive_files:
        # Check which files are already in database
        file_ids = [f.get("id") for f in drive_files if f.get("id")]
        existing_files = await check_existing_files(file_ids)
        
        print(f"Found {len(existing_files)} existing files in database out of {len(drive_files)} total files")
        for file_info in drive_files:
            file_id = file_info.get("id")
            if not file_id:
                continue
                
            # Check if file exists in database and is up-to-date
            if file_id in existing_files:
                existing_file = existing_files[file_id]
                print(f"File {file_info.get('name', 'Unknown')} already exists in database, skipping")
                # Check if file was updated (you could compare timestamps here)
                # For now, we'll assume existing files are up-to-date
                continue
            
            # Process new file
            try:
                print(f"Processing new file: {file_info.get('name', 'Unknown')}")
                processed_file = await process_new_file(client, file_info)
                if processed_file:
                    print(f"Successfully processed file: {file_info.get('name', 'Unknown')}")
                    new_files.append(processed_file)
                else:
                    print(f"Failed to process file: {file_info.get('name', 'Unknown')}")
            except Exception as e:
                print(f"Error processing file {file_id}: {e}")
                import traceback
                traceback.print_exc()
                continue
    
    # Step 4: Add results from newly processed files
    new_results = []
    if new_files:
        # Generate query embedding once
        query_embedding = np.array(embed_texts([query])[0], dtype=float)
        
        for file_data in new_files:
            if file_data.get("chunks"):
                for chunk in file_data["chunks"]:
                    # Calculate similarity score
                    chunk_embedding = np.array(chunk["embedding"], dtype=float)
                    score = cosine_similarity(query_embedding, chunk_embedding)
                    
                    new_results.append({
                        "chunk_id": chunk["id"],
                        "title": file_data["title"],
                        "url": file_data["url"],
                        "snippet": chunk["text"][:300],
                        "score": score,
                    })
    
    # Combine all results and sort by score
    all_results = db_results + new_results
    all_results.sort(key=lambda x: x["score"], reverse=True)
    
    print(f"Total results: {len(all_results)} (DB: {len(db_results)}, New: {len(new_results)})")
    
    return {"results": all_results[:TOP_K]}


async def check_existing_files(file_ids: List[str]) -> Dict[str, Any]:
    """Check which files already exist in the database"""
    if not file_ids:
        return {}
    
    try:
        # Use Supabase client directly
        db_client = get_supabase_client()
        result = db_client.table('documents').select('drive_file_id, title, url, updated_at').in_('drive_file_id', file_ids).execute()
        
        existing = {}
        for row in result.data:
            existing[row["drive_file_id"]] = {
                "title": row["title"],
                "url": row["url"],
                "updated_at": row["updated_at"]
            }
        return existing
    except Exception as e:
        print(f"Error checking existing files: {e}")
        return {}


async def process_new_file(client: GDriveMCPClient, file_info: Dict[str, Any]) -> Dict[str, Any]:
    """Process a new file from Google Drive and store it in the database"""
    file_id = file_info.get("id")
    title = file_info.get("name", "Unknown")
    url = file_info.get("webViewLink", "")
    mime_type = file_info.get("mimeType", "")
    
    try:
        # Download file content
        file_content = await client.get_file(file_id)
        text = file_content.get("text", "")
        
        if not text:
            print(f"No text content found for file {file_id}")
            return None
        
        # Calculate checksum
        checksum = hashlib.sha256(text.encode("utf-8")).hexdigest()
        
        # Use Supabase client directly
        db_client = get_supabase_client()
        
        # Ensure source exists
        source_result = db_client.table('sources').select('id').eq('provider', 'gdrive').execute()
        if not source_result.data:
            source_result = db_client.table('sources').insert({
                'provider': 'gdrive',
                'name': 'Google Drive'
            }).execute()
        source_id = source_result.data[0]['id']
        
        # Insert document
        doc_result = db_client.table('documents').insert({
            'source_id': source_id,
            'title': title,
            'mime_type': mime_type,
            'drive_file_id': file_id,
            'url': url,
            'checksum': checksum
        }).execute()
        
        if not doc_result.data:
            print(f"Failed to insert document {file_id}")
            return None
        
        document_id = doc_result.data[0]['id']
        
        # Create chunks
        chunk_size = 2000
        overlap = 200
        chunks = []
        i = 0
        while i < len(text):
            chunks.append(text[i : i + chunk_size])
            i += chunk_size - overlap
        
        # Insert chunks
        db_client.table('chunks').delete().eq('document_id', document_id).execute()
        
        chunk_data = []
        for idx, chunk_text in enumerate(chunks):
            chunk_result = db_client.table('chunks').insert({
                'document_id': document_id,
                'chunk_index': idx,
                'text': chunk_text,
                'token_count': len(chunk_text.split())
            }).execute()
            
            if chunk_result.data:
                chunk_data.append({
                    'id': chunk_result.data[0]['id'],
                    'text': chunk_text
                })
        
        # Generate embeddings in batches
        if chunk_data:
            print(f"Generating embeddings for {len(chunk_data)} chunks...")
            embeddings = embed_texts([chunk['text'] for chunk in chunk_data])
            
            # Insert embeddings
            db_client.table('embeddings').delete().in_('chunk_id', [chunk['id'] for chunk in chunk_data]).execute()
            
            # Batch insert embeddings
            embedding_data = []
            for chunk, embedding in zip(chunk_data, embeddings):
                embedding_data.append({
                    'chunk_id': chunk['id'],
                    'embedding': embedding,
                    'model': os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
                })
            
            # Insert all embeddings at once
            db_client.table('embeddings').insert(embedding_data).execute()
            print(f"Successfully inserted {len(embedding_data)} embeddings")
        
        return {
            "title": title,
            "url": url,
            "chunks": [{"id": chunk['id'], "text": chunk['text'], "embedding": emb} 
                      for chunk, emb in zip(chunk_data, embeddings)]
        }
        
    except Exception as e:
        print(f"Error processing file {file_id}: {e}")
        import traceback
        traceback.print_exc()
        return None


async def search_database(query: str) -> List[Dict[str, Any]]:
    """Search the database for relevant chunks"""
    try:
        # Generate query embedding
        query_embedding = np.array(embed_texts([query])[0], dtype=float)
        
        with db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    select e.chunk_id, e.embedding, d.title, d.url, c.text
                    from embeddings e
                    join chunks c on c.id = e.chunk_id
                    join documents d on d.id = c.document_id
                    limit 2000
                """)
                rows = cur.fetchall()
        
        results = []
        for r in rows:
            # Handle both string and list formats for embeddings
            embedding = r["embedding"]
            if isinstance(embedding, str):
                import json
                try:
                    emb = np.array(json.loads(embedding), dtype=float)
                except (json.JSONDecodeError, ValueError):
                    continue
            else:
                emb = np.array(embedding, dtype=float)
            
            score = cosine_similarity(query_embedding, emb)
            results.append({
                "chunk_id": r["chunk_id"],
                "title": r["title"],
                "url": r["url"],
                "snippet": r["text"][:300],
                "score": score,
            })
        
        return results
    except Exception as e:
        print(f"Error searching database: {e}")
        return []


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Calculate cosine similarity between two vectors"""
    denom = (np.linalg.norm(a) * np.linalg.norm(b))
    return float(np.dot(a, b) / denom) if denom != 0 else 0.0

from typing import Any, Dict, List

from api.services import db
from api.services.embedding import embed_texts
import numpy as np


TOP_K = 5


async def run_node(inputs: Dict[str, Any]) -> Dict[str, Any]:
    query = inputs.get("normalized_query") or inputs.get("query")
    if not query:
        return {"results": []}
    # Embed query and compute cosine similarity in Python vs stored vectors
    q_vec = np.array(embed_texts([query])[0], dtype=float)
    with db.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                select e.chunk_id, e.embedding, d.title, d.url, c.text
                from embeddings e
                join chunks c on c.id = e.chunk_id
                join documents d on d.id = c.document_id
                limit 2000
                """
            )
            rows = cur.fetchall()
    def cosine(a: np.ndarray, b: np.ndarray) -> float:
        denom = (np.linalg.norm(a) * np.linalg.norm(b))
        return float(np.dot(a, b) / denom) if denom != 0 else 0.0
    scored = []
    for r in rows:
        # Handle both string and list formats for embeddings
        embedding = r["embedding"]
        if isinstance(embedding, str):
            # Parse string representation of array
            import json
            try:
                emb = np.array(json.loads(embedding), dtype=float)
            except (json.JSONDecodeError, ValueError):
                # If parsing fails, skip this embedding
                continue
        else:
            emb = np.array(embedding, dtype=float)
        
        score = cosine(q_vec, emb)
        scored.append({
            "chunk_id": r["chunk_id"],
            "title": r["title"],
            "url": r["url"],
            "snippet": r["text"][:300],
            "score": score,
        })
    scored.sort(key=lambda x: x["score"], reverse=True)
    return {"results": scored[:TOP_K]}



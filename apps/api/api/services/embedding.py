import os
from typing import List

import numpy as np
from openai import OpenAI


MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")


def embed_texts(texts: List[str]) -> List[List[float]]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        # Fallback: simple hashing-based pseudo-embedding for local dev without API key
        return [_hash_embed(t) for t in texts]
    client = OpenAI(api_key=api_key)
    resp = client.embeddings.create(model=MODEL, input=texts)
    return [d.embedding for d in resp.data]


def _hash_embed(text: str, dim: int = 1536) -> List[float]:
    rng = np.random.default_rng(abs(hash(text)) % (2**32))
    vec = rng.normal(size=dim)
    norm = np.linalg.norm(vec)
    return (vec / (norm if norm != 0 else 1.0)).astype(float).tolist()



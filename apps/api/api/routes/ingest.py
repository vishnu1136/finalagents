from fastapi import APIRouter
from pydantic import BaseModel

from api.integrations.mcp_client import GDriveMCPClient
from api.services import db
from api.services.embedding import embed_texts
import hashlib
import os
from typing import List

router = APIRouter()


class SyncRequest(BaseModel):
    query: str | None = None
    mime_types: list[str] | None = None
    updated_after: str | None = None


@router.post("/gdrive/sync")
async def gdrive_sync(body: SyncRequest) -> dict:
    client = GDriveMCPClient()
    files = await client.list_files(query=body.query, mime_types=body.mime_types, updated_after=body.updated_after)
    created = 0
    # Ensure a default source exists
    with db.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("insert into sources (provider, name) values ('gdrive','Google Drive') on conflict do nothing")
        conn.commit()
    for f in files:
        file_id = f.get("id")
        title = f.get("name")
        url = f.get("webViewLink") or f.get("alternateLink")
        mime_type = f.get("mimeType")
        file = await client.get_file(file_id)
        text: str = file.get("text", "")
        checksum = hashlib.sha256(text.encode("utf-8")).hexdigest()

        # Upsert document
        with db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    insert into documents (source_id, title, mime_type, drive_file_id, url, checksum)
                    values (
                        (select id from sources where provider='gdrive' limit 1), %s, %s, %s, %s, %s
                    )
                    on conflict (drive_file_id) do update set title=excluded.title, mime_type=excluded.mime_type,
                      url=excluded.url, checksum=excluded.checksum, updated_at=now()
                    returning id
                    """,
                    (title, mime_type, file_id, url, checksum),
                )
                doc_id_row = cur.fetchone()
                if not doc_id_row:
                    continue
                document_id = doc_id_row["id"]

                # Simple chunking (characters)
                chunk_size = 2000
                overlap = 200
                chunks: List[str] = []
                i = 0
                while i < len(text):
                    chunks.append(text[i : i + chunk_size])
                    i += chunk_size - overlap

                # Insert chunks
                cur.execute("delete from chunks where document_id=%s", (document_id,))
                for idx, chunk_text in enumerate(chunks):
                    cur.execute(
                        "insert into chunks (document_id, chunk_index, text, token_count) values (%s, %s, %s, %s) returning id",
                        (document_id, idx, chunk_text, len(chunk_text.split())),
                    )
                created += 1

        # Embeddings for latest chunks
        with db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("select id, text from chunks where document_id=%s order by chunk_index", (document_id,))
                rows = cur.fetchall()
                if rows:
                    embeds = embed_texts([r["text"] for r in rows])
                    cur.execute("delete from embeddings where chunk_id = any(%s)", ([r["id"] for r in rows],))
                    for row, emb in zip(rows, embeds):
                        cur.execute(
                            "insert into embeddings (chunk_id, embedding, model) values (%s, %s, %s)",
                            (row["id"], emb, os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")),
                        )
            conn.commit()

    return {"processed_documents": created}



<!-- 8615ffac-3809-47f5-98a6-79dfcba4284c 6397e658-7d55-4431-aed9-12aa84305000 -->
# Internal Knowledge Base Navigator (MVP)

## Scope

- Source: Google Drive only (no auth/ACLs; public/dev service account scope)
- Pipeline: Query Understanding → Search → Answer Generation → Source Linking (Sequential)
- Stack: Next.js (React), FastAPI, Supabase (Postgres + Vector), LangGraph, MCP, A2A

## High-level Architecture

- Next.js app `apps/web` calls FastAPI `apps/api` endpoints
- FastAPI orchestrates LangGraph agents; stores docs, chunks, and embeddings in Supabase
- MCP server provides Google Drive document listing and content retrieval to Search/ingestion
- A2A used as the message envelope for inter-agent calls inside LangGraph nodes

## Supabase schema (Postgres + pgvector)

- `sources` (id, provider, external_id, name)
- `documents` (id, source_id, title, mime_type, drive_file_id, url, checksum, created_at, updated_at)
- `chunks` (id, document_id, chunk_index, text, token_count)
- `embeddings` (id, chunk_id, embedding vector, model, created_at)
- `queries` (id, query_text, created_at)
- `query_results` (id, query_id, chunk_id, score)

Minimal DDL (abbrev):

```sql
create table sources (
  id uuid primary key default gen_random_uuid(),
  provider text not null check (provider in ('gdrive')),
  external_id text,
  name text
);
create table documents (
  id uuid primary key default gen_random_uuid(),
  source_id uuid references sources(id),
  title text,
  mime_type text,
  drive_file_id text unique,
  url text,
  checksum text,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);
create table chunks (
  id uuid primary key default gen_random_uuid(),
  document_id uuid references documents(id) on delete cascade,
  chunk_index int not null,
  text text not null,
  token_count int
);
create extension if not exists vector;
create table embeddings (
  id uuid primary key default gen_random_uuid(),
  chunk_id uuid references chunks(id) on delete cascade,
  embedding vector(1536),
  model text,
  created_at timestamptz default now()
);
create index on embeddings using ivfflat (embedding vector_cosine_ops);
create table queries (
  id uuid primary key default gen_random_uuid(),
  query_text text not null,
  created_at timestamptz default now()
);
create table query_results (
  id uuid primary key default gen_random_uuid(),
  query_id uuid references queries(id) on delete cascade,
  chunk_id uuid references chunks(id) on delete cascade,
  score float8
);
```

## Backend (FastAPI) – `apps/api`

- `api/main.py`: app factory, CORS, router mount
- `api/routes/ingest.py`:
  - POST `/ingest/gdrive/sync` → list files via MCP, fetch content, upsert docs/chunks, queue embeddings
- `api/routes/search.py`:
  - POST `/search` { query } → run LangGraph pipeline, return answer + citations
- `api/routes/admin.py`:
  - GET `/healthz`
- `api/services/db.py`: Supabase/Postgres client + SQL helpers
- `api/services/embedding.py`: embed texts (OpenAI/Local) and persist vectors
- `api/agents/graph.py`: LangGraph definition
- `api/agents/nodes/*.py`:
  - `query_understanding_node.py`
  - `search_node.py` (vector search over `embeddings` joined to `chunks`/`documents`)
  - `answer_generation_node.py`
  - `source_linking_node.py`
- `api/protocol/a2a.py`: A2A message schemas + helpers
- `api/integrations/mcp_client.py`: MCP client for Google Drive server

Key FastAPI contracts:

```python
# POST /search
{
  "query": "How do we request PTO?"
}
-> {
  "answer": "...",
  "sources": [{"title":"PTO Policy","url":"https://drive.google.com/file/...","snippet":"..."}]
}
```

## Agents with LangGraph – `api/agents/graph.py`

- Graph nodes wire as: `understand` → `search` → `answer` → `link`
- Each node receives/returns an A2A-like envelope:
```python
{
  "type": "agent_message",
  "from": "web",
  "to": "search_agent",
  "payload": {...},
  "trace_id": "..."
}
```

- `search_node` uses SQL cosine similarity over `embeddings.embedding` and returns top-k chunks with doc refs
- `answer_generation_node` builds RAG prompt from chunks

## MCP – Google Drive

- Add an MCP server providing tools:
  - `gdrive.list_files(query, mime_types, updated_after)`
  - `gdrive.get_file(file_id)` → text content (convert docx/gdoc via export)
- `api/integrations/mcp_client.py` calls these tools for ingestion
- For MVP, scope to Google Docs and PDFs; use text extraction via export APIs

## A2A (Agent-to-Agent) usage

- Define lightweight Pydantic models in `api/protocol/a2a.py` for message envelopes
- Inside LangGraph nodes, wrap inputs/outputs with A2A envelopes for clarity and future inter-process agents

## Frontend (Next.js) – `apps/web`

- `app/page.tsx`: query input, answer display, sources list
- `components/SearchBox.tsx`: input + submit
- `components/Answer.tsx`: renders markdown
- `components/Sources.tsx`: list of titles/links/snippets
- Calls FastAPI `/search`
- `pages/api/ingest` (optional proxy) or run ingest from backend only

Minimal UI event flow:

```ts
const res = await fetch("/api/search", { method: "POST", body: JSON.stringify({ query }) });
```

## Ingestion flow

1) Trigger `/ingest/gdrive/sync` (manual button or cron)

2) List GDrive files via MCP

3) For each file: fetch content, text normalize, chunk (e.g., 1k tokens, 200 overlap)

4) Upsert `documents`, `chunks`

5) Batch embed new chunks → `embeddings`

## Configuration

- `.env` (backend): SUPABASE_URL, SUPABASE_KEY, DATABASE_URL, OPENAI_API_KEY (or local embedding), GDRIVE_* (for MCP server), CORS_ORIGIN
- `.env` (web): API_BASE_URL

## Testing & Observability

- Unit tests for chunking, vector search, and graph node I/O
- Basic tracing IDs in A2A envelopes and logs per node

## Deliverables

- Next.js app with search UI
- FastAPI with ingestion + search endpoints
- Supabase SQL migration
- LangGraph agent pipeline with A2A envelopes
- MCP GDrive integration

### To-dos

- [ ] Create Supabase schema and vector index for documents/chunks/embeddings
- [ ] Add MCP server/client to list and fetch Google Drive files
- [ ] Build FastAPI ingestion endpoint using MCP and chunking/upsert
- [ ] Embed chunks and write vectors to pgvector via Supabase
- [ ] Implement cosine similarity SQL over embeddings joined to docs/chunks
- [ ] Create LangGraph graph with four nodes and A2A envelopes
- [ ] Expose POST /search to run graph and return answer + sources
- [ ] Build minimal Next.js UI: input, answer, sources list
- [ ] Wire .env config for Supabase, embeddings, and MCP GDrive
- [ ] Add unit tests and basic tracing/logging for nodes and endpoints



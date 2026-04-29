# AI Conversation Summarizer

REST API that ingests customer-service conversation transcripts, runs OpenAI
analysis (summary, sentiment, key topics), and persists the results in
PostgreSQL for retrieval and search.

Built with **Python 3.12 · FastAPI · SQLAlchemy · PostgreSQL · OpenAI · Docker**.

---

## Architecture

```
            +-------------------+
   client → |  FastAPI service  | ──► OpenAI (gpt-4o-mini, structured JSON)
            |   (uvicorn)       |
            +---------+---------+
                      │
                      ▼
              PostgreSQL 16
              (conversations table)
```

Layered code:

```
app/
├── main.py             FastAPI app + exception handlers
├── config.py           env-driven Pydantic Settings
├── database.py         SQLAlchemy engine / session
├── models.py           Conversation ORM model
├── schemas.py          Pydantic I/O schemas
├── routers/
│   └── conversations.py      4 endpoints
└── services/
    ├── aiService.py          OpenAI wrapper (mockable)
    └── conversationService.py DB operations
```

---

## Quickstart

```bash
git clone <this repo>
cd convSummarizer
cp .env.example .env          # set OPENAI_API_KEY
docker compose up --build
```

The API is now live at `http://localhost:8000` and migrations have been applied
automatically. Visit `http://localhost:8000/docs` for the interactive Swagger UI.

---

## Endpoints

### `POST /conversations`

Submit a transcript. Triggers a synchronous OpenAI analysis and stores the
result.

```bash
curl -X POST http://localhost:8000/conversations \
  -H 'Content-Type: application/json' \
  -d '{
    "rawTranscript": "Customer: My internet has been down for two hours. Agent: I am very sorry, let me check your line right now."
  }'
```

Response `201`:

```json
{
  "id": "1d7e2d5e-2c1a-4f6b-9e2a-9b1f1f5e2a4c",
  "rawTranscript": "Customer: My internet has been down ...",
  "summary": "The customer reported a two-hour internet outage. The agent apologized and began checking the line.",
  "sentimentLabel": "negative",
  "sentimentScore": -0.4,
  "keyTopics": ["internet outage", "customer support", "troubleshooting"],
  "createdAt": "2026-04-29T16:42:11.123456+00:00"
}
```

### `GET /conversations/{id}`

```bash
curl http://localhost:8000/conversations/1d7e2d5e-2c1a-4f6b-9e2a-9b1f1f5e2a4c
```

### `GET /conversations`

Paginated list, ordered by `createdAt DESC`.

```bash
curl 'http://localhost:8000/conversations?limit=20&offset=0'
```

### `GET /conversations/search?q=`

Case-insensitive substring search across `rawTranscript` and `summary`.

```bash
curl 'http://localhost:8000/conversations/search?q=refund'
```

---

## Environment variables

| Name | Description | Default |
|---|---|---|
| `OPENAI_API_KEY` | OpenAI API key | — (required) |
| `OPENAI_MODEL` | Chat model name | `gpt-4o-mini` |
| `databaseUrl` | SQLAlchemy database URL | `postgresql+psycopg://postgres:postgres@db:5432/convsummarizer` |
| `appEnv` | Free-form environment label | `development` |

---

## Running tests

```bash
pip install -e ".[dev]"
# requires a local Postgres reachable via $databaseUrl
alembic upgrade head
pytest --cov=app --cov-report=term-missing
```

CI runs the full suite on every push and PR with an 85% coverage gate.

---

## Production extensions (out of scope for this demo)

- **Async job queue** — replace the synchronous OpenAI call in `POST /conversations`
  with a Celery / RQ worker (Redis broker). The endpoint would return `202`
  immediately with a `pending` row; clients poll `GET /conversations/{id}` for
  the final analysis. This unlocks retries, backpressure, and horizontal scaling
  of workers independent of the API.
- **Postgres full-text search** — swap the ILIKE search for a `tsvector` column
  with a GIN index for ranked results.
- **Per-speaker sentiment** — extend the AI schema to emit
  `{ "agent": "...", "customer": "..." }` for richer contact-center analytics.
- **AuthN/AuthZ + multi-tenancy** — add OAuth2 / API keys and a `tenantId`
  column with row-level security.
- **Streaming responses** — stream summaries token-by-token via SSE for live
  agent-assist use cases.

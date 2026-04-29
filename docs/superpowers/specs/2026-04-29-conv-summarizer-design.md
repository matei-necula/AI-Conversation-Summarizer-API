# AI Conversation Summarizer — Design Spec

**Date:** 2026-04-29
**Author:** mateictaro@gmail.com
**Purpose:** REST API that ingests customer-service conversation transcripts, runs OpenAI analysis (summary, sentiment, topics), and persists results in Postgres for retrieval and search. Built as a portfolio project for a Cresta internship application.

## Tech Stack

- Python 3.12, FastAPI, SQLAlchemy 2.x, Alembic, Pydantic v2
- PostgreSQL 16
- OpenAI Python SDK (`gpt-4o-mini`, structured output via JSON schema)
- Docker + Docker Compose
- pytest, pytest-cov, httpx, ruff
- GitHub Actions CI

## Conventions

- **camelCase** identifiers throughout the Python code (overrides PEP 8 per project preference). Database column names also camelCase (quoted in SQL).
- No code comments unless a non-obvious WHY is required.

## Architecture

Layered FastAPI service with a single Postgres dependency. Synchronous OpenAI calls inside `POST /conversations`. Async/queue-based processing (Celery, RQ, or FastAPI BackgroundTasks) is documented in the README as a production extension but is out of scope.

```
convSummarizer/
├── app/
│   ├── main.py              # FastAPI app, router wiring, lifespan
│   ├── config.py            # Pydantic Settings (env-driven)
│   ├── database.py          # SQLAlchemy engine, session, Base
│   ├── models.py            # Conversation ORM model
│   ├── schemas.py           # Pydantic request/response models
│   ├── routers/
│   │   └── conversations.py # 4 endpoints
│   ├── services/
│   │   ├── aiService.py     # OpenAI wrapper (mockable)
│   │   └── conversationService.py
│   └── exceptions.py        # Custom exceptions + handlers
├── alembic/                 # migrations
├── tests/
│   ├── conftest.py
│   ├── test_endpoints.py
│   ├── test_aiService.py
│   └── test_errors.py
├── .github/workflows/ci.yml
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
├── .env.example
└── README.md
```

**Boundaries:**
- Routers handle HTTP only (validation, status codes, dependency injection).
- `conversationService` orchestrates DB operations and AI calls.
- `aiService` is the only module that imports the OpenAI SDK; tests inject a stub via dependency override.

## Data Model

Postgres table `conversations`:

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | `gen_random_uuid()` default |
| `rawTranscript` | TEXT NOT NULL | original input |
| `summary` | TEXT NOT NULL | AI-generated, 2–3 sentences |
| `sentimentLabel` | VARCHAR(16) NOT NULL | `positive` / `neutral` / `negative` |
| `sentimentScore` | DOUBLE PRECISION NOT NULL | range `-1.0 .. 1.0` |
| `keyTopics` | JSONB NOT NULL | array of lowercase strings |
| `createdAt` | TIMESTAMPTZ NOT NULL | default `now()` |

**Indexes:** PK on `id`; B-tree on `createdAt` for descending list ordering.

**Migration:** single Alembic revision creates the table and indexes. Compose runs `alembic upgrade head` on container start.

## Pydantic Schemas

- `ConversationCreate`: `{ rawTranscript: str }` (`min_length=1`, stripped, must be non-whitespace)
- `ConversationOut`: `{ id, rawTranscript, summary, sentimentLabel, sentimentScore, keyTopics, createdAt }` — camelCase serialized
- `ConversationList`: `{ items: list[ConversationOut], total: int }`
- `AiAnalysis` (internal): `{ summary, sentimentLabel, sentimentScore, keyTopics }`

## AI Service

Single OpenAI call per request using structured output (JSON schema response format). Model: `gpt-4o-mini`.

System prompt:
```
You analyze customer-service conversation transcripts.
Return JSON matching the schema:
- summary: 2-3 sentence neutral summary
- sentimentLabel: one of positive|neutral|negative (overall customer sentiment)
- sentimentScore: float in [-1.0, 1.0]
- keyTopics: 3-6 short topic tags, lowercase
```

`aiService.analyze(transcript: str) -> AiAnalysis`. Constructor takes an OpenAI client so tests inject a fake. Any OpenAI exception or malformed response raises `AiServiceError` → mapped to HTTP 502.

## Endpoints

All under `/conversations`. **Route order: `/search` declared before `/{id}` to avoid UUID-path collisions.**

| Method | Path | Behavior |
|---|---|---|
| `POST /conversations` | Validate body → `aiService.analyze` (sync) → insert row → 201 with `ConversationOut` |
| `GET /conversations` | `?limit=50&offset=0` → `ConversationList` ordered by `createdAt DESC` |
| `GET /conversations/search?q=` | `q` required (min_length=1) → `ILIKE '%q%'` on `rawTranscript OR summary` → `ConversationList` |
| `GET /conversations/{id}` | UUID path param → `ConversationOut` or 404 |

## Error Handling

Custom exceptions registered with FastAPI exception handlers:

| Exception | HTTP | When |
|---|---|---|
| Pydantic ValidationError | 422 | invalid request body / params |
| `ConversationNotFound` | 404 | `GET /{id}` miss |
| `AiServiceError` | 502 | OpenAI failure or malformed response |
| Unhandled | 500 | logged, generic message |

## Testing Strategy

**`test_aiService.py`** — unit, OpenAI client mocked
- Returns parsed `AiAnalysis` on valid response
- Raises `AiServiceError` on OpenAI exception
- Raises `AiServiceError` on malformed JSON

**`test_endpoints.py`** — integration, real Postgres in CI, AI service overridden
- `POST /conversations` → 201, row persisted, AI fields populated
- `GET /conversations/{id}` → 200 with correct payload
- `GET /conversations` → list ordered by createdAt DESC, pagination works
- `GET /conversations/search?q=` → matches transcript and summary, case-insensitive
- Search route does not collide with `/{id}` route

**`test_errors.py`** — error paths
- `POST` empty body → 422
- `POST` whitespace-only transcript → 422
- `GET /{id}` unknown UUID → 404
- `GET /{id}` malformed UUID → 422
- `POST` when AI raises → 502
- `GET /search` missing `q` → 422

**Fixtures:** transactional `dbSession`, `mockAiService` dependency override, `client` (`TestClient`).

## CI/CD

`.github/workflows/ci.yml`:
- Trigger: push + PR to any branch
- Python 3.12; install via `pip install -e .[dev]`
- Steps: ruff lint → start Postgres service container → `alembic upgrade head` → `pytest --cov=app --cov-fail-under=85`
- Coverage threshold: **85%**

## Docker

- **Dockerfile:** Python 3.12-slim base, non-root user, install deps, run `uvicorn app.main:app`.
- **docker-compose.yml:** two services — `api` (build local Dockerfile, `OPENAI_API_KEY` from env) and `db` (postgres:16, named volume). API healthcheck waits for DB; entrypoint runs `alembic upgrade head` then uvicorn.

## README

Sections: project intro, architecture diagram (text), quickstart (`docker compose up`), example `curl` requests for each endpoint, environment variables, running tests, **"Production extensions" section** noting async job queue (Celery/RQ + Redis) as the next step beyond synchronous OpenAI calls.

## Out of Scope

- Authentication / authorization
- Multi-tenant data isolation
- Streaming responses
- Per-speaker sentiment (kept single overall sentiment)
- Postgres full-text search (kept ILIKE)
- Async job queue (mentioned in README only)

# AI News Aggregator

Streamlit UI + background worker that ingests RSS feeds, stores articles in Postgres, ranks recommendations per user, and (optionally) sends an email digest.

## Architecture (high level)

```mermaid
flowchart LR
  subgraph UI[Web UI]
    S[Streamlit\nnews_aggregator/ui/app.py]
  end

  subgraph Worker[Background Worker]
    W[Worker\nmain.py → scheduler.run_daily_pipeline()]
  end

  subgraph DB[(PostgreSQL)]
    P[(articles/users/interactions)]
  end

  RSS[RSS feeds] --> W
  W --> P
  S --> P
  W --> RESEND[Resend API (optional)]
```

## Required environment variables

- **Always required**
  - `DATABASE_URL`: SQLAlchemy URL (Postgres recommended)
  - `APP_ENV`: `local` / `production` (used for config/logging conventions)
  - `LOG_LEVEL`: e.g. `INFO`
- **Email (only if you enable sending)**
  - `SEND_EMAILS`: `true`/`false`
  - `RESEND_API_KEY`
  - `EMAIL_FROM`

See `.env.example` for the full list of supported variables.

## Local dev (Docker Compose)

1) Create your env file:

```bash
cp .env.example .env
```

2) Start:

```bash
docker compose up --build
```

3) Open the UI:
- `http://localhost:8501`

### Fresh start (delete volumes)

```bash
docker compose down -v
docker compose up --build
```

## Running roles

- **UI (Streamlit)**: `news_aggregator/ui/app.py`
  - Docker default command runs the UI
  - Initializes the DB schema on startup (`init_db()`)
- **Worker (pipeline)**: `main.py`
  - Run with `python main.py`
  - Initializes the DB schema before running the pipeline (`init_db()`)

## Render deployment

You’ll deploy **two services from the same repo** (same Dockerfile):

### 1) PostgreSQL

Create a Render PostgreSQL instance and copy its **Internal Database URL** (or External if you prefer).

### 2) Web Service (Streamlit UI)

- **Environment**: Docker
- **Dockerfile path**: `Dockerfile`
- **Start command**: (leave default Docker CMD)  
  The image default starts Streamlit.
- **Env vars**:
  - `DATABASE_URL`
  - `APP_ENV=production`
  - `LOG_LEVEL=INFO`
  - Optional: `OPENAI_API_KEY`, `OPENAI_MODEL`, `RSS_URLS`, weights

### 3) Background Worker

- **Environment**: Docker
- **Dockerfile path**: `Dockerfile`
- **Start command**:

```bash
python main.py
```

- **Env vars**:
  - `DATABASE_URL`
  - `APP_ENV=production`
  - `LOG_LEVEL=INFO`
  - Email (optional):
    - `SEND_EMAILS=true`
    - `RESEND_API_KEY`
    - `EMAIL_FROM`

## Resume / ATS bullets (example)

- Built a Dockerized Streamlit + Python worker system that ingests RSS feeds, stores content in PostgreSQL, and serves personalized recommendations.
- Implemented environment-driven configuration with fail-fast validation and secrets hygiene for production deployments.
- Designed a pipeline to normalize and deduplicate RSS articles and generate per-user ranked digests.
- Added lightweight retry-based fault tolerance for RSS ingestion and email delivery to reduce transient failures.


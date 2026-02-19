# You Predict Core

YouTube video performance prediction platform. Ingests YouTube data via the Data API v3 and PubSubHubbub push notifications, builds a BigQuery data warehouse, engineers ML features, and predicts video virality.

See `data_model.md` for complete table schemas, column definitions, partitioning, clustering, and write patterns.

## Tech Stack

- **Language:** Python 3.13+
- **Package manager:** uv
- **Server:** FastAPI + Uvicorn (deployed on Cloud Run)
- **Orchestration:** Cloud Scheduler (triggers Cloud Run pipeline endpoints on a cron)
- **Fan-out:** Cloud Tasks for delayed snapshot/comment/transcript polling
- **Data validation:** Pydantic v2
- **Warehouse:** BigQuery
- **Raw storage:** Google Cloud Storage
- **YouTube:** google-api-python-client (Data API v3), youtube-transcript-api
- **ML:** scikit-learn, XGBoost
- **Linting:** Ruff
- **Type checking:** mypy
- **Testing:** pytest

## Architecture

The system has **one deployment target** (Cloud Run) and **three trigger mechanisms**:

| Component | Deployed to | Handles |
|-----------|-------------|---------|
| FastAPI server | **Cloud Run** | Webhook + Cloud Tasks targets + scheduled pipeline endpoints |

```
  ┌──────────────────────────────┐
  │       Cloud Scheduler        │
  │  (cron triggers via HTTP)    │
  │                              │
  │  daily_channel_refresh  0 0  │
  │  daily_video_refresh   0 12  │
  │  compute_features      0 13  │
  │  compute_marts        30 13  │
  │  quality_checks        0 14  │
  │  expire_monitoring     0 1   │
  └──────────────┬───────────────┘
                 │ HTTP POST
┌────────────────┼────────────────────────────────────────────┐
│           Cloud Run (FastAPI)                               │
│                │                                            │
│  ┌─────────────┐  ┌───────────────┐  ┌────────────────┐   │
│  │  Webhook     │  │ Task Handlers │  │  Pipelines     │   │
│  │  GET  /wh    │  │ POST /tasks/  │  │  POST /pipe/   │   │
│  │  POST /wh    │  │  snapshot/    │  │  channel-ref   │   │
│  └──────┬──────┘  │  comments/    │  │  video-ref     │   │
│         │         │  transcript/  │  │  features      │   │
│         │         └───────┬───────┘  │  marts         │   │
│         │                 │          │  quality        │   │
│         │                 │          │  expire         │   │
│         ▼                 ▼          └───────┬────────┘   │
│  ┌─────────────────────────────────────────────────────┐  │
│  │                     engines/                         │  │
│  │  transforms · features · ml · quality · discovery   │  │
│  └──────────────────────┬──────────────────────────────┘  │
│                         ▼                                  │
│  ┌─────────────────────────────────────────────────────┐  │
│  │                   data_sources/                      │  │
│  │  youtube/ · gcs · bigquery                          │  │
│  └─────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────┘
         │                   │                      │
         ▼                   ▼                      ▼
   ┌───────────┐      ┌───────────┐          ┌───────────┐
   │  YouTube   │      │ BigQuery  │          │    GCS    │
   │  Data API  │      │           │          │  (raw)    │
   └───────────┘      └───────────┘          └───────────┘
```

### 1. Webhook — PubSubHubbub (Cloud Run)

YouTube pushes Atom XML notifications when tracked channels upload new videos. The webhook handles two request types:

**Subscription verification (GET):** YouTube sends a `hub.challenge` query parameter that must be echoed back in plaintext to confirm endpoint ownership.

```
GET /webhook?hub.challenge=abc123
  → 200 OK, PlainTextResponse body: "abc123"
```

**New video notification (POST):** YouTube POSTs Atom XML. We parse it using XML namespaces (`atom:entry`, `yt:videoId`, `yt:channelId`, `atom:published`), extract the video and channel IDs, write to `video_monitoring`, and enqueue the fan-out tasks.

```
POST /webhook (Atom XML body)
  → Parse XML: extract video_id, channel_id, published_at
  → Idempotency check: if video_id already exists in video_monitoring, return 200 OK (skip duplicate)
  → MERGE into video_monitoring (engines/discovery.py)
  → Enqueue Cloud Tasks (services/fanout.py):
      12 snapshot tasks at intervals [1, 2, 4, 6, 8, 12, 16, 20, 24, 36, 48, 72] hours
      2 comment pull tasks at [24, 72] hours
      1 transcript fetch at ~24 hours
  → 200 OK
```

### 2. Fan-out Tasks — Cloud Tasks (Cloud Run)

When a video is discovered, `services/fanout.py` enqueues tasks with delayed delivery. Each task is an HTTP POST to the same Cloud Run service with `scheduleTime` set to `published_at + interval_hours`.

Intervals are plain integers representing hours after publish.

```
POST /tasks/snapshot/{video_id}?interval=4
  → Fetch video stats from YouTube API (statistics-only, lightweight)
  → Store raw JSON in GCS (always first — raw data must be preserved before any processing)
  → MERGE → fact_video_snapshot on (video_id, snapshot_type)
    (handles Cloud Tasks at-least-once redelivery — duplicates update instead of creating extra rows)

POST /tasks/comments/{video_id}
  → Fetch commentThreads from YouTube API (paginated)
  → Store raw JSON in GCS first
  → MERGE → fact_comment on comment_id (handles duplicate pulls)

POST /tasks/transcript/{video_id}
  → Fetch transcript via youtube-transcript-api (no API quota)
  → Store raw text in GCS first
  → MERGE → dim_video_transcript on video_id (handles redelivery)
```

Cloud Tasks handles retries automatically on failure. All task handlers are idempotent — redelivery produces the same result without duplicate rows.

### 3. Scheduled Pipelines — Cloud Scheduler

All regularly-running jobs are triggered by Cloud Scheduler, which sends HTTP POST requests to pipeline endpoints on the same Cloud Run service. Pipeline logic lives in `engines/` — the route handlers in `services/pipelines.py` are thin wrappers that invoke engine functions.

**Critical ordering within each pipeline:** Raw data is ALWAYS saved to GCS before any processing or transformation begins. GCS is the source of truth — if a transform fails, we still have the raw data and can reprocess later. A pipeline must never reach a state where processing failed and the raw data wasn't persisted.

```
Ingest from YouTube API
  → Write raw JSON to GCS          ← This MUST succeed first
  → THEN transform GCS → BigQuery  ← This can fail and be retried from GCS
```

| Endpoint | Cron (UTC) | What it does |
|----------|------------|-------------|
| `POST /pipelines/daily-channel-refresh` | `0 0 * * *` | Ingest all tracked channels → GCS → dim_channel + fact_channel_snapshot |
| `POST /pipelines/daily-video-refresh` | `0 12 * * *` | Ingest active video metadata → GCS → dim_video |
| `POST /pipelines/compute-features` | `0 13 * * *` | Run feature SQL with dependency ordering (see below) |
| `POST /pipelines/compute-marts` | `30 13 * * *` | Run mart SQL: video_summary, channel_daily |
| `POST /pipelines/quality-checks` | `0 14 * * *` | Run DQ checks on all tables → data_quality_results |
| `POST /pipelines/expire-monitoring` | `0 1 * * *` | Deactivate videos past their monitoring window |

Feature dependency chain enforced by execution order within the `compute-features` handler:
```
ml_feature_channel (daily, independent)
  → ml_feature_video_performance (depends on channel features for performance_vs_channel_avg)
ml_feature_video_content (per video, independent)
ml_feature_temporal (per video, independent)
ml_feature_comment_aggregates (after comment pulls, independent)
```

## Repo Structure

```
you-predict-core/
├── CLAUDE.md                         ← You are here (architecture + conventions)
├── data_model.md                     ← Data warehouse spec (tables, columns, write patterns)
├── pyproject.toml                    ← Dependencies and tool config
├── Dockerfile                        ← Cloud Run deployment
├── .env.example                      ← Required environment variables template
├── main.py                           ← FastAPI app entrypoint
│
├── src/
│   ├── config/                       ── Settings, constants, GCP client factories
│   │   ├── settings.py                  Pydantic BaseSettings (env vars, project config)
│   │   ├── constants.py                 Enums, snapshot intervals, business logic constants
│   │   └── clients.py                   get_bq_client(), get_gcs_client(), get_tasks_client()
│   │
│   ├── models/                       ── Pydantic models (data contracts for every boundary)
│   │   ├── raw.py                       YouTube API response models
│   │   ├── dimensions.py               DimChannel, DimVideo, DimCategory, DimDate, DimVideoTranscript
│   │   ├── facts.py                     FactVideoSnapshot, FactChannelSnapshot, FactComment
│   │   ├── monitoring.py               VideoMonitoring
│   │   ├── features.py                 ML feature vector models
│   │   ├── ml.py                        ModelRegistry, PredictionLog, ExperimentLog
│   │   └── operational.py              PipelineRunLog, DataQualityResult
│   │
│   ├── data_sources/                 ── External system connectors (API clients, storage I/O)
│   │   ├── youtube/                     YouTube Data API v3 wrapper
│   │   │   ├── client.py                  Auth, rate limiting, quota tracking, retries
│   │   │   ├── channels.py               channels.list (metadata + stats in one call)
│   │   │   ├── videos.py                 videos.list (full metadata)
│   │   │   ├── snapshots.py              videos.list (statistics-only, lightweight)
│   │   │   ├── comments.py               commentThreads.list (paginated)
│   │   │   └── transcripts.py            youtube-transcript-api (no quota cost)
│   │   ├── gcs.py                       GCS read/write: upload_json(), read_json(), list_blobs()
│   │   ├── gcs_paths.py                 Path builders for raw layer naming conventions
│   │   ├── bigquery.py                  BQ operations: append_rows(), delete_insert(), merge()
│   │   └── bigquery_schemas.py          SchemaField definitions for all tables
│   │
│   ├── engines/                      ── Core processing logic
│   │   ├── transforms/                  GCS raw JSON → BigQuery dim/fact tables
│   │   │   ├── base.py                    Base transformer: extract → validate → load
│   │   │   ├── channels.py               → dim_channel + fact_channel_snapshot
│   │   │   ├── videos.py                 → dim_video
│   │   │   ├── snapshots.py              → fact_video_snapshot (deltas, hours_since_publish)
│   │   │   ├── comments.py               → fact_comment (dedup, sentiment, toxicity)
│   │   │   └── transcripts.py            → dim_video_transcript (word count, readability)
│   │   ├── features/                    SQL-based feature computation
│   │   │   ├── runner.py                  Load .sql, parameterize, execute, log
│   │   │   └── registry.py               Dependency graph + execution order
│   │   ├── ml/                          Machine learning pipelines
│   │   │   ├── dataset.py                 Build training DataFrames, label creation
│   │   │   ├── training.py                Fit models, metrics, serialize to GCS
│   │   │   ├── serving.py                 Load model, predict → ml_prediction_log
│   │   │   ├── registry.py                Model lifecycle (register, promote, archive)
│   │   │   ├── evaluation.py              Backfill actuals, error metrics, drift detection
│   │   │   └── experiments.py             A/B experiment management
│   │   ├── quality/                     Data quality framework
│   │   │   ├── checks.py                  DQ check definitions
│   │   │   └── runner.py                  Execute checks → data_quality_results
│   │   └── discovery.py                 Video discovery + video_monitoring lifecycle
│   │
│   ├── services/                     ── FastAPI routes (Cloud Run HTTP surface only)
│   │   ├── webhook.py                   PubSubHubbub GET (challenge) + POST (notification)
│   │   ├── fanout.py                    Enqueue Cloud Tasks with delayed delivery
│   │   ├── snapshot_handler.py          Endpoints Cloud Tasks hits (snapshots, comments, transcripts)
│   │   └── pipelines.py                 Scheduled pipeline endpoints (triggered by Cloud Scheduler)
│   │
│   ├── scripts/                      ── Bootstrap, seed, and ad-hoc scripts
│   │   ├── bootstrap_all.py             Run all bootstrap + seed steps in order
│   │   ├── bootstrap_gcs.py             Create GCS buckets (raw + models)
│   │   ├── bootstrap_bigquery.py        Create BQ dataset + all tables from schemas
│   │   ├── bootstrap_cloud_tasks.py     Create Cloud Tasks queue
│   │   ├── seed_categories.py           Populate dim_category (~32 YouTube categories)
│   │   ├── seed_dates.py                Populate dim_date (2026-2028)
│   │   ├── subscribe_channels.py        Subscribe to PubSubHubbub for all tracked channels
│   │   └── backfill.py                  Replay GCS raw data → rebuild BQ tables
│   │
│   ├── sql/                          ── Pure SQL (executed by engines/features/runner.py)
│   │   ├── features/                    Feature computation queries (MERGE)
│   │   │   ├── video_performance.sql
│   │   │   ├── video_content.sql
│   │   │   ├── temporal.sql
│   │   │   ├── channel.sql
│   │   │   └── comment_aggregates.sql
│   │   ├── marts/                       Mart rollup queries (MERGE/INSERT)
│   │   │   ├── video_summary.sql
│   │   │   └── channel_daily.sql
│   │   └── quality/                     DQ check queries
│   │       ├── freshness_checks.sql
│   │       ├── row_count_checks.sql
│   │       └── null_rate_checks.sql
│   │
│   └── utils/                        ── Shared utilities (leaf — imports nothing from src)
│       ├── retry.py                     Exponential backoff decorator
│       ├── timestamps.py                ISO parsing, timezone handling, age calculations
│       ├── text.py                      Emoji detection, caps ratio, power words, readability
│       ├── ids.py                       UUID generation
│       └── pagination.py               Paginated API response handler
│
└── tests/
    ├── conftest.py                      Shared fixtures (mock GCP clients, sample responses)
    ├── test_models/
    ├── test_data_sources/
    ├── test_engines/
    ├── test_services/
    └── fixtures/                        Sample API response JSON for tests
```

## Module Dependency Flow

Code imports only flow downward. Never import upward.

```
services/          → engines/       (FastAPI routes invoke engine functions)
                     engines/       → data_sources/    → config/
                                    → models/          → config/
utils/             (leaf — imported by anyone, imports nothing from src)
```

- **services/** is the sole entry point — webhook, task handlers, and pipeline routes all call into `engines/`
- **engines/** does all the actual work (transforms, features, ML, quality)
- **data_sources/** handles all external I/O (YouTube API, GCS, BigQuery)
- **models/** defines Pydantic data contracts for every boundary
- **utils/** is a standalone leaf

## Data Flow

See `data_model.md` for column-level detail on every table below.

```
YouTube API / PubSubHubbub
        │
        ▼
   ┌─────────┐     Append-only raw JSON blobs (bronze layer)
   │   GCS   │     gs://you-predict-raw/{prefix}/{id}/{id}_{timestamp}.json
   └────┬────┘     ↑ ALWAYS persisted BEFORE any downstream processing
        │
        │  engines/transforms/
        ▼
   ┌──────────┐    dim_channel, dim_video, fact_video_snapshot,
   │ BigQuery  │    fact_channel_snapshot, fact_comment, video_monitoring
   │ dim/fact  │
   └────┬─────┘
        │  sql/features/*.sql
        ▼
   ┌──────────┐    ml_feature_video_performance, ml_feature_channel,
   │ BigQuery  │    ml_feature_video_content, ml_feature_temporal,
   │ features  │    ml_feature_comment_aggregates
   └────┬─────┘
        │  sql/marts/*.sql
        ▼
   ┌──────────┐    mart_video_summary, mart_channel_daily
   │ BigQuery  │
   │  marts    │
   └────┬─────┘
        │  engines/ml/
        ▼
   ┌──────────┐    ml_model_registry, ml_prediction_log, ml_experiment_log
   │  MLOps   │
   └──────────┘
```

## Key Invariants

- **GCS is the source of truth.** Raw data is always written to GCS before any processing. Everything in BigQuery from dim/fact onward is recomputable by replaying raw GCS blobs (`scripts/backfill.py`). If a transform fails, the raw data is still safe in GCS.
- **No SCD2.** Dimensions are current-state only (daily MERGE refresh). Historical state can be recovered from GCS snapshots.
- **Append-only raw layer.** GCS blobs are never overwritten or deleted.
- **Pydantic at every boundary.** API responses, GCS blobs, and BQ rows all pass through Pydantic models for validation.
- **SQL stays as SQL.** Feature and mart computations live in `src/sql/` as `.sql` files, not Python strings. Parameterized with `{project}` and `{dataset}` at execution time.
- **Snapshot intervals are integers.** Always in hours (e.g., `1`, `4`, `24`). The constant `SNAPSHOT_INTERVALS_HOURS` in `config/constants.py` is the canonical list.

## Bootstrap (Setting Up From Scratch)

Scripts in `src/scripts/` create all required infrastructure and seed data. Run everything at once or individually:

```bash
# All-in-one (runs steps 1-5 in order):
uv run python -m src.scripts.bootstrap_all

# Or run individually:
uv run python -m src.scripts.bootstrap_gcs           # 1. GCS buckets
uv run python -m src.scripts.bootstrap_bigquery       # 2. BQ dataset + all 21 tables
uv run python -m src.scripts.bootstrap_cloud_tasks    # 3. Cloud Tasks queue
uv run python -m src.scripts.seed_categories          # 4. ~32 YouTube categories
uv run python -m src.scripts.seed_dates               # 5. 2026-2028 calendar

# Later (after Cloud Run is deployed):
uv run python -m src.scripts.subscribe_channels       # Subscribe to PubSubHubbub

# If you need to rebuild BQ from existing GCS data:
uv run python -m src.scripts.backfill --date 2026-02-15
```

All bootstrap scripts are idempotent — safe to run multiple times without side effects.
Seed scripts (categories, dates) wipe and re-insert for a clean reset.

## Environment Variables

No prefix. Loaded via Pydantic BaseSettings from `.env` file or environment.

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GCP_PROJECT_ID` | Yes | — | GCP project ID |
| `YOUTUBE_API_KEY` | Yes | — | YouTube Data API v3 key |
| `CLOUD_RUN_SERVICE_URL` | Yes (prod) | — | Base URL of Cloud Run service (Cloud Tasks targeting) |
| `GCS_RAW_BUCKET` | No | `you-predict-raw` | Raw data GCS bucket |
| `GCS_MODEL_BUCKET` | No | `you-predict-models` | ML model artifact bucket |
| `BQ_DATASET` | No | `you_predict_warehouse` | BigQuery dataset name |
| `CLOUD_TASKS_QUEUE` | No | `snapshot-fanout` | Cloud Tasks queue name |
| `CLOUD_TASKS_LOCATION` | No | `us-east1` | Cloud Tasks queue region |
| `MONITORING_WINDOW_HOURS` | No | `72` | How long to poll a video after publish |

## Development

```bash
# Install dependencies
uv sync

# Install with dev dependencies
uv sync --group dev

# Run server locally
uv run uvicorn main:app --reload

# Run tests
uv run pytest tests/

# Lint + format
uv run ruff check src/ tests/
uv run ruff format src/ tests/

# Type check
uv run mypy src/
```

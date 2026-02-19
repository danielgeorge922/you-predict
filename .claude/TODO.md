# You Predict Core — Build Roadmap

## Phase 0: Project Setup
- [x] Add all dependencies to `pyproject.toml` (fastapi, uvicorn, google-cloud-bigquery, google-cloud-storage, google-cloud-tasks, google-api-python-client, youtube-transcript-api, pydantic-settings; dev: ruff, mypy, pytest)
- [x] `uv sync` to install everything
- [x] Create `.env.example` with all env vars from CLAUDE.md
- [x] Create a real `.gitignore` (.venv/, .env, __pycache__/, *.pyc, .mypy_cache/)
- [x] Add ruff + mypy config to `pyproject.toml`
- [x] Delete duplicate `src/settings.py` (keep only `src/config/settings.py`)

## Phase 1: Foundation (pure Python, no GCP needed)
- [x] `src/utils/timestamps.py` — ISO parsing, timezone handling, age calculations
- [x] `src/utils/text.py` — emoji detection, caps ratio, power words, readability
- [x] `src/utils/retry.py` — exponential backoff decorator
- [x] `src/utils/ids.py` — UUID generation
- [x] `src/config/constants.py` — FanoutSchedule dataclass, enums, classifier StrEnums
- [x] `src/config/clients.py` — get_bq_client(), get_gcs_client(), get_tasks_client() (lru_cache factories)
- [x] `src/models/raw.py` — YouTube API response Pydantic models
- [x] `src/models/dimensions.py` — DimChannel (with current stats), DimVideo (with current stats), DimCategory, DimDate, DimVideoTranscript
- [x] `src/models/facts.py` — FactVideoSnapshot, FactChannelSnapshot, FactComment
- [x] `src/models/monitoring.py` — VideoMonitoring
- [x] `src/models/features.py` — ML feature vector models
- [x] `src/models/ml.py` — ModelRegistry, PredictionLog, ExperimentLog
- [x] `src/models/operational.py` — PipelineRunLog, DataQualityResult
- [ ] Unit tests for models and utils

## Phase 2: Data Sources (need GCP project + YouTube API key)
- [x] Set up GCP project, enable APIs (YouTube, BigQuery, Cloud Storage, Cloud Tasks)
- [x] Get YouTube API key
- [x] `src/data_sources/youtube/client.py` — auth, pagination, service builder
- [x] `src/data_sources/youtube/channels.py` — channels.list (batched)
- [x] `src/data_sources/youtube/videos.py` — videos.list (full metadata, batched)
- [x] `src/data_sources/youtube/snapshots.py` — videos.list (statistics-only)
- [x] `src/data_sources/youtube/comments.py` — commentThreads.list (paginated)
- [x] `src/data_sources/youtube/transcripts.py` — youtube-transcript-api wrapper
- [x] `src/data_sources/gcs.py` — GCSService class (upload_json, upload_text, read_json, read_text, list_blobs)
- [x] `src/data_sources/gcs_paths.py` — GCSPathBuilder class
- [x] `src/data_sources/bigquery_schemas.py` — SchemaField definitions for all 22 tables + TABLE_REGISTRY
- [x] `src/data_sources/bigquery.py` — BigQueryService class (append_rows, run_query, run_merge, create_table)
- [ ] Sanity-test each data source against real GCP

## Phase 3: Bootstrap & Seed (stand up infrastructure)
- [x] `src/scripts/bootstrap_gcs.py` — create GCS buckets
- [x] `src/scripts/bootstrap_bigquery.py` — create BQ dataset + all tables from schemas
- [x] `src/scripts/bootstrap_cloud_tasks.py` — create Cloud Tasks queue
- [x] `src/scripts/bootstrap_all.py` — single runner for all bootstrap + seed steps
- [x] `src/scripts/seed_categories.py` — insert ~32 YouTube categories
- [x] `src/scripts/seed_dates.py` — insert 2026-2028 date dimension
- [x] `src/scripts/seed_tracked_channels.py` — MERGE channel IDs into tracked_channels
- [x] Run `uv run python -m src.scripts.bootstrap_all` — all 22 tables created, categories + dates seeded
- [x] Add channel IDs to `seed_tracked_channels.py` and run it — 5 channels seeded

## Phase 4: Engines (pipeline logic)
- [x] `src/engines/transforms/base.py` — base transformer pattern (extract → validate → load)
- [x] `src/engines/transforms/channels.py` — raw JSON → dim_channel + fact_channel_snapshot
- [x] `src/engines/transforms/videos.py` — raw JSON → dim_video
- [x] `src/engines/transforms/snapshots.py` — raw JSON → fact_video_snapshot (deltas, actual_captured_at)
- [x] `src/engines/transforms/comments.py` — raw JSON → fact_comment
- [x] `src/engines/transforms/transcripts.py` — raw text → dim_video_transcript
- [x] `src/engines/discovery.py` — video_monitoring lifecycle + get_tracked_channel_ids()
- [x] Test transforms with fixture JSON

## Phase 5: FastAPI Server (wire it together)
- [x] `main.py` — proper FastAPI app with router includes
- [x] `src/services/webhook.py` — GET challenge echo + POST XML parse → discovery → fanout
- [x] `src/services/fanout.py` — enqueue Cloud Tasks with delayed delivery
- [x] `src/services/snapshot_handler.py` — /tasks/snapshot, /tasks/comments, /tasks/transcript
- [x] `src/services/pipelines.py` — /pipelines/daily-channel-refresh, etc.
- [x] Test locally with `uvicorn main:app --reload`

## Phase 6: Deploy & Wire Cloud Infra (THE MILESTONE — live data starts here)
- [x] Write `Dockerfile` + `.dockerignore`
- [x] `src/scripts/subscribe_channels.py` — subscribe to PubSubHubbub for tracked channels
- [x] Enable required GCP APIs (run, artifactregistry, cloudbuild, cloudtasks, cloudscheduler, secretmanager, bigquery, storage)
- [x] Add `roles/cloudtasks.enqueuer` to `you-predict-master-account` service account
- [x] Create Artifact Registry repository (`you-predict-core-repo`, us-east1)
- [x] Deploy to Cloud Run (`gcloud run deploy --source .`, revision `you-predict-core-00001`)
- [x] Set env vars on Cloud Run service (all 8 non-secret vars)
- [x] Store `YOUTUBE_API_KEY` in Secret Manager, inject into Cloud Run via `--set-secrets`
- [x] Make Cloud Run service publicly accessible (`allUsers` → `roles/run.invoker`)
- [x] Create Cloud Scheduler jobs (6 cron triggers, all ENABLED, us-east1)
- [x] Run `subscribe_channels.py` — 5 channels subscribed to PubSubHubbub (all 202 Accepted)
- [x] Create `Makefile` with `make deploy`, `make logs`, `make test`, `make lint`, `make subscribe`, etc.
- [x] Fix Cloud Run ingress (--ingress=all) and IAM binding (allUsers run.invoker) — initial deploy had wrong settings
- [x] Fix CLOUD_RUN_SERVICE_URL — actual URL is 2n75rmagqa-ue.a.run.app, update env var + Cloud Scheduler jobs + re-subscribe
- [x] Install make via winget (ezwinports.make 4.4.1) + fix `make logs` to use `gcloud beta`
- [x] Create `testing.http` for REST Client — webhook challenge, simulated XML notification, pipeline triggers
- [x] End-to-end test: uploaded video → webhook POST 200 → MERGE 1 row → 20 Cloud Tasks enqueued ✓
- [x] Add `/pipelines/renew-subscriptions` endpoint — re-subscribes all tracked channels to PubSubHubbub
- [x] Add `make renew-scheduler` to Makefile — creates Cloud Scheduler job (every 4 days, `0 0 */4 * *`)
- [x] Run `make deploy` + `make renew-scheduler` — deploy new endpoint + create renewal scheduler job
- [x] Set up Error Reporting → email notifications (danielgeorge922@gmail.com) — alerts on new unhandled exceptions
- [x] Fix Cloud Tasks 403: `--no-allow-unauthenticated` in Makefile was stripping allUsers binding on every deploy → changed to `--allow-unauthenticated`; added `make logs-history` target
- [x] Verified fact_video_snapshot rows appearing: 1h + 2h snapshots confirmed in BQ ✓

## Phase 7: SQL Features & Marts
- [ ] `src/sql/features/channel.sql`
- [ ] `src/sql/features/video_performance.sql`
- [ ] `src/sql/features/video_content.sql`
- [ ] `src/sql/features/temporal.sql`
- [ ] `src/sql/features/comment_aggregates.sql`
- [ ] `src/sql/marts/video_summary.sql`
- [ ] `src/sql/marts/channel_daily.sql`
- [ ] `src/engines/features/runner.py` — load SQL, parameterize {project}/{dataset}, execute
- [ ] `src/engines/features/registry.py` — dependency graph + execution order
- [ ] Run features pipeline, verify tables in BQ

## Phase 8: Data Quality
- [ ] `src/sql/quality/freshness_checks.sql`
- [ ] `src/sql/quality/row_count_checks.sql`
- [ ] `src/sql/quality/null_rate_checks.sql`
- [ ] `src/engines/quality/checks.py` + `runner.py`
- [ ] Wire into /pipelines/quality-checks endpoint

## Phase 9: ML Pipeline (needs real data collected first)
- [ ] `src/engines/ml/dataset.py` — build training DataFrame, define labels, enforce temporal cutoff
- [ ] `src/engines/ml/training.py` — fit XGBoost, metrics, serialize to GCS
- [ ] `src/engines/ml/serving.py` — load model, predict, log to ml_prediction_log
- [ ] `src/engines/ml/registry.py` — model lifecycle (register, promote, archive)
- [ ] `src/engines/ml/evaluation.py` — backfill actuals, compute error metrics
- [ ] `src/scripts/backfill.py` — replay GCS raw data → rebuild BQ tables

## Phase 10: Tests & Polish
- [x] `tests/conftest.py` — shared fixtures, mock GCP clients
- [x] `tests/fixtures/` — sample API response JSON (channel, 2 videos, stats-only, comment threads)
- [x] Tests for engines (transforms: channels, videos, snapshots, comments, transcripts; discovery)
- [x] Tests for models (`test_raw`, `test_dimensions`, `test_facts`, `test_monitoring`, `test_operational`)
- [x] Tests for utils (`test_timestamps`, `test_text`, `test_retry`, `test_ids`)
- [x] Tests for config (`test_constants`)
- [x] Tests for data_sources (`test_bigquery_schemas`, `test_gcs_paths`)
- [x] Tests for scripts (`test_seed_categories`, `test_seed_dates`)
- [x] 256 tests passing (fixed 2 failing schema tests after tracked_channels table was added)
- [x] `ruff check src/ tests/` passes clean
- [x] `mypy src/` passes clean (50 source files)
- [ ] Tests for services (`test_webhook`, `test_snapshot_handler`, `test_pipelines`)
- [ ] Write README with setup instructions

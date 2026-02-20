# TODO

## Done

### Ingestion layer (Phases 1–6)
- [x] Webhook — PubSubHubbub GET (challenge) + POST (notification + fanout)
- [x] Fan-out — Cloud Tasks snapshot / comments / transcript handlers
- [x] Transforms — `dim_channel`, `dim_video`, `fact_video_snapshot`, `fact_channel_snapshot`, `fact_comment`, `dim_video_transcript`
- [x] Pipelines — `daily-channel-refresh`, `daily-video-refresh`, `expire-monitoring`, `renew-subscriptions`
- [x] YouTube API client — channels, videos, snapshots, comments, transcripts
- [x] Bootstrap scripts — GCS, BigQuery (21 tables), Cloud Tasks, seed categories/dates/channels
- [x] PubSubHubbub subscription script

### Feature computation (Phase 7a)
- [x] `src/sql/features/channel.sql`
- [x] `src/sql/features/video_performance.sql`
- [x] `src/sql/features/video_content.sql`
- [x] `src/sql/features/temporal.sql`
- [x] `src/sql/features/comment_aggregates.sql`
- [x] `src/engines/features/runner.py` + `registry.py`
- [x] `POST /pipelines/compute-features` wired

---

## Up next

### Schema fix — drop + recreate `ml_feature_video_performance`
The schema was expanded (added 3h/10h/14h/18h/22h intervals, full likes/comments time series,
view velocity at all intervals, removed `hours_to_10k_views`). The table is empty so just drop
it in the BQ console and run:
```bash
uv run python -m src.scripts.bootstrap_bigquery
```

### Mart computation (Phase 7b)
- [ ] `src/sql/marts/video_summary.sql` — one row per video, `virality_label` via `PERCENT_RANK()` on `views_72h` partitioned by `channel_id`
- [ ] `src/sql/marts/channel_daily.sql` — one row per channel per day
- [ ] `src/engines/marts/runner.py`
- [ ] `POST /pipelines/compute-marts` wired

### Data quality checks (Phase 8)
- [ ] `src/sql/quality/freshness_checks.sql`
- [ ] `src/sql/quality/row_count_checks.sql`
- [ ] `src/sql/quality/null_rate_checks.sql`
- [ ] `src/engines/quality/checks.py` + `runner.py`
- [ ] `POST /pipelines/quality-checks` wired

### ML layer (Phase 9)
- [ ] `src/engines/ml/dataset.py` — build training DataFrames from feature tables, label creation from `virality_label`
- [ ] `src/engines/ml/training.py` — fit XGBoost, serialize model + scaler to GCS
- [ ] `src/engines/ml/serving.py` — load model, predict → `ml_prediction_log`
- [ ] `src/engines/ml/registry.py` — register / promote / archive models in `ml_model_registry`
- [ ] `src/engines/ml/evaluation.py` — backfill actuals, compute error metrics, drift detection
- [ ] `src/engines/ml/experiments.py` — A/B experiment management

### Deferred enrichments
- [ ] NLP title features — `title_sentiment`, `title_clickbait_score` in `ml_feature_video_content` (requires Python text processing pass after SQL compute)
- [ ] `comment_language_entropy` in `ml_feature_comment_aggregates`
- [ ] `channel_momentum_score` + `avg_time_between_uploads_7d` in `ml_feature_channel`

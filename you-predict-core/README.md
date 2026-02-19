# you-predict-core

YouTube video performance prediction backend. Ingests YouTube data via the Data API v3 and PubSubHubbub push notifications, builds a BigQuery data warehouse, engineers ML features, and predicts video virality.

---

## Quick start

```bash
uv sync --group dev        # install dependencies
cp .env.example .env       # fill in GCP_PROJECT_ID, YOUTUBE_API_KEY, etc.
make bootstrap             # create GCS buckets, BQ dataset + tables, Cloud Tasks queue, seed categories + dates
```

---

## Tracked channels

The list of YouTube channels the system monitors lives in one place:

**[src/scripts/seed_tracked_channels.py](src/scripts/seed_tracked_channels.py)** — the `TRACKED_CHANNELS` list.

```python
TRACKED_CHANNELS: list[tuple[str, str]] = [
    ("UCxxxxxxxxxxxxxxxxxxxxxxxx", "Channel nickname or notes"),
    ...
]
```

Each entry is `(channel_id, notes)`. The channel ID is the `UC...` string from the channel URL.

### Adding or removing a channel

1. Edit `TRACKED_CHANNELS` in `src/scripts/seed_tracked_channels.py`.
2. Push the change to BigQuery and re-subscribe to PubSubHubbub:

```bash
make seed-and-subscribe
```

Or run the two steps individually:

```bash
make seed-channels   # writes the list to the tracked_channels BQ table (idempotent MERGE)
make subscribe       # subscribes every active channel to PubSubHubbub push notifications
```

> Both steps are idempotent — safe to re-run any number of times without side effects.
> `seed-channels` preserves the original `added_at` timestamp on existing rows.

### To deactivate a channel without removing it

Set `is_active = FALSE` directly in BigQuery on the `tracked_channels` table. The channel will be skipped by all pipelines and won't be re-subscribed next time `make subscribe` runs.

---

## Common commands

| Command | What it does |
|---------|-------------|
| `make dev` | Run FastAPI server locally on port 8080 (hot reload) |
| `make test` | Run pytest |
| `make lint` | Ruff lint check |
| `make fmt` | Ruff format |
| `make typecheck` | mypy |
| `make bootstrap` | Full infrastructure + seed setup (run once from scratch) |
| `make seed-channels` | Push `TRACKED_CHANNELS` list → BigQuery `tracked_channels` table |
| `make subscribe` | Subscribe all active BQ channels to PubSubHubbub |
| `make seed-and-subscribe` | `seed-channels` + `subscribe` in one shot |
| `make deploy` | Deploy to Cloud Run |
| `make logs` | Tail live Cloud Run logs |
| `make logs-history` | Last 200 Cloud Run log entries |

---

## Architecture & data model

See [CLAUDE.md](CLAUDE.md) for the full architecture, module dependency rules, and pipeline descriptions.
See [data_model.md](data_model.md) for complete BigQuery table schemas, column definitions, and write patterns.

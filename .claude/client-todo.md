# You Predict Client — Integration Roadmap

## Phase A: Backend API Endpoints (FastAPI changes)

- [ ] Add CORS middleware to `main.py` — allow requests from `localhost:3000` and Vercel production URL
- [ ] Create `src/services/data_api.py` — new router with GET endpoints for the frontend
- [ ] `GET /channels` — return all tracked channels from `dim_channel` (channel_id, title, thumbnail_url, subscriber_count, subscriber_tier)
- [ ] `GET /channels/{channel_id}/videos` — return recent videos for a channel from `dim_video` joined with latest `fact_video_snapshot` stats; query param: `limit` (default 20)
- [ ] `GET /videos/{video_id}` — return single video detail with all snapshots over time (for future growth chart)
- [ ] Register new router in `main.py`
- [ ] Deploy updated backend (`make deploy`)

## Phase B: Frontend Type Fixes

- [ ] `consts/channels.ts` — change `id` from `number` to `string` (YouTube channel IDs are strings like `UCr-GHkKLpT9DgBXHQXI2WAw`)
- [ ] `components/VideoCard.tsx` — update `VideoData.channel_id` from `number` to `string`
- [ ] `components/VideoCard.tsx` — add 4th classification label `"above_avg"` to match backend `ViralityLabel` enum (`viral | above_avg | normal | below_avg`); current frontend has 3 labels (`viral | average | underperforming`)
- [ ] `components/VideoCard.tsx` — add UI treatment for `"above_avg"` and `"normal"` labels (color, badge text)
- [ ] Update all other files that reference `channel_id: number` or the 3-label classification union

## Phase C: Frontend Environment & API Layer

- [ ] Create `client/.env.local` with `NEXT_PUBLIC_API_URL=https://you-predict-core-2n75rmagqa-ue.a.run.app`
- [ ] Create `client/.env.example` documenting the variable
- [ ] Create `client/lib/api.ts` — typed fetch wrapper with `getChannels()` and `getChannelVideos(channelId)` functions

## Phase D: Replace Hardcoded Data with Real API Calls

- [ ] `app/predictions/page.tsx` — replace `consts/channels.ts` import with `getChannels()` API call; handle loading/error state
- [ ] `app/predictions/[id]/page.tsx` — replace `consts/videos.ts` import with `getChannelVideos(id)` API call; handle loading/error/empty state
- [ ] `components/ChannelsSidebar.tsx` — accept channels as props (passed down from page) instead of importing from consts
- [ ] `components/VideoCard.tsx` — update thumbnail source from hardcoded rickroll to real `dim_video.thumbnail_url`
- [ ] Remove `consts/channels.ts` and `consts/videos.ts` once replaced (or keep as fallback mock data)

## Phase E: Handle Missing Predictions Gracefully

Predictions don't exist yet (Phase 9 ML pipeline not built). Frontend currently shows fake `predictedClassification` / `actualClassification` / `wasCorrect` values.

- [ ] Add `predicted_virality: string | null` and `actual_virality: string | null` to video API response (null until ML pipeline runs)
- [ ] `components/VideoCard.tsx` — show "Pending prediction" placeholder when `predicted_virality` is null instead of crashing or showing fake data
- [ ] Hide `wasCorrect` badge when `actualClassification` is null (video too recent)

## Phase F: Hardcoded Content Cleanup

- [ ] `components/Header.tsx` — update GitHub link from `https://github.com/danielgeorge922/you-predict` to correct repo URL
- [ ] `components/Header.tsx` — update Design Docs link from placeholder Google Doc URL to real doc (or remove)
- [ ] `components/Header.tsx` — remove/hide "Retrain Model" button and version dropdown until ML pipeline is built (Phase 9)
- [ ] `consts/mainpage.ts` — update homepage ML stats (85.2% accuracy, 2M+ videos, 127 features, <50ms) — either remove or mark as aspirational targets
- [ ] `consts/mainpage.ts` — update "How" section tech description to match actual stack (no Kafka — uses Cloud Tasks + PubSubHubbub)

## Phase G: Deployment

- [ ] Create `client/.gitignore` entry for `.env.local` if not already present
- [ ] Deploy frontend to Vercel — connect repo, set `NEXT_PUBLIC_API_URL` env var in Vercel dashboard
- [ ] Add Vercel production URL to CORS allowlist in FastAPI
- [ ] Verify end-to-end: Vercel frontend → Cloud Run API → BigQuery

## Phase H: Future (after Phase 9 ML pipeline is built)

- [ ] Wire `GET /channels/{channel_id}/videos` to include real `predicted_virality` from `ml_prediction_log`
- [ ] Wire `GET /videos/{video_id}` to return snapshot time series for growth chart
- [ ] Wire "Retrain Model" button to trigger `POST /pipelines/train-model` (Phase 9 endpoint)
- [ ] Replace hardcoded version dropdown with real model versions from `ml_model_registry`

---

## Phase I: Nav Restructure + New Pages (UI Sprint)

Planned nav: **[ Predictions ] [ Model Performance ] [ Channel Analytics ]**

### I-1: Nav + routing cleanup ✅ (mostly done)
- [x] Header routes updated: `Predictions` → `/predictions`, `Model Health` → `/model-health`, `Channel Analytics` → `/channel-analytics`
- [x] Old pages deleted (`inference-visualization`, `model-performance`, `model-monitoring`)
- [x] New page stubs created (`predictions`, `model-health`, `channel-analytics`)
- [ ] `components/Header.tsx` — rename `"Model Health"` → `"Model Performance"` (label + href: `/model-performance`)
- [ ] Rename `app/model-health/` → `app/model-performance/`

### I-2: Predictions page enhancements
- [ ] Add `StatBar` component at top of `/predictions` page
  - Fields: videos being monitored, total predictions made, model accuracy
  - Dummy values for now; replace with real API data in Phase D/H
- [ ] `components/VideoCard.tsx` — add `confidence` field to `VideoData` interface (0–1 float)
  - Display as `"Viral — 87% confidence"` next to classification badge
- [ ] `consts/videos.ts` — add `confidence` values to all dummy video entries

### I-3: Model Performance page (`app/model-performance/page.tsx`)
Merges the old Model Performance + Model Monitoring placeholders into one page.

- [ ] Install Recharts: `npm install recharts` in `client/`
- [ ] Create `consts/modelPerformance.ts` — dummy data:
  - Summary metrics (overall accuracy, precision/recall/F1 for viral class)
  - 3×3 confusion matrix values (underperforming / average / viral)
  - Top 10 feature importances (name + importance score)
  - Confidence distribution histogram buckets
  - Model version history (version, trained date, accuracy, status)
- [ ] `components/ConfusionMatrix.tsx` — 3×3 colored grid, diagonal = correct
- [ ] `components/FeatureImportanceChart.tsx` — horizontal bar chart (Recharts)
- [ ] `components/ConfidenceHistogram.tsx` — histogram of prediction confidence scores
- [ ] `app/model-performance/page.tsx` — assemble sections:
  1. Summary metric card row (4 cards)
  2. Confusion matrix + feature importance side-by-side
  3. Confidence distribution histogram
  4. Model version timeline table

### I-4: Channel Analytics — two-tier routing

Two levels: cross-channel overview + per-channel deep dive.
Copy sidebar pattern from predictions (same layout.tsx + ChannelsSidebar approach, links point to `/channel-analytics/[id]`).

#### Routing structure
```
/channel-analytics          → cross-channel overview (comparative)
/channel-analytics/[id]     → single channel deep dive
```

#### I-4a: Routing + layout scaffold
- [ ] Create `app/channel-analytics/layout.tsx` — copy `app/predictions/layout.tsx`, sidebar links point to `/channel-analytics/[id]`
- [ ] Update `components/ChannelsSidebar.tsx` — accept a `basePath` prop (defaults to `/predictions`) so it can be reused for channel analytics
- [ ] Create `app/channel-analytics/[id]/page.tsx` — stub

#### I-4b: Dummy data (`consts/channelAnalytics.ts`)
- [ ] Per-channel benchmark data: `avg_views_30d`, `viral_rate`, `engagement_rate` (like/view ratio), `comment_rate`, `uploads_per_week`, `subscriber_tier`, `consistency_score` (std dev of views)
- [ ] Channel growth snapshots: `{date, subscriber_count, view_count}[]` per channel (last 90 days)
- [ ] Upload cadence data: `{video_id, title, published_at, days_since_prev}[]` per channel
- [ ] Duration buckets: `{bucket: "0-5min"|"5-10"|"10-20"|"20+", avg_views, video_count}[]` per channel
- [ ] Comment sentiment trend: `{week, avg_sentiment, avg_toxicity}[]` per channel
- [ ] Title evolution: `{month, avg_title_length, avg_caps_ratio, avg_power_words}[]` per channel

#### I-4c: Cross-channel overview (`/channel-analytics`)
- [ ] **Channel Volatility Scatter** (Recharts ScatterChart) — x = avg views, y = std dev of views; each dot = channel; quadrants: "Consistent Hits" (high avg, low variance), "Boom or Bust" (high avg, high variance), "Reliable Niche" (low avg, low variance), "Unpredictable" (low avg, high variance)
- [ ] **Engagement Rate Rankings** — horizontal bar chart, channels ranked by like/view ratio and comment/view ratio side by side
- [ ] **Channel Benchmarks Table** — sortable: Channel, Tier badge, Avg Views, Viral Rate, Engagement Rate, Consistency Score, Uploads/wk
- [ ] Assemble `/channel-analytics/page.tsx`:
  1. Page header + description
  2. Volatility scatter (full width)
  3. Engagement rankings + benchmarks table side by side

#### I-4d: Per-channel deep dive (`/channel-analytics/[id]`)
Layout mirrors `/predictions/[id]` — sidebar on left, content on right, breadcrumb at top.

**Growth & Health section**
- [ ] **Subscriber Growth Curve** — Recharts LineChart, `{date, subscriber_count}[]` over last 90 days
- [ ] **Upload Cadence Chart** — bar chart of days between each upload; highlight gaps > 14 days in red; shows consistency visually

**Content Strategy section**
- [ ] **Duration Sweet Spot** — bar chart of duration buckets (0-5min / 5-10 / 10-20 / 20+) with avg views per bucket for this channel specifically
- [ ] **Upload Frequency vs Performance** — scatter: `{uploads_in_last_7d, avg_views_that_week}` over time — does posting more hurt per-video performance?

**Audience Intelligence section**
- [ ] **Comment Sentiment Trend** — dual-line chart: avg_sentiment (blue) + avg_toxicity (red) over time; flat/declining sentiment = early warning
- [ ] **Controversy Signal** — scatter: toxicity score vs view count per video — do divisive comment sections drive more views for this channel?

**Title Evolution section**
- [ ] **Title Strategy Over Time** — multi-line chart: title length, caps ratio, power word count per month — shows how the channel has iterated on its content strategy

- [ ] Assemble `/channel-analytics/[id]/page.tsx`:
  1. Breadcrumb + channel header (same pattern as predictions/[id])
  2. Growth & Health section (subscriber curve + cadence side by side)
  3. Content Strategy section (duration sweet spot + frequency scatter)
  4. Audience Intelligence section (sentiment trend + controversy scatter)
  5. Title Evolution section (full width)

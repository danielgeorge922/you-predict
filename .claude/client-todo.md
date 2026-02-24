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

- [ ] `app/inference-visualization/page.tsx` — replace `consts/channels.ts` import with `getChannels()` API call; handle loading/error state
- [ ] `app/inference-visualization/[id]/page.tsx` — replace `consts/videos.ts` import with `getChannelVideos(id)` API call; handle loading/error/empty state
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

Planned nav: **[ Predictions ] [ Model Health ] [ Channel Analytics ]**
Replaces: Inference Visualization | Model Performance | Model Monitoring

### I-1: Nav + routing cleanup
- [ ] `components/Header.tsx` — update `routes` array: rename labels and update hrefs
  - `"Inference Visualization"` → `"Predictions"` (href stays `/inference-visualization`)
  - `"Model Performance"` → `"Model Health"` (href: `/model-health`)
  - `"Model Monitoring"` → delete (redirect to `/model-health`)
- [ ] Rename `app/model-performance/` → `app/model-health/`
- [ ] Delete `app/model-monitoring/page.tsx` (or add redirect to `/model-health`)

### I-2: Predictions page enhancements
- [ ] Add `StatBar` component at top of `/inference-visualization` page
  - Fields: videos being monitored, total predictions made, model accuracy
  - Dummy values for now; replace with real API data in Phase D/H
- [ ] `components/VideoCard.tsx` — add `confidence` field to `VideoData` interface (0–1 float)
  - Display as `"Viral — 87% confidence"` next to classification badge
- [ ] `consts/videos.ts` — add `confidence` values to all dummy video entries

### I-3: Model Health page (`app/model-health/page.tsx`)
Merges the old Model Performance + Model Monitoring placeholders into one page.

- [ ] Install Recharts: `npm install recharts` in `client/`
- [ ] Create `consts/modelHealth.ts` — dummy data:
  - Summary metrics (overall accuracy, precision/recall/F1 for viral class)
  - 3×3 confusion matrix values (underperforming / average / viral)
  - Top 10 feature importances (name + importance score)
  - Confidence distribution histogram buckets
  - Model version history (version, trained date, accuracy, status)
- [ ] `components/ConfusionMatrix.tsx` — 3×3 colored grid, diagonal = correct
- [ ] `components/FeatureImportanceChart.tsx` — horizontal bar chart (Recharts)
- [ ] `components/ConfidenceHistogram.tsx` — histogram of prediction confidence scores
- [ ] `app/model-health/page.tsx` — assemble sections:
  1. Summary metric card row (4 cards)
  2. Confusion matrix + feature importance side-by-side
  3. Confidence distribution histogram
  4. Model version timeline table

### I-4: Channel Analytics page (`app/channel-analytics/`)
Product analytics focused — answers "what drives virality on these channels?"

- [ ] Add `"Channel Analytics"` tab to Header routes (href: `/channel-analytics`)
- [ ] Create `consts/channelAnalytics.ts` — dummy data:
  - Per-channel benchmarks: avg_views_30d, viral_rate, engagement_rate, uploads_per_week, subscriber_tier
  - Posting heatmap: 7×24 grid of avg view velocity (day × hour)
  - Velocity curves: 3 arrays of {hour, views} for viral / average / underperforming
- [ ] `components/ChannelBenchmarkTable.tsx` — sortable table (click column header to sort)
  - Columns: Channel, Subscriber Tier, Avg Views, Viral Rate, Engagement Rate, Uploads/wk
  - Tier badge (micro/small/medium/large) with color coding
- [ ] `components/PostingHeatmap.tsx` — 7×24 color grid (Tailwind bg-opacity for intensity)
  - Rows = Mon–Sun, Cols = 12am–11pm, color = view velocity quartile
- [ ] `components/VelocityCurveChart.tsx` — multi-line chart (Recharts LineChart)
  - 3 traces: viral (green), average (yellow), underperforming (red)
  - X = hours since publish (0–72), Y = cumulative views
- [ ] `app/channel-analytics/page.tsx` — assemble sections:
  1. Page header with description
  2. Channel Benchmarks sortable table
  3. Best Time to Post heatmap (with insight callout)
  4. View Velocity Curves (72h window)

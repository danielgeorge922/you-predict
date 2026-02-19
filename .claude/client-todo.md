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
- [ ] Implement `app/model-performance/page.tsx` — show model metrics from `ml_experiment_log`
- [ ] Implement `app/model-monitoring/page.tsx` — show drift detection, accuracy over time from `ml_experiment_log`
- [ ] Wire "Retrain Model" button to trigger `POST /pipelines/train-model` (Phase 9 endpoint)
- [ ] Replace hardcoded version dropdown with real model versions from `ml_model_registry`

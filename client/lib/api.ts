const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function apiFetch<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`API error ${res.status}: ${path}`);
  return res.json() as Promise<T>;
}

// ---------------------------------------------------------------------------
// /analytics/channels  →  TopChannelsTable
// ---------------------------------------------------------------------------
export interface ChannelRow {
  channel_id: string;
  channel_name: string;
  thumbnail_url: string;
  subscriber_count: number;
  view_count: number;
  video_count: number;
  subscriber_growth_rate_30d: number;
  avg_views_per_video_30d: number;
  avg_engagement_rate_30d: number;
  channel_momentum_score: number;
}

export async function fetchChannels(): Promise<ChannelRow[]> {
  const res = await apiFetch<{ data: ChannelRow[] }>("/analytics/channels");
  return res.data;
}

// ---------------------------------------------------------------------------
// /analytics/channel-movers  →  BiggestMoversTable
// ---------------------------------------------------------------------------
export interface ChannelMoverRow {
  channel_id: string;
  channel_name: string;
  thumbnail_url: string;
  views_delta: number;
  subs_delta: number;
  snapshot_date: string;
}

export async function fetchChannelMovers(): Promise<ChannelMoverRow[]> {
  const res = await apiFetch<{ data: ChannelMoverRow[] }>("/analytics/channel-movers");
  return res.data;
}

// ---------------------------------------------------------------------------
// /analytics/summary?days=N  →  StatCards
// ---------------------------------------------------------------------------
export interface SummaryStats {
  total_views_delta: number | null;
  total_subs_delta: number | null;
  videos_published: number | null;
  avg_toxicity_pct: number | null;
}

export async function fetchSummary(days: number): Promise<SummaryStats> {
  return apiFetch<SummaryStats>(`/analytics/summary?days=${days}`);
}

// ---------------------------------------------------------------------------
// Formatting helpers
// ---------------------------------------------------------------------------
export function formatDelta(n: number | null): string {
  if (n === null || n === undefined) return "—";
  const abs = Math.abs(n);
  const sign = n >= 0 ? "+" : "-";
  if (abs >= 1_000_000) return `${sign}${(abs / 1_000_000).toFixed(1)}M`;
  if (abs >= 1_000) return `${sign}${(abs / 1_000).toFixed(1)}K`;
  return `${sign}${abs}`;
}

export function formatCount(n: number | null): string {
  if (n === null || n === undefined) return "—";
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(0)}K`;
  return String(n);
}

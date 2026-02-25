const STAT_CARDS = [
  {
    label: "Total Views Δ (Yesterday)",
    value: "—",
    sub: "vs prior day",
  },
  {
    label: "Total Subs Δ (Yesterday)",
    value: "—",
    sub: "vs prior day",
  },
  {
    label: "Videos Published (7d)",
    value: "16%",
    sub: "across all channels",
  },
  {
    label: "Avg Toxicity (72h)",
    value: "13%",
    sub: "comments sampled",
  },
];

export default STAT_CARDS;

export interface DurationPerformanceRow {
  bucket: string;
  median_perf: number;
}

export const DURATION_PERFORMANCE_DATA: DurationPerformanceRow[] = [
  { bucket: "0–60s", median_perf: 0.71 },
  { bucket: "1–3m", median_perf: 0.94 },
  { bucket: "3–8m", median_perf: 1.15 },
  { bucket: "8–15m", median_perf: 1.28 },
  { bucket: "15m+", median_perf: 1.42 },
];

export interface TopChannelRow {
  name: string;
  avatar: string;
  subs: string;
  growth_30d: string;
  views_per_video: string;
  engagement: string;
  momentum: number;
}

export const TOP_CHANNELS_DATA: TopChannelRow[] = [
  { name: "TechInsights", avatar: "/Daniel.png", subs: "2.4M", growth_30d: "+3.2%", views_per_video: "142K", engagement: "4.8%", momentum: 8.7 },
  { name: "FinanceDaily", avatar: "/Daniel.png", subs: "890K", growth_30d: "+1.8%", views_per_video: "68K", engagement: "3.1%", momentum: 7.4 },
  { name: "CodeWithMike", avatar: "/Daniel.png", subs: "310K", growth_30d: "+5.1%", views_per_video: "29K", engagement: "6.2%", momentum: 9.1 },
  { name: "WorldNewsNow", avatar: "/Daniel.png", subs: "5.1M", growth_30d: "+0.4%", views_per_video: "380K", engagement: "1.9%", momentum: 5.2 },
  { name: "DIYBuilders", avatar: "/Daniel.png", subs: "1.2M", growth_30d: "+2.7%", views_per_video: "95K", engagement: "5.5%", momentum: 7.9 },
  { name: "GameVault", avatar: "/Daniel.png", subs: "640K", growth_30d: "-0.3%", views_per_video: "41K", engagement: "2.8%", momentum: 4.1 },
];

export interface ToxicityScatterPoint {
  perf: number;
  toxicity: number;
  comments: number;
  channel: string;
}

export const TOXICITY_SCATTER_DATA: ToxicityScatterPoint[] = [
  { perf: 1.82, toxicity: 0.08, comments: 420, channel: "TechInsights" },
  { perf: 0.64, toxicity: 0.31, comments: 180, channel: "WorldNewsNow" },
  { perf: 1.45, toxicity: 0.12, comments: 310, channel: "CodeWithMike" },
  { perf: 0.92, toxicity: 0.22, comments: 95, channel: "FinanceDaily" },
  { perf: 2.10, toxicity: 0.06, comments: 540, channel: "TechInsights" },
  { perf: 0.48, toxicity: 0.45, comments: 870, channel: "WorldNewsNow" },
  { perf: 1.21, toxicity: 0.18, comments: 230, channel: "DIYBuilders" },
  { perf: 0.73, toxicity: 0.29, comments: 140, channel: "GameVault" },
  { perf: 1.67, toxicity: 0.09, comments: 390, channel: "CodeWithMike" },
  { perf: 0.55, toxicity: 0.38, comments: 610, channel: "WorldNewsNow" },
  { perf: 1.33, toxicity: 0.15, comments: 275, channel: "DIYBuilders" },
  { perf: 0.89, toxicity: 0.24, comments: 120, channel: "FinanceDaily" },
  { perf: 1.95, toxicity: 0.05, comments: 480, channel: "TechInsights" },
  { perf: 0.61, toxicity: 0.41, comments: 760, channel: "WorldNewsNow" },
  { perf: 1.10, toxicity: 0.20, comments: 200, channel: "GameVault" },
];

export interface BiggestMoverRow {
  channel: string;
  avatar: string;
  views_delta: string;
  subs_delta: string;
  views_positive: boolean;
  subs_positive: boolean;
}

export const BIGGEST_MOVERS_DATA: BiggestMoverRow[] = [
  { channel: "TechInsights", avatar: "/Daniel.png", views_delta: "+284K", subs_delta: "+1.2K", views_positive: true, subs_positive: true },
  { channel: "CodeWithMike", avatar: "/Daniel.png", views_delta: "+97K", subs_delta: "+880", views_positive: true, subs_positive: true },
  { channel: "WorldNewsNow", avatar: "/Daniel.png", views_delta: "+531K", subs_delta: "-340", views_positive: true, subs_positive: false },
  { channel: "DIYBuilders", avatar: "/Daniel.png", views_delta: "+143K", subs_delta: "+560", views_positive: true, subs_positive: true },
  { channel: "GameVault", avatar: "/Daniel.png", views_delta: "-18K", subs_delta: "-210", views_positive: false, subs_positive: false },
  { channel: "FinanceDaily", avatar: "/Daniel.png", views_delta: "+62K", subs_delta: "+190", views_positive: true, subs_positive: true },
];

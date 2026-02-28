const STAT_CARDS = [
  {
    label: "Total Views Δ (Yesterday)",
    value: "+6.2M",
    sub: "vs prior day",
  },
  {
    label: "Total Subs Δ (Yesterday)",
    value: "+10.0K",
    sub: "vs prior day",
  },
  {
    label: "Videos Published (7d)",
    value: "35",
    sub: "across all channels",
  },
  {
    label: "Avg Toxicity (72h)",
    value: "—",
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
  { name: "EpicRoberto", avatar: "https://yt3.ggpht.com/xtHf63u-ReyMuWFN-rAsODVcZxTAWK7xUtT3DGf49dyGHXeKXbDHkw_9PM7zaUM5vaaK7gCo=s800-c-k-c0x00ffffff-no-rj", subs: "103", growth_30d: "+0.0%", views_per_video: "1", engagement: "+0.0%", momentum: 0.0 },
  { name: "Ashnflash", avatar: "https://yt3.ggpht.com/geXi0g-H4Iy9ep4b1a3jH9rzIWu8E-pfpLUE2oZHaMlX5qVHirzKjRm3TmDY4WmYPccPn0oYNw=s800-c-k-c0x00ffffff-no-rj", subs: "338K", growth_30d: "+0.0%", views_per_video: "10K", engagement: "+5.5%", momentum: 0.0 },
  { name: "Max Euceda", avatar: "https://yt3.ggpht.com/1FUsE21qbR3hjBQIkqKnQuXVftgwq2znieFddFdjcVeTlfE4QsYga4Uwbhkfly1iAslzo4vuBQ=s800-c-k-c0x00ffffff-no-rj", subs: "1.2M", growth_30d: "+0.0%", views_per_video: "5K", engagement: "+6.3%", momentum: 0.0 },
  { name: "supertf", avatar: "https://yt3.ggpht.com/SkCJLEgoplj1Sz0up7aDn5WZGbZz6muxop6LMtgEnoS48FmhURoYMF1GejEpM4R0athPzb-5=s800-c-k-c0x00ffffff-no-rj", subs: "397K", growth_30d: "+0.0%", views_per_video: "130K", engagement: "+5.4%", momentum: 0.0 },
  { name: "Sam Sulek", avatar: "https://yt3.ggpht.com/H3ehrP8Mfb5MjbV3CQ3uwFMe-GisGvVzNHPUcw_u8CL7vA3Od7lveegfGqBz6KYKVej7EncHkQ=s800-c-k-c0x00ffffff-no-rj", subs: "4.4M", growth_30d: "+0.0%", views_per_video: "108K", engagement: "+4.7%", momentum: 0.0 },
  { name: "Seatin Man of Legends", avatar: "https://yt3.ggpht.com/ytc/AIdro_ldSafeeJnu8p3rt2Ydvg1jxCcNjJVftGIVdoJUnfrYKjU=s800-c-k-c0x00ffffff-no-rj", subs: "324K", growth_30d: "+0.0%", views_per_video: "14K", engagement: "+5.8%", momentum: 0.0 },
  { name: "penguinz0", avatar: "https://yt3.ggpht.com/ytc/AIdro_kOWn68FmChjExAEGw0vjLBpiP907ccNT5wASHcBjZeEuA=s800-c-k-c0x00ffffff-no-rj", subs: "17.8M", growth_30d: "+0.0%", views_per_video: "1.0M", engagement: "+3.8%", momentum: 0.0 },
];

export interface ToxicityScatterPoint {
  perf: number;
  toxicity: number;
  comments: number;
  channel: string;
}

export const TOXICITY_SCATTER_DATA: ToxicityScatterPoint[] = [
  { perf: 1.82, toxicity: 0.08, comments: 420, channel: "—" },
  { perf: 0.64, toxicity: 0.31, comments: 180, channel: "—" },
  { perf: 1.45, toxicity: 0.12, comments: 310, channel: "—" },
  { perf: 0.92, toxicity: 0.22, comments: 95,  channel: "—" },
  { perf: 2.10, toxicity: 0.06, comments: 540, channel: "—" },
  { perf: 0.48, toxicity: 0.45, comments: 870, channel: "—" },
  { perf: 1.21, toxicity: 0.18, comments: 230, channel: "—" },
  { perf: 0.73, toxicity: 0.29, comments: 140, channel: "—" },
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
  { channel: "penguinz0", avatar: "https://yt3.ggpht.com/ytc/AIdro_kOWn68FmChjExAEGw0vjLBpiP907ccNT5wASHcBjZeEuA=s800-c-k-c0x00ffffff-no-rj", views_delta: "+5.0M", subs_delta: "+0", views_positive: true, subs_positive: true },
  { channel: "Sam Sulek", avatar: "https://yt3.ggpht.com/H3ehrP8Mfb5MjbV3CQ3uwFMe-GisGvVzNHPUcw_u8CL7vA3Od7lveegfGqBz6KYKVej7EncHkQ=s800-c-k-c0x00ffffff-no-rj", views_delta: "+401.7K", subs_delta: "+10.0K", views_positive: true, subs_positive: true },
  { channel: "supertf", avatar: "https://yt3.ggpht.com/SkCJLEgoplj1Sz0up7aDn5WZGbZz6muxop6LMtgEnoS48FmhURoYMF1GejEpM4R0athPzb-5=s800-c-k-c0x00ffffff-no-rj", views_delta: "+385.1K", subs_delta: "+0", views_positive: true, subs_positive: true },
  { channel: "Max Euceda", avatar: "https://yt3.ggpht.com/1FUsE21qbR3hjBQIkqKnQuXVftgwq2znieFddFdjcVeTlfE4QsYga4Uwbhkfly1iAslzo4vuBQ=s800-c-k-c0x00ffffff-no-rj", views_delta: "+307.8K", subs_delta: "+0", views_positive: true, subs_positive: true },
  { channel: "Ashnflash", avatar: "https://yt3.ggpht.com/geXi0g-H4Iy9ep4b1a3jH9rzIWu8E-pfpLUE2oZHaMlX5qVHirzKjRm3TmDY4WmYPccPn0oYNw=s800-c-k-c0x00ffffff-no-rj", views_delta: "+51.2K", subs_delta: "+0", views_positive: true, subs_positive: true },
  { channel: "Seatin Man of Legends", avatar: "https://yt3.ggpht.com/ytc/AIdro_ldSafeeJnu8p3rt2Ydvg1jxCcNjJVftGIVdoJUnfrYKjU=s800-c-k-c0x00ffffff-no-rj", views_delta: "+43.2K", subs_delta: "+0", views_positive: true, subs_positive: true },
  { channel: "EpicRoberto", avatar: "https://yt3.ggpht.com/xtHf63u-ReyMuWFN-rAsODVcZxTAWK7xUtT3DGf49dyGHXeKXbDHkw_9PM7zaUM5vaaK7gCo=s800-c-k-c0x00ffffff-no-rj", views_delta: "+0", subs_delta: "+0", views_positive: true, subs_positive: true },
];

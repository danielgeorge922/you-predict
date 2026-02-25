import STAT_CARDS from "@/consts/channelAnalyticsGeneral";
import StatCard from "@/components/channelAnalytics/StatCard";
import React from "react";

/**
 * General / All-Channels Analytics dashboard
 * Goal: quick market overview + discovery + “what works” insights
 *
 * Your empty rows become:
 * Row 1: 4 Stat Cards (yesterday + 30d rollups)
 * Row 2: Global “What works” chart + Top Channels table
 * Row 3: Toxicity vs Performance scatter + Movers table (spikes)
 */
const ChannelAnalyticsPage = () => {
  return (
    <div className="p-8 w-full space-y-8">
      <div className="flex items-end justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Channel Analytics</h1>
          <p className="text-sm text-muted-foreground">
            All channels overview — trends, leaders, and cross-channel patterns.
          </p>
        </div>

        {/* Optional: global controls */}
        <div className="flex gap-2">
          {/* Date range dropdown: 7d / 30d / 90d */}
          {/* Subscriber tier filter */}
          {/* Topic filter */}
          dasojo
        </div>
      </div>

      {/* Row 1: 4 Stat Cards (STAT CARDS) */}
      {/* Suggested metrics:
          1) Total Views Δ (Yesterday)  -> sum(fact_channel_snapshot.views_delta latest day)
          2) Total Subs Δ (Yesterday)   -> sum(fact_channel_snapshot.subs_delta latest day)
          3) Videos Published (7d)      -> count(dim_video where published_at in last 7d)
          4) Avg Toxicity (24h/72h)     -> avg(ml_feature_comment_aggregates.avg_toxicity for vids in range)
      */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {STAT_CARDS.map((card) => (
          <StatCard
            key={card.label}
            title={card.label}
            value={card.value}
            change={card.sub}
          />
        ))}
      </div>

      {/* Row 2: "What Works" + Top Channels table */}
      {/* Left chart options (pick ONE for v1):
          A) Best Posting Times Heatmap (Hour x Day) using ml_feature_temporal + performance_vs_channel_avg
          B) Duration Bucket vs Performance (horizontal bar) using ml_feature_video_content.duration_bucket + performance_vs_channel_avg
         Since your comment says "sideways bar chart", use (B).
      */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">
        {/* Left: Horizontal bar chart */}
        <div className="rounded-xl border p-4 lg:col-span-2">
          <div className="flex items-center justify-between mb-2">
            <h2 className="text-lg font-semibold">
              What Works: Duration vs Performance
            </h2>
            <span className="text-xs text-muted-foreground">
              metric: median performance_vs_channel_avg
            </span>
          </div>

          {/* CHART: Horizontal bar chart
              X: median performance_vs_channel_avg (or views_72h normalized)
              Y: duration_bucket (e.g., 0-60s, 1-3m, 3-8m, 8-15m, 15m+)
          */}
          <div className="h-72 rounded-lg bg-muted/30 flex items-center justify-center text-sm text-muted-foreground">
            Horizontal Bar Chart Placeholder
          </div>

          <p className="mt-3 text-xs text-muted-foreground">
            Use this to tell a simple global story: “Across all channels, this
            duration band tends to outperform.”
          </p>
        </div>

        {/* Right: Top channels table */}
        {/* Table metric options (keep to 5-6 cols):
            channel_name, subscriber_count, subscriber_growth_rate_30d,
            avg_views_per_video_30d, avg_engagement_rate_30d, channel_momentum_score
        */}
        <div className="rounded-xl border p-4 lg:col-span-3">
          <div className="flex items-center justify-between mb-2">
            <h2 className="text-lg font-semibold">
              Top Channels (30d Momentum)
            </h2>
            <span className="text-xs text-muted-foreground">
              source: ml_feature_channel (latest computed_date)
            </span>
          </div>

          <div className="overflow-auto rounded-lg border">
            <table className="w-full text-sm">
              <thead className="bg-muted/40 text-muted-foreground">
                <tr>
                  <th className="text-left p-3">Channel</th>
                  <th className="text-right p-3">Subs</th>
                  <th className="text-right p-3">30d Growth</th>
                  <th className="text-right p-3">Views/Video (30d)</th>
                  <th className="text-right p-3">Engagement (30d)</th>
                  <th className="text-right p-3">Momentum</th>
                </tr>
              </thead>
              <tbody>
                {/* Map rows here */}
                <tr className="border-t">
                  <td className="p-3">—</td>
                  <td className="p-3 text-right">—</td>
                  <td className="p-3 text-right">—</td>
                  <td className="p-3 text-right">—</td>
                  <td className="p-3 text-right">—</td>
                  <td className="p-3 text-right">—</td>
                </tr>
              </tbody>
            </table>
          </div>

          <p className="mt-3 text-xs text-muted-foreground">
            Clicking a row should navigate to the channel-specific analytics
            page.
          </p>
        </div>
      </div>

      {/* Row 3: Toxicity vs Performance + Biggest Movers */}
      {/* Left chart:
          Scatter plot across videos (or channels) showing relationship between toxicity and performance.
          Best with videos:
            X: performance_vs_channel_avg
            Y: toxic_ratio (or avg_toxicity)
            Size: comments_sampled
            Color (optional): subscriber_tier or duration_bucket
      */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">
        <div className="rounded-xl border p-4 lg:col-span-3">
          <div className="flex items-center justify-between mb-2">
            <h2 className="text-lg font-semibold">
              Audience Reaction: Toxicity vs Performance
            </h2>
            <span className="text-xs text-muted-foreground">
              videos with 72h window
            </span>
          </div>

          <div className="h-80 rounded-lg bg-muted/30 flex items-center justify-center text-sm text-muted-foreground">
            Scatter Plot Placeholder
          </div>

          <p className="mt-3 text-xs text-muted-foreground">
            This is your “signature” chart — it differentiates YouPredict from
            generic YouTube dashboards.
          </p>
        </div>

        {/* Right: Movers table (daily deltas / anomalies) */}
        {/* Use latest day from fact_channel_snapshot:
            channel_name, views_delta, subs_delta, videos_delta
           Optional: spike_score (z-score vs 30d)
        */}
        <div className="rounded-xl border p-4 lg:col-span-2">
          <div className="flex items-center justify-between mb-2">
            <h2 className="text-lg font-semibold">
              Biggest Movers (Yesterday)
            </h2>
            <span className="text-xs text-muted-foreground">
              source: fact_channel_snapshot (latest snapshot_date)
            </span>
          </div>

          <div className="overflow-auto rounded-lg border">
            <table className="w-full text-sm">
              <thead className="bg-muted/40 text-muted-foreground">
                <tr>
                  <th className="text-left p-3">Channel</th>
                  <th className="text-right p-3">Views Δ</th>
                  <th className="text-right p-3">Subs Δ</th>
                </tr>
              </thead>
              <tbody>
                <tr className="border-t">
                  <td className="p-3">—</td>
                  <td className="p-3 text-right">—</td>
                  <td className="p-3 text-right">—</td>
                </tr>
              </tbody>
            </table>
          </div>

          <p className="mt-3 text-xs text-muted-foreground">
            This answers “what changed since yesterday?” and makes the dashboard
            feel alive.
          </p>
        </div>
      </div>
    </div>
  );
};

export default ChannelAnalyticsPage;

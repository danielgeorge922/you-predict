import React from "react";

/**
 * Channel-Specific Analytics page
 * Goal: diagnose this channel + show what to do next
 *
 * Sections:
 * 1) Header (channel identity + quick filters)
 * 2) Row 1: 4 stat cards (channel health)
 * 3) Row 2: Growth timeline + Upload cadence/consistency
 * 4) Row 3: Recent videos performance table + Velocity curves (72h)
 * 5) Row 4: Audience reaction (sentiment/toxicity) + “high-toxicity/high-perf” list
 * 6) Row 5: Auto Insights (best time, duration, title patterns)
 */
const ChannelAnalyticsPage = () => {
  return (
    <div className="p-8 w-full space-y-8">
      {/* Header */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div className="flex items-center gap-3">
          {/* Channel thumbnail */}
          <div className="h-12 w-12 rounded-lg bg-muted/40 border" />
          <div>
            <h1 className="text-2xl font-semibold">Channel Name</h1>
            <p className="text-sm text-muted-foreground">
              Channel-specific analytics — growth, content performance, and
              audience reaction.
            </p>
          </div>
        </div>

        {/* Controls */}
        <div className="flex flex-wrap gap-2">
          {/* Date range: 7d / 30d / 90d */}
          {/* Cohort: last N videos / videos in range */}
          {/* Toggle: Longform / Shorts (duration_bucket) */}
          {/* Toggle: Include livestreams */}
          <div className="h-9 w-28 rounded-md border bg-background" />
          <div className="h-9 w-32 rounded-md border bg-background" />
          <div className="h-9 w-32 rounded-md border bg-background" />
        </div>
      </div>

      {/* Row 1: 4 Stat Cards (channel health snapshot) */}
      {/* Suggested cards:
          1) Subscribers (30d Δ) -> dim_channel.subscriber_count + sum(subs_delta 30d)
          2) Views (30d Δ)       -> sum(views_delta 30d)
          3) Upload Frequency    -> ml_feature_channel.upload_frequency_7d / 30d
          4) Momentum / Consistency -> channel_momentum_score + view_consistency_score
      */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="rounded-xl border p-4">
          <p className="text-sm text-muted-foreground">Subscribers (30d Δ)</p>
          <p className="text-2xl font-semibold">—</p>
          <p className="text-xs text-muted-foreground">
            current subs + 30d change
          </p>
        </div>

        <div className="rounded-xl border p-4">
          <p className="text-sm text-muted-foreground">Views (30d Δ)</p>
          <p className="text-2xl font-semibold">—</p>
          <p className="text-xs text-muted-foreground">total views gained</p>
        </div>

        <div className="rounded-xl border p-4">
          <p className="text-sm text-muted-foreground">Upload Frequency</p>
          <p className="text-2xl font-semibold">—</p>
          <p className="text-xs text-muted-foreground">7d / 30d uploads</p>
        </div>

        <div className="rounded-xl border p-4">
          <p className="text-sm text-muted-foreground">
            Momentum / Consistency
          </p>
          <p className="text-2xl font-semibold">—</p>
          <p className="text-xs text-muted-foreground">
            momentum + consistency score
          </p>
        </div>
      </div>

      {/* Row 2: Growth timeline + upload cadence */}
      {/* Left: time series from fact_channel_snapshot (views/subs)
         Right: small cards or chart:
            - avg_time_between_uploads_7d
            - days_since_last_upload (from ml_feature_temporal aggregated to latest)
            - view_consistency_score
      */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">
        <div className="rounded-xl border p-4 lg:col-span-3">
          <div className="flex items-center justify-between mb-2">
            <h2 className="text-lg font-semibold">Growth Trend</h2>
            <span className="text-xs text-muted-foreground">
              source: fact_channel_snapshot
            </span>
          </div>

          {/* CHART: Line chart (toggle Views/Subs) */}
          <div className="h-80 rounded-lg bg-muted/30 flex items-center justify-center text-sm text-muted-foreground">
            Line Chart Placeholder (Views & Subs over time)
          </div>

          <p className="mt-3 text-xs text-muted-foreground">
            Optional: mark publish dates from dim_video as vertical markers to
            connect uploads → growth.
          </p>
        </div>

        <div className="rounded-xl border p-4 lg:col-span-2 space-y-3">
          <h2 className="text-lg font-semibold">
            Heat Map for weekday uploaded and avg views
          </h2>

          <div className="rounded-lg border p-3">
            <p className="text-sm text-muted-foreground">
              Avg time between uploads (7d)
            </p>
            <p className="text-xl font-semibold">—</p>
          </div>

          <div className="rounded-lg border p-3">
            <p className="text-sm text-muted-foreground">
              Days since last upload
            </p>
            <p className="text-xl font-semibold">—</p>
          </div>

          <div className="rounded-lg border p-3">
            <p className="text-sm text-muted-foreground">
              View consistency score
            </p>
            <p className="text-xl font-semibold">—</p>
          </div>

          <div className="rounded-lg border p-3">
            <p className="text-sm text-muted-foreground">
              Engagement rate (30d)
            </p>
            <p className="text-xl font-semibold">—</p>
          </div>
        </div>
      </div>

      {/* Row 3: Recent videos table + 72h velocity curves */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">
        {/* Recent videos performance table */}
        {/* Columns:
            title, published_at, duration_bucket,
            views_72h, peak_velocity, engagement_acceleration,
            performance_vs_channel_avg, toxic_ratio
        */}
        <div className="rounded-xl border p-4 lg:col-span-3">
          <div className="flex items-center justify-between mb-2">
            <h2 className="text-lg font-semibold">
              Recent Uploads Performance (72h)
            </h2>
            <span className="text-xs text-muted-foreground">
              source: ml_feature_video_performance +
              ml_feature_comment_aggregates
            </span>
          </div>

          <div className="overflow-auto rounded-lg border">
            <table className="w-full text-sm">
              <thead className="bg-muted/40 text-muted-foreground">
                <tr>
                  <th className="text-left p-3">Video</th>
                  <th className="text-right p-3">Views 72h</th>
                  <th className="text-right p-3">vs Avg</th>
                  <th className="text-right p-3">Peak Vel</th>
                  <th className="text-right p-3">Toxic %</th>
                </tr>
              </thead>
              <tbody>
                <tr className="border-t">
                  <td className="p-3">—</td>
                  <td className="p-3 text-right">—</td>
                  <td className="p-3 text-right">—</td>
                  <td className="p-3 text-right">—</td>
                  <td className="p-3 text-right">—</td>
                </tr>
              </tbody>
            </table>
          </div>

          <p className="mt-3 text-xs text-muted-foreground">
            Make rows clickable → open video detail drawer (optional) or jump to
            a video page.
          </p>
        </div>

        {/* Velocity curves */}
        <div className="rounded-xl border p-4 lg:col-span-2">
          <div className="flex items-center justify-between mb-2">
            <h2 className="text-lg font-semibold">72h Velocity Curves</h2>
            <span className="text-xs text-muted-foreground">
              views_1h → views_72h
            </span>
          </div>

          {/* CHART: Multi-line showing top 3 videos + channel median curve */}
          <div className="h-80 rounded-lg bg-muted/30 flex items-center justify-center text-sm text-muted-foreground">
            Velocity Curves Placeholder
          </div>

          <p className="mt-3 text-xs text-muted-foreground">
            This is a strong portfolio chart: compare early velocity to final
            outcome.
          </p>
        </div>
      </div>

      {/* Row 4: Audience reaction (sentiment/toxicity) */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">
        {/* Left: sentiment/toxicity trends or distribution */}
        <div className="rounded-xl border p-4 lg:col-span-3">
          <div className="flex items-center justify-between mb-2">
            <h2 className="text-lg font-semibold">Audience Reaction</h2>
            <span className="text-xs text-muted-foreground">
              source: ml_feature_comment_aggregates
            </span>
          </div>

          {/* CHART OPTIONS (pick one for v1):
              A) Scatter: performance_vs_channel_avg vs toxic_ratio (within this channel)
              B) Bar: toxic_ratio by recent videos
              C) Line: avg_toxicity over publish date (cohort)
          */}
          <div className="h-80 rounded-lg bg-muted/30 flex items-center justify-center text-sm text-muted-foreground">
            Reaction Chart Placeholder (Toxicity / Sentiment)
          </div>

          <div className="mt-3 grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="rounded-lg border p-3">
              <p className="text-xs text-muted-foreground">Avg Sentiment</p>
              <p className="text-lg font-semibold">—</p>
            </div>
            <div className="rounded-lg border p-3">
              <p className="text-xs text-muted-foreground">Toxic Ratio</p>
              <p className="text-lg font-semibold">—</p>
            </div>
            <div className="rounded-lg border p-3">
              <p className="text-xs text-muted-foreground">Unique Commenters</p>
              <p className="text-lg font-semibold">—</p>
            </div>
            <div className="rounded-lg border p-3">
              <p className="text-xs text-muted-foreground">Creator Replies</p>
              <p className="text-lg font-semibold">—</p>
            </div>
          </div>
        </div>

        {/* Right: “Notable” list */}
        {/* Two tabs:
            - High Performance + Low Toxicity (winners)
            - High Performance + High Toxicity (controversial)
        */}
        <div className="rounded-xl border p-4 lg:col-span-2">
          <div className="flex items-center justify-between mb-2">
            <h2 className="text-lg font-semibold">Notable Videos</h2>
            <span className="text-xs text-muted-foreground">quadrants</span>
          </div>

          <div className="space-y-2">
            <div className="rounded-lg border p-3">
              <p className="text-sm font-medium">High perf • Low toxicity</p>
              <p className="text-xs text-muted-foreground">
                Top candidates to replicate
              </p>
            </div>
            <div className="rounded-lg border p-3">
              <p className="text-sm font-medium">High perf • High toxicity</p>
              <p className="text-xs text-muted-foreground">
                Controversial content bucket
              </p>
            </div>
            <div className="rounded-lg border p-3">
              <p className="text-sm font-medium">Low perf • High toxicity</p>
              <p className="text-xs text-muted-foreground">
                Avoid patterns here
              </p>
            </div>
          </div>

          <p className="mt-3 text-xs text-muted-foreground">
            Each item can open a drawer with top comments (from fact_comment) if
            you want to flex.
          </p>
        </div>
      </div>

      {/* Row 5: Auto Insights (the “coach” section) */}
      {/* Compute these as simple comparisons vs channel baseline:
          - best day/time to post
          - best duration_bucket
          - title patterns (has_number, has_question, caps_ratio bins)
          - topic keywords (from transcript) correlated with performance/toxicity
      */}
      <div className="rounded-xl border p-4">
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-lg font-semibold">Actionable Insights</h2>
          <span className="text-xs text-muted-foreground">rules-based</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <div className="rounded-lg border p-4">
            <p className="text-sm font-medium">Best posting window</p>
            <p className="text-xs text-muted-foreground mt-1">
              Example: Tue–Thu 4–7pm performs +18% vs channel baseline
            </p>
          </div>

          <div className="rounded-lg border p-4">
            <p className="text-sm font-medium">Best duration band</p>
            <p className="text-xs text-muted-foreground mt-1">
              Example: 8–15 min videos outperform by +11%
            </p>
          </div>

          <div className="rounded-lg border p-4">
            <p className="text-sm font-medium">Title pattern that wins</p>
            <p className="text-xs text-muted-foreground mt-1">
              Example: Titles with numbers perform +9% median vs no-number
              titles
            </p>
          </div>
        </div>

        <p className="mt-3 text-xs text-muted-foreground">
          This section makes your product feel “smart” without needing heavy ML.
        </p>
      </div>
    </div>
  );
};

export default ChannelAnalyticsPage;

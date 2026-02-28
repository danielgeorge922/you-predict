"""One-time BigQuery pull → prints updated channelAnalyticsGeneral.ts to stdout.

Usage:
  uv run python -m src.scripts.export_dashboard_data

Paste the output into client/consts/channelAnalyticsGeneral.ts.
"""

import sys

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]

from src.config.clients import get_bq_client, get_settings
from src.data_sources.bigquery import BigQueryService

# ── helpers ──────────────────────────────────────────────────────────────────

def fmt_count(n: int | float | None) -> str:
    if n is None:
        return "—"
    n = int(n)
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.0f}K"
    return str(n)


def fmt_delta(n: int | float | None) -> str:
    if n is None:
        return "—"
    n = int(n)
    sign = "+" if n >= 0 else "-"
    abs_n = abs(n)
    if abs_n >= 1_000_000:
        return f"{sign}{abs_n / 1_000_000:.1f}M"
    if abs_n >= 1_000:
        return f"{sign}{abs_n / 1_000:.1f}K"
    return f"{sign}{abs_n}"


def fmt_pct(rate: float | None) -> str:
    if rate is None:
        return "—"
    sign = "+" if rate >= 0 else ""
    return f"{sign}{rate * 100:.1f}%"


# ── queries ──────────────────────────────────────────────────────────────────

TOP_CHANNELS_SQL = """
SELECT
  c.channel_id,
  c.channel_name,
  COALESCE(c.channel_thumbnail_url, '') AS channel_thumbnail_url,
  COALESCE(c.subscriber_count, 0) AS subscriber_count,
  COALESCE(f.subscriber_growth_rate_30d, 0.0) AS growth_30d,
  COALESCE(f.avg_views_per_video_30d, 0.0) AS views_per_video,
  COALESCE(f.avg_engagement_rate_30d, 0.0) AS engagement,
  COALESCE(f.channel_momentum_score, 0.0) AS momentum
FROM `{project}.{dataset}.dim_channel` c
LEFT JOIN (
  SELECT *
  FROM `{project}.{dataset}.ml_feature_channel`
  WHERE computed_date = (
    SELECT MAX(computed_date) FROM `{project}.{dataset}.ml_feature_channel`
  )
) f ON c.channel_id = f.channel_id
ORDER BY f.channel_momentum_score DESC NULLS LAST
"""

MOVERS_SQL = """
SELECT
  c.channel_name,
  COALESCE(c.channel_thumbnail_url, '') AS channel_thumbnail_url,
  s.views_delta,
  s.subs_delta
FROM `{project}.{dataset}.fact_channel_snapshot` s
JOIN `{project}.{dataset}.dim_channel` c ON s.channel_id = c.channel_id
WHERE s.snapshot_date = (
  SELECT MAX(snapshot_date) FROM `{project}.{dataset}.fact_channel_snapshot`
)
ORDER BY ABS(s.views_delta) DESC NULLS LAST
"""

SUMMARY_SQL = """
SELECT
  COALESCE(SUM(views_delta), 0) AS total_views_delta,
  COALESCE(SUM(subs_delta), 0)  AS total_subs_delta
FROM `{project}.{dataset}.fact_channel_snapshot`
WHERE snapshot_date = (
  SELECT MAX(snapshot_date) FROM `{project}.{dataset}.fact_channel_snapshot`
)
"""

VIDEOS_SQL = """
SELECT COUNT(*) AS video_count
FROM `{project}.{dataset}.dim_video`
WHERE DATE(published_at) >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
"""


# ── main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    settings = get_settings()
    bq = BigQueryService(get_bq_client(), settings.gcp_project_id, settings.bq_dataset)

    print("Querying BigQuery...", file=sys.stderr)

    try:
        top_rows = bq.run_query(TOP_CHANNELS_SQL)
    except Exception as e:
        print(f"  top_channels query failed: {e}", file=sys.stderr)
        top_rows = []

    try:
        mover_rows = bq.run_query(MOVERS_SQL)
    except Exception as e:
        print(f"  movers query failed: {e}", file=sys.stderr)
        mover_rows = []

    try:
        summary_rows = bq.run_query(SUMMARY_SQL)
        summary = summary_rows[0] if summary_rows else {}
    except Exception as e:
        print(f"  summary query failed: {e}", file=sys.stderr)
        summary = {}

    try:
        vid_rows = bq.run_query(VIDEOS_SQL)
        videos_published = int(vid_rows[0]["video_count"]) if vid_rows else 0
    except Exception as e:
        print(f"  videos query failed: {e}", file=sys.stderr)
        videos_published = 0

    print("Done. Output below:\n", file=sys.stderr)

    # ── build TypeScript output ───────────────────────────────────────────────

    # STAT_CARDS
    total_views = summary.get("total_views_delta")
    total_subs = summary.get("total_subs_delta")

    print("""const STAT_CARDS = [
  {
    label: "Total Views Δ (Yesterday)",""")
    print(f'    value: "{fmt_delta(total_views)}",')
    print("""    sub: "vs prior day",
  },
  {
    label: "Total Subs Δ (Yesterday)",""")
    print(f'    value: "{fmt_delta(total_subs)}",')
    print("""    sub: "vs prior day",
  },
  {
    label: "Videos Published (7d)",""")
    print(f'    value: "{videos_published}",')
    print("""    sub: "across all channels",
  },
  {
    label: "Avg Toxicity (72h)",
    value: "—",
    sub: "comments sampled",
  },
];

export default STAT_CARDS;
""")

    # DURATION_PERFORMANCE_DATA (unchanged — no SQL data for this yet)
    print("""export interface DurationPerformanceRow {
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
""")

    # TOP_CHANNELS_DATA
    print("""export interface TopChannelRow {
  name: string;
  avatar: string;
  subs: string;
  growth_30d: string;
  views_per_video: string;
  engagement: string;
  momentum: number;
}
""")
    print("export const TOP_CHANNELS_DATA: TopChannelRow[] = [")
    for r in top_rows:
        name = r["channel_name"].replace('"', '\\"')
        avatar = r["channel_thumbnail_url"] or "/Daniel.png"
        subs = fmt_count(r["subscriber_count"])
        growth = fmt_pct(r.get("growth_30d"))
        vpv = fmt_count(r.get("views_per_video"))
        eng = fmt_pct(r.get("engagement"))
        momentum = round(float(r.get("momentum") or 0), 1)
        print(f'  {{ name: "{name}", avatar: "{avatar}", subs: "{subs}", growth_30d: "{growth}", views_per_video: "{vpv}", engagement: "{eng}", momentum: {momentum} }},')
    print("];\n")

    # TOXICITY_SCATTER_DATA (unchanged — no SQL data yet)
    print("""export interface ToxicityScatterPoint {
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
""")

    # BIGGEST_MOVERS_DATA
    print("""export interface BiggestMoverRow {
  channel: string;
  avatar: string;
  views_delta: string;
  subs_delta: string;
  views_positive: boolean;
  subs_positive: boolean;
}
""")
    print("export const BIGGEST_MOVERS_DATA: BiggestMoverRow[] = [")
    for r in mover_rows:
        name = r["channel_name"].replace('"', '\\"')
        avatar = r["channel_thumbnail_url"] or "/Daniel.png"
        vd = int(r.get("views_delta") or 0)
        sd = int(r.get("subs_delta") or 0)
        print(
            f'  {{ channel: "{name}", avatar: "{avatar}", '
            f'views_delta: "{fmt_delta(vd)}", subs_delta: "{fmt_delta(sd)}", '
            f'views_positive: {"true" if vd >= 0 else "false"}, '
            f'subs_positive: {"true" if sd >= 0 else "false"} }},'
        )
    print("];")


if __name__ == "__main__":
    main()

"""Feature execution order registry.

channel must run before video_performance because video_performance.sql
joins ml_feature_channel to compute performance_vs_channel_avg.
All other features are independent and can run in any order.
"""

FEATURE_EXECUTION_ORDER: list[str] = [
    "channel",           # independent — must run first
    "video_performance", # depends on ml_feature_channel
    "video_content",     # independent
    "temporal",          # independent
    "comment_aggregates", # independent
]

"""Video monitoring lifecycle model."""

from datetime import datetime

from pydantic import BaseModel


class VideoMonitoring(BaseModel):
    video_id: str
    channel_id: str
    published_at: datetime
    discovered_at: datetime
    monitoring_until: datetime
    first_seen_at: datetime
    is_active: bool = True
    inactive_reason: str | None = None

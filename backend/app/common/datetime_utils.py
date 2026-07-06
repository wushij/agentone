"""backend/app/common/datetime_utils.py"""

from __future__ import annotations

from datetime import datetime, timezone


def serialize_datetime(dt: datetime | None) -> str | None:
    """Serialize DB datetimes as UTC ISO-8601 with Z suffix."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    return dt.isoformat().replace("+00:00", "Z")

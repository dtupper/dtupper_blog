"""Publication timestamps: naive values mean UTC; explicit offsets are retained."""

from datetime import date, datetime, timezone


def parse_date(value: date | str) -> datetime:
    if isinstance(value, str):
        value = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if not isinstance(value, datetime):
        value = datetime.combine(value, datetime.min.time())
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value

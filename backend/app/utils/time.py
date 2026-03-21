from datetime import datetime, timezone
from zoneinfo import ZoneInfo

HK_TZ = ZoneInfo("Asia/Hong_Kong")


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def ensure_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def to_hk(value: datetime | None) -> datetime | None:
    utc_value = ensure_utc(value)
    if utc_value is None:
        return None
    return utc_value.astimezone(HK_TZ)


def to_iso(value: datetime | None) -> str | None:
    utc_value = ensure_utc(value)
    if utc_value is None:
        return None
    return utc_value.isoformat().replace("+00:00", "Z")

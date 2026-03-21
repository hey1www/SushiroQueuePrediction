from dataclasses import dataclass
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import QueueSnapshot, StoreSnapshot
from app.utils.time import utc_now


@dataclass
class EtaEstimate:
    estimated_wait_minutes: int | None
    confidence: str
    reason: str
    rate_per_minute: float | None = None


def _is_ticketing_active(snapshot: StoreSnapshot | None) -> tuple[bool, str]:
    if snapshot is None:
        return False, "no snapshot available"
    if snapshot.store_status != "OPEN":
        return False, "store is not open"

    local_on = snapshot.local_ticketing_status == "ON"
    net_status = snapshot.net_ticket_status or ""
    net_on = any(token in net_status for token in ("ONLINE", "MANUAL", "ON"))

    if not local_on and not net_on:
        return False, "ticketing is currently unavailable"
    return True, "ticketing available"


def _compute_rate_from_snapshots(queue_snapshots: list[QueueSnapshot]) -> float | None:
    valid = [snapshot for snapshot in queue_snapshots if snapshot.queue_max is not None]
    if len(valid) < 2:
        return None

    first = valid[0]
    last = valid[-1]
    minutes = (last.ts - first.ts).total_seconds() / 60
    if minutes <= 0:
        return None

    delta = last.queue_max - first.queue_max
    if delta <= 0:
        return None
    return delta / minutes


def get_recent_queue_progress_rate(
    db: Session,
    store_id: int,
    reference_ts,
    window_minutes: int = 15,
) -> float | None:
    """Estimate recent queue progression speed from the latest 15 minutes."""

    start_ts = reference_ts - timedelta(minutes=window_minutes)
    rows = db.execute(
        select(QueueSnapshot)
        .where(
            QueueSnapshot.store_id == store_id,
            QueueSnapshot.ts >= start_ts,
            QueueSnapshot.ts <= reference_ts,
        )
        .order_by(QueueSnapshot.ts.asc(), QueueSnapshot.id.asc())
    ).scalars().all()
    return _compute_rate_from_snapshots(rows)


def get_historical_queue_progress_rate(
    db: Session,
    store_id: int,
    reference_ts,
    lookback_days: int = 28,
) -> float | None:
    """Fallback queue progression speed using same-hour historical samples."""

    start_ts = reference_ts - timedelta(days=lookback_days)
    rows = db.execute(
        select(QueueSnapshot)
        .where(
            QueueSnapshot.store_id == store_id,
            QueueSnapshot.ts >= start_ts,
            QueueSnapshot.ts <= reference_ts,
        )
        .order_by(QueueSnapshot.ts.asc(), QueueSnapshot.id.asc())
    ).scalars().all()

    rates: list[float] = []
    previous: QueueSnapshot | None = None
    target_hour = reference_ts.hour

    for row in rows:
        if row.ts.hour != target_hour or row.queue_max is None:
            previous = row
            continue
        if previous is None or previous.queue_max is None:
            previous = row
            continue
        minutes = (row.ts - previous.ts).total_seconds() / 60
        delta = row.queue_max - previous.queue_max
        if 0 < minutes <= 30 and delta > 0:
            rates.append(delta / minutes)
        previous = row

    if not rates:
        return None
    return sum(rates) / len(rates)


def get_previous_wait(db: Session, store_id: int, reference_ts, window_minutes: int = 15) -> int | None:
    start_ts = reference_ts - timedelta(minutes=window_minutes)
    previous = db.execute(
        select(StoreSnapshot)
        .where(
            StoreSnapshot.store_id == store_id,
            StoreSnapshot.ts >= start_ts,
            StoreSnapshot.ts < reference_ts,
            StoreSnapshot.wait.is_not(None),
        )
        .order_by(StoreSnapshot.ts.desc(), StoreSnapshot.id.desc())
        .limit(1)
    ).scalar_one_or_none()
    return previous.wait if previous else None


def calculate_eta(
    db: Session,
    store_id: int,
    snapshot: StoreSnapshot | None,
    queue_snapshot: QueueSnapshot | None,
) -> EtaEstimate:
    """Return a simple, explainable ETA with graceful fallbacks."""

    settings = get_settings()
    active, inactive_reason = _is_ticketing_active(snapshot)
    if not active:
        return EtaEstimate(estimated_wait_minutes=None, confidence="low", reason=inactive_reason)

    if snapshot is None or snapshot.wait is None:
        return EtaEstimate(estimated_wait_minutes=None, confidence="low", reason="wait is unavailable")
    if snapshot.wait == 0:
        return EtaEstimate(estimated_wait_minutes=0, confidence="high", reason="no waiting groups right now")

    reference_ts = queue_snapshot.ts if queue_snapshot else snapshot.ts if snapshot else utc_now()
    recent_rate = get_recent_queue_progress_rate(db, store_id, reference_ts)
    historical_rate = None

    if recent_rate is not None:
        raw_rate = recent_rate
        reason = "using recent queue progression"
        confidence = "high"
    else:
        historical_rate = get_historical_queue_progress_rate(db, store_id, reference_ts)
        if historical_rate is not None:
            raw_rate = historical_rate
            reason = "using historical average queue progression"
            confidence = "medium"
        else:
            raw_rate = settings.eta_min_rate
            reason = "falling back to minimum service rate"
            confidence = "low"

    effective_service_rate = max(raw_rate * settings.eta_alpha, settings.eta_min_rate)
    eta_minutes = round(snapshot.wait / effective_service_rate) if effective_service_rate > 0 else settings.eta_max_minutes

    previous_wait = get_previous_wait(db, store_id, reference_ts)
    if previous_wait is not None and previous_wait > 0:
        previous_eta = previous_wait / effective_service_rate
        eta_minutes = round((eta_minutes * 0.7) + (previous_eta * 0.3))
        confidence = "medium" if confidence == "high" else confidence

    cap = snapshot.wait_time_cap or settings.eta_max_minutes
    eta_minutes = max(0, min(cap, settings.eta_max_minutes, eta_minutes))

    return EtaEstimate(
        estimated_wait_minutes=eta_minutes,
        confidence=confidence,
        reason=reason,
        rate_per_minute=effective_service_rate,
    )

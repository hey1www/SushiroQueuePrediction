from collections import defaultdict
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app import schemas
from app.models import QueueSnapshot, StoreSnapshot
from app.services.stores import list_store_bundles
from app.utils.time import to_hk, to_iso, utc_now


def get_store_history(db: Session, store_id: int, hours: int = 6) -> schemas.StoreHistoryResponse:
    """Merge store and queue snapshots into one chart-friendly time series."""

    hours = max(1, min(hours, 72))
    since = utc_now() - timedelta(hours=hours)

    store_rows = db.execute(
        select(StoreSnapshot)
        .where(StoreSnapshot.store_id == store_id, StoreSnapshot.ts >= since)
        .order_by(StoreSnapshot.ts.asc(), StoreSnapshot.id.asc())
    ).scalars().all()
    queue_rows = db.execute(
        select(QueueSnapshot)
        .where(QueueSnapshot.store_id == store_id, QueueSnapshot.ts >= since)
        .order_by(QueueSnapshot.ts.asc(), QueueSnapshot.id.asc())
    ).scalars().all()

    store_by_ts = {to_iso(row.ts): row for row in store_rows}
    queue_by_ts = {to_iso(row.ts): row for row in queue_rows}
    seen_ts = set(store_by_ts.keys()) | set(queue_by_ts.keys())
    points: list[schemas.HistoryPoint] = []

    for ts_key in sorted(seen_ts):
        store_row = store_by_ts.get(ts_key)
        queue_row = queue_by_ts.get(ts_key)
        points.append(
            schemas.HistoryPoint(
                timestamp=ts_key,
                wait=store_row.wait if store_row else None,
                waiting_group=store_row.waiting_group if store_row else None,
                queue_max=queue_row.queue_max if queue_row else None,
                queue_min=queue_row.queue_min if queue_row else None,
            )
        )

    return schemas.StoreHistoryResponse(
        store_id=store_id,
        generated_at=to_iso(utc_now()),
        hours=hours,
        points=points,
    )


def _average(values: list[int | float]) -> float | None:
    if not values:
        return None
    return round(sum(values) / len(values), 2)


def _build_hour_buckets(values_by_hour: dict[int, list[float]], metric: str) -> list[schemas.HourBucket]:
    buckets: list[schemas.HourBucket] = []
    for hour in range(24):
        values = values_by_hour.get(hour, [])
        average = _average(values)
        bucket = schemas.HourBucket(hour=hour, label=f"{hour:02d}:00")
        if metric == "wait":
            bucket.average_wait = average
        else:
            bucket.average_queue_progress = average
        buckets.append(bucket)
    return buckets


def get_store_analytics(db: Session, store_id: int) -> schemas.StoreAnalyticsResponse:
    """Compute the v1 analytics summary for one store."""

    now_utc = utc_now()
    since = now_utc - timedelta(days=28)

    store_rows = db.execute(
        select(StoreSnapshot)
        .where(StoreSnapshot.store_id == store_id, StoreSnapshot.ts >= since)
        .order_by(StoreSnapshot.ts.asc(), StoreSnapshot.id.asc())
    ).scalars().all()
    queue_rows = db.execute(
        select(QueueSnapshot)
        .where(QueueSnapshot.store_id == store_id, QueueSnapshot.ts >= since)
        .order_by(QueueSnapshot.ts.asc(), QueueSnapshot.id.asc())
    ).scalars().all()

    hk_now = to_hk(now_utc)
    today_key = hk_now.date()

    today_waits: list[int] = []
    weekday_waits: list[int] = []
    weekend_waits: list[int] = []
    today_by_hour: dict[int, list[float]] = defaultdict(list)
    history_by_hour: dict[int, list[float]] = defaultdict(list)

    for row in store_rows:
        if row.wait is None:
            continue
        hk_dt = to_hk(row.ts)
        history_by_hour[hk_dt.hour].append(float(row.wait))
        if hk_dt.date() == today_key:
            today_waits.append(row.wait)
            today_by_hour[hk_dt.hour].append(float(row.wait))
        if hk_dt.weekday() >= 5:
            weekend_waits.append(row.wait)
        else:
            weekday_waits.append(row.wait)

    queue_rates_by_hour: dict[int, list[float]] = defaultdict(list)
    previous_queue: QueueSnapshot | None = None
    for row in queue_rows:
        if previous_queue is None:
            previous_queue = row
            continue
        if previous_queue.queue_max is None or row.queue_max is None:
            previous_queue = row
            continue
        minutes = (row.ts - previous_queue.ts).total_seconds() / 60
        delta = row.queue_max - previous_queue.queue_max
        if 0 < minutes <= 30 and delta >= 0:
            queue_rates_by_hour[to_hk(row.ts).hour].append(delta / minutes)
        previous_queue = row

    hourly_average_wait = _build_hour_buckets(history_by_hour, metric="wait")
    hourly_average_queue_progress = _build_hour_buckets(queue_rates_by_hour, metric="progress")

    peak_hours = sorted(
        (
            schemas.HourBucket(
                hour=hour,
                label=f"{hour:02d}:00",
                average_wait=_average(values),
            )
            for hour, values in today_by_hour.items()
        ),
        key=lambda bucket: bucket.average_wait or -1,
        reverse=True,
    )[:3]

    recommended_hours = sorted(
        (
            schemas.HourBucket(
                hour=hour,
                label=f"{hour:02d}:00",
                average_wait=_average(values),
            )
            for hour, values in history_by_hour.items()
            if values
        ),
        key=lambda bucket: bucket.average_wait if bucket.average_wait is not None else 10**9,
    )[:3]

    current_hour_historical_average_wait = _average(history_by_hour.get(hk_now.hour, []))

    return schemas.StoreAnalyticsResponse(
        store_id=store_id,
        generated_at=to_iso(now_utc),
        today_average_wait=_average(today_waits),
        current_hour_historical_average_wait=current_hour_historical_average_wait,
        weekday_average_wait=_average(weekday_waits),
        weekend_average_wait=_average(weekend_waits),
        peak_hours=peak_hours,
        recommended_hours=recommended_hours,
        hourly_average_wait=hourly_average_wait,
        hourly_average_queue_progress=hourly_average_queue_progress,
    )


def get_fastest_recommendations(
    db: Session,
    region: str | None = None,
    limit: int = 5,
) -> schemas.RecommendationsResponse:
    """Rank stores with a simple wait + ETA + status score."""

    bundles = list_store_bundles(db, region=region)
    eligible = [bundle for bundle in bundles if bundle.snapshot and bundle.snapshot.store_status == "OPEN"]
    if not eligible:
        eligible = bundles

    wait_values = [bundle.snapshot.wait for bundle in eligible if bundle.snapshot and bundle.snapshot.wait is not None]
    eta_values = [bundle.eta.estimated_wait_minutes for bundle in eligible if bundle.eta.estimated_wait_minutes is not None]
    max_wait = max(wait_values) if wait_values else None
    max_eta = max(eta_values) if eta_values else None

    items: list[schemas.RecommendationItem] = []
    latest_ts = None

    for bundle in eligible:
        snapshot = bundle.snapshot
        if snapshot is None:
            continue

        wait = snapshot.wait
        eta = bundle.eta.estimated_wait_minutes
        if wait is None:
            wait_component = 1
        elif not max_wait or max_wait <= 0:
            wait_component = 0
        else:
            wait_component = wait / max_wait

        if eta is None:
            eta_component = 1
        elif not max_eta or max_eta <= 0:
            eta_component = 0
        else:
            eta_component = eta / max_eta
        status_penalty = 0 if snapshot.local_ticketing_status == "ON" else 0.35
        score = round((0.45 * wait_component) + (0.45 * eta_component) + (0.1 * status_penalty), 4)

        reasons: list[str] = []
        if wait is not None:
            reasons.append(f"wait {wait}")
        if eta is not None:
            reasons.append(f"ETA {eta} min")
        if snapshot.local_ticketing_status == "ON":
            reasons.append("local ticketing on")
        items.append(
            schemas.RecommendationItem(
                store_id=bundle.store.id,
                name=bundle.store.name or f"Store {bundle.store.id}",
                area=bundle.store.area,
                region=bundle.store.region,
                wait=wait,
                eta_minutes=eta,
                score=score,
                reason=", ".join(reasons) if reasons else "fallback recommendation",
            )
        )
        latest_ts = max(filter(None, [latest_ts, to_iso(snapshot.ts)]), default=to_iso(snapshot.ts))

    items.sort(key=lambda item: (item.score, item.eta_minutes if item.eta_minutes is not None else 10**9, item.name))

    return schemas.RecommendationsResponse(
        generated_at=to_iso(utc_now()),
        data_updated_at=latest_ts,
        recommendations=items[: max(1, min(limit, 10))],
    )

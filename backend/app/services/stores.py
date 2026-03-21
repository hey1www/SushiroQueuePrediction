from dataclasses import dataclass

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app import models, schemas
from app.services.eta import EtaEstimate, calculate_eta
from app.utils.json_utils import load_int_list
from app.utils.time import to_iso


@dataclass
class StoreBundle:
    store: models.Store
    snapshot: models.StoreSnapshot | None
    queue: models.QueueSnapshot | None
    eta: EtaEstimate


def get_store_or_none(db: Session, store_id: int) -> models.Store | None:
    return db.get(models.Store, store_id)


def get_latest_store_snapshot(db: Session, store_id: int) -> models.StoreSnapshot | None:
    return db.execute(
        select(models.StoreSnapshot)
        .where(models.StoreSnapshot.store_id == store_id)
        .order_by(desc(models.StoreSnapshot.ts), desc(models.StoreSnapshot.id))
        .limit(1)
    ).scalar_one_or_none()


def get_latest_queue_snapshot(db: Session, store_id: int) -> models.QueueSnapshot | None:
    return db.execute(
        select(models.QueueSnapshot)
        .where(models.QueueSnapshot.store_id == store_id)
        .order_by(desc(models.QueueSnapshot.ts), desc(models.QueueSnapshot.id))
        .limit(1)
    ).scalar_one_or_none()


def list_store_bundles(
    db: Session,
    region: str | None = None,
    area: str | None = None,
) -> list[StoreBundle]:
    """Load stores together with their latest snapshots and ETA estimates."""

    query = select(models.Store)
    if region:
        query = query.where(models.Store.region == region)
    if area:
        query = query.where(models.Store.area == area)
    stores = db.execute(query.order_by(models.Store.region.asc(), models.Store.area.asc(), models.Store.id.asc())).scalars().all()

    bundles: list[StoreBundle] = []
    for store in stores:
        snapshot = get_latest_store_snapshot(db, store.id)
        queue = get_latest_queue_snapshot(db, store.id)
        eta = calculate_eta(db, store.id, snapshot, queue)
        bundles.append(StoreBundle(store=store, snapshot=snapshot, queue=queue, eta=eta))
    return bundles


def serialize_queue_summary(queue_snapshot: models.QueueSnapshot | None) -> schemas.QueueSummary:
    if queue_snapshot is None:
        return schemas.QueueSummary()
    return schemas.QueueSummary(
        store_queue=load_int_list(queue_snapshot.store_queue_json),
        queue_min=queue_snapshot.queue_min,
        queue_max=queue_snapshot.queue_max,
        queue_count=queue_snapshot.queue_count,
        queue_span=queue_snapshot.queue_span,
        separate_queue=queue_snapshot.separate_queue,
    )


def serialize_queue_detail(queue_snapshot: models.QueueSnapshot | None) -> schemas.QueueDetail:
    if queue_snapshot is None:
        return schemas.QueueDetail()
    return schemas.QueueDetail(
        store_queue=load_int_list(queue_snapshot.store_queue_json),
        booth_queue=load_int_list(queue_snapshot.booth_queue_json),
        mixed_queue=load_int_list(queue_snapshot.mixed_queue_json),
        counter_queue=load_int_list(queue_snapshot.counter_queue_json),
        store_counter_queue=load_int_list(queue_snapshot.store_counter_queue_json),
        store_booth_queue=load_int_list(queue_snapshot.store_booth_queue_json),
        reservation_queue=load_int_list(queue_snapshot.reservation_queue_json),
        reservation_counter_queue=load_int_list(queue_snapshot.reservation_counter_queue_json),
        reservation_booth_queue=load_int_list(queue_snapshot.reservation_booth_queue_json),
        queue_min=queue_snapshot.queue_min,
        queue_max=queue_snapshot.queue_max,
        queue_count=queue_snapshot.queue_count,
        queue_span=queue_snapshot.queue_span,
        separate_queue=queue_snapshot.separate_queue,
    )


def serialize_eta(eta: EtaEstimate) -> schemas.EtaResponse:
    return schemas.EtaResponse(
        estimated_wait_minutes=eta.estimated_wait_minutes,
        confidence=eta.confidence,
        reason=eta.reason,
    )


def serialize_current_store(bundle: StoreBundle) -> schemas.StoreCurrent:
    store = bundle.store
    snapshot = bundle.snapshot
    return schemas.StoreCurrent(
        id=store.id,
        name=store.name,
        address=store.address,
        area=store.area,
        region=store.region,
        latitude=store.latitude,
        longitude=store.longitude,
        tables_capacity=store.tables_capacity,
        counters_capacity=store.counters_capacity,
        seat_config=store.seat_config,
        commencement_date=store.commencement_date,
        data_updated_at=to_iso(snapshot.ts if snapshot else None),
        store_status=snapshot.store_status if snapshot else None,
        net_ticket_status=snapshot.net_ticket_status if snapshot else None,
        local_ticketing_status=snapshot.local_ticketing_status if snapshot else None,
        reservation_status=snapshot.reservation_status if snapshot else None,
        checkin_status=snapshot.checkin_status if snapshot else None,
        wait=snapshot.wait if snapshot else None,
        waiting_group=snapshot.waiting_group if snapshot else None,
        wait_time_counter=snapshot.wait_time_counter if snapshot else None,
        wait_time_cap=snapshot.wait_time_cap if snapshot else None,
        waiting_group_table=snapshot.waiting_group_table if snapshot else None,
        waiting_group_counter=snapshot.waiting_group_counter if snapshot else None,
        waiting_group_pair=snapshot.waiting_group_pair if snapshot else None,
        queue=serialize_queue_summary(bundle.queue),
        eta=serialize_eta(bundle.eta),
    )


def list_current_stores(
    db: Session,
    region: str | None = None,
    area: str | None = None,
    open_only: bool = False,
    local_ticket_only: bool = False,
    sort: str = "wait",
) -> tuple[str | None, list[schemas.StoreCurrent]]:
    """Return the filtered current-store view used by the dashboard."""

    bundles = list_store_bundles(db, region=region, area=area)
    items: list[schemas.StoreCurrent] = []
    latest_ts: str | None = None

    for bundle in bundles:
        item = serialize_current_store(bundle)
        if open_only and item.store_status != "OPEN":
            continue
        if local_ticket_only and item.local_ticketing_status != "ON":
            continue
        items.append(item)
        latest_ts = max(filter(None, [latest_ts, item.data_updated_at]), default=item.data_updated_at)

    def wait_sort_key(store: schemas.StoreCurrent) -> tuple[int, str]:
        return (store.wait if store.wait is not None else 10**9, store.name or "")

    def eta_sort_key(store: schemas.StoreCurrent) -> tuple[int, int, str]:
        eta = store.eta.estimated_wait_minutes
        return (
            eta if eta is not None else 10**9,
            store.wait if store.wait is not None else 10**9,
            store.name or "",
        )

    if sort == "eta":
        items.sort(key=eta_sort_key)
    elif sort == "name":
        items.sort(key=lambda store: store.name or "")
    else:
        items.sort(key=wait_sort_key)

    return latest_ts, items

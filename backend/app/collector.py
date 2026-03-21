import logging
from dataclasses import dataclass

import requests
from requests.adapters import HTTPAdapter
from sqlalchemy.orm import Session
from urllib3.util.retry import Retry

from app.config import Settings, get_settings
from app.models import QueueSnapshot, Store, StoreSnapshot
from app.utils.json_utils import dumps_json, normalize_queue_list
from app.utils.time import utc_now

logger = logging.getLogger(__name__)


@dataclass
class CollectionStats:
    collected_at: str
    store_count: int
    queue_success_count: int
    queue_error_count: int


class SushiroApiClient:
    """Thin HTTP client for the public Sushiro Hong Kong endpoints."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        retry = Retry(
            total=2,
            read=2,
            connect=2,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"],
        )
        adapter = HTTPAdapter(max_retries=retry)
        self.session = requests.Session()
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)
        self.session.headers.update(
            {
                "User-Agent": "sushiro-hk-assistant/1.0",
                "Accept": "application/json",
            }
        )

    def fetch_storelist(self) -> list[dict]:
        """Fetch the current store list payload."""

        response = self.session.get(
            self.settings.storelist_url,
            timeout=self.settings.request_timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, list):
            raise ValueError("storelist response is not a list")
        return [item for item in payload if isinstance(item, dict)]

    def fetch_groupqueues(self, store_id: int) -> tuple[dict, bool]:
        """Fetch queue data for one store and flag application-level error payloads."""

        url = self.settings.groupqueues_url_template.format(store_id=store_id)
        response = self.session.get(url, timeout=self.settings.request_timeout_seconds)
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise ValueError(f"groupqueues response for store {store_id} is not an object")
        has_error = "code" in payload and "message" in payload
        return payload, has_error


def _int_or_none(value: object) -> int | None:
    try:
        if value is None or value == "":
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


def _upsert_store(db: Session, store_payload: dict) -> Store:
    store_id = int(store_payload["id"])
    store = db.get(Store, store_id)
    if store is None:
        store = Store(id=store_id)
        db.add(store)

    store.name = store_payload.get("name")
    store.address = store_payload.get("address")
    store.area = store_payload.get("area")
    store.region = store_payload.get("region")
    store.latitude = store_payload.get("latitude")
    store.longitude = store_payload.get("longitude")
    store.tables_capacity = _int_or_none(store_payload.get("tablesCapacity"))
    store.counters_capacity = _int_or_none(store_payload.get("countersCapacity"))
    store.seat_config = _int_or_none(store_payload.get("seatConfig"))
    store.commencement_date = store_payload.get("commencementDate")
    return store


def _create_store_snapshot(ts, store_id: int, store_payload: dict) -> StoreSnapshot:
    return StoreSnapshot(
        ts=ts,
        store_id=store_id,
        store_status=store_payload.get("storeStatus"),
        net_ticket_status=store_payload.get("netTicketStatus"),
        local_ticketing_status=store_payload.get("localTicketingStatus"),
        reservation_status=store_payload.get("reservationStatus"),
        checkin_status=store_payload.get("checkinStatus"),
        wait=_int_or_none(store_payload.get("wait")),
        waiting_group=_int_or_none(store_payload.get("waitingGroup")),
        wait_time_counter=_int_or_none(store_payload.get("waitTimeCounter")),
        wait_time_cap=_int_or_none(store_payload.get("waitTimeCap")),
        waiting_group_table=_int_or_none(store_payload.get("waitingGroupTable")),
        waiting_group_counter=_int_or_none(store_payload.get("waitingGroupCounter")),
        waiting_group_pair=_int_or_none(store_payload.get("waitingGroupPair")),
        raw_storelist_json=dumps_json(store_payload),
    )


def _create_queue_snapshot(ts, store_id: int, groupqueues_payload: dict) -> QueueSnapshot:
    store_queue = normalize_queue_list(groupqueues_payload.get("storeQueue"))
    booth_queue = normalize_queue_list(groupqueues_payload.get("boothQueue"))
    mixed_queue = normalize_queue_list(groupqueues_payload.get("mixedQueue"))
    counter_queue = normalize_queue_list(groupqueues_payload.get("counterQueue"))
    store_counter_queue = normalize_queue_list(groupqueues_payload.get("storeCounterQueue"))
    store_booth_queue = normalize_queue_list(groupqueues_payload.get("storeBoothQueue"))
    reservation_queue = normalize_queue_list(groupqueues_payload.get("reservationQueue"))
    reservation_counter_queue = normalize_queue_list(groupqueues_payload.get("reservationCounterQueue"))
    reservation_booth_queue = normalize_queue_list(groupqueues_payload.get("reservationBoothQueue"))

    queue_min = min(store_queue) if store_queue else None
    queue_max = max(store_queue) if store_queue else None
    queue_count = len(store_queue) if store_queue else 0
    queue_span = (queue_max - queue_min) if store_queue and queue_min is not None and queue_max is not None else None

    return QueueSnapshot(
        ts=ts,
        store_id=store_id,
        separate_queue=_int_or_none(groupqueues_payload.get("separateQueue")),
        store_queue_json=dumps_json(store_queue),
        booth_queue_json=dumps_json(booth_queue),
        mixed_queue_json=dumps_json(mixed_queue),
        counter_queue_json=dumps_json(counter_queue),
        store_counter_queue_json=dumps_json(store_counter_queue),
        store_booth_queue_json=dumps_json(store_booth_queue),
        reservation_queue_json=dumps_json(reservation_queue),
        reservation_counter_queue_json=dumps_json(reservation_counter_queue),
        reservation_booth_queue_json=dumps_json(reservation_booth_queue),
        queue_min=queue_min,
        queue_max=queue_max,
        queue_count=queue_count,
        queue_span=queue_span,
        raw_groupqueues_json=dumps_json(groupqueues_payload),
    )


def collect_once(db: Session, settings: Settings | None = None) -> CollectionStats:
    """Run one collection cycle and persist both store and queue snapshots."""

    settings = settings or get_settings()
    client = SushiroApiClient(settings)
    ts = utc_now()

    store_payloads = client.fetch_storelist()
    queue_success_count = 0
    queue_error_count = 0

    try:
        for store_payload in store_payloads:
            store = _upsert_store(db, store_payload)
            store_id = store.id
            db.add(_create_store_snapshot(ts, store_id, store_payload))

        db.flush()

        for store_payload in store_payloads:
            store_id = int(store_payload["id"])
            queue_payload: dict
            has_error = False

            try:
                queue_payload, has_error = client.fetch_groupqueues(store_id)
            except Exception as exc:  # noqa: BLE001
                logger.warning("groupqueues collection failed for store %s: %s", store_id, exc)
                queue_payload = {
                    "message": str(exc),
                    "code": "REQUEST_FAILED",
                    "storeQueue": [],
                    "boothQueue": [],
                    "mixedQueue": [],
                    "counterQueue": [],
                    "storeCounterQueue": [],
                    "storeBoothQueue": [],
                    "reservationQueue": [],
                    "reservationCounterQueue": [],
                    "reservationBoothQueue": [],
                    "separateQueue": None,
                }
                has_error = True

            db.add(_create_queue_snapshot(ts, store_id, queue_payload))
            if has_error:
                queue_error_count += 1
            else:
                queue_success_count += 1

        db.commit()
    except Exception:
        db.rollback()
        raise

    logger.info(
        "collection finished at %s with %s stores, %s queue successes, %s queue errors",
        ts.isoformat(),
        len(store_payloads),
        queue_success_count,
        queue_error_count,
    )

    return CollectionStats(
        collected_at=ts.isoformat(),
        store_count=len(store_payloads),
        queue_success_count=queue_success_count,
        queue_error_count=queue_error_count,
    )

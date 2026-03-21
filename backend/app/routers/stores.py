from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import schemas
from app.db import get_db
from app.services.analytics import get_store_analytics, get_store_history
from app.services.stores import (
    get_store_or_none,
    list_current_stores,
    list_store_bundles,
    serialize_current_store,
    serialize_queue_detail,
)
from app.utils.time import to_iso, utc_now

router = APIRouter(prefix="/api/stores", tags=["stores"])


@router.get("/current", response_model=schemas.StoresCurrentResponse)
def get_current_stores(
    region: str | None = Query(default=None),
    area: str | None = Query(default=None),
    open_only: bool = Query(default=False),
    local_ticket_only: bool = Query(default=False),
    sort: str = Query(default="wait", pattern="^(wait|eta|name)$"),
    db: Session = Depends(get_db),
) -> schemas.StoresCurrentResponse:
    """Dashboard endpoint for the latest store states."""

    data_updated_at, stores = list_current_stores(
        db,
        region=region,
        area=area,
        open_only=open_only,
        local_ticket_only=local_ticket_only,
        sort=sort,
    )
    return schemas.StoresCurrentResponse(
        generated_at=to_iso(utc_now()),
        data_updated_at=data_updated_at,
        stores=stores,
    )


@router.get("/{store_id}", response_model=schemas.StoreDetailResponse)
def get_store_detail(store_id: int, db: Session = Depends(get_db)) -> schemas.StoreDetailResponse:
    """Return one store with its latest queue details and summary analytics."""

    store = get_store_or_none(db, store_id)
    if store is None:
        raise HTTPException(status_code=404, detail="Store not found")

    bundle = next((item for item in list_store_bundles(db) if item.store.id == store_id), None)
    if bundle is None:
        raise HTTPException(status_code=404, detail="Store not found")

    analytics = get_store_analytics(db, store_id)
    return schemas.StoreDetailResponse(
        generated_at=to_iso(utc_now()),
        data_updated_at=serialize_current_store(bundle).data_updated_at,
        store=serialize_current_store(bundle),
        latest_queue=serialize_queue_detail(bundle.queue),
        summary=schemas.AnalyticsSummary(
            today_average_wait=analytics.today_average_wait,
            peak_hours=analytics.peak_hours,
            recommended_hours=analytics.recommended_hours,
        ),
    )


@router.get("/{store_id}/history", response_model=schemas.StoreHistoryResponse)
def get_store_history_route(
    store_id: int,
    hours: int = Query(default=6, ge=1, le=72),
    db: Session = Depends(get_db),
) -> schemas.StoreHistoryResponse:
    """Return recent history points for the selected store."""

    if get_store_or_none(db, store_id) is None:
        raise HTTPException(status_code=404, detail="Store not found")
    return get_store_history(db, store_id, hours=hours)


@router.get("/{store_id}/analytics", response_model=schemas.StoreAnalyticsResponse)
def get_store_analytics_route(store_id: int, db: Session = Depends(get_db)) -> schemas.StoreAnalyticsResponse:
    """Return historical summary metrics for the selected store."""

    if get_store_or_none(db, store_id) is None:
        raise HTTPException(status_code=404, detail="Store not found")
    return get_store_analytics(db, store_id)

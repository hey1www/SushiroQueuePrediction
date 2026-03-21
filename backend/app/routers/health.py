from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import models, schemas
from app.utils.time import to_iso, utc_now


def build_health_response(db: Session) -> schemas.HealthResponse:
    store_count = db.execute(select(func.count(models.Store.id))).scalar_one()
    last_snapshot = db.execute(select(func.max(models.StoreSnapshot.ts))).scalar_one()
    status = "ok" if last_snapshot else "degraded"
    return schemas.HealthResponse(
        status=status,
        generated_at=to_iso(utc_now()),
        last_snapshot_at=to_iso(last_snapshot),
        store_count=store_count,
    )

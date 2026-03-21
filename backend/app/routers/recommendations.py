from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app import schemas
from app.db import get_db
from app.services.analytics import get_fastest_recommendations

router = APIRouter(prefix="/api/recommendations", tags=["recommendations"])


@router.get("/fastest", response_model=schemas.RecommendationsResponse)
def get_fastest_recommendations_route(
    region: str | None = Query(default=None),
    limit: int = Query(default=5, ge=1, le=10),
    db: Session = Depends(get_db),
) -> schemas.RecommendationsResponse:
    """Return the fastest-store shortlist for the dashboard and analytics page."""

    return get_fastest_recommendations(db, region=region, limit=limit)

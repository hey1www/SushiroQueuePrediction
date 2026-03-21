import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.db import SessionLocal, get_db, init_db
from app.routers.health import build_health_response
from app.routers.recommendations import router as recommendations_router
from app.routers.stores import router as stores_router
from app.scheduler import create_scheduler
from app.collector import collect_once
from app.config import get_settings

settings = get_settings()
logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()

    try:
        with SessionLocal() as db:
            collect_once(db)
    except Exception:  # noqa: BLE001
        logger.exception("initial collection failed; API will continue with existing data")

    scheduler = create_scheduler()
    scheduler.start()
    app.state.scheduler = scheduler
    yield
    scheduler.shutdown(wait=False)


app = FastAPI(
    title="Sushiro Hong Kong Queue Assistant API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health(db: Session = Depends(get_db)):
    return build_health_response(db)


app.include_router(stores_router)
app.include_router(recommendations_router)

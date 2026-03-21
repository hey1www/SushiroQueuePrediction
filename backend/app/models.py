from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Store(Base):
    """Static store metadata that changes rarely."""

    __tablename__ = "stores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    area: Mapped[str | None] = mapped_column(String(128), nullable=True)
    region: Mapped[str | None] = mapped_column(String(128), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    tables_capacity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    counters_capacity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    seat_config: Mapped[int | None] = mapped_column(Integer, nullable=True)
    commencement_date: Mapped[str | None] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    snapshots: Mapped[list["StoreSnapshot"]] = relationship(back_populates="store")
    queue_snapshots: Mapped[list["QueueSnapshot"]] = relationship(back_populates="store")


class StoreSnapshot(Base):
    """Per-collection snapshot for store status and wait counters."""

    __tablename__ = "store_snapshots"
    __table_args__ = (Index("ix_store_snapshots_store_id_ts", "store_id", "ts"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id"), nullable=False)
    store_status: Mapped[str | None] = mapped_column(String(64), nullable=True)
    net_ticket_status: Mapped[str | None] = mapped_column(String(64), nullable=True)
    local_ticketing_status: Mapped[str | None] = mapped_column(String(64), nullable=True)
    reservation_status: Mapped[str | None] = mapped_column(String(64), nullable=True)
    checkin_status: Mapped[str | None] = mapped_column(String(64), nullable=True)
    wait: Mapped[int | None] = mapped_column(Integer, nullable=True)
    waiting_group: Mapped[int | None] = mapped_column(Integer, nullable=True)
    wait_time_counter: Mapped[int | None] = mapped_column(Integer, nullable=True)
    wait_time_cap: Mapped[int | None] = mapped_column(Integer, nullable=True)
    waiting_group_table: Mapped[int | None] = mapped_column(Integer, nullable=True)
    waiting_group_counter: Mapped[int | None] = mapped_column(Integer, nullable=True)
    waiting_group_pair: Mapped[int | None] = mapped_column(Integer, nullable=True)
    raw_storelist_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    store: Mapped["Store"] = relationship(back_populates="snapshots")


class QueueSnapshot(Base):
    """Per-collection snapshot for queue displays and derived queue metrics."""

    __tablename__ = "queue_snapshots"
    __table_args__ = (Index("ix_queue_snapshots_store_id_ts", "store_id", "ts"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id"), nullable=False)
    separate_queue: Mapped[int | None] = mapped_column(Integer, nullable=True)
    store_queue_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    booth_queue_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    mixed_queue_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    counter_queue_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    store_counter_queue_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    store_booth_queue_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    reservation_queue_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    reservation_counter_queue_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    reservation_booth_queue_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    queue_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    queue_max: Mapped[int | None] = mapped_column(Integer, nullable=True)
    queue_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    queue_span: Mapped[int | None] = mapped_column(Integer, nullable=True)
    raw_groupqueues_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    store: Mapped["Store"] = relationship(back_populates="queue_snapshots")

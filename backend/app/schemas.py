from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class SchemaBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class HealthResponse(SchemaBase):
    status: Literal["ok", "degraded"]
    generated_at: str
    last_snapshot_at: str | None = None
    store_count: int


class EtaResponse(SchemaBase):
    estimated_wait_minutes: int | None = None
    confidence: Literal["low", "medium", "high"]
    reason: str


class QueueSummary(SchemaBase):
    store_queue: list[int] = Field(default_factory=list)
    queue_min: int | None = None
    queue_max: int | None = None
    queue_count: int | None = None
    queue_span: int | None = None
    separate_queue: int | None = None


class QueueDetail(QueueSummary):
    booth_queue: list[int] = Field(default_factory=list)
    mixed_queue: list[int] = Field(default_factory=list)
    counter_queue: list[int] = Field(default_factory=list)
    store_counter_queue: list[int] = Field(default_factory=list)
    store_booth_queue: list[int] = Field(default_factory=list)
    reservation_queue: list[int] = Field(default_factory=list)
    reservation_counter_queue: list[int] = Field(default_factory=list)
    reservation_booth_queue: list[int] = Field(default_factory=list)


class StoreCurrent(SchemaBase):
    id: int
    name: str | None = None
    address: str | None = None
    area: str | None = None
    region: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    tables_capacity: int | None = None
    counters_capacity: int | None = None
    seat_config: int | None = None
    commencement_date: str | None = None
    data_updated_at: str | None = None
    store_status: str | None = None
    net_ticket_status: str | None = None
    local_ticketing_status: str | None = None
    reservation_status: str | None = None
    checkin_status: str | None = None
    wait: int | None = None
    waiting_group: int | None = None
    wait_time_counter: int | None = None
    wait_time_cap: int | None = None
    waiting_group_table: int | None = None
    waiting_group_counter: int | None = None
    waiting_group_pair: int | None = None
    queue: QueueSummary
    eta: EtaResponse


class StoresCurrentResponse(SchemaBase):
    generated_at: str
    data_updated_at: str | None = None
    stores: list[StoreCurrent]


class HourBucket(SchemaBase):
    hour: int
    label: str
    average_wait: float | None = None
    average_queue_progress: float | None = None


class StoreAnalyticsResponse(SchemaBase):
    store_id: int
    generated_at: str
    today_average_wait: float | None = None
    current_hour_historical_average_wait: float | None = None
    weekday_average_wait: float | None = None
    weekend_average_wait: float | None = None
    peak_hours: list[HourBucket] = Field(default_factory=list)
    recommended_hours: list[HourBucket] = Field(default_factory=list)
    hourly_average_wait: list[HourBucket] = Field(default_factory=list)
    hourly_average_queue_progress: list[HourBucket] = Field(default_factory=list)


class AnalyticsSummary(SchemaBase):
    today_average_wait: float | None = None
    peak_hours: list[HourBucket] = Field(default_factory=list)
    recommended_hours: list[HourBucket] = Field(default_factory=list)


class StoreDetailResponse(SchemaBase):
    generated_at: str
    data_updated_at: str | None = None
    store: StoreCurrent
    latest_queue: QueueDetail
    summary: AnalyticsSummary


class HistoryPoint(SchemaBase):
    timestamp: str
    wait: int | None = None
    waiting_group: int | None = None
    queue_max: int | None = None
    queue_min: int | None = None


class StoreHistoryResponse(SchemaBase):
    store_id: int
    generated_at: str
    hours: int
    points: list[HistoryPoint]


class RecommendationItem(SchemaBase):
    store_id: int
    name: str
    area: str | None = None
    region: str | None = None
    wait: int | None = None
    eta_minutes: int | None = None
    score: float
    reason: str


class RecommendationsResponse(SchemaBase):
    generated_at: str
    data_updated_at: str | None = None
    recommendations: list[RecommendationItem]

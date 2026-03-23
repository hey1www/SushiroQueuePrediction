export interface EtaResponse {
  estimated_wait_minutes: number | null;
  confidence: "low" | "medium" | "high";
  reason: string;
}

export interface QueueSummary {
  store_queue: number[];
  queue_min: number | null;
  queue_max: number | null;
  queue_count: number | null;
  queue_span: number | null;
  separate_queue: number | null;
}

export interface QueueDetail extends QueueSummary {
  booth_queue: number[];
  mixed_queue: number[];
  counter_queue: number[];
  store_counter_queue: number[];
  store_booth_queue: number[];
  reservation_queue: number[];
  reservation_counter_queue: number[];
  reservation_booth_queue: number[];
}

export interface StoreCurrent {
  id: number;
  name: string | null;
  address: string | null;
  area: string | null;
  region: string | null;
  latitude: number | null;
  longitude: number | null;
  tables_capacity: number | null;
  counters_capacity: number | null;
  seat_config: number | null;
  commencement_date: string | null;
  data_updated_at: string | null;
  store_status: string | null;
  net_ticket_status: string | null;
  local_ticketing_status: string | null;
  reservation_status: string | null;
  checkin_status: string | null;
  wait: number | null;
  waiting_group: number | null;
  wait_time_counter: number | null;
  wait_time_cap: number | null;
  waiting_group_table: number | null;
  waiting_group_counter: number | null;
  waiting_group_pair: number | null;
  queue: QueueSummary;
  eta: EtaResponse;
}

export interface StoresCurrentResponse {
  generated_at: string;
  data_updated_at: string | null;
  stores: StoreCurrent[];
}

export interface HourBucket {
  hour: number;
  label: string;
  average_wait: number | null;
  average_queue_progress: number | null;
}

export interface HistoricalProfileContext {
  requested_profile: string;
  matched_profile: string;
  requested_profile_label: string;
  matched_profile_label: string;
  slot_label: string;
  match_label: string;
  fallback_level: string;
  fallback_label: string;
  sample_count: number;
  average_wait: number | null;
  average_waiting_group: number | null;
  average_queue_progress: number | null;
}

export interface StoreAnalyticsResponse {
  store_id: number;
  generated_at: string;
  today_average_wait: number | null;
  current_hour_historical_average_wait: number | null;
  weekday_average_wait: number | null;
  weekend_average_wait: number | null;
  current_profile_context: HistoricalProfileContext | null;
  peak_hours: HourBucket[];
  recommended_hours: HourBucket[];
  hourly_average_wait: HourBucket[];
  hourly_average_queue_progress: HourBucket[];
}

export interface AnalyticsSummary {
  today_average_wait: number | null;
  peak_hours: HourBucket[];
  recommended_hours: HourBucket[];
}

export interface StoreDetailResponse {
  generated_at: string;
  data_updated_at: string | null;
  store: StoreCurrent;
  latest_queue: QueueDetail;
  summary: AnalyticsSummary;
}

export interface HistoryPoint {
  timestamp: string;
  wait: number | null;
  waiting_group: number | null;
  eta_minutes: number | null;
  eta_confidence: "low" | "medium" | "high" | null;
  eta_reason: string | null;
  queue_max: number | null;
  queue_min: number | null;
  reservation_queue_max: number | null;
}

export interface StoreHistoryResponse {
  store_id: number;
  generated_at: string;
  hours: number;
  points: HistoryPoint[];
}

export interface RecommendationItem {
  store_id: number;
  name: string;
  area: string | null;
  region: string | null;
  wait: number | null;
  eta_minutes: number | null;
  score: number;
  reason: string;
}

export interface RecommendationsResponse {
  generated_at: string;
  data_updated_at: string | null;
  recommendations: RecommendationItem[];
}

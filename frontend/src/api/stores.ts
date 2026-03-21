import { getJson } from "./client";
import type {
  RecommendationsResponse,
  StoreAnalyticsResponse,
  StoreDetailResponse,
  StoreHistoryResponse,
  StoresCurrentResponse,
} from "../types/api";

export function fetchCurrentStores(params?: {
  region?: string;
  area?: string;
  open_only?: boolean;
  local_ticket_only?: boolean;
  sort?: "wait" | "eta" | "name";
}) {
  return getJson<StoresCurrentResponse>("/stores/current", params);
}

export function fetchStoreDetail(storeId: number) {
  return getJson<StoreDetailResponse>(`/stores/${storeId}`);
}

export function fetchStoreHistory(storeId: number, hours = 6) {
  return getJson<StoreHistoryResponse>(`/stores/${storeId}/history`, { hours });
}

export function fetchStoreAnalytics(storeId: number) {
  return getJson<StoreAnalyticsResponse>(`/stores/${storeId}/analytics`);
}

export function fetchRecommendations(params?: { region?: string; limit?: number }) {
  return getJson<RecommendationsResponse>("/recommendations/fastest", params);
}

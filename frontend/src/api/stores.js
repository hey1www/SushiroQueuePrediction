import { getJson } from "./client";
export function fetchCurrentStores(params) {
    return getJson("/stores/current", params);
}
export function fetchStoreDetail(storeId) {
    return getJson(`/stores/${storeId}`);
}
export function fetchStoreHistory(storeId, hours = 6) {
    return getJson(`/stores/${storeId}/history`, { hours });
}
export function fetchStoreAnalytics(storeId) {
    return getJson(`/stores/${storeId}/analytics`);
}
export function fetchRecommendations(params) {
    return getJson("/recommendations/fastest", params);
}

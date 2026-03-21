<template>
  <section class="page-stack">
    <section class="hero-card">
      <div>
        <p class="eyebrow">即時總覽</p>
        <h2>全港門店即時看板</h2>
      </div>
      <div class="hero-actions">
        <button class="button-link button-link--solid" @click="loadDashboard">立即更新</button>
        <RouterLink class="button-link" to="/analytics">查看分析</RouterLink>
      </div>
    </section>

    <section class="stats-row">
      <StatPanel label="門店數量" :value="String(response?.stores.length || 0)" hint="目前回傳的門店總數" />
      <StatPanel label="營業中" :value="String(openStoreCount)" hint="目前仍在營業的門店" />
      <StatPanel label="最快預估" :value="lowestEtaLabel" hint="以可估算門店為準" />
      <StatPanel label="更新時間" :value="formatDateTime(response?.data_updated_at)" hint="香港時間" />
    </section>

    <section v-if="topRecommendation" class="recommend-card">
      <div>
        <p class="eyebrow">快速建議</p>
        <h3>{{ topRecommendation.name }}</h3>
      </div>
      <div class="recommend-card__meta">
        <span>{{ formatRegionArea(topRecommendation.region, topRecommendation.area) }}</span>
        <span>等候 {{ formatOptionalNumber(topRecommendation.wait) }} 組</span>
        <span>預估 {{ formatOptionalNumber(topRecommendation.eta_minutes, ' 分鐘') }}</span>
      </div>
      <p>{{ formatRecommendationReason(topRecommendation.reason) }}</p>
    </section>

    <section class="panel">
      <div class="filter-row">
        <label>
          <span>區域</span>
          <select v-model="filters.region">
            <option value="">全部</option>
            <option v-for="region in regions" :key="region" :value="region">{{ region }}</option>
          </select>
        </label>
        <label>
          <span>排序方式</span>
          <select v-model="filters.sort">
            <option value="eta">按預估等候</option>
            <option value="wait">按等候組數</option>
            <option value="name">按門店名稱</option>
          </select>
        </label>
        <label class="checkbox-field">
          <input v-model="filters.openOnly" type="checkbox" />
          <span>只看營業中</span>
        </label>
        <label class="checkbox-field">
          <input v-model="filters.localTicketOnly" type="checkbox" />
          <span>只看可現場派籌</span>
        </label>
      </div>
    </section>

    <p v-if="errorMessage" class="error-banner">{{ errorMessage }}</p>
    <p v-if="loading" class="muted-text">正在載入門店資料…</p>

    <section class="store-grid" v-if="response">
      <StoreCard v-for="store in response.stores" :key="store.id" :store="store" />
    </section>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from "vue";
import { RouterLink } from "vue-router";

import { fetchCurrentStores, fetchRecommendations } from "../api/stores";
import StatPanel from "../components/StatPanel.vue";
import StoreCard from "../components/StoreCard.vue";
import { useDashboardFilters } from "../stores/useFilters";
import type { RecommendationsResponse, StoresCurrentResponse } from "../types/api";
import { formatDateTime, formatOptionalNumber, formatRecommendationReason, formatRegionArea } from "../utils/format";

const filters = useDashboardFilters();
const response = ref<StoresCurrentResponse | null>(null);
const recommendations = ref<RecommendationsResponse | null>(null);
const loading = ref(false);
const errorMessage = ref("");
const regions = ref<string[]>([]);
let refreshTimer: number | undefined;

const openStoreCount = computed(
  () => response.value?.stores.filter((store) => store.store_status === "OPEN").length || 0,
);

const lowestEtaLabel = computed(() => {
  const etaValues = response.value?.stores
    .map((store) => store.eta.estimated_wait_minutes)
    .filter((value): value is number => value !== null);
  if (!etaValues?.length) return "暫無估算";
  return `${Math.min(...etaValues)} 分鐘`;
});

const topRecommendation = computed(() => recommendations.value?.recommendations[0] || null);

async function loadDashboard() {
  loading.value = true;
  errorMessage.value = "";

  try {
    const [storesResponse, recommendationResponse] = await Promise.all([
      fetchCurrentStores({
        region: filters.region || undefined,
        open_only: filters.openOnly,
        local_ticket_only: filters.localTicketOnly,
        sort: filters.sort,
      }),
      fetchRecommendations({
        region: filters.region || undefined,
        limit: 5,
      }),
    ]);

    response.value = storesResponse;
    recommendations.value = recommendationResponse;

    if (!regions.value.length) {
      const allStores = await fetchCurrentStores();
      regions.value = [...new Set(allStores.stores.map((store) => store.region).filter(Boolean) as string[])];
    }
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : "載入失敗";
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  loadDashboard();
  refreshTimer = window.setInterval(loadDashboard, 60000);
});

onUnmounted(() => {
  if (refreshTimer) {
    window.clearInterval(refreshTimer);
  }
});

watch(
  () => [filters.region, filters.openOnly, filters.localTicketOnly, filters.sort],
  () => {
    loadDashboard();
  },
);
</script>

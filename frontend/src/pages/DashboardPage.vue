<template>
  <section class="page-stack">
    <section class="hero-card">
      <div>
        <p class="eyebrow">Real-time Overview</p>
        <h2>全港门店实时看板</h2>
        <p class="hero-text">
          所有数据只来自自建后端 API。页面会优先展示当前 wait、显示号码集合和可解释 ETA。
        </p>
      </div>
      <div class="hero-actions">
        <button class="button-link button-link--solid" @click="loadDashboard">立即刷新</button>
        <RouterLink class="button-link" to="/analytics">查看分析页</RouterLink>
      </div>
    </section>

    <section class="stats-row">
      <StatPanel label="门店数量" :value="String(response?.stores.length || 0)" hint="当前返回的门店总数" />
      <StatPanel label="营业中" :value="String(openStoreCount)" hint="storeStatus = OPEN" />
      <StatPanel label="最低 ETA" :value="lowestEtaLabel" hint="基于当前可估算门店" />
      <StatPanel label="数据更新时间" :value="formatDateTime(response?.data_updated_at)" hint="Asia/Hong_Kong" />
    </section>

    <section v-if="topRecommendation" class="recommend-card">
      <div>
        <p class="eyebrow">Fastest Pick</p>
        <h3>{{ topRecommendation.name }}</h3>
      </div>
      <div class="recommend-card__meta">
        <span>{{ topRecommendation.region }} / {{ topRecommendation.area }}</span>
        <span>wait {{ formatOptionalNumber(topRecommendation.wait) }}</span>
        <span>ETA {{ formatOptionalNumber(topRecommendation.eta_minutes, " 分钟") }}</span>
      </div>
      <p>{{ topRecommendation.reason }}</p>
    </section>

    <section class="panel">
      <div class="filter-row">
        <label>
          <span>区域</span>
          <select v-model="filters.region">
            <option value="">全部</option>
            <option v-for="region in regions" :key="region" :value="region">{{ region }}</option>
          </select>
        </label>
        <label>
          <span>排序</span>
          <select v-model="filters.sort">
            <option value="eta">按 ETA</option>
            <option value="wait">按 wait</option>
            <option value="name">按名称</option>
          </select>
        </label>
        <label class="checkbox-field">
          <input v-model="filters.openOnly" type="checkbox" />
          <span>只看营业中</span>
        </label>
        <label class="checkbox-field">
          <input v-model="filters.localTicketOnly" type="checkbox" />
          <span>只看可现场派筹</span>
        </label>
      </div>
    </section>

    <p v-if="errorMessage" class="error-banner">{{ errorMessage }}</p>
    <p v-if="loading" class="muted-text">正在加载门店数据…</p>

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
import { formatDateTime, formatOptionalNumber } from "../utils/format";

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
  if (!etaValues?.length) return "--";
  return `${Math.min(...etaValues)} 分钟`;
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
    errorMessage.value = error instanceof Error ? error.message : "加载失败";
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

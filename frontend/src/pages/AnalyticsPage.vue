<template>
  <section class="page-stack">
    <section class="hero-card">
      <div>
        <p class="eyebrow">擁擠分析</p>
        <h2>擁擠分析與快速推薦</h2>
        <p class="hero-text">
          以同一門店的歷史時段資料作為基底，先看預估等待時間，再看號碼推進速度，方便快速比較午市與晚市壓力。
        </p>
      </div>
    </section>

    <section class="panel control-row">
      <label>
        <span>選擇門店</span>
        <select v-model="selectedStoreId">
          <option v-for="store in stores" :key="store.id" :value="store.id">
            {{ store.name }}
          </option>
        </select>
      </label>
      <button class="button-link button-link--solid" @click="loadPage">重新整理</button>
    </section>

    <section class="stats-row" v-if="analytics">
      <StatPanel label="今日平均等待時間" :value="formatOptionalNumber(analytics.today_average_wait, ' 分鐘', 2)" />
      <StatPanel label="平日平均" :value="formatOptionalNumber(analytics.weekday_average_wait, ' 分鐘', 2)" />
      <StatPanel label="週末平均" :value="formatOptionalNumber(analytics.weekend_average_wait, ' 分鐘', 2)" />
      <StatPanel
        label="目前時段歷史均值"
        :value="formatOptionalNumber(analytics.current_hour_historical_average_wait, ' 分鐘', 2)"
      />
    </section>

    <p v-if="errorMessage" class="error-banner">{{ errorMessage }}</p>

    <section class="chart-grid" v-if="analytics">
      <TrendChart
        eyebrow="等待時間"
        title="按小時平均預估等待時間"
        :headline="waitChartHeadline"
        description="近 28 日同一時段的平均預估等待時間，單位為分鐘，可直接看出午市與晚市高峰。"
        :labels="hourLabels"
        :series="waitChartSeries"
      />
      <TrendChart
        eyebrow="推進速度"
        title="按小時平均號碼推進"
        :headline="progressChartHeadline"
        description="依顯示號碼推進節奏估算消化速度；數值越高，現場排隊消化越快。"
        :labels="hourLabels"
        :series="progressChartSeries"
      />
    </section>

    <section class="dual-grid" v-if="analytics">
      <section class="panel">
        <div class="section-header">
          <div>
            <p class="eyebrow">時段觀察</p>
            <h3>今日高峰時段</h3>
          </div>
        </div>
        <p class="panel-intro">以今日已收集到的資料為主，優先標出目前最擁擠的幾個時段。</p>
        <div class="tag-row">
          <span v-for="bucket in analytics.peak_hours" :key="bucket.hour" class="soft-tag">
            {{ bucket.label }} ・ {{ formatOptionalNumber(bucket.average_wait, ' 分鐘', 1) }}
          </span>
        </div>
      </section>

      <section class="panel">
        <div class="section-header">
          <div>
            <p class="eyebrow">時段建議</p>
            <h3>較佳造訪時段</h3>
          </div>
        </div>
        <p class="panel-intro">從近 28 日歷史均值挑出等待時間較低的時段，適合先作參考。</p>
        <div class="tag-row">
          <span v-for="bucket in analytics.recommended_hours" :key="bucket.hour" class="soft-tag soft-tag--good">
            {{ bucket.label }} ・ {{ formatOptionalNumber(bucket.average_wait, ' 分鐘', 1) }}
          </span>
        </div>
      </section>
    </section>

    <section class="dual-grid">
      <section class="panel">
        <div class="section-header">
          <div>
            <p class="eyebrow">目前排行</p>
            <h3>當前擁擠排名</h3>
          </div>
        </div>
        <div class="table-list">
          <div v-for="store in congestionRanking" :key="store.id" class="table-row">
            <div>
              <strong>{{ store.name }}</strong>
              <small>{{ formatRegionArea(store.region, store.area) }}</small>
            </div>
            <div class="table-row__metrics">
              <span>等待時間 {{ formatOptionalNumber(store.wait, ' 分鐘') }}</span>
              <span>ETA {{ store.eta.estimated_wait_minutes ?? "--" }} 分鐘</span>
            </div>
          </div>
        </div>
      </section>

      <section class="panel">
        <div class="section-header">
          <div>
            <p class="eyebrow">快速推薦</p>
            <h3>目前最快建議</h3>
          </div>
        </div>
        <div class="table-list">
          <div
            v-for="recommendation in recommendations?.recommendations || []"
            :key="recommendation.store_id"
            class="table-row"
          >
            <div>
              <strong>{{ recommendation.name }}</strong>
              <small>{{ formatRecommendationReason(recommendation.reason) }}</small>
            </div>
            <div class="table-row__metrics">
              <span>等待時間 {{ formatOptionalNumber(recommendation.wait, ' 分鐘') }}</span>
              <span>ETA {{ formatOptionalNumber(recommendation.eta_minutes, ' 分鐘') }}</span>
              <span>分數 {{ formatOptionalNumber(recommendation.score, '', 3) }}</span>
            </div>
          </div>
        </div>
      </section>
    </section>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";

import { fetchCurrentStores, fetchRecommendations, fetchStoreAnalytics } from "../api/stores";
import StatPanel from "../components/StatPanel.vue";
import TrendChart from "../components/TrendChart.vue";
import type { RecommendationsResponse, StoreAnalyticsResponse, StoreCurrent } from "../types/api";
import { formatOptionalNumber, formatRecommendationReason, formatRegionArea } from "../utils/format";

const stores = ref<StoreCurrent[]>([]);
const selectedStoreId = ref<number | null>(null);
const analytics = ref<StoreAnalyticsResponse | null>(null);
const recommendations = ref<RecommendationsResponse | null>(null);
const errorMessage = ref("");

const congestionRanking = computed(() =>
  [...stores.value].sort((left, right) => (right.wait || -1) - (left.wait || -1)).slice(0, 8),
);

const hourLabels = computed(() => analytics.value?.hourly_average_wait.map((bucket) => bucket.label) || []);

const waitChartSeries = computed(() => [
  {
    name: "平均等待時間",
    color: "#e85d3f",
    fill: true,
    values: analytics.value?.hourly_average_wait.map((bucket) => bucket.average_wait) || [],
  },
]);

const progressChartSeries = computed(() => [
  {
    name: "號碼推進",
    color: "#3f7cff",
    fill: true,
    values: analytics.value?.hourly_average_queue_progress.map((bucket) => bucket.average_queue_progress) || [],
  },
]);

const waitChartHeadline = computed(() => {
  const buckets = analytics.value?.hourly_average_wait.filter((bucket) => bucket.average_wait !== null) || [];
  if (!buckets.length) return "暫無足夠資料";
  const highest = [...buckets].sort((left, right) => (right.average_wait || 0) - (left.average_wait || 0))[0];
  return `${highest.label} 最長 ${formatOptionalNumber(highest.average_wait, " 分鐘", 1)}`;
});

const progressChartHeadline = computed(() => {
  const buckets =
    analytics.value?.hourly_average_queue_progress.filter((bucket) => bucket.average_queue_progress !== null) || [];
  if (!buckets.length) return "暫無足夠資料";
  const fastest = [...buckets].sort(
    (left, right) => (right.average_queue_progress || 0) - (left.average_queue_progress || 0),
  )[0];
  return `${fastest.label} 最快 ${formatOptionalNumber(fastest.average_queue_progress, " 組/分", 2)}`;
});

async function loadPage() {
  errorMessage.value = "";
  try {
    const current = await fetchCurrentStores();
    stores.value = current.stores;
    if (!selectedStoreId.value && current.stores.length) {
      selectedStoreId.value = current.stores[0].id;
    }

    recommendations.value = await fetchRecommendations({ limit: 5 });
    if (selectedStoreId.value) {
      analytics.value = await fetchStoreAnalytics(selectedStoreId.value);
    }
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : "載入失敗";
  }
}

watch(
  selectedStoreId,
  async (storeId) => {
    if (!storeId) return;
    try {
      analytics.value = await fetchStoreAnalytics(storeId);
    } catch (error) {
      errorMessage.value = error instanceof Error ? error.message : "載入分析資料失敗";
    }
  },
);

onMounted(() => {
  loadPage();
});
</script>

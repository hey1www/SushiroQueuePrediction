<template>
  <section class="page-stack">
    <section class="hero-card">
      <div>
        <p class="eyebrow">Analytics</p>
        <h2>拥挤分析与快速推荐</h2>
        <p class="hero-text">
          分析页把当前排名和单店历史统计放在一起，方便先横向比较，再纵向看门店曲线。
        </p>
      </div>
    </section>

    <section class="panel control-row">
      <label>
        <span>选择门店</span>
        <select v-model="selectedStoreId">
          <option v-for="store in stores" :key="store.id" :value="store.id">
            {{ store.name }}
          </option>
        </select>
      </label>
      <button class="button-link button-link--solid" @click="loadPage">刷新数据</button>
    </section>

    <section class="stats-row" v-if="analytics">
      <StatPanel label="今日平均 wait" :value="formatOptionalNumber(analytics.today_average_wait)" />
      <StatPanel label="工作日均值" :value="formatOptionalNumber(analytics.weekday_average_wait)" />
      <StatPanel label="周末均值" :value="formatOptionalNumber(analytics.weekend_average_wait)" />
      <StatPanel
        label="当前时段历史均值"
        :value="formatOptionalNumber(analytics.current_hour_historical_average_wait)"
      />
    </section>

    <p v-if="errorMessage" class="error-banner">{{ errorMessage }}</p>

    <section class="chart-grid" v-if="analytics">
      <TrendChart
        title="按小时平均 wait"
        label="historical wait"
        color="#e85d3f"
        :values="analytics.hourly_average_wait.map((bucket) => bucket.average_wait)"
        start-label="00:00"
        end-label="23:00"
      />
      <TrendChart
        title="按小时平均 queue 推进"
        label="historical progress"
        color="#3f7cff"
        :values="analytics.hourly_average_queue_progress.map((bucket) => bucket.average_queue_progress)"
        start-label="00:00"
        end-label="23:00"
      />
    </section>

    <section class="dual-grid">
      <section class="panel">
        <div class="section-header">
          <div>
            <p class="eyebrow">Current Ranking</p>
            <h3>当前拥挤排名</h3>
          </div>
        </div>
        <div class="table-list">
          <div v-for="store in congestionRanking" :key="store.id" class="table-row">
            <div>
              <strong>{{ store.name }}</strong>
              <small>{{ store.region }} / {{ store.area }}</small>
            </div>
            <div class="table-row__metrics">
              <span>wait {{ formatOptionalNumber(store.wait) }}</span>
              <span>ETA {{ store.eta.estimated_wait_minutes ?? "--" }}</span>
            </div>
          </div>
        </div>
      </section>

      <section class="panel">
        <div class="section-header">
          <div>
            <p class="eyebrow">Fastest Stores</p>
            <h3>当前最快推荐</h3>
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
              <small>{{ recommendation.reason }}</small>
            </div>
            <div class="table-row__metrics">
              <span>score {{ recommendation.score }}</span>
              <span>ETA {{ formatOptionalNumber(recommendation.eta_minutes) }}</span>
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
import { formatOptionalNumber } from "../utils/format";

const stores = ref<StoreCurrent[]>([]);
const selectedStoreId = ref<number | null>(null);
const analytics = ref<StoreAnalyticsResponse | null>(null);
const recommendations = ref<RecommendationsResponse | null>(null);
const errorMessage = ref("");

const congestionRanking = computed(() =>
  [...stores.value].sort((left, right) => (right.wait || -1) - (left.wait || -1)).slice(0, 8),
);

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
    errorMessage.value = error instanceof Error ? error.message : "加载失败";
  }
}

watch(
  selectedStoreId,
  async (storeId) => {
    if (!storeId) return;
    try {
      analytics.value = await fetchStoreAnalytics(storeId);
    } catch (error) {
      errorMessage.value = error instanceof Error ? error.message : "加载分析数据失败";
    }
  },
);

onMounted(() => {
  loadPage();
});
</script>

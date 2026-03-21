<template>
  <section class="page-stack" v-if="detail">
    <section class="hero-card">
      <div>
        <p class="eyebrow">Store Detail</p>
        <h2>{{ detail.store.name }}</h2>
        <p class="hero-text">
          {{ detail.store.region }} / {{ detail.store.area }} · {{ detail.store.address }}
        </p>
      </div>
      <div class="hero-actions">
        <RouterLink class="button-link" to="/">返回看板</RouterLink>
      </div>
    </section>

    <section class="stats-row">
      <StatPanel label="当前 wait" :value="formatOptionalNumber(detail.store.wait)" />
      <StatPanel label="waitingGroup" :value="formatOptionalNumber(detail.store.waiting_group)" />
      <StatPanel label="ETA" :value="formatEta(detail.store.eta)" :hint="detail.store.eta.reason" />
      <StatPanel label="更新时间" :value="formatDateTime(detail.data_updated_at)" />
    </section>

    <section class="panel detail-grid">
      <div>
        <p class="eyebrow">Current Queue</p>
        <h3>最新显示号码</h3>
        <code v-if="detail.latest_queue.store_queue.length">{{ detail.latest_queue.store_queue.join(", ") }}</code>
        <p v-else class="muted-text">当前没有可用的 storeQueue。</p>
      </div>
      <div class="detail-summary">
        <div>
          <span>queue min</span>
          <strong>{{ formatOptionalNumber(detail.latest_queue.queue_min) }}</strong>
        </div>
        <div>
          <span>queue max</span>
          <strong>{{ formatOptionalNumber(detail.latest_queue.queue_max) }}</strong>
        </div>
        <div>
          <span>queue count</span>
          <strong>{{ formatOptionalNumber(detail.latest_queue.queue_count) }}</strong>
        </div>
        <div>
          <span>queue span</span>
          <strong>{{ formatOptionalNumber(detail.latest_queue.queue_span) }}</strong>
        </div>
      </div>
    </section>

    <section class="chart-grid" v-if="history">
      <TrendChart
        title="最近 6 小时 wait 曲线"
        label="wait"
        color="#e85d3f"
        :values="history.points.map((point) => point.wait)"
        :start-label="historyStartLabel"
        :end-label="historyEndLabel"
      />
      <TrendChart
        title="最近 6 小时 waitingGroup"
        label="waitingGroup"
        color="#3f7cff"
        :values="history.points.map((point) => point.waiting_group)"
        :start-label="historyStartLabel"
        :end-label="historyEndLabel"
      />
      <TrendChart
        title="最近 6 小时 queue max"
        label="queue_max"
        color="#12a37d"
        :values="history.points.map((point) => point.queue_max)"
        :start-label="historyStartLabel"
        :end-label="historyEndLabel"
      />
    </section>

    <section class="panel" v-if="analytics">
      <div class="section-header">
        <div>
          <p class="eyebrow">Today Insight</p>
          <h3>今日高峰与建议时段</h3>
        </div>
      </div>
      <div class="insight-columns">
        <div>
          <p class="muted-text">今日平均 wait</p>
          <strong class="display-value">{{ formatOptionalNumber(analytics.today_average_wait) }}</strong>
        </div>
        <div>
          <p class="muted-text">当前时段历史均值</p>
          <strong class="display-value">{{ formatOptionalNumber(analytics.current_hour_historical_average_wait) }}</strong>
        </div>
      </div>
      <div class="tag-groups">
        <div>
          <p class="muted-text">今日高峰</p>
          <div class="tag-row">
            <span v-for="bucket in analytics.peak_hours" :key="bucket.hour" class="soft-tag">
              {{ bucket.label }} · {{ formatOptionalNumber(bucket.average_wait) }}
            </span>
          </div>
        </div>
        <div>
          <p class="muted-text">建议时段</p>
          <div class="tag-row">
            <span v-for="bucket in analytics.recommended_hours" :key="bucket.hour" class="soft-tag soft-tag--good">
              {{ bucket.label }} · {{ formatOptionalNumber(bucket.average_wait) }}
            </span>
          </div>
        </div>
      </div>
    </section>
  </section>

  <section v-else class="page-stack">
    <p v-if="loading" class="muted-text">正在加载门店详情…</p>
    <p v-else-if="errorMessage" class="error-banner">{{ errorMessage }}</p>
  </section>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { RouterLink, useRoute } from "vue-router";

import { fetchStoreAnalytics, fetchStoreDetail, fetchStoreHistory } from "../api/stores";
import StatPanel from "../components/StatPanel.vue";
import TrendChart from "../components/TrendChart.vue";
import type { StoreAnalyticsResponse, StoreDetailResponse, StoreHistoryResponse } from "../types/api";
import { formatDateTime, formatEta, formatOptionalNumber } from "../utils/format";

const route = useRoute();
const detail = ref<StoreDetailResponse | null>(null);
const history = ref<StoreHistoryResponse | null>(null);
const analytics = ref<StoreAnalyticsResponse | null>(null);
const loading = ref(false);
const errorMessage = ref("");

const historyStartLabel = computed(() => {
  const points = history.value?.points || [];
  return points.length ? formatDateTime(points[0].timestamp) : "--";
});

const historyEndLabel = computed(() => {
  const points = history.value?.points || [];
  return points.length ? formatDateTime(points[points.length - 1].timestamp) : "--";
});

async function loadStore() {
  const storeId = Number(route.params.storeId);
  if (!storeId) {
    errorMessage.value = "无效的门店 ID";
    return;
  }

  loading.value = true;
  errorMessage.value = "";

  try {
    const [detailResponse, historyResponse, analyticsResponse] = await Promise.all([
      fetchStoreDetail(storeId),
      fetchStoreHistory(storeId, 6),
      fetchStoreAnalytics(storeId),
    ]);
    detail.value = detailResponse;
    history.value = historyResponse;
    analytics.value = analyticsResponse;
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : "加载失败";
  } finally {
    loading.value = false;
  }
}

watch(
  () => route.params.storeId,
  () => {
    loadStore();
  },
  { immediate: true },
);
</script>

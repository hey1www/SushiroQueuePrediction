<template>
  <section class="page-stack" v-if="detail">
    <section class="hero-card">
      <div>
        <p class="eyebrow">門店詳情</p>
        <h2>{{ detail.store.name }}</h2>
        <p class="hero-text">
          {{ formatRegionArea(detail.store.region, detail.store.area) }} ・ {{ detail.store.address }}
        </p>
      </div>
      <div class="hero-actions">
        <RouterLink class="button-link" to="/">返回看板</RouterLink>
      </div>
    </section>

    <section class="stats-row">
      <StatPanel label="等候組數" :value="formatOptionalNumber(detail.store.wait)" />
      <StatPanel label="候位組數" :value="formatOptionalNumber(detail.store.waiting_group)" />
      <StatPanel label="預估等候" :value="formatEta(detail.store.eta)" :hint="formatEtaReason(detail.store.eta.reason)" />
      <StatPanel label="更新時間" :value="formatDateTime(detail.data_updated_at)" />
    </section>

    <section class="panel detail-grid">
      <div>
        <p class="eyebrow">顯示號碼</p>
        <h3>最新顯示號碼</h3>
        <div class="queue-display-list">
          <div>
            <p class="muted-text">現場取號</p>
            <code v-if="latestQueueDisplay.onsiteQueue.length">{{ latestQueueDisplay.onsiteQueue.join(", ") }}</code>
            <p v-else class="muted-text">目前沒有可用的現場號碼資料。</p>
          </div>
          <div v-if="latestQueueDisplay.reservationQueue.length">
            <p class="muted-text">手機預約</p>
            <code>{{ latestQueueDisplay.reservationQueue.join(", ") }}</code>
          </div>
        </div>
      </div>
      <div class="detail-summary">
        <div>
          <span>現場最小號碼</span>
          <strong>{{ formatOptionalNumber(latestQueueDisplay.queueMin) }}</strong>
        </div>
        <div>
          <span>現場最大號碼</span>
          <strong>{{ formatOptionalNumber(latestQueueDisplay.queueMax) }}</strong>
        </div>
        <div>
          <span>顯示數量</span>
          <strong>{{ formatOptionalNumber(latestQueueDisplay.queueCount) }}</strong>
        </div>
        <div>
          <span>號碼跨度</span>
          <strong>{{ formatOptionalNumber(latestQueueDisplay.queueSpan) }}</strong>
        </div>
      </div>
    </section>

    <section class="chart-grid" v-if="history">
      <TrendChart
        eyebrow="等候走勢"
        title="最近 6 小時等候組數"
        :headline="detailWaitHeadline"
        description="顯示最近 6 小時等候組數走勢；數值越高，代表現場等待壓力越大。"
        :labels="historyLabels"
        :series="[
          {
            name: '等候組數',
            color: '#e85d3f',
            fill: true,
            values: history.points.map((point) => point.wait),
          },
        ]"
      />
      <TrendChart
        eyebrow="候位密度"
        title="最近 6 小時候位組數"
        :headline="detailWaitingGroupHeadline"
        description="顯示最近 6 小時候位組數變化，可用來對照等候組數的變動節奏。"
        :labels="historyLabels"
        :series="[
          {
            name: '候位組數',
            color: '#3f7cff',
            fill: true,
            values: history.points.map((point) => point.waiting_group),
          },
        ]"
      />
      <TrendChart
        eyebrow="號碼推進"
        title="最近 6 小時顯示號碼上限"
        :headline="detailQueueHeadline"
        description="綠線表示現場取號上限，紫線表示手機預約號上限，用來觀察兩種隊列的推進節奏。"
        :labels="historyLabels"
        :series="[
          {
            name: '現場取號',
            color: '#12a37d',
            fill: true,
            values: onsiteQueueHistoryValues,
          },
          {
            name: '手機預約',
            color: '#5b66f5',
            dashed: true,
            values: reservationQueueHistoryValues,
          },
        ]"
      />
    </section>

    <section class="panel" v-if="analytics">
      <div class="section-header">
        <div>
          <p class="eyebrow">今日觀察</p>
          <h3>今日高峰與建議時段</h3>
        </div>
      </div>
      <div class="insight-columns">
        <div>
          <p class="muted-text">今日平均等候</p>
          <strong class="display-value">{{ formatOptionalNumber(analytics.today_average_wait, ' 組', 2) }}</strong>
        </div>
        <div>
          <p class="muted-text">目前時段歷史均值</p>
          <strong class="display-value">{{ formatOptionalNumber(analytics.current_hour_historical_average_wait, ' 組', 2) }}</strong>
        </div>
      </div>
      <div class="tag-groups">
        <div>
          <p class="muted-text">今日高峰</p>
          <div class="tag-row">
            <span v-for="bucket in analytics.peak_hours" :key="bucket.hour" class="soft-tag">
              {{ bucket.label }} ・ {{ formatOptionalNumber(bucket.average_wait, ' 組', 1) }}
            </span>
          </div>
        </div>
        <div>
          <p class="muted-text">建議時段</p>
          <div class="tag-row">
            <span v-for="bucket in analytics.recommended_hours" :key="bucket.hour" class="soft-tag soft-tag--good">
              {{ bucket.label }} ・ {{ formatOptionalNumber(bucket.average_wait, ' 組', 1) }}
            </span>
          </div>
        </div>
      </div>
    </section>
  </section>

  <section v-else class="page-stack">
    <p v-if="loading" class="muted-text">正在載入門店詳情…</p>
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
import {
  formatDateTime,
  formatEta,
  formatEtaReason,
  formatOptionalNumber,
  formatRegionArea,
  formatTime,
} from "../utils/format";

const route = useRoute();
const detail = ref<StoreDetailResponse | null>(null);
const history = ref<StoreHistoryResponse | null>(null);
const analytics = ref<StoreAnalyticsResponse | null>(null);
const loading = ref(false);
const errorMessage = ref("");
const RESERVATION_QUEUE_THRESHOLD = 8000;

const latestQueueDisplay = computed(() => {
  const latestQueue = detail.value?.latest_queue;
  if (!latestQueue) {
    return {
      onsiteQueue: [] as number[],
      reservationQueue: [] as number[],
      queueMin: null as number | null,
      queueMax: null as number | null,
      queueCount: null as number | null,
      queueSpan: null as number | null,
    };
  }

  const onsiteQueue = latestQueue.store_queue.filter((number) => number < RESERVATION_QUEUE_THRESHOLD);
  const reservationQueue = latestQueue.reservation_queue.length
    ? latestQueue.reservation_queue.filter((number) => number >= RESERVATION_QUEUE_THRESHOLD)
    : latestQueue.store_queue.filter((number) => number >= RESERVATION_QUEUE_THRESHOLD);
  const queueMin = onsiteQueue.length ? Math.min(...onsiteQueue) : null;
  const queueMax = onsiteQueue.length ? Math.max(...onsiteQueue) : null;
  const queueCount = onsiteQueue.length;
  const queueSpan = queueMin !== null && queueMax !== null ? queueMax - queueMin : null;

  return {
    onsiteQueue,
    reservationQueue,
    queueMin,
    queueMax,
    queueCount,
    queueSpan,
  };
});

const onsiteQueueHistoryValues = computed(() =>
  (history.value?.points || []).map((point) => getOnsiteQueueMax(point)),
);

const reservationQueueHistoryValues = computed(() =>
  (history.value?.points || []).map((point) => getReservationQueueMax(point)),
);

const historyLabels = computed(() => {
  const points = history.value?.points || [];
  return points.map((point) => formatTime(point.timestamp));
});

const detailWaitHeadline = computed(() => {
  const latest = [...(history.value?.points || [])].reverse().find((point) => point.wait !== null)?.wait;
  return latest === undefined || latest === null ? "暫無資料" : `最新 ${formatOptionalNumber(latest, " 組")}`;
});

const detailWaitingGroupHeadline = computed(() => {
  const latest = [...(history.value?.points || [])].reverse().find((point) => point.waiting_group !== null)?.waiting_group;
  return latest === undefined || latest === null ? "暫無資料" : `最新 ${formatOptionalNumber(latest, " 組")}`;
});

const detailQueueHeadline = computed(() => {
  const latestOnsite = [...onsiteQueueHistoryValues.value].reverse().find((value) => value !== null);
  const latestReservation = [...reservationQueueHistoryValues.value].reverse().find((value) => value !== null);

  if (latestOnsite !== undefined && latestOnsite !== null && latestReservation !== undefined && latestReservation !== null) {
    return `現場 ${formatOptionalNumber(latestOnsite)} ・ 預約 ${formatOptionalNumber(latestReservation)}`;
  }
  if (latestOnsite !== undefined && latestOnsite !== null) {
    return `現場 ${formatOptionalNumber(latestOnsite)}`;
  }
  if (latestReservation !== undefined && latestReservation !== null) {
    return `預約 ${formatOptionalNumber(latestReservation)}`;
  }
  return "暫無資料";
});

function getOnsiteQueueMax(point: StoreHistoryResponse["points"][number]) {
  if (point.queue_max === null || point.queue_max === undefined) return null;
  return point.queue_max >= RESERVATION_QUEUE_THRESHOLD ? null : point.queue_max;
}

function getReservationQueueMax(point: StoreHistoryResponse["points"][number]) {
  if (point.reservation_queue_max !== null && point.reservation_queue_max !== undefined) {
    return point.reservation_queue_max >= RESERVATION_QUEUE_THRESHOLD ? point.reservation_queue_max : null;
  }
  if (point.queue_max !== null && point.queue_max !== undefined && point.queue_max >= RESERVATION_QUEUE_THRESHOLD) {
    return point.queue_max;
  }
  return null;
}

async function loadStore() {
  const storeId = Number(route.params.storeId);
  if (!storeId) {
    errorMessage.value = "無效的門店 ID";
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
    errorMessage.value = error instanceof Error ? error.message : "載入失敗";
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

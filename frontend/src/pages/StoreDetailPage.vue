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
        title="當天等候組數"
        :headline="detailWaitHeadline"
        description="顯示當天 10:00 至 23:00 的等候組數走勢；數值越高，代表現場等待壓力越大。"
        :labels="historyTimeline"
        x-axis-type="time"
        :x-min="chartRange.start"
        :x-max="chartRange.end"
        :series="[
          {
            name: '等候組數',
            color: '#e85d3f',
            fill: true,
            values: waitHistoryValues,
          },
        ]"
      />
      <TrendChart
        eyebrow="候位密度"
        title="當天候位組數"
        :headline="detailWaitingGroupHeadline"
        description="顯示當天 10:00 至 23:00 的候位組數變化，可用來對照等候節奏。"
        :labels="historyTimeline"
        x-axis-type="time"
        :x-min="chartRange.start"
        :x-max="chartRange.end"
        :series="[
          {
            name: '候位組數',
            color: '#3f7cff',
            fill: true,
            values: waitingGroupHistoryValues,
          },
        ]"
      />
      <div class="dual-grid">
        <TrendChart
          eyebrow="號碼推進"
          title="當天現場顯示號碼上限"
          :headline="detailOnsiteQueueHeadline"
          description="顯示當天 10:00 至 23:00 的現場取號上限，用來觀察現場隊列推進。"
          :labels="historyTimeline"
          x-axis-type="time"
          :x-min="chartRange.start"
          :x-max="chartRange.end"
          :series="[
            {
              name: '現場取號',
              color: '#12a37d',
              fill: true,
              values: onsiteQueueHistoryValues,
            },
          ]"
        />
        <TrendChart
          eyebrow="預約進度"
          title="當天手機預約號上限"
          :headline="detailReservationQueueHeadline"
          description="顯示當天 10:00 至 23:00 的手機預約號上限；展示值已去掉開頭的 8。"
          :labels="historyTimeline"
          x-axis-type="time"
          :x-min="chartRange.start"
          :x-max="chartRange.end"
          :series="[
            {
              name: '手機預約',
              color: '#5b66f5',
              fill: true,
              values: reservationQueueHistoryValues,
            },
          ]"
        />
      </div>
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
} from "../utils/format";

const route = useRoute();
const detail = ref<StoreDetailResponse | null>(null);
const history = ref<StoreHistoryResponse | null>(null);
const analytics = ref<StoreAnalyticsResponse | null>(null);
const loading = ref(false);
const errorMessage = ref("");
const RESERVATION_QUEUE_THRESHOLD = 8000;
const HK_DATE_FORMATTER = new Intl.DateTimeFormat("en-CA", {
  timeZone: "Asia/Hong_Kong",
  year: "numeric",
  month: "2-digit",
  day: "2-digit",
});

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
    reservationQueue: reservationQueue.map((number) => normalizeReservationNumber(number)),
    queueMin,
    queueMax,
    queueCount,
    queueSpan,
  };
});

const chartDateKey = computed(() => {
  const latestTimestamp = [...(history.value?.points || [])].reverse().find((point) => point.timestamp)?.timestamp;
  return getHongKongDateKey(detail.value?.data_updated_at || latestTimestamp || new Date().toISOString());
});

const chartRange = computed(() => ({
  start: `${chartDateKey.value}T10:00:00+08:00`,
  end: `${chartDateKey.value}T23:00:00+08:00`,
}));

const dayHistoryPoints = computed(() => {
  const startMs = Date.parse(chartRange.value.start);
  const endMs = Date.parse(chartRange.value.end);

  return (history.value?.points || []).filter((point) => {
    const pointMs = Date.parse(point.timestamp);
    return Number.isFinite(pointMs) && pointMs >= startMs && pointMs <= endMs;
  });
});

const historyTimeline = computed(() => dayHistoryPoints.value.map((point) => point.timestamp));
const waitHistoryValues = computed(() => dayHistoryPoints.value.map((point) => point.wait));
const waitingGroupHistoryValues = computed(() => dayHistoryPoints.value.map((point) => point.waiting_group));
const onsiteQueueHistoryValues = computed(() =>
  dayHistoryPoints.value.map((point) => getOnsiteQueueMax(point)),
);

const reservationQueueHistoryValues = computed(() =>
  dayHistoryPoints.value.map((point) => getReservationQueueDisplayMax(point)),
);

const detailWaitHeadline = computed(() => {
  const latest = [...dayHistoryPoints.value].reverse().find((point) => point.wait !== null)?.wait;
  return latest === undefined || latest === null ? "暫無資料" : `最新 ${formatOptionalNumber(latest, " 組")}`;
});

const detailWaitingGroupHeadline = computed(() => {
  const latest = [...dayHistoryPoints.value].reverse().find((point) => point.waiting_group !== null)?.waiting_group;
  return latest === undefined || latest === null ? "暫無資料" : `最新 ${formatOptionalNumber(latest, " 組")}`;
});

const detailOnsiteQueueHeadline = computed(() => {
  const latestOnsite = [...onsiteQueueHistoryValues.value].reverse().find((value) => value !== null);
  if (latestOnsite !== undefined && latestOnsite !== null) {
    return `最新 ${formatOptionalNumber(latestOnsite)}`;
  }
  return "暫無資料";
});

const detailReservationQueueHeadline = computed(() => {
  const latestReservation = [...reservationQueueHistoryValues.value].reverse().find((value) => value !== null);
  if (latestReservation !== undefined && latestReservation !== null) {
    return `最新 ${formatOptionalNumber(latestReservation)}`;
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

function getReservationQueueDisplayMax(point: StoreHistoryResponse["points"][number]) {
  return normalizeReservationNumber(getReservationQueueMax(point));
}

function normalizeReservationNumber(value: number | null | undefined) {
  if (value === null || value === undefined) return null;
  if (value >= RESERVATION_QUEUE_THRESHOLD) return value - RESERVATION_QUEUE_THRESHOLD;
  return value;
}

function getHongKongDateKey(value: string) {
  const parts = HK_DATE_FORMATTER.formatToParts(new Date(value));
  const year = parts.find((part) => part.type === "year")?.value ?? "0000";
  const month = parts.find((part) => part.type === "month")?.value ?? "01";
  const day = parts.find((part) => part.type === "day")?.value ?? "01";
  return `${year}-${month}-${day}`;
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
      fetchStoreHistory(storeId, 24),
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

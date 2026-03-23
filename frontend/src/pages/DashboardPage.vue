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
      <StatPanel label="最快 ETA" :value="lowestEtaLabel" hint="以本地 ETA 可估算門店為準" />
      <StatPanel label="更新時間" :value="formatDateTime(response?.data_updated_at)" hint="香港時間" />
    </section>

    <section v-if="quickSuggestion" class="recommend-card">
      <div class="recommend-card__header">
        <div>
          <p class="eyebrow">快速建議</p>
          <h3>{{ quickSuggestion.title }}</h3>
        </div>
        <small class="recommend-card__count">{{ quickSuggestion.summary }}</small>
      </div>
      <div class="recommend-card__meta">
        <span>{{ quickSuggestion.description }}</span>
      </div>
      <div v-if="quickSuggestion.mode === 'queue_free'" class="recommend-chip-grid">
        <RouterLink
          v-for="item in quickSuggestion.items"
          :key="item.id"
          class="recommend-chip recommend-chip--link"
          :to="`/stores/${item.id}`"
        >
          <strong>{{ item.name }}</strong>
          <small>{{ formatRegionArea(item.region, item.area) }}</small>
          <span>候位組數 {{ formatOptionalNumber(item.waiting_group, " 桌") }}</span>
          <span>本地 ETA {{ formatOptionalNumber(item.eta_minutes, " 分鐘") }}</span>
        </RouterLink>
      </div>
      <div v-else class="recommend-list">
        <article v-for="item in quickSuggestion.items" :key="item.id" class="recommend-item">
          <div class="recommend-item__head">
            <strong>{{ item.name }}</strong>
            <small>{{ formatRegionArea(item.region, item.area) }}</small>
          </div>
          <div class="recommend-item__metrics">
            <span>預估等待時間 {{ formatOptionalNumber(item.wait, " 分鐘") }}</span>
            <span>現場號碼數 {{ formatOptionalNumber(item.queue_count) }}</span>
            <span>候位組數 {{ formatOptionalNumber(item.waiting_group, " 桌") }}</span>
          </div>
        </article>
      </div>
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
            <option value="eta">按 ETA</option>
            <option value="wait">按預估等待時間</option>
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

    <p v-if="response && !visibleStores.length" class="muted-text">目前無需在下方重複展示的排隊門店。</p>

    <section class="store-grid" v-if="visibleStores.length">
      <StoreCard v-for="store in visibleStores" :key="store.id" :store="store" />
    </section>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from "vue";
import { RouterLink } from "vue-router";

import { fetchCurrentStores } from "../api/stores";
import StatPanel from "../components/StatPanel.vue";
import StoreCard from "../components/StoreCard.vue";
import { useDashboardFilters } from "../stores/useFilters";
import type { StoreCurrent, StoresCurrentResponse } from "../types/api";
import { formatDateTime, formatOptionalNumber, formatRegionArea } from "../utils/format";

interface QuickSuggestionItem {
  id: number;
  name: string;
  area: string | null;
  region: string | null;
  wait: number | null;
  waiting_group: number | null;
  eta_minutes: number | null;
  queue_count: number | null;
}

interface QuickSuggestion {
  mode: "queue_free" | "ranked";
  title: string;
  summary: string;
  description: string;
  items: QuickSuggestionItem[];
}

const filters = useDashboardFilters();
const response = ref<StoresCurrentResponse | null>(null);
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

const recommendableStores = computed(() =>
  (response.value?.stores || []).filter(
    (store) => store.store_status === "OPEN" && store.local_ticketing_status === "ON",
  ),
);

const queueFreeStores = computed(() =>
  recommendableStores.value.filter((store) => isQueueFreeStore(store)).sort(compareSuggestedStores),
);

const queueFreeStoreIds = computed(() => new Set(queueFreeStores.value.map((store) => store.id)));

const rankedStores = computed(() =>
  [...recommendableStores.value].filter((store) => !isQueueFreeStore(store)).sort(compareSuggestedStores).slice(0, 3),
);

const visibleStores = computed(() =>
  (response.value?.stores || []).filter((store) => !queueFreeStoreIds.value.has(store.id)),
);

const quickSuggestion = computed<QuickSuggestion | null>(() => {
  if (!recommendableStores.value.length) return null;

  if (queueFreeStores.value.length) {
    return {
      mode: "queue_free",
      title: "目前免排隊門店",
      summary: `共 ${queueFreeStores.value.length} 間`,
      description: "候位組數為 0 的門店會先集中到這裡；如果同時有多家，全部都值得優先考慮。",
      items: queueFreeStores.value.map(toQuickSuggestionItem),
    };
  }

  return {
    mode: "ranked",
    title: "目前較快建議",
    summary: `優先顯示 ${rankedStores.value.length} 間`,
    description: "目前可現場派籌門店都在排隊，以下先按預估等待時間，再按現場號碼數與候位組數排序。",
    items: rankedStores.value.map(toQuickSuggestionItem),
  };
});

function isQueueFreeStore(store: StoreCurrent) {
  if (store.waiting_group === 0) return true;
  if (store.waiting_group !== null) return false;
  return store.wait === 0 || store.eta.estimated_wait_minutes === 0;
}

function comparableWait(store: StoreCurrent) {
  return store.wait ?? store.eta.estimated_wait_minutes ?? Number.POSITIVE_INFINITY;
}

function comparableQueueCount(store: StoreCurrent) {
  return store.queue.queue_count ?? Number.POSITIVE_INFINITY;
}

function comparableWaitingGroup(store: StoreCurrent) {
  return store.waiting_group ?? Number.POSITIVE_INFINITY;
}

function compareSuggestedStores(left: StoreCurrent, right: StoreCurrent) {
  const nameDiff = (left.name || "").localeCompare(right.name || "", "zh-HK");

  return (
    comparableWait(left) - comparableWait(right) ||
    comparableQueueCount(left) - comparableQueueCount(right) ||
    comparableWaitingGroup(left) - comparableWaitingGroup(right) ||
    nameDiff
  );
}

function toQuickSuggestionItem(store: StoreCurrent): QuickSuggestionItem {
  return {
    id: store.id,
    name: store.name || `門店 ${store.id}`,
    area: store.area,
    region: store.region,
    wait: store.wait,
    waiting_group: store.waiting_group,
    eta_minutes: store.eta.estimated_wait_minutes,
    queue_count: store.queue.queue_count,
  };
}

async function loadDashboard() {
  loading.value = true;
  errorMessage.value = "";

  try {
    const storesResponse = await fetchCurrentStores({
      region: filters.region || undefined,
      open_only: filters.openOnly,
      local_ticket_only: filters.localTicketOnly,
      sort: filters.sort,
    });

    response.value = storesResponse;

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

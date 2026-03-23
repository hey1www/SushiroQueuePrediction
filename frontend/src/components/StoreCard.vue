<template>
  <article class="store-card">
    <div class="store-card__head">
      <div class="store-card__title-block">
        <p class="eyebrow">{{ formatRegionArea(store.region, store.area) }}</p>
        <h3>{{ store.name }}</h3>
        <div class="store-card__badges">
          <StatusBadge :label="formatStoreStatus(store.store_status)" :tone="statusTone(store.store_status)" />
          <StatusBadge :label="formatLocalTicketingStatus(store.local_ticketing_status)" :tone="statusTone(store.local_ticketing_status)" />
        </div>
      </div>
    </div>

    <div class="metric-grid">
      <div>
        <p>預估等待時間</p>
        <strong>{{ formatOptionalNumber(store.wait, ' 分鐘') }}</strong>
      </div>
      <div>
        <p>候位組數</p>
        <strong>{{ formatOptionalNumber(store.waiting_group) }}</strong>
      </div>
      <div>
        <p>顯示號碼數</p>
        <strong>{{ formatOptionalNumber(onsiteQueueCount) }}</strong>
      </div>
      <div>
        <p>本地 ETA</p>
        <strong>{{ formatEta(store.eta) }}</strong>
      </div>
    </div>

    <div class="queue-strip">
      <span>目前顯示號碼</span>
      <code v-if="onsiteQueue.length">
        {{ onsiteQueue.join(", ") }}
      </code>
      <span v-else>暫無可用顯示號碼資料</span>
    </div>

    <p class="store-card__reason">{{ formatEtaReason(store.eta.reason) }}</p>

    <div class="store-card__footer">
      <small>更新時間 {{ formatDateTime(store.data_updated_at) }}</small>
      <RouterLink class="button-link" :to="`/stores/${store.id}`">查看詳情</RouterLink>
    </div>
  </article>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { RouterLink } from "vue-router";

import type { StoreCurrent } from "../types/api";
import {
  formatDateTime,
  formatEta,
  formatEtaReason,
  formatLocalTicketingStatus,
  formatOptionalNumber,
  formatRegionArea,
  formatStoreStatus,
  statusTone,
} from "../utils/format";
import StatusBadge from "./StatusBadge.vue";

const props = defineProps<{
  store: StoreCurrent;
}>();

const RESERVATION_QUEUE_THRESHOLD = 8000;

const onsiteQueue = computed(() => props.store.queue.store_queue.filter((number) => number < RESERVATION_QUEUE_THRESHOLD));
const onsiteQueueCount = computed(() => onsiteQueue.value.length);
</script>

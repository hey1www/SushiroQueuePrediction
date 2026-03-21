<template>
  <article class="store-card">
    <div class="store-card__head">
      <div>
        <p class="eyebrow">{{ formatRegionArea(store.region, store.area) }}</p>
        <h3>{{ store.name }}</h3>
      </div>
      <div class="store-card__badges">
        <StatusBadge :label="formatStoreStatus(store.store_status)" :tone="statusTone(store.store_status)" />
        <StatusBadge :label="formatLocalTicketingStatus(store.local_ticketing_status)" :tone="statusTone(store.local_ticketing_status)" />
      </div>
    </div>

    <div class="metric-grid">
      <div>
        <p>等候組數</p>
        <strong>{{ formatOptionalNumber(store.wait) }}</strong>
      </div>
      <div>
        <p>候位組數</p>
        <strong>{{ formatOptionalNumber(store.waiting_group) }}</strong>
      </div>
      <div>
        <p>顯示號碼數</p>
        <strong>{{ formatOptionalNumber(store.queue.queue_count) }}</strong>
      </div>
      <div>
        <p>預估等候</p>
        <strong>{{ formatEta(store.eta) }}</strong>
      </div>
    </div>

    <div class="queue-strip">
      <span>目前顯示號碼</span>
      <code v-if="store.queue.store_queue.length">
        {{ store.queue.store_queue.join(", ") }}
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

defineProps<{
  store: StoreCurrent;
}>();
</script>

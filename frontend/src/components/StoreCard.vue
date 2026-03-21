<template>
  <article class="store-card">
    <div class="store-card__head">
      <div>
        <p class="eyebrow">{{ store.region }} / {{ store.area }}</p>
        <h3>{{ store.name }}</h3>
      </div>
      <div class="store-card__badges">
        <StatusBadge :label="store.store_status || 'UNKNOWN'" :tone="statusTone(store.store_status)" />
        <StatusBadge
          :label="store.local_ticketing_status === 'ON' ? '现场派筹中' : '现场派筹停'"
          :tone="statusTone(store.local_ticketing_status)"
        />
      </div>
    </div>

    <div class="metric-grid">
      <div>
        <p>当前 wait</p>
        <strong>{{ formatOptionalNumber(store.wait) }}</strong>
      </div>
      <div>
        <p>waitingGroup</p>
        <strong>{{ formatOptionalNumber(store.waiting_group) }}</strong>
      </div>
      <div>
        <p>storeQueue 数量</p>
        <strong>{{ formatOptionalNumber(store.queue.queue_count) }}</strong>
      </div>
      <div>
        <p>ETA</p>
        <strong>{{ formatEta(store.eta) }}</strong>
      </div>
    </div>

    <div class="queue-strip">
      <span>显示号码</span>
      <code v-if="store.queue.store_queue.length">
        {{ store.queue.store_queue.join(", ") }}
      </code>
      <span v-else>暂无可用 queue 数据</span>
    </div>

    <p class="store-card__reason">{{ store.eta.reason }}</p>

    <div class="store-card__footer">
      <small>更新时间 {{ formatDateTime(store.data_updated_at) }}</small>
      <RouterLink class="button-link" :to="`/stores/${store.id}`">详情</RouterLink>
    </div>
  </article>
</template>

<script setup lang="ts">
import { RouterLink } from "vue-router";

import type { StoreCurrent } from "../types/api";
import { formatDateTime, formatEta, formatOptionalNumber, statusTone } from "../utils/format";
import StatusBadge from "./StatusBadge.vue";

defineProps<{
  store: StoreCurrent;
}>();
</script>

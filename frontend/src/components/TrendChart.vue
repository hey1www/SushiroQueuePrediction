<template>
  <section class="chart-card">
    <div class="chart-header">
      <div>
        <p class="eyebrow">{{ label }}</p>
        <h3>{{ title }}</h3>
      </div>
      <strong>{{ latestValue }}</strong>
    </div>
    <div v-if="hasValues" class="chart-shell">
      <svg viewBox="0 0 100 40" preserveAspectRatio="none" class="chart-svg">
        <path :d="areaPath" class="chart-area" :style="{ '--chart-color': color }" />
        <path :d="linePath" class="chart-line" :style="{ '--chart-color': color }" />
      </svg>
      <div class="chart-axis">
        <span>{{ startLabel }}</span>
        <span>{{ endLabel }}</span>
      </div>
    </div>
    <div v-else class="empty-inline">暂无足够历史数据</div>
  </section>
</template>

<script setup lang="ts">
import { computed } from "vue";

const props = defineProps<{
  title: string;
  label: string;
  color: string;
  values: Array<number | null>;
  startLabel: string;
  endLabel: string;
  suffix?: string;
}>();

const validValues = computed(() => props.values.filter((value): value is number => value !== null));
const hasValues = computed(() => validValues.value.length >= 2);
const latestValue = computed(() => {
  const latest = [...props.values].reverse().find((value) => value !== null);
  if (latest === undefined) return "--";
  return `${latest}${props.suffix || ""}`;
});

const points = computed(() => {
  if (!hasValues.value) return [];
  const min = Math.min(...validValues.value);
  const max = Math.max(...validValues.value);
  const range = max - min || 1;

  return props.values.map((value, index) => {
    const x = props.values.length === 1 ? 0 : (index / (props.values.length - 1)) * 100;
    if (value === null) {
      return { x, y: null };
    }
    const normalized = (value - min) / range;
    const y = 35 - normalized * 28;
    return { x, y };
  });
});

const linePath = computed(() => {
  if (!hasValues.value) return "";
  let path = "";
  points.value.forEach((point) => {
    if (point.y === null) return;
    path += path ? ` L ${point.x} ${point.y}` : `M ${point.x} ${point.y}`;
  });
  return path;
});

const areaPath = computed(() => {
  if (!linePath.value) return "";
  const visiblePoints = points.value.filter((point) => point.y !== null) as Array<{ x: number; y: number }>;
  const first = visiblePoints[0];
  const last = visiblePoints[visiblePoints.length - 1];
  return `${linePath.value} L ${last.x} 38 L ${first.x} 38 Z`;
});
</script>

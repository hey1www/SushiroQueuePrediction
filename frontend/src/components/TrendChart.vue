<template>
  <section class="chart-card">
    <div class="chart-header chart-header--rich">
      <div class="chart-heading">
        <p class="eyebrow">{{ eyebrow }}</p>
        <div class="chart-title-line">
          <h3>{{ title }}</h3>
          <strong v-if="headline" class="chart-headline">{{ headline }}</strong>
        </div>
        <p v-if="description" class="chart-description">{{ description }}</p>
      </div>
      <div v-if="legendItems.length" class="chart-legend">
        <span v-for="item in legendItems" :key="item.name" class="chart-legend__item">
          <i :style="{ '--legend-color': item.color }" />
          {{ item.name }}
        </span>
      </div>
    </div>

    <div v-if="hasValues" class="chart-shell chart-shell--detailed">
      <svg viewBox="0 0 720 320" preserveAspectRatio="none" class="chart-svg chart-svg--detailed">
        <defs>
          <linearGradient
            v-for="series in renderedSeries"
            :id="series.gradientId"
            :key="series.gradientId"
            x1="0"
            y1="0"
            x2="0"
            y2="1"
          >
            <stop offset="0%" :stop-color="series.color" stop-opacity="0.28" />
            <stop offset="100%" :stop-color="series.color" stop-opacity="0.02" />
          </linearGradient>
        </defs>

        <g class="chart-gridlines">
          <g v-for="tick in yTicks" :key="tick.value">
            <line
              :x1="layout.left"
              :x2="layout.right"
              :y1="tick.y"
              :y2="tick.y"
              class="chart-gridline"
            />
            <text :x="layout.left - 14" :y="tick.y + 4" class="chart-gridlabel" text-anchor="end">
              {{ tick.label }}
            </text>
          </g>

          <g v-for="tick in xTicks" :key="tick.index">
            <line
              :x1="tick.x"
              :x2="tick.x"
              :y1="layout.top"
              :y2="layout.bottom"
              class="chart-baseline"
            />
            <text :x="tick.x" :y="layout.bottom + 22" class="chart-gridlabel chart-gridlabel--x" text-anchor="middle">
              {{ tick.label }}
            </text>
          </g>
        </g>

        <g v-for="series in renderedSeries" :key="series.name">
          <path
            v-for="(areaPath, index) in series.areaPaths"
            :key="`${series.name}-area-${index}`"
            :d="areaPath"
            class="chart-area"
            :style="{ fill: `url(#${series.gradientId})` }"
          />
          <path
            :d="series.linePath"
            class="chart-line"
            :style="{
              stroke: series.color,
              strokeDasharray: series.dashed ? '8 8' : '',
            }"
          />
          <circle
            v-for="point in series.highlightPoints"
            :key="`${series.name}-${point.x}-${point.y}`"
            :cx="point.x"
            :cy="point.y"
            r="4.4"
            class="chart-point"
            :style="{ fill: series.color }"
          />
        </g>
      </svg>

      <div class="chart-preview">
        <svg viewBox="0 0 720 72" preserveAspectRatio="none" class="chart-preview__svg">
          <g v-for="series in renderedSeries" :key="`${series.name}-preview`">
            <path
              v-for="(areaPath, index) in series.previewAreaPaths"
              :key="`${series.name}-preview-area-${index}`"
              :d="areaPath"
              class="chart-preview__area"
              :style="{ fill: series.color }"
            />
            <path
              :d="series.previewLinePath"
              class="chart-preview__line"
              :style="{ stroke: series.color }"
            />
          </g>
        </svg>
        <div class="chart-preview__window" />
      </div>
    </div>

    <div v-else class="empty-inline">{{ emptyText }}</div>
  </section>
</template>

<script setup lang="ts">
import { computed } from "vue";

import { formatNumber } from "../utils/format";

interface ChartSeriesInput {
  name: string;
  color: string;
  values: Array<number | null>;
  fill?: boolean;
  dashed?: boolean;
}

interface CoordinatePoint {
  x: number;
  y: number;
  value: number;
  index: number;
}

const props = withDefaults(
  defineProps<{
    title: string;
    labels: string[];
    series: ChartSeriesInput[];
    eyebrow?: string;
    description?: string;
    headline?: string;
    emptyText?: string;
  }>(),
  {
    eyebrow: "趨勢圖",
    description: "",
    headline: "",
    emptyText: "暫無足夠歷史資料",
  },
);

const layout = {
  left: 62,
  right: 688,
  top: 24,
  bottom: 276,
};

const previewLayout = {
  top: 10,
  bottom: 60,
};

const plotWidth = layout.right - layout.left;
const plotHeight = layout.bottom - layout.top;
const previewHeight = previewLayout.bottom - previewLayout.top;

const allValues = computed(() =>
  props.series.flatMap((series) => series.values.filter((value): value is number => value !== null)),
);

const hasValues = computed(
  () => props.series.some((series) => series.values.filter((value): value is number => value !== null).length >= 2),
);

const legendItems = computed(() => props.series.filter((series) => series.values.some((value) => value !== null)));

const yRange = computed(() => {
  if (!allValues.value.length) {
    return { min: 0, max: 1 };
  }

  const maxValue = Math.max(...allValues.value);
  const paddedMax = getNiceMax(maxValue <= 0 ? 1 : maxValue * 1.08);
  return { min: 0, max: paddedMax };
});

const yTicks = computed(() => {
  const tickCount = 4;
  const step = (yRange.value.max - yRange.value.min) / tickCount;
  return Array.from({ length: tickCount + 1 }, (_, index) => {
    const value = yRange.value.min + step * index;
    return {
      value,
      y: layout.bottom - ((value - yRange.value.min) / (yRange.value.max - yRange.value.min || 1)) * plotHeight,
      label: formatAxisValue(value),
    };
  });
});

const xTicks = computed(() => {
  if (!props.labels.length) return [];
  const desiredCount = Math.min(6, props.labels.length);
  const indexes = new Set<number>([0, props.labels.length - 1]);
  for (let index = 1; index < desiredCount - 1; index += 1) {
    indexes.add(Math.round((index / (desiredCount - 1)) * (props.labels.length - 1)));
  }

  return [...indexes]
    .sort((left, right) => left - right)
    .map((index) => ({
      index,
      label: props.labels[index],
      x: toX(index, props.labels.length),
    }));
});

const renderedSeries = computed(() =>
  props.series.map((series, seriesIndex) => {
    const points = series.values.map((value, index) =>
      value === null
        ? null
        : {
            index,
            value,
            x: toX(index, series.values.length),
            y: toY(value),
          },
    );

    const previewPoints = series.values.map((value, index) =>
      value === null
        ? null
        : {
            index,
            value,
            x: toX(index, series.values.length),
            y: toPreviewY(value),
          },
    );

    return {
      ...series,
      gradientId: `chart-gradient-${seriesIndex}`,
      linePath: buildLinePath(points),
      areaPaths: series.fill ? buildAreaPaths(points, layout.bottom) : [],
      previewLinePath: buildLinePath(previewPoints),
      previewAreaPaths: series.fill ? buildAreaPaths(previewPoints, previewLayout.bottom) : [],
      highlightPoints: buildHighlightPoints(points),
    };
  }),
);

function getNiceMax(value: number) {
  const safeValue = Math.max(1, value);
  const magnitude = 10 ** Math.floor(Math.log10(safeValue));
  const normalized = safeValue / magnitude;
  const steps = [1, 1.2, 1.5, 2, 2.5, 3, 4, 5, 6, 8, 10];
  const step = steps.find((candidate) => normalized <= candidate) || 10;
  return step * magnitude;
}

function formatAxisValue(value: number) {
  if (value >= 100) return formatNumber(Math.round(value));
  if (value >= 10) return formatNumber(Number(value.toFixed(1)), 1).replace(/\.0$/, "");
  return formatNumber(Number(value.toFixed(1)), 1).replace(/\.0$/, "");
}

function toX(index: number, total: number) {
  if (total <= 1) return layout.left;
  return layout.left + (index / (total - 1)) * plotWidth;
}

function toY(value: number) {
  return layout.bottom - ((value - yRange.value.min) / (yRange.value.max - yRange.value.min || 1)) * plotHeight;
}

function toPreviewY(value: number) {
  return (
    previewLayout.bottom -
    ((value - yRange.value.min) / (yRange.value.max - yRange.value.min || 1)) * previewHeight
  );
}

function buildLinePath(points: Array<CoordinatePoint | null>) {
  let path = "";
  let segmentStarted = false;

  points.forEach((point) => {
    if (!point) {
      segmentStarted = false;
      return;
    }

    path += segmentStarted ? ` L ${point.x} ${point.y}` : `M ${point.x} ${point.y}`;
    segmentStarted = true;
  });

  return path;
}

function buildAreaPaths(points: Array<CoordinatePoint | null>, baseline: number) {
  const segments = buildSegments(points);
  return segments
    .filter((segment) => segment.length >= 2)
    .map((segment) => {
      const first = segment[0];
      const last = segment[segment.length - 1];
      const line = segment.map((point, index) => `${index === 0 ? "M" : "L"} ${point.x} ${point.y}`).join(" ");
      return `${line} L ${last.x} ${baseline} L ${first.x} ${baseline} Z`;
    });
}

function buildSegments(points: Array<CoordinatePoint | null>) {
  const segments: CoordinatePoint[][] = [];
  let current: CoordinatePoint[] = [];

  points.forEach((point) => {
    if (point) {
      current.push(point);
      return;
    }
    if (current.length) {
      segments.push(current);
      current = [];
    }
  });

  if (current.length) {
    segments.push(current);
  }

  return segments;
}

function buildHighlightPoints(points: Array<CoordinatePoint | null>) {
  const visiblePoints = points.filter((point): point is CoordinatePoint => point !== null);
  if (!visiblePoints.length) return [];

  const lastPoint = visiblePoints[visiblePoints.length - 1];
  const maxPoint = [...visiblePoints].sort((left, right) => right.value - left.value)[0];

  if (lastPoint.index === maxPoint.index) {
    return [lastPoint];
  }

  return [maxPoint, lastPoint];
}
</script>

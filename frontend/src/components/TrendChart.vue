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

    <div v-if="hasValues" class="chart-shell chart-shell--interactive">
      <div ref="chartRef" class="chart-canvas" />
      <p class="chart-interaction-hint">懸停查看數值，拖動下方時間窗可縮放；同頁同時間軸圖表會同步聯動。</p>
    </div>

    <div v-else class="empty-inline">{{ emptyText }}</div>
  </section>
</template>

<script setup lang="ts">
import {
  computed,
  nextTick,
  onBeforeUnmount,
  onMounted,
  ref,
  watch,
} from "vue";
import { LineChart, type LineSeriesOption } from "echarts/charts";
import {
  AxisPointerComponent,
  DataZoomComponent,
  GridComponent,
  TooltipComponent,
  type AxisPointerComponentOption,
  type DataZoomComponentOption,
  type GridComponentOption,
  type TooltipComponentOption,
} from "echarts/components";
import {
  connect,
  init,
  use,
  type ComposeOption,
  type EChartsType,
} from "echarts/core";
import { CanvasRenderer } from "echarts/renderers";

import { formatNumber } from "../utils/format";

use([LineChart, GridComponent, TooltipComponent, DataZoomComponent, AxisPointerComponent, CanvasRenderer]);

type TrendChartOption = ComposeOption<
  GridComponentOption | TooltipComponentOption | DataZoomComponentOption | AxisPointerComponentOption | LineSeriesOption
>;

interface ChartSeriesInput {
  name: string;
  color: string;
  values: Array<number | null>;
  fill?: boolean;
  dashed?: boolean;
}

interface TooltipParam {
  axisValue?: string;
  axisValueLabel?: string;
  color?: string;
  dataIndex: number;
  seriesName: string;
  value: number | null | [string, number | null];
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

const chartRef = ref<HTMLDivElement | null>(null);

let chart: EChartsType | null = null;
let resizeObserver: ResizeObserver | null = null;

const visibleSeries = computed(() =>
  props.series.filter((series) => series.values.some((value) => value !== null)),
);

const legendItems = computed(() => visibleSeries.value);

const hasValues = computed(
  () =>
    props.labels.length >= 2 &&
    visibleSeries.value.some(
      (series) => series.values.filter((value): value is number => value !== null).length >= 2,
    ),
);

const chartGroup = computed(() => `trend-chart-${hashString(props.labels.join("|"))}`);
const showZoomSlider = computed(() => props.labels.length > 10);
const axisLabelInterval = computed(() => getAxisLabelInterval(props.labels.length));

watch(
  hasValues,
  async (value) => {
    if (value) {
      await nextTick();
      initChart();
      renderChart();
      return;
    }

    destroyChart();
  },
  { immediate: true },
);

watch(
  () => [props.labels, props.series, props.title],
  () => {
    if (!hasValues.value) return;
    renderChart();
  },
  { deep: true },
);

watch(chartGroup, () => {
  if (!chart) return;
  bindChartGroup();
});

onMounted(async () => {
  if (!hasValues.value) return;
  await nextTick();
  initChart();
  renderChart();
});

onBeforeUnmount(() => {
  destroyChart();
});

function initChart() {
  if (!chartRef.value) return;

  if (!chart) {
    chart = init(chartRef.value, undefined, { renderer: "canvas" });
  }

  bindChartGroup();
  attachResizeObserver();
}

function destroyChart() {
  resizeObserver?.disconnect();
  resizeObserver = null;

  if (chart) {
    chart.dispose();
    chart = null;
  }
}

function attachResizeObserver() {
  if (!chartRef.value || resizeObserver) return;

  resizeObserver = new ResizeObserver(() => {
    chart?.resize();
  });
  resizeObserver.observe(chartRef.value);
}

function bindChartGroup() {
  if (!chart) return;
  chart.group = chartGroup.value;
  connect(chartGroup.value);
}

function renderChart() {
  if (!chart) return;

  chart.setOption(buildOption(), { notMerge: true, lazyUpdate: true });
  chart.resize();
}

function buildOption(): TrendChartOption {
  const bottomPadding = showZoomSlider.value ? 84 : 34;

  return {
    animationDuration: 280,
    animationDurationUpdate: 220,
    grid: {
      left: 18,
      right: 18,
      top: 20,
      bottom: bottomPadding,
      containLabel: true,
    },
    tooltip: {
      trigger: "axis",
      axisPointer: {
        type: "cross",
        snap: true,
        lineStyle: {
          color: "rgba(23, 32, 42, 0.26)",
          width: 1,
        },
        crossStyle: {
          color: "rgba(23, 32, 42, 0.16)",
          width: 1,
        },
        label: {
          backgroundColor: "#17202a",
          color: "#fffdf8",
          borderRadius: 8,
          padding: [6, 8],
        },
      },
      backgroundColor: "transparent",
      borderWidth: 0,
      padding: 0,
      extraCssText: "box-shadow:none;",
      formatter: (rawParams) => formatTooltip(rawParams),
    },
    xAxis: {
      type: "category",
      boundaryGap: false,
      data: props.labels,
      axisLine: {
        lineStyle: {
          color: "rgba(23, 32, 42, 0.08)",
        },
      },
      axisTick: {
        show: false,
      },
      axisLabel: {
        color: "#5e6872",
        fontSize: 11,
        hideOverlap: true,
        interval: axisLabelInterval.value,
        margin: 14,
      },
      axisPointer: {
        label: {
          formatter: (params) => String(params.value),
        },
      },
    },
    yAxis: {
      type: "value",
      scale: true,
      min: (value) => {
        const minValue = Number.isFinite(value.min) ? value.min : 0;
        return Math.min(0, minValue);
      },
      axisLine: {
        show: false,
      },
      axisTick: {
        show: false,
      },
      axisLabel: {
        color: "#5e6872",
        fontSize: 11,
        margin: 12,
        formatter: (value: number) => formatMetric(value),
      },
      splitLine: {
        lineStyle: {
          color: "rgba(23, 32, 42, 0.08)",
          type: "dashed",
        },
      },
    },
    dataZoom: [
      {
        type: "inside",
        filterMode: "none",
        zoomOnMouseWheel: "ctrl",
        moveOnMouseWheel: false,
        moveOnMouseMove: true,
      },
      {
        type: "slider",
        show: showZoomSlider.value,
        bottom: 12,
        height: 38,
        brushSelect: false,
        filterMode: "none",
        start: 0,
        end: 100,
        borderColor: "transparent",
        backgroundColor: "rgba(63, 124, 255, 0.08)",
        fillerColor: "rgba(63, 124, 255, 0.16)",
        dataBackground: {
          lineStyle: {
            color: "rgba(95, 128, 214, 0.55)",
            width: 1.5,
          },
          areaStyle: {
            color: "rgba(95, 128, 214, 0.12)",
          },
        },
        selectedDataBackground: {
          lineStyle: {
            color: "rgba(63, 124, 255, 0.9)",
            width: 1.6,
          },
          areaStyle: {
            color: "rgba(63, 124, 255, 0.18)",
          },
        },
        handleIcon:
          "path://M8.2,0.5h7.6c4.2,0,7.7,3.4,7.7,7.7v31.6c0,4.2-3.4,7.7-7.7,7.7H8.2c-4.2,0-7.7-3.4-7.7-7.7V8.2C0.5,3.9,3.9,0.5,8.2,0.5z M10.9,13.2v21.6 M15.1,13.2v21.6",
        handleSize: "92%",
        handleStyle: {
          color: "#fffdf8",
          borderColor: "rgba(63, 124, 255, 0.28)",
          borderWidth: 1,
          shadowBlur: 12,
          shadowColor: "rgba(67, 53, 24, 0.08)",
        },
        moveHandleSize: 0,
        labelFormatter: "",
      },
    ],
    series: visibleSeries.value.map((series) => buildSeriesOption(series)),
  };
}

function buildSeriesOption(series: ChartSeriesInput): LineSeriesOption {
  const latestIndex = findLatestIndex(series.values);
  const latestValue = latestIndex === -1 ? null : series.values[latestIndex];

  return {
    name: series.name,
    type: "line",
    smooth: true,
    connectNulls: false,
    showSymbol: false,
    symbol: "circle",
    symbolSize: 7,
    data: series.values,
    lineStyle: {
      color: series.color,
      width: 3,
      cap: "round",
      join: "round",
      type: series.dashed ? "dashed" : "solid",
    },
    itemStyle: {
      color: series.color,
      borderColor: "#fffdf8",
      borderWidth: 2,
    },
    emphasis: {
      focus: "series",
      scale: true,
      lineStyle: {
        width: 3.6,
      },
      itemStyle: {
        shadowBlur: 12,
        shadowColor: withAlpha(series.color, 0.18),
      },
    },
    areaStyle: series.fill
      ? {
          color: {
            type: "linear",
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: withAlpha(series.color, 0.28) },
              { offset: 1, color: withAlpha(series.color, 0.03) },
            ],
          },
        }
      : undefined,
    markPoint:
      latestIndex === -1 || latestValue === null
        ? undefined
        : {
            symbol: "circle",
            symbolSize: 12,
            silent: true,
            itemStyle: {
              color: series.color,
              borderColor: "#fffdf8",
              borderWidth: 2,
            },
            data: [
              {
                name: series.name,
                coord: [props.labels[latestIndex], latestValue],
                value: latestValue,
              },
            ],
            label: {
              show: false,
            },
          },
  };
}

function formatTooltip(rawParams: unknown) {
  const params = (Array.isArray(rawParams) ? rawParams : [rawParams]) as TooltipParam[];
  const first = params[0];
  if (!first) return "";

  const dataIndex = first.dataIndex;
  const label = first.axisValueLabel || first.axisValue || props.labels[dataIndex] || "--";

  const rows = visibleSeries.value.map((series) => {
    const value = series.values[dataIndex];
    const previousValue = findPreviousValue(series.values, dataIndex);
    const delta = value === null || previousValue === null ? null : value - previousValue;

    return {
      name: series.name,
      color: series.color,
      value,
      delta,
    };
  });

  return `
    <div class="trendchart-tooltip">
      <div class="trendchart-tooltip__header">${escapeHtml(label)}</div>
      <div class="trendchart-tooltip__rows">
        ${rows
          .map((row) => {
            const deltaClass =
              row.delta === null ? "" : row.delta > 0 ? "trendchart-tooltip__delta--up" : row.delta < 0 ? "trendchart-tooltip__delta--down" : "";

            return `
              <div class="trendchart-tooltip__row">
                <span class="trendchart-tooltip__meta">
                  <i class="trendchart-tooltip__swatch" style="--tooltip-swatch:${row.color}"></i>
                  <span>${escapeHtml(row.name)}</span>
                </span>
                <span class="trendchart-tooltip__value">
                  ${row.value === null ? "--" : escapeHtml(formatMetric(row.value))}
                  ${
                    row.delta === null
                      ? ""
                      : `<small class="trendchart-tooltip__delta ${deltaClass}">${escapeHtml(formatDelta(row.delta))}</small>`
                  }
                </span>
              </div>
            `;
          })
          .join("")}
      </div>
    </div>
  `;
}

function findLatestIndex(values: Array<number | null>) {
  for (let index = values.length - 1; index >= 0; index -= 1) {
    if (values[index] !== null) {
      return index;
    }
  }
  return -1;
}

function findPreviousValue(values: Array<number | null>, index: number) {
  for (let cursor = index - 1; cursor >= 0; cursor -= 1) {
    if (values[cursor] !== null) {
      return values[cursor];
    }
  }
  return null;
}

function getAxisLabelInterval(total: number) {
  if (total <= 8) return 0;
  return Math.max(0, Math.ceil(total / 8) - 1);
}

function formatMetric(value: number) {
  if (!Number.isFinite(value)) return "--";

  const abs = Math.abs(value);
  const digits = Number.isInteger(value) ? 0 : abs < 10 ? 2 : abs < 100 ? 1 : 0;
  const rounded = Number(value.toFixed(digits));
  return formatNumber(rounded, digits);
}

function formatDelta(value: number) {
  const sign = value > 0 ? "+" : value < 0 ? "−" : "±";
  return `${sign}${formatMetric(Math.abs(value))}`;
}

function withAlpha(color: string, alpha: number) {
  if (!color.startsWith("#")) return color;

  let normalized = color.slice(1);
  if (normalized.length === 3) {
    normalized = normalized
      .split("")
      .map((char) => char + char)
      .join("");
  }

  const r = Number.parseInt(normalized.slice(0, 2), 16);
  const g = Number.parseInt(normalized.slice(2, 4), 16);
  const b = Number.parseInt(normalized.slice(4, 6), 16);

  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

function hashString(input: string) {
  let hash = 0;
  for (let index = 0; index < input.length; index += 1) {
    hash = (hash << 5) - hash + input.charCodeAt(index);
    hash |= 0;
  }
  return Math.abs(hash).toString(36);
}

function escapeHtml(value: string) {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}
</script>

import type { EtaResponse } from "../types/api";

const hkDateTime = new Intl.DateTimeFormat("zh-HK", {
  timeZone: "Asia/Hong_Kong",
  month: "2-digit",
  day: "2-digit",
  hour: "2-digit",
  minute: "2-digit",
  hour12: false,
});

const hkTime = new Intl.DateTimeFormat("zh-HK", {
  timeZone: "Asia/Hong_Kong",
  hour: "2-digit",
  minute: "2-digit",
  hour12: false,
});

const numberFormatters = new Map<number, Intl.NumberFormat>();

function getNumberFormatter(digits: number) {
  if (!numberFormatters.has(digits)) {
    numberFormatters.set(
      digits,
      new Intl.NumberFormat("zh-HK", {
        minimumFractionDigits: digits,
        maximumFractionDigits: digits,
      }),
    );
  }
  return numberFormatters.get(digits)!;
}

export function formatDateTime(value: string | null | undefined) {
  if (!value) return "暫無資料";
  return hkDateTime.format(new Date(value));
}

export function formatTime(value: string | null | undefined) {
  if (!value) return "--:--";
  return hkTime.format(new Date(value));
}

export function formatNumber(value: number, digits = 0) {
  return getNumberFormatter(digits).format(value);
}

export function formatOptionalNumber(value: number | null | undefined, suffix = "", digits = 0) {
  if (value === null || value === undefined) return "--";
  return `${formatNumber(value, digits)}${suffix}`;
}

export function formatEta(eta: EtaResponse) {
  if (eta.estimated_wait_minutes === null) return "暫停估算";
  return `${eta.estimated_wait_minutes} 分鐘`;
}

export function formatStoreStatus(value: string | null | undefined) {
  if (value === "OPEN") return "營業中";
  if (!value) return "狀態未明";
  if (value.includes("CLOSING")) return "即將休息";
  return "暫停營業";
}

export function formatLocalTicketingStatus(value: string | null | undefined) {
  return value === "ON" ? "現場派籌中" : "現場派籌暫停";
}

export function formatEtaReason(reason: string | null | undefined) {
  if (!reason) return "暫無說明";

  const exactMap: Record<string, string> = {
    "no snapshot available": "暫無最新快照，未能估算。",
    "store is not open": "門店尚未營業，暫不提供預估。",
    "ticketing is currently unavailable": "目前未開放派籌，暫不提供預估。",
    "ticketing available": "目前可派籌。",
    "wait is unavailable": "缺少等候資料，暫不提供預估。",
    "no waiting groups right now": "目前幾乎無需等候。",
    "using recent queue progression": "依近 15 分鐘顯示號碼推進速度估算。",
    "using historical average queue progression": "改用同時段歷史平均推進速度估算。",
    "falling back to minimum service rate": "資料不足，改用保守服務速度估算。",
  };

  return exactMap[reason] || reason;
}

export function formatRecommendationReason(reason: string | null | undefined) {
  if (!reason) return "暫無推薦說明";
  return reason
    .replace(/\bwait (\d+(?:\.\d+)?)\b/gi, "等候 $1 組")
    .replace(/\bETA (\d+(?:\.\d+)?) min\b/gi, "預估 $1 分鐘")
    .replace(/local ticketing on/gi, "可現場派籌")
    .replace(/fallback recommendation/gi, "以保守規則給出推薦")
    .replace(/,\s*/g, " ・ ");
}

export function formatRegionArea(region: string | null | undefined, area: string | null | undefined) {
  return [region, area].filter(Boolean).join("・") || "未分區";
}

export function statusTone(value: string | null | undefined) {
  if (value === "OPEN" || value === "ON") return "good";
  if (!value || value === "OFF") return "muted";
  if (value.includes("CLOSING")) return "warn";
  return "accent";
}

export function confidenceTone(value: EtaResponse["confidence"]) {
  if (value === "high") return "good";
  if (value === "medium") return "accent";
  return "warn";
}

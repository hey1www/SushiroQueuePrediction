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
    "queue metrics are unavailable": "缺少候位組數或等待時間資料，暫不提供 ETA。",
    "using upstream waiting time": "直接採用上游回傳的預估等待時間。",
    "blending upstream waiting time with recent queue progression": "結合上游等待時間與近 15 分鐘叫號速度推算 ETA。",
    "using recent queue progression with waiting groups": "依候位組數與近 15 分鐘叫號速度推算 ETA。",
    "blending upstream waiting time with historical queue progression": "結合上游等待時間與同時段歷史叫號速度推算 ETA。",
    "using historical average queue progression with waiting groups": "依候位組數與同時段歷史叫號速度推算 ETA。",
    "blending historical waiting profile, recent queue progression, and upstream waiting time":
      "結合同類歷史等待輪廓、近 15 分鐘叫號速度與上游等待時間推算 ETA。",
    "blending historical waiting profile with recent queue progression":
      "結合同類歷史等待輪廓與近 15 分鐘叫號速度推算 ETA。",
    "blending historical waiting profile with upstream waiting time":
      "結合同類歷史等待輪廓與上游等待時間推算 ETA。",
    "using historical waiting profile": "依同日型同時段歷史等待輪廓推算 ETA。",
    "blending historical queue progression profile with upstream waiting time":
      "結合同日型歷史叫號速度與上游等待時間推算 ETA。",
    "using historical queue progression profile": "依同日型歷史叫號速度推算 ETA。",
    "blending recent queue progression with upstream waiting time":
      "結合近 15 分鐘叫號速度與上游等待時間推算 ETA。",
    "falling back to minimum service rate with waiting groups": "資料不足，改用候位組數與保守服務速度推算 ETA。",
    "wait is unavailable": "缺少預估等待時間資料，暫不提供 ETA。",
    "no waiting groups right now": "目前顯示幾乎無需等待。",
    "using recent queue progression": "依近 15 分鐘顯示號碼推進速度推算 ETA。",
    "using historical average queue progression": "改用同時段歷史平均推進速度推算 ETA。",
    "falling back to minimum service rate": "資料不足，改用保守服務速度推算 ETA。",
  };

  return exactMap[reason] || reason;
}

export function formatRecommendationReason(reason: string | null | undefined) {
  if (!reason) return "暫無推薦說明";
  return reason
    .replace(/\bwait (\d+(?:\.\d+)?)\b/gi, "等待時間 $1 分鐘")
    .replace(/\bETA (\d+(?:\.\d+)?) min\b/gi, "ETA $1 分鐘")
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

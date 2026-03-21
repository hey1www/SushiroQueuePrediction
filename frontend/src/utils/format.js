const hkDateTime = new Intl.DateTimeFormat("zh-HK", {
    timeZone: "Asia/Hong_Kong",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
});
export function formatDateTime(value) {
    if (!value)
        return "暂无数据";
    return hkDateTime.format(new Date(value));
}
export function formatOptionalNumber(value, suffix = "") {
    if (value === null || value === undefined)
        return "--";
    return `${value}${suffix}`;
}
export function formatEta(eta) {
    if (eta.estimated_wait_minutes === null)
        return "暂停估算";
    return `${eta.estimated_wait_minutes} 分钟`;
}
export function statusTone(value) {
    if (value === "OPEN" || value === "ON")
        return "good";
    if (!value || value === "OFF")
        return "muted";
    if (value.includes("CLOSING"))
        return "warn";
    return "accent";
}
export function confidenceTone(value) {
    if (value === "high")
        return "good";
    if (value === "medium")
        return "accent";
    return "warn";
}

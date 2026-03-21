const API_BASE = (import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000/api").replace(/\/$/, "");
function buildUrl(path, query) {
    const url = new URL(`${API_BASE}${path}`);
    Object.entries(query || {}).forEach(([key, value]) => {
        if (value === undefined || value === null || value === "") {
            return;
        }
        url.searchParams.set(key, String(value));
    });
    return url.toString();
}
export async function getJson(path, query) {
    const response = await fetch(buildUrl(path, query), {
        headers: {
            Accept: "application/json",
        },
    });
    if (!response.ok) {
        throw new Error(`API request failed: ${response.status} ${response.statusText}`);
    }
    return (await response.json());
}

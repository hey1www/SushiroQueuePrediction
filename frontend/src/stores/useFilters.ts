import { reactive } from "vue";

export type SortMode = "wait" | "eta" | "name";

const filters = reactive({
  region: "",
  openOnly: false,
  localTicketOnly: false,
  sort: "eta" as SortMode,
});

export function useDashboardFilters() {
  return filters;
}

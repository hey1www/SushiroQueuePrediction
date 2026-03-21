import { reactive } from "vue";
const filters = reactive({
    region: "",
    openOnly: false,
    localTicketOnly: false,
    sort: "eta",
});
export function useDashboardFilters() {
    return filters;
}

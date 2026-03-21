import { createRouter, createWebHashHistory } from "vue-router";
import AnalyticsPage from "./pages/AnalyticsPage.vue";
import DashboardPage from "./pages/DashboardPage.vue";
import StoreDetailPage from "./pages/StoreDetailPage.vue";
const router = createRouter({
    history: createWebHashHistory(import.meta.env.BASE_URL),
    routes: [
        {
            path: "/",
            name: "dashboard",
            component: DashboardPage,
        },
        {
            path: "/stores/:storeId",
            name: "store-detail",
            component: StoreDetailPage,
        },
        {
            path: "/analytics",
            name: "analytics",
            component: AnalyticsPage,
        },
    ],
});
export default router;

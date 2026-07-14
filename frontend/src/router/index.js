import { createRouter, createWebHistory } from "vue-router";
import { useAuthStore } from "@/stores/auth";

import Login from "@/views/Login.vue";
import MainLayout from "@/layouts/MainLayout.vue";
import Home from "@/views/Home.vue";
import DataCollection from "@/views/DataCollection.vue";
import SentimentAnalysis from "@/views/SentimentAnalysis.vue";
import VisualizationCenter from "@/views/VisualizationCenter.vue";
import History from "@/views/History.vue";
import Settings from "@/views/Settings.vue";

const routes = [
  { path: "/login", component: Login },
  {
    path: "/",
    component: MainLayout,
    children: [
      { path: "", component: Home },
      { path: "collection", component: DataCollection },
      { path: "analysis", component: SentimentAnalysis },
      { path: "visualization/:eventId", component: VisualizationCenter },
      { path: "history", component: History },
      { path: "settings", component: Settings }
    ]
  }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

router.beforeEach((to, _from, next) => {
  const auth = useAuthStore();
  const token = auth.token || localStorage.getItem("token");

  if (to.path !== "/login" && !token) return next("/login");
  if ((to.path === "/" || to.path === "") && !token) return next("/login");
  if (to.path === "/login" && token) return next("/");
  next();
});

export default router;
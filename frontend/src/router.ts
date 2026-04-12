import { createRouter, createWebHistory } from "vue-router";

import { showDevPanels } from "./config/runtime";
import AdminWorkspaceView from "./views/AdminWorkspaceView.vue";
import ShopWorkbenchView from "./views/ShopWorkbenchView.vue";

type AdminSection = "system" | "knowledge" | "catalog";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: "/",
      name: "shop",
      component: ShopWorkbenchView,
      meta: { appView: "shop" as const },
    },
    {
      path: "/admin",
      redirect: "/admin/system",
    },
    {
      path: "/admin/system",
      name: "admin-system",
      component: AdminWorkspaceView,
      meta: {
        appView: "admin-system" as const,
        adminSection: "system" as AdminSection,
      },
    },
    {
      path: "/admin/knowledge",
      name: "admin-knowledge",
      component: AdminWorkspaceView,
      meta: {
        appView: "admin-knowledge" as const,
        adminSection: "knowledge" as AdminSection,
      },
    },
    {
      path: "/admin/catalog",
      name: "admin-catalog",
      component: AdminWorkspaceView,
      meta: {
        appView: "admin-catalog" as const,
        adminSection: "catalog" as AdminSection,
      },
    },
    {
      path: "/:pathMatch(.*)*",
      redirect: "/",
    },
  ],
  scrollBehavior() {
    return { top: 0 };
  },
});

router.beforeEach((to) => {
  if (!showDevPanels && to.path.startsWith("/admin")) {
    return { path: "/" };
  }

  return true;
});

export default router;

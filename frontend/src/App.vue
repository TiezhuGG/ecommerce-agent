<script setup lang="ts">
import { computed } from "vue";
import { useRoute, useRouter } from "vue-router";

import { showDevPanels } from "./config/runtime";
import { useAdminWorkspace } from "./composables/useAdminWorkspace";
import { useShopWorkbench } from "./composables/useShopWorkbench";

type AdminSection = "system" | "knowledge" | "catalog";
type AppView = "shop" | "admin-system" | "admin-knowledge" | "admin-catalog";

const route = useRoute();
const router = useRouter();

const activeView = computed<AppView>(() => {
  const name = String(route.name ?? "shop");

  if (name === "admin-knowledge") {
    return "admin-knowledge";
  }

  if (name === "admin-catalog") {
    return "admin-catalog";
  }

  if (name === "admin-system") {
    return "admin-system";
  }

  return "shop";
});

const adminSection = computed<AdminSection>(() => {
  if (activeView.value === "admin-knowledge") {
    return "knowledge";
  }

  if (activeView.value === "admin-catalog") {
    return "catalog";
  }

  return "system";
});

const isAdminView = computed(() => activeView.value !== "shop");

function navigateTo(view: AppView, replace = false) {
  const target = { name: view };
  if (replace) {
    void router.replace(target);
    return;
  }

  void router.push(target);
}

function navigateAdminSection(section: AdminSection) {
  if (section === "knowledge") {
    navigateTo("admin-knowledge");
    return;
  }

  if (section === "catalog") {
    navigateTo("admin-catalog");
    return;
  }

  navigateTo("admin-system");
}

const adminWorkspace = useAdminWorkspace();
const shopWorkbench = useShopWorkbench({
  onResumeToShop: () => navigateTo("shop"),
});

const routeViewProps = computed(() => {
  if (isAdminView.value) {
    return {
      ...adminWorkspace.viewModel.value,
      ...shopWorkbench.viewModel.value.historyPanel,
      selectedAgentResult: shopWorkbench.viewModel.value.agent.result,
      refreshHistory: shopWorkbench.viewModel.value.refreshHistory,
      inspectAgentThread: shopWorkbench.viewModel.value.inspectAgentThread,
      inspectAgentRun: shopWorkbench.viewModel.value.inspectAgentRun,
      resumeAgentThread: shopWorkbench.viewModel.value.resumeAgentThread,
      activeSection: adminSection.value,
      navigateSection: navigateAdminSection,
    };
  }

  return {
    ...shopWorkbench.viewModel.value,
    showDevPanels,
    goToAdminSystem: () => navigateTo("admin-system"),
    goToAdminKnowledge: () => navigateTo("admin-knowledge"),
    goToAdminCatalog: () => navigateTo("admin-catalog"),
  };
});
</script>

<template>
  <main
    class="mx-auto flex min-h-screen w-full max-w-[1440px] flex-col gap-6 px-4 py-6 sm:px-6 lg:px-8 lg:py-10"
  >
    <section class="panel px-5 py-4 sm:px-6">
      <div class="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <p class="text-sm font-semibold uppercase tracking-[0.24em] text-amber-700">
            Ecommerce Agent
          </p>
          <p class="mt-1 text-sm leading-6 text-slate-600">
            这里是应用根壳层，只负责页面切换、导航入口和状态分发。普通用户走前台导购链路，
            开发与运营相关能力则统一收敛到后台工作区。
          </p>
        </div>

        <div class="flex flex-wrap gap-2">
          <button
            type="button"
            class="rounded-full px-4 py-2 text-sm transition"
            :class="
              !isAdminView
                ? 'bg-ink text-white'
                : 'border border-slate-200 text-slate-700 hover:border-slate-300 hover:bg-slate-50'
            "
            @click="navigateTo('shop')"
          >
            用户导购页
          </button>

          <button
            v-if="showDevPanels"
            type="button"
            class="rounded-full px-4 py-2 text-sm transition"
            :class="
              isAdminView
                ? 'bg-amber-500 text-white'
                : 'border border-slate-200 text-slate-700 hover:border-slate-300 hover:bg-slate-50'
            "
            @click="navigateTo('admin-system')"
          >
            后台工作区
          </button>
        </div>
      </div>

      <p v-if="!showDevPanels" class="mt-4 text-xs leading-6 text-slate-500">
        当前按普通用户视角运行，后台工作区默认隐藏。生产环境需要显式设置
        <code>VITE_SHOW_DEV_PANELS=true</code> 才允许进入 <code>/admin/*</code>。
      </p>
    </section>

    <RouterView v-slot="{ Component }">
      <component :is="Component" v-if="Component" v-bind="routeViewProps" />
    </RouterView>
  </main>
</template>

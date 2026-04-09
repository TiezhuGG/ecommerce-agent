<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";

import {
  chatWithAgent,
  fetchAgentPrecheck,
  fetchAgentRunDetail,
  fetchAgentThreadDetail,
  fetchRecentAgentRuns,
  fetchRecentAgentThreads,
} from "./api/agent";
import { requestJson } from "./api/client";
import { compareProducts } from "./api/compare";
import type { CompareResponse } from "./api/contracts/compare";
import { askFaq } from "./api/faq";
import { fetchProducts } from "./api/products";
import { suggestedFaqQuestions } from "./data/mockFaqEntries";
import type {
  AgentConversationTurn,
  AgentPrecheck,
  AgentResult,
  AgentRunHistory,
  AgentThreadDetail,
  AgentThreadHistory,
} from "./types/agent";
import type { Product, SearchFilters } from "./types/catalog";
import type { FaqAskResult } from "./types/faq";
import type { HealthResponse } from "./types/system";

type AdminSection = "system" | "knowledge" | "catalog";
type AppView = "shop" | "admin-system" | "admin-knowledge" | "admin-catalog";

const route = useRoute();
const router = useRouter();

const health = ref<HealthResponse | null>(null);
const healthLoading = ref(false);
const healthErrorMessage = ref("");

const agentPrecheck = ref<AgentPrecheck | null>(null);
const agentPrecheckLoading = ref(false);
const agentPrecheckErrorMessage = ref("");

const filters = ref<SearchFilters>({
  keyword: "",
  category: "",
  brand: "",
  maxPrice: null,
});

const products = ref<Product[]>([]);
const productsLoading = ref(false);
const productsErrorMessage = ref("");
const appliedFilters = ref<string[]>([]);
const availableCategories = ref<string[]>([]);
const availableBrands = ref<string[]>([]);
const recommendedProductIds = ref<string[]>([]);

const selectedProductIds = ref<string[]>([]);

const compareResult = ref<CompareResponse | null>(null);
const compareLoading = ref(false);
const compareErrorMessage = ref("");

const agentResult = ref<AgentResult | null>(null);
const agentLoading = ref(false);
const agentErrorMessage = ref("");
const currentAgentThreadId = ref<string | null>(null);
const agentConversationContext = ref<AgentConversationTurn[]>([]);
const agentRunHistory = ref<AgentRunHistory | null>(null);
const agentThreadHistory = ref<AgentThreadHistory | null>(null);
const agentHistoryLoading = ref(false);
const agentHistoryErrorMessage = ref("");
const selectedAgentRunId = ref<string | null>(null);
const selectedAgentThreadId = ref<string | null>(null);
const agentRunDetailLoading = ref(false);
const agentRunDetailErrorMessage = ref("");
const agentThreadDetail = ref<AgentThreadDetail | null>(null);
const agentThreadDetailLoading = ref(false);
const agentThreadDetailErrorMessage = ref("");

const faqResult = ref<FaqAskResult | null>(null);
const faqLoading = ref(false);
const faqErrorMessage = ref("");

const devPanelsOverride = String(import.meta.env.VITE_SHOW_DEV_PANELS ?? "")
  .trim()
  .toLowerCase();

const showDevPanels = computed(() => {
  if (devPanelsOverride === "true") {
    return true;
  }

  if (devPanelsOverride === "false") {
    return false;
  }

  return import.meta.env.DEV;
});

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

const devEntryLabel = computed(() =>
  import.meta.env.DEV
    ? "开发环境默认开放后台入口，后台路径现在由 vue-router 正式管理。"
    : "生产环境默认隐藏后台入口，只有显式开启 VITE_SHOW_DEV_PANELS 后才允许进入 /admin/*。",
);

const selectedProducts = computed(() => {
  const productMap = new Map<string, Product>();

  for (const product of products.value) {
    productMap.set(product.id, product);
  }

  for (const product of compareResult.value?.compared_products ?? []) {
    productMap.set(product.id, product);
  }

  return selectedProductIds.value
    .map((productId) => productMap.get(productId))
    .filter((product): product is Product => Boolean(product));
});

const showComparePanel = computed(
  () =>
    selectedProducts.value.length > 0 ||
    Boolean(compareResult.value) ||
    compareLoading.value ||
    Boolean(compareErrorMessage.value),
);

const showHistoryPanel = computed(
  () =>
    agentHistoryLoading.value ||
    Boolean(agentHistoryErrorMessage.value) ||
    Boolean(currentAgentThreadId.value) ||
    (agentRunHistory.value?.items.length ?? 0) > 0 ||
    (agentThreadHistory.value?.items.length ?? 0) > 0,
);

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

function syncUiFromAgentResult(result: AgentResult, restoreFilters: boolean) {
  recommendedProductIds.value = result.recommendedProductIds;

  if (result.compareResult) {
    compareResult.value = result.compareResult;
    selectedProductIds.value = result.compareResult.compared_products.map((product) => product.id);
  } else {
    selectedProductIds.value =
      result.threadState?.selectedProductIds.length
        ? [...result.threadState.selectedProductIds]
        : [...result.selectedProductIds];
  }

  if (restoreFilters && result.threadState?.searchFilters) {
    filters.value = { ...result.threadState.searchFilters };
  }
}

async function loadHealth() {
  healthLoading.value = true;
  healthErrorMessage.value = "";

  try {
    health.value = await requestJson<HealthResponse>("/health");
  } catch (error) {
    healthErrorMessage.value =
      error instanceof Error ? error.message : "未知错误，无法访问后端。";
  } finally {
    healthLoading.value = false;
  }
}

async function loadAgentPrecheck() {
  agentPrecheckLoading.value = true;
  agentPrecheckErrorMessage.value = "";

  try {
    agentPrecheck.value = await fetchAgentPrecheck();
  } catch (error) {
    agentPrecheck.value = null;
    agentPrecheckErrorMessage.value =
      error instanceof Error ? error.message : "未知错误，无法完成 Agent 预检。";
  } finally {
    agentPrecheckLoading.value = false;
  }
}

async function loadAgentHistory() {
  agentHistoryLoading.value = true;
  agentHistoryErrorMessage.value = "";

  try {
    const [runHistory, threadHistory] = await Promise.all([
      fetchRecentAgentRuns(),
      fetchRecentAgentThreads(),
    ]);
    agentRunHistory.value = runHistory;
    agentThreadHistory.value = threadHistory;

    if (
      selectedAgentThreadId.value &&
      !threadHistory.items.some((item) => item.threadId === selectedAgentThreadId.value)
    ) {
      selectedAgentThreadId.value = null;
      agentThreadDetail.value = null;
    }

    if (
      selectedAgentRunId.value &&
      !runHistory.items.some((item) => item.runId === selectedAgentRunId.value)
    ) {
      selectedAgentRunId.value = null;
    }
  } catch (error) {
    agentRunHistory.value = null;
    agentThreadHistory.value = null;
    agentHistoryErrorMessage.value =
      error instanceof Error ? error.message : "未知错误，无法加载 Agent 历史记录。";
  } finally {
    agentHistoryLoading.value = false;
  }
}

async function loadProducts() {
  productsLoading.value = true;
  productsErrorMessage.value = "";

  try {
    const result = await fetchProducts(filters.value);
    products.value = result.items;
    appliedFilters.value = result.applied_filters;
    availableCategories.value = result.available_categories;
    availableBrands.value = result.available_brands;

    const currentIds = new Set(result.items.map((item) => item.id));
    selectedProductIds.value = selectedProductIds.value.filter((id) => currentIds.has(id));
  } catch (error) {
    products.value = [];
    productsErrorMessage.value =
      error instanceof Error ? error.message : "未知错误，无法加载商品列表。";
  } finally {
    productsLoading.value = false;
  }
}

async function submitFaq(question: string) {
  faqLoading.value = true;
  faqErrorMessage.value = "";

  try {
    faqResult.value = await askFaq(question);
  } catch (error) {
    faqResult.value = null;
    faqErrorMessage.value =
      error instanceof Error ? error.message : "未知错误，无法查询知识库。";
  } finally {
    faqLoading.value = false;
  }
}

async function loadCompare(productIds: string[]) {
  compareLoading.value = true;
  compareErrorMessage.value = "";

  try {
    compareResult.value = await compareProducts(productIds);
  } catch (error) {
    compareResult.value = null;
    compareErrorMessage.value =
      error instanceof Error ? error.message : "未知错误，无法生成商品对比。";
  } finally {
    compareLoading.value = false;
  }
}

function updateFilters(nextFilters: SearchFilters) {
  filters.value = nextFilters;
}

function resetFilters() {
  filters.value = {
    keyword: "",
    category: "",
    brand: "",
    maxPrice: null,
  };
}

function toggleCompare(productId: string) {
  if (selectedProductIds.value.includes(productId)) {
    selectedProductIds.value = selectedProductIds.value.filter((id) => id !== productId);
    return;
  }

  if (selectedProductIds.value.length >= 3) {
    selectedProductIds.value = [...selectedProductIds.value.slice(1), productId];
    return;
  }

  selectedProductIds.value = [...selectedProductIds.value, productId];
}

async function runAgentPrompt(query: string) {
  agentLoading.value = true;
  agentErrorMessage.value = "";
  agentRunDetailErrorMessage.value = "";

  try {
    const result = await chatWithAgent(
      query,
      selectedProductIds.value,
      agentConversationContext.value,
      currentAgentThreadId.value,
    );
    agentResult.value = result;
    currentAgentThreadId.value = result.threadId;
    selectedAgentRunId.value = result.runId;
    selectedAgentThreadId.value = result.threadId;
    syncUiFromAgentResult(result, false);
    agentConversationContext.value = [
      ...agentConversationContext.value,
      {
        userMessage: query,
        agentAnswer: result.finalAnswer,
        route: result.route,
        selectedProductIds: result.selectedProductIds,
        recommendedProductIds: result.recommendedProductIds,
      },
    ].slice(-4);
    void loadAgentHistory();
  } catch (error) {
    agentResult.value = null;
    agentErrorMessage.value =
      error instanceof Error ? error.message : "未知错误，无法完成 Agent 执行。";
  } finally {
    agentLoading.value = false;
  }
}

function clearAgentConversation() {
  currentAgentThreadId.value = null;
  agentConversationContext.value = [];
  selectedAgentThreadId.value = null;
}

function buildConversationContextFromResult(result: AgentResult): AgentConversationTurn[] {
  return [
    ...result.conversationContext,
    {
      userMessage: result.message,
      agentAnswer: result.finalAnswer,
      route: result.route,
      selectedProductIds: result.selectedProductIds,
      recommendedProductIds: result.recommendedProductIds,
    },
  ].slice(-4);
}

async function inspectAgentRun(runId: string) {
  agentRunDetailLoading.value = true;
  agentRunDetailErrorMessage.value = "";
  selectedAgentRunId.value = runId;

  try {
    const result = await fetchAgentRunDetail(runId);
    agentResult.value = result;
    selectedAgentThreadId.value = result.threadId;
    syncUiFromAgentResult(result, false);
  } catch (error) {
    agentRunDetailErrorMessage.value =
      error instanceof Error ? error.message : "未知错误，无法加载 Agent 运行详情。";
  } finally {
    agentRunDetailLoading.value = false;
  }
}

async function inspectAgentThread(threadId: string) {
  if (selectedAgentThreadId.value === threadId && agentThreadDetail.value) {
    selectedAgentThreadId.value = null;
    agentThreadDetail.value = null;
    agentThreadDetailErrorMessage.value = "";
    return;
  }

  agentThreadDetailLoading.value = true;
  agentThreadDetailErrorMessage.value = "";
  selectedAgentThreadId.value = threadId;

  try {
    agentThreadDetail.value = await fetchAgentThreadDetail(threadId);
  } catch (error) {
    agentThreadDetail.value = null;
    agentThreadDetailErrorMessage.value =
      error instanceof Error ? error.message : "未知错误，无法加载线程时间线。";
  } finally {
    agentThreadDetailLoading.value = false;
  }
}

async function resumeAgentThread(runId: string) {
  agentRunDetailLoading.value = true;
  agentRunDetailErrorMessage.value = "";
  selectedAgentRunId.value = runId;

  try {
    const result = await fetchAgentRunDetail(runId);
    agentResult.value = result;
    currentAgentThreadId.value = result.threadId;
    selectedAgentThreadId.value = result.threadId;
    agentConversationContext.value = buildConversationContextFromResult(result);
    syncUiFromAgentResult(result, true);
    navigateTo("shop");
  } catch (error) {
    agentRunDetailErrorMessage.value =
      error instanceof Error ? error.message : "未知错误，无法恢复历史会话。";
  } finally {
    agentRunDetailLoading.value = false;
  }
}

function applyAgentFilters() {
  if (!agentResult.value?.parsedIntent) {
    return;
  }

  filters.value = { ...agentResult.value.parsedIntent.searchFilters };
}

function applyAgentFaqResult() {
  if (!agentResult.value?.faqResult) {
    return;
  }

  faqResult.value = agentResult.value.faqResult;
}

function applyAgentCompareResult() {
  if (!agentResult.value?.compareResult) {
    return;
  }

  compareResult.value = agentResult.value.compareResult;
  selectedProductIds.value = agentResult.value.compareResult.compared_products.map(
    (product) => product.id,
  );
}

const routeViewProps = computed(() => {
  if (isAdminView.value) {
    return {
      health: health.value,
      healthLoading: healthLoading.value,
      healthErrorMessage: healthErrorMessage.value,
      refreshHealth: loadHealth,
      agentPrecheck: agentPrecheck.value,
      agentPrecheckLoading: agentPrecheckLoading.value,
      agentPrecheckErrorMessage: agentPrecheckErrorMessage.value,
      refreshPrecheck: loadAgentPrecheck,
      entryLabel: devEntryLabel.value,
      activeSection: adminSection.value,
      navigateSection: navigateAdminSection,
    };
  }

  return {
    catalog: {
      filters: filters.value,
      categories: availableCategories.value,
      brands: availableBrands.value,
      products: products.value,
      productsLoading: productsLoading.value,
      productsErrorMessage: productsErrorMessage.value,
      appliedFilters: appliedFilters.value,
      selectedProductIds: selectedProductIds.value,
      recommendedProductIds: recommendedProductIds.value,
      selectedProducts: selectedProducts.value,
      compareResult: compareResult.value,
      compareLoading: compareLoading.value,
      compareErrorMessage: compareErrorMessage.value,
      showComparePanel: showComparePanel.value,
    },
    agent: {
      result: agentResult.value,
      loading: agentLoading.value,
      errorMessage: agentErrorMessage.value,
      currentThreadId: currentAgentThreadId.value,
      conversationContext: agentConversationContext.value,
    },
    faq: {
      suggestedQuestions: suggestedFaqQuestions,
      result: faqResult.value,
      loading: faqLoading.value,
      errorMessage: faqErrorMessage.value,
    },
    historyPanel: {
      visible: showHistoryPanel.value,
      history: agentRunHistory.value,
      threadHistory: agentThreadHistory.value,
      threadDetail: agentThreadDetail.value,
      loading: agentHistoryLoading.value,
      errorMessage: agentHistoryErrorMessage.value,
      selectedRunId: selectedAgentRunId.value,
      selectedThreadId: selectedAgentThreadId.value,
      currentThreadId: currentAgentThreadId.value,
      threadDetailLoading: agentThreadDetailLoading.value,
      detailLoading: agentRunDetailLoading.value,
      threadDetailErrorMessage: agentThreadDetailErrorMessage.value,
      detailErrorMessage: agentRunDetailErrorMessage.value,
    },
    updateFilters,
    resetFilters,
    submitAgentPrompt: runAgentPrompt,
    applyAgentFilters,
    applyAgentFaqResult,
    applyAgentCompareResult,
    clearAgentConversation,
    toggleCompare,
    submitFaq,
    refreshHistory: loadAgentHistory,
    inspectAgentThread,
    inspectAgentRun,
    resumeAgentThread,
    showDevPanels: showDevPanels.value,
    goToAdminSystem: () => navigateTo("admin-system"),
    goToAdminKnowledge: () => navigateTo("admin-knowledge"),
    goToAdminCatalog: () => navigateTo("admin-catalog"),
  };
});

let searchTimer: ReturnType<typeof setTimeout> | null = null;

watch(
  filters,
  () => {
    if (searchTimer) {
      clearTimeout(searchTimer);
    }

    searchTimer = setTimeout(() => {
      void loadProducts();
    }, 250);
  },
  { deep: true },
);

watch(
  selectedProductIds,
  (ids) => {
    if (ids.length < 2) {
      compareResult.value = null;
      compareErrorMessage.value = "";
      return;
    }

    void loadCompare(ids);
  },
  { deep: true },
);

onMounted(() => {
  void loadHealth();
  void loadAgentPrecheck();
  void loadAgentHistory();
  void loadProducts();
  void submitFaq(suggestedFaqQuestions[0] ?? "支持七天无理由退换货吗？");
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
            用户入口固定为 `/`，后台入口固定为 `/admin/*`。当前由根壳层统一持有状态，真实页面结构已经迁移到路由页面组件。
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
        当前按用户视角运行，后台工作区默认隐藏。生产环境需显式设置 `VITE_SHOW_DEV_PANELS=true` 才允许进入 `/admin/*`。
      </p>
    </section>

    <RouterView v-slot="{ Component }">
      <component :is="Component" v-if="Component" v-bind="routeViewProps" />
    </RouterView>
  </main>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";

import {
  chatWithAgent,
  fetchAgentPrecheck,
  fetchAgentRunDetail,
  fetchRecentAgentRuns,
} from "./api/agent";
import { requestJson } from "./api/client";
import { compareProducts } from "./api/compare";
import { askFaq } from "./api/faq";
import type { CompareResponse } from "./api/contracts/compare";
import { fetchProducts } from "./api/products";
import AgentPrecheckCard from "./components/AgentPrecheckCard.vue";
import AgentPromptPanel from "./components/AgentPromptPanel.vue";
import AgentRunHistoryCard from "./components/AgentRunHistoryCard.vue";
import ComparePanel from "./components/ComparePanel.vue";
import FaqPanel from "./components/FaqPanel.vue";
import HealthStatusCard from "./components/HealthStatusCard.vue";
import KnowledgeBaseAdminPanel from "./components/KnowledgeBaseAdminPanel.vue";
import ProductCatalogAdminPanel from "./components/ProductCatalogAdminPanel.vue";
import ProductGrid from "./components/ProductGrid.vue";
import SearchFiltersPanel from "./components/SearchFiltersPanel.vue";
import { suggestedFaqQuestions } from "./data/mockFaqEntries";
import type { AgentPrecheck, AgentResult, AgentRunHistory } from "./types/agent";
import type { Product, SearchFilters } from "./types/catalog";
import type { FaqAskResult } from "./types/faq";
import type { HealthResponse } from "./types/system";

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
const agentRunHistory = ref<AgentRunHistory | null>(null);
const agentRunHistoryLoading = ref(false);
const agentRunHistoryErrorMessage = ref("");
const selectedAgentRunId = ref<string | null>(null);
const agentRunDetailLoading = ref(false);
const agentRunDetailErrorMessage = ref("");

const faqResult = ref<FaqAskResult | null>(null);
const faqLoading = ref(false);
const faqErrorMessage = ref("");

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

async function loadAgentRunHistory() {
  agentRunHistoryLoading.value = true;
  agentRunHistoryErrorMessage.value = "";

  try {
    agentRunHistory.value = await fetchRecentAgentRuns();
  } catch (error) {
    agentRunHistory.value = null;
    agentRunHistoryErrorMessage.value =
      error instanceof Error ? error.message : "未知错误，无法加载 Agent 运行历史。";
  } finally {
    agentRunHistoryLoading.value = false;
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
    const result = await chatWithAgent(query, selectedProductIds.value);
    agentResult.value = result;
    selectedAgentRunId.value = result.runId;
    recommendedProductIds.value = result.recommendedProductIds;
    void loadAgentRunHistory();
  } catch (error) {
    agentResult.value = null;
    agentErrorMessage.value =
      error instanceof Error ? error.message : "未知错误，无法完成 Agent 执行。";
  } finally {
    agentLoading.value = false;
  }
}

async function inspectAgentRun(runId: string) {
  agentRunDetailLoading.value = true;
  agentRunDetailErrorMessage.value = "";
  selectedAgentRunId.value = runId;

  try {
    const result = await fetchAgentRunDetail(runId);
    agentResult.value = result;
    recommendedProductIds.value = result.recommendedProductIds;
  } catch (error) {
    agentRunDetailErrorMessage.value =
      error instanceof Error ? error.message : "未知错误，无法加载 Agent 运行详情。";
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
  selectedProductIds.value = agentResult.value.compareResult.compared_products.map((product) => product.id);
}

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
  void loadAgentRunHistory();
  void loadProducts();
  void submitFaq(suggestedFaqQuestions[0] ?? "支持七天无理由退换货吗？");
});
</script>

<template>
  <main
    class="mx-auto flex min-h-screen w-full max-w-[1440px] flex-col gap-6 px-4 py-6 sm:px-6 lg:px-8 lg:py-10"
  >
    <section class="panel overflow-hidden">
      <div class="grid gap-8 px-6 py-8 lg:grid-cols-[1.2fr_0.8fr] lg:px-8 lg:py-10">
        <div>
          <p class="text-sm font-semibold uppercase tracking-[0.28em] text-amber-700">
            电商导购 Agent / 第九轮迭代
          </p>
          <h1 class="mt-4 text-4xl font-semibold tracking-tight text-ink sm:text-5xl">
            升级 FAQ 为知识库检索，让 Agent 能返回“答案 + 引用片段”
          </h1>
          <p class="mt-5 max-w-3xl text-base leading-8 text-slate-600">
            这一轮的重点不是再加一个孤立接口，而是把原来的 FAQ 工具升级成轻量 RAG。
            后端会先做本地检索，再把命中的知识片段交给模型生成回答；即使模型失败，也还能基于片段走模板回退。
            前端现在不仅能看到答案，还能看到检索模式、命中的知识片段和 Agent 的复用轨迹。
          </p>

          <div class="mt-6 flex flex-wrap gap-3">
            <span class="chip bg-amber-100 text-amber-800">商品搜索工具</span>
            <span class="chip bg-sky-100 text-sky-800">知识库 RAG</span>
            <span class="chip bg-emerald-100 text-emerald-800">商品对比工具</span>
            <span class="chip bg-violet-100 text-violet-800">LangGraph 编排</span>
          </div>
        </div>

        <div class="rounded-[28px] bg-ink p-6 text-white">
          <p class="text-sm font-semibold uppercase tracking-[0.24em] text-amber-300">
            本轮重点
          </p>
          <ul class="mt-5 space-y-4 text-sm leading-7 text-slate-200">
            <li>1. FAQ 工具升级为知识库检索，返回命中的引用片段。</li>
            <li>2. Agent 复用知识库结果，并把引用信息写入工具调用轨迹。</li>
            <li>3. 前端知识库面板展示检索模式、引用片段和继续追问建议。</li>
            <li>4. Agent 工作台补充知识库结果回填区，便于观察 RAG 链路。</li>
          </ul>
        </div>
      </div>
    </section>

    <HealthStatusCard
      :health="health"
      :loading="healthLoading"
      :error-message="healthErrorMessage"
      :on-refresh="loadHealth"
    />

    <section class="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
      <SearchFiltersPanel
        :filters="filters"
        :categories="availableCategories"
        :brands="availableBrands"
        @update="updateFilters"
        @reset="resetFilters"
      />

      <div class="grid gap-6">
        <AgentPrecheckCard
          :precheck="agentPrecheck"
          :loading="agentPrecheckLoading"
          :error-message="agentPrecheckErrorMessage"
          @refresh="loadAgentPrecheck"
        />
        <AgentPromptPanel
          :result="agentResult"
          :loading="agentLoading"
          :error-message="agentErrorMessage"
          @submit="runAgentPrompt"
          @apply-filters="applyAgentFilters"
          @apply-faq="applyAgentFaqResult"
          @apply-compare="applyAgentCompareResult"
        />
        <AgentRunHistoryCard
          :history="agentRunHistory"
          :loading="agentRunHistoryLoading"
          :error-message="agentRunHistoryErrorMessage"
          :selected-run-id="selectedAgentRunId"
          :detail-loading="agentRunDetailLoading"
          :detail-error-message="agentRunDetailErrorMessage"
          @refresh="loadAgentRunHistory"
          @inspect="inspectAgentRun"
        />
      </div>
    </section>

    <section class="grid gap-6 2xl:grid-cols-[1.1fr_0.9fr]">
      <ProductGrid
        :products="products"
        :selected-ids="selectedProductIds"
        :recommended-ids="recommendedProductIds"
        :loading="productsLoading"
        :error-message="productsErrorMessage"
        :applied-filters="appliedFilters"
        @toggle-compare="toggleCompare"
      />
      <ComparePanel
        :selected-products="selectedProducts"
        :result="compareResult"
        :loading="compareLoading"
        :error-message="compareErrorMessage"
      />
    </section>

    <section class="grid gap-6 2xl:grid-cols-[1.02fr_0.98fr]">
      <FaqPanel
        :suggested-questions="suggestedFaqQuestions"
        :result="faqResult"
        :loading="faqLoading"
        :error-message="faqErrorMessage"
        @submit="submitFaq"
      />
      <KnowledgeBaseAdminPanel />
    </section>

    <ProductCatalogAdminPanel />
  </main>
</template>

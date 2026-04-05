<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";

import { fetchAgentPrecheck, chatWithAgent } from "./api/agent";
import { requestJson } from "./api/client";
import { compareProducts } from "./api/compare";
import { askFaq } from "./api/faq";
import type { CompareResponse } from "./api/contracts/compare";
import type { FaqAskResponse } from "./api/contracts/faq";
import { fetchProducts } from "./api/products";
import AgentPrecheckCard from "./components/AgentPrecheckCard.vue";
import AgentPromptPanel from "./components/AgentPromptPanel.vue";
import ComparePanel from "./components/ComparePanel.vue";
import FaqPanel from "./components/FaqPanel.vue";
import HealthStatusCard from "./components/HealthStatusCard.vue";
import ProductGrid from "./components/ProductGrid.vue";
import SearchFiltersPanel from "./components/SearchFiltersPanel.vue";
import { suggestedFaqQuestions } from "./data/mockFaqEntries";
import type { AgentPrecheck, AgentResult } from "./types/agent";
import type { Product, SearchFilters } from "./types/catalog";
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

const faqResult = ref<FaqAskResponse | null>(null);
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
    healthErrorMessage.value = error instanceof Error ? error.message : "未知错误，无法访问后端。";
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
    productsErrorMessage.value = error instanceof Error ? error.message : "未知错误，无法加载商品列表。";
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
    faqErrorMessage.value = error instanceof Error ? error.message : "未知错误，无法查询 FAQ。";
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
    compareErrorMessage.value = error instanceof Error ? error.message : "未知错误，无法生成商品对比。";
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

  try {
    const result = await chatWithAgent(query, selectedProductIds.value);
    agentResult.value = result;
    recommendedProductIds.value = result.recommendedProductIds;

    // 当 Agent 在导购场景里完成了意图解析，就把结果回填到搜索筛选区。
    // 这一步很关键，因为它体现了“模型负责理解，业务接口负责执行”的典型分层。
    if (result.parsedIntent) {
      filters.value = { ...result.parsedIntent.searchFilters };
    }

    // FAQ 路由命中后，直接把 FAQ 工具结果同步到 FAQ 面板，方便你观察工具复用。
    if (result.faqResult) {
      faqResult.value = result.faqResult;
    }

    // 对比路由命中后，把对比结果和商品选择状态同步到对比面板。
    if (result.compareResult) {
      compareResult.value = result.compareResult;
      selectedProductIds.value = result.compareResult.compared_products.map((product) => product.id);
    }
  } catch (error) {
    agentResult.value = null;
    agentErrorMessage.value = error instanceof Error ? error.message : "未知错误，无法完成 Agent 执行。";
  } finally {
    agentLoading.value = false;
  }
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
            电商导购 Agent / 第八轮迭代
          </p>
          <h1 class="mt-4 text-4xl font-semibold tracking-tight text-ink sm:text-5xl">
            接入 LangGraph 单 Agent 编排，把搜索、FAQ、对比和意图解析串成一条可观察的业务链路
          </h1>
          <p class="mt-5 max-w-3xl text-base leading-8 text-slate-600">
            这一轮的重点不是再加一个独立接口，而是把已有工具能力真正编排起来。
            Agent 会先判断当前问题属于导购、FAQ 还是商品对比，再决定调用哪一个业务工具，
            并把执行轨迹完整展示在前端工作台里。
          </p>

          <div class="mt-6 flex flex-wrap gap-3">
            <span class="chip bg-amber-100 text-amber-800">商品搜索工具</span>
            <span class="chip bg-sky-100 text-sky-800">FAQ 工具</span>
            <span class="chip bg-emerald-100 text-emerald-800">商品对比工具</span>
            <span class="chip bg-violet-100 text-violet-800">LangGraph 编排</span>
          </div>
        </div>

        <div class="rounded-[28px] bg-ink p-6 text-white">
          <p class="text-sm font-semibold uppercase tracking-[0.24em] text-amber-300">
            本轮重点
          </p>
          <ul class="mt-5 space-y-4 text-sm leading-7 text-slate-200">
            <li>1. 新增 `/agent/precheck`，先看环境和依赖是否满足 Agent 运行条件。</li>
            <li>2. 新增 `/agent/chat`，把路由、工具调用和最终回答串进 LangGraph。</li>
            <li>3. 前端意图解析面板升级为 Agent 工作台，展示完整执行轨迹。</li>
            <li>4. 清理商品与 FAQ 数据源乱码，保证接口与页面都是正常中文。</li>
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

    <FaqPanel
      :suggested-questions="suggestedFaqQuestions"
      :result="faqResult"
      :loading="faqLoading"
      :error-message="faqErrorMessage"
      @submit="submitFaq"
    />
  </main>
</template>

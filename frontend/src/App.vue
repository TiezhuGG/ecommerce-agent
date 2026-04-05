<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";

import type { CompareResponse } from "./api/contracts/compare";
import type { FaqAskResponse } from "./api/contracts/faq";
import { compareProducts } from "./api/compare";
import { askFaq } from "./api/faq";
import { parseIntent } from "./api/intent";
import { fetchProducts } from "./api/products";
import AgentPromptPanel from "./components/AgentPromptPanel.vue";
import ComparePanel from "./components/ComparePanel.vue";
import FaqPanel from "./components/FaqPanel.vue";
import HealthStatusCard from "./components/HealthStatusCard.vue";
import ProductGrid from "./components/ProductGrid.vue";
import SearchFiltersPanel from "./components/SearchFiltersPanel.vue";
import { suggestedFaqQuestions } from "./data/mockFaqEntries";
import type { AgentResult } from "./types/agent";
import type { Product, SearchFilters } from "./types/catalog";
import type { HealthResponse } from "./types/system";

const apiBaseUrl = "http://127.0.0.1:8000";

const health = ref<HealthResponse | null>(null);
const healthLoading = ref(false);
const healthErrorMessage = ref("");

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

const selectedProducts = computed(() =>
  products.value.filter((product) => selectedProductIds.value.includes(product.id)),
);

async function loadHealth() {
  healthLoading.value = true;
  healthErrorMessage.value = "";

  try {
    const response = await fetch(`${apiBaseUrl}/health`);

    if (!response.ok) {
      throw new Error(`请求失败，状态码 ${response.status}`);
    }

    health.value = (await response.json()) as HealthResponse;
  } catch (error) {
    healthErrorMessage.value = error instanceof Error ? error.message : "未知错误，无法访问后端。";
  } finally {
    healthLoading.value = false;
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
    const parsed = await parseIntent(query);
    agentResult.value = parsed;

    // AI 解析出的结构化条件会直接回填到页面筛选状态。
    // 这样你可以直观看到：模型输出并不是直接展示给用户，而是先变成系统可执行的参数。
    filters.value = { ...parsed.searchFilters };
  } catch (error) {
    agentResult.value = null;
    agentErrorMessage.value = error instanceof Error ? error.message : "未知错误，无法完成意图解析。";
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
    // 当用户选中至少 2 个商品时，自动请求后端对比接口。
    // 这样你能清楚看到：对比能力已经不是前端拼文案，而是独立的业务工具。
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
            电商导购 Agent · 第六轮迭代
          </p>
          <h1 class="mt-4 text-4xl font-semibold tracking-tight text-ink sm:text-5xl">
            接入 OpenAI 意图解析，让 AI 开始理解需求，但仍由业务系统返回商品事实
          </h1>
          <p class="mt-5 max-w-3xl text-base leading-8 text-slate-600">
            现在项目里已经有四类能力：商品搜索、FAQ 查询、商品对比、AI 意图解析。
            这一轮的重点不是让模型直接推荐商品，而是先让它把用户自然语言转换成系统可执行的结构化条件，
            再去调用已有业务工具完成搜索。
          </p>

          <div class="mt-6 flex flex-wrap gap-3">
            <span class="chip bg-amber-100 text-amber-800">商品搜索工具</span>
            <span class="chip bg-sky-100 text-sky-800">FAQ 工具</span>
            <span class="chip bg-emerald-100 text-emerald-800">商品对比工具</span>
            <span class="chip bg-violet-100 text-violet-800">OpenAI 意图解析</span>
          </div>
        </div>

        <div class="rounded-[28px] bg-ink p-6 text-white">
          <p class="text-sm font-semibold uppercase tracking-[0.24em] text-amber-300">
            本轮重点
          </p>
          <ul class="mt-5 space-y-4 text-sm leading-7 text-slate-200">
            <li>1. 新增 `/intent/parse` 后端接口，专门负责自然语言转结构化条件。</li>
            <li>2. 前端 Agent 面板改成真实请求后端，而不是本地假逻辑演示。</li>
            <li>3. AI 只负责理解意图，商品事实仍然由 `/products` 返回。</li>
            <li>4. 顺手清理本轮涉及页面里的乱码，并扩充商品目录到 30 条真实品牌型号。</li>
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

    <section class="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
      <SearchFiltersPanel
        :filters="filters"
        :categories="availableCategories"
        :brands="availableBrands"
        @update="updateFilters"
        @reset="resetFilters"
      />
      <AgentPromptPanel
        :result="agentResult"
        :loading="agentLoading"
        :error-message="agentErrorMessage"
        @submit="runAgentPrompt"
      />
    </section>

    <section class="grid gap-6 2xl:grid-cols-[1.1fr_0.9fr]">
      <ProductGrid
        :products="products"
        :selected-ids="selectedProductIds"
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

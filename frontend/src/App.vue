<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";

import { fetchProducts } from "./api/products";
import AgentPromptPanel from "./components/AgentPromptPanel.vue";
import ComparePanel from "./components/ComparePanel.vue";
import FaqPanel from "./components/FaqPanel.vue";
import HealthStatusCard from "./components/HealthStatusCard.vue";
import ProductGrid from "./components/ProductGrid.vue";
import SearchFiltersPanel from "./components/SearchFiltersPanel.vue";
import { mockFaqEntries } from "./data/mockFaqEntries";
import type { AgentResult, HealthResponse, Product, SearchFilters } from "./types";

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
const agentResult = ref<AgentResult | null>(null);

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
    healthErrorMessage.value =
      error instanceof Error ? error.message : "未知错误，无法访问后端";
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

    // When the result set changes, keep only compare selections that still exist
    // in the latest backend response. This avoids stale selection state.
    const currentIds = new Set(result.items.map((item) => item.id));
    selectedProductIds.value = selectedProductIds.value.filter((id) => currentIds.has(id));
  } catch (error) {
    products.value = [];
    productsErrorMessage.value =
      error instanceof Error ? error.message : "未知错误，无法加载商品列表";
  } finally {
    productsLoading.value = false;
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

function buildAgentResult(query: string, visibleProducts: Product[]): AgentResult {
  const lowerQuery = query.toLowerCase();
  const inferredFilters: string[] = [];

  if (lowerQuery.includes("耳机")) {
    inferredFilters.push("分类：蓝牙耳机");
  }
  if (lowerQuery.includes("键盘")) {
    inferredFilters.push("分类：机械键盘");
  }
  if (lowerQuery.includes("显示器")) {
    inferredFilters.push("分类：显示器");
  }
  if (lowerQuery.includes("鼠标")) {
    inferredFilters.push("分类：鼠标");
  }
  if (lowerQuery.includes("通勤")) {
    inferredFilters.push("场景：通勤");
  }
  if (lowerQuery.includes("办公")) {
    inferredFilters.push("场景：办公");
  }

  const priceMatch = query.match(/(\d{2,5})/);
  if (priceMatch) {
    inferredFilters.push(`预算上限：¥${priceMatch[1]}`);
  }

  const topProducts = visibleProducts.slice(0, 2).map((product) => product.name);
  const title = topProducts.length
    ? `已为你锁定 ${topProducts.length} 个重点候选商品`
    : "当前条件下没有理想候选商品";

  const answer = topProducts.length
    ? `结合当前检索结果，我优先建议你关注 ${topProducts.join("、")}。注意这里的推荐仍然是前端演示逻辑，但它已经建立在真实后端商品检索结果之上，后续接入 LangGraph 后，这里会升级为“先检索，再推理，再生成解释”的正式工作流。`
    : "当前商品检索没有命中结果。后续接入 Agent 后，这里会增加补充提问和替代推荐逻辑。";

  return {
    title,
    parsedIntent: "搜索导购",
    appliedFilters: inferredFilters.length
      ? inferredFilters
      : ["未识别到明确条件，先参考当前可见商品结果"],
    answer,
    executionSteps: [
      "第 1 步：根据自然语言识别预算、品类和场景关键词",
      "第 2 步：结合当前后端商品搜索结果筛出候选集",
      "第 3 步：生成面向用户的推荐摘要与解释",
    ],
  };
}

function runAgentPrompt(query: string) {
  if (!query) {
    return;
  }

  agentResult.value = buildAgentResult(query, products.value);
}

let searchTimer: ReturnType<typeof setTimeout> | null = null;

watch(
  filters,
  () => {
    // A tiny debounce keeps the UI responsive while preventing a request on
    // every single keystroke. This is a common pattern before introducing a
    // more advanced data-fetching layer.
    if (searchTimer) {
      clearTimeout(searchTimer);
    }

    searchTimer = setTimeout(() => {
      void loadProducts();
    }, 250);
  },
  { deep: true },
);

onMounted(() => {
  void loadHealth();
  void loadProducts();
});
</script>

<template>
  <main class="mx-auto flex min-h-screen w-full max-w-[1440px] flex-col gap-6 px-4 py-6 sm:px-6 lg:px-8 lg:py-10">
    <section class="panel overflow-hidden">
      <div class="grid gap-8 px-6 py-8 lg:grid-cols-[1.2fr_0.8fr] lg:px-8 lg:py-10">
        <div>
          <p class="text-sm font-semibold uppercase tracking-[0.28em] text-amber-700">
            电商导购 Agent · 第二轮迭代
          </p>
          <h1 class="mt-4 text-4xl font-semibold tracking-tight text-ink sm:text-5xl">
            先把商品搜索做成真实后端能力，再逐步接上 AI 工作流
          </h1>
          <p class="mt-5 max-w-3xl text-base leading-8 text-slate-600">
            这轮的核心变化是：商品结果已经不再依赖前端静态筛选，而是改为请求 FastAPI
            的真实接口。后面无论是 FAQ、对比分析，还是 LangGraph 推荐工作流，都会沿着这条“前端发请求
            -> 后端提供业务工具 -> AI 只做理解与编排”的路线继续演进。
          </p>

          <div class="mt-6 flex flex-wrap gap-3">
            <span class="chip bg-amber-100 text-amber-800">真实品牌与型号</span>
            <span class="chip bg-sky-100 text-sky-800">后端商品搜索接口</span>
            <span class="chip bg-emerald-100 text-emerald-800">中文响应式页面</span>
            <span class="chip bg-violet-100 text-violet-800">LangGraph 预留</span>
          </div>
        </div>

        <div class="rounded-[28px] bg-ink p-6 text-white">
          <p class="text-sm font-semibold uppercase tracking-[0.24em] text-amber-300">
            第二轮重点
          </p>
          <ul class="mt-5 space-y-4 text-sm leading-7 text-slate-200">
            <li>1. 商品数据迁到后端，作为真实业务检索工具</li>
            <li>2. 前端筛选条件映射为 HTTP 查询参数</li>
            <li>3. 商品结果区消费后端接口返回结果</li>
            <li>4. FAQ 与导购区暂时保留演示逻辑，不混在本轮一起做</li>
            <li>5. 每一轮新增一份 docs 复盘文档，方便后面系统回顾</li>
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
      <AgentPromptPanel :result="agentResult" @submit="runAgentPrompt" />
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
      <ComparePanel :selected-products="selectedProducts" />
    </section>

    <FaqPanel :entries="mockFaqEntries" />
  </main>
</template>

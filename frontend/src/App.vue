<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";

import type { CompareResponse } from "./api/contracts/compare";
import type { FaqAskResponse } from "./api/contracts/faq";
import { compareProducts } from "./api/compare";
import { askFaq } from "./api/faq";
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

async function submitFaq(question: string) {
  faqLoading.value = true;
  faqErrorMessage.value = "";

  try {
    faqResult.value = await askFaq(question);
  } catch (error) {
    faqResult.value = null;
    faqErrorMessage.value =
      error instanceof Error ? error.message : "未知错误，无法查询 FAQ";
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
      error instanceof Error ? error.message : "未知错误，无法生成商品对比";
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
  if (lowerQuery.includes("固态") || lowerQuery.includes("ssd")) {
    inferredFilters.push("分类：移动固态硬盘");
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
    ? `结合当前检索结果，我优先建议你关注 ${topProducts.join("、")}。注意这里的推荐仍然是前端演示逻辑，但它已经建立在真实后端商品检索结果之上。等我们接入 LangGraph 后，这里会升级为“意图解析 -> 工具调用 -> 生成解释”的正式 Agent 工作流。`
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
    // 这样你可以清楚看到：对比能力已经不是前端拼文案，而是独立的业务工具。
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
  <main class="mx-auto flex min-h-screen w-full max-w-[1440px] flex-col gap-6 px-4 py-6 sm:px-6 lg:px-8 lg:py-10">
    <section class="panel overflow-hidden">
      <div class="grid gap-8 px-6 py-8 lg:grid-cols-[1.2fr_0.8fr] lg:px-8 lg:py-10">
        <div>
          <p class="text-sm font-semibold uppercase tracking-[0.28em] text-amber-700">
            电商导购 Agent · 第五轮迭代
          </p>
          <h1 class="mt-4 text-4xl font-semibold tracking-tight text-ink sm:text-5xl">
            把商品对比也做成后端工具，形成更完整的 Agent 编排基座
          </h1>
          <p class="mt-5 max-w-3xl text-base leading-8 text-slate-600">
            现在项目里已经有三个真实业务工具：商品搜索、FAQ 查询、商品对比。后续 LangGraph
            接入时，它的职责会进一步聚焦在“理解意图、调用工具、组织答案”，而不是自己捏造事实。
          </p>

          <div class="mt-6 flex flex-wrap gap-3">
            <span class="chip bg-amber-100 text-amber-800">商品搜索工具</span>
            <span class="chip bg-sky-100 text-sky-800">FAQ 工具</span>
            <span class="chip bg-emerald-100 text-emerald-800">商品对比工具</span>
            <span class="chip bg-violet-100 text-violet-800">LangGraph 预备完成</span>
          </div>
        </div>

        <div class="rounded-[28px] bg-ink p-6 text-white">
          <p class="text-sm font-semibold uppercase tracking-[0.24em] text-amber-300">
            第五轮重点
          </p>
          <ul class="mt-5 space-y-4 text-sm leading-7 text-slate-200">
            <li>1. 新增商品对比后端接口与规则型总结逻辑</li>
            <li>2. 前端对比区改为请求后端，不再只靠本地拼接摘要</li>
            <li>3. 项目里形成三个可被 Agent 复用的业务工具</li>
            <li>4. 顺手清理残留乱码，保持中文可读性</li>
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

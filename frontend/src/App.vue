<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import AgentPromptPanel from "./components/AgentPromptPanel.vue";
import ComparePanel from "./components/ComparePanel.vue";
import FaqPanel from "./components/FaqPanel.vue";
import HealthStatusCard from "./components/HealthStatusCard.vue";
import ProductGrid from "./components/ProductGrid.vue";
import SearchFiltersPanel from "./components/SearchFiltersPanel.vue";
import { mockFaqEntries, mockProducts } from "./data/mockCatalog";
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

const selectedProductIds = ref<string[]>([]);
const agentResult = ref<AgentResult | null>(null);

const categories = [...new Set(mockProducts.map((product) => product.category))];
const brands = [...new Set(mockProducts.map((product) => product.brand))];

const filteredProducts = computed(() =>
  mockProducts.filter((product) => {
    const keyword = filters.value.keyword.trim().toLowerCase();
    const matchesKeyword =
      !keyword ||
      product.name.toLowerCase().includes(keyword) ||
      product.summary.toLowerCase().includes(keyword) ||
      product.tags.some((tag) => tag.toLowerCase().includes(keyword));

    const matchesCategory =
      !filters.value.category || product.category === filters.value.category;
    const matchesBrand = !filters.value.brand || product.brand === filters.value.brand;
    const matchesPrice =
      filters.value.maxPrice === null || product.price <= filters.value.maxPrice;

    return matchesKeyword && matchesCategory && matchesBrand && matchesPrice;
  }),
);

const selectedProducts = computed(() =>
  mockProducts.filter((product) => selectedProductIds.value.includes(product.id)),
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

function buildAgentResult(query: string, products: Product[]): AgentResult {
  const lowerQuery = query.toLowerCase();
  const inferredFilters: string[] = [];

  if (lowerQuery.includes("耳机")) {
    inferredFilters.push("分类：蓝牙耳机");
  }
  if (lowerQuery.includes("键盘")) {
    inferredFilters.push("分类：机械键盘");
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

  const topProducts = products.slice(0, 2).map((product) => product.name);
  const title = topProducts.length
    ? `已为你锁定 ${topProducts.length} 个重点候选商品`
    : "未找到理想商品，建议放宽预算或关键词";

  const answer = topProducts.length
    ? `结合你的需求，我优先保留了 ${topProducts.join("、")}。当前演示版会根据输入里的预算、品类和场景词做简单匹配，后续接入 LangGraph 后，会把这一步升级为真正的多节点导购工作流。`
    : "当前筛选条件下没有匹配商品。后续真实版本会加入更细的补充提问和替代推荐逻辑。";

  return {
    title,
    parsedIntent: "搜索导购",
    appliedFilters: inferredFilters.length ? inferredFilters : ["未识别到明确条件，按默认候选商品展示"],
    answer,
    executionSteps: [
      "第 1 步：识别用户输入中的预算、品类和场景关键词",
      "第 2 步：根据条件筛选静态商品样本",
      "第 3 步：汇总候选商品并生成推荐摘要",
    ],
  };
}

function runAgentPrompt(query: string) {
  if (!query) {
    return;
  }

  const lowerQuery = query.toLowerCase();
  const matchedProducts = mockProducts.filter((product) => {
    if (lowerQuery.includes("耳机") && product.category === "蓝牙耳机") {
      return true;
    }
    if (lowerQuery.includes("键盘") && product.category === "机械键盘") {
      return true;
    }
    if (lowerQuery.includes("显示器") && product.category === "显示器") {
      return true;
    }
    return lowerQuery.includes(product.brand.toLowerCase());
  });

  const candidateProducts = matchedProducts.length ? matchedProducts : filteredProducts.value;
  agentResult.value = buildAgentResult(query, candidateProducts);
}

onMounted(() => {
  void loadHealth();
});
</script>

<template>
  <main class="mx-auto flex min-h-screen w-full max-w-[1440px] flex-col gap-6 px-4 py-6 sm:px-6 lg:px-8 lg:py-10">
    <section class="panel overflow-hidden">
      <div class="grid gap-8 px-6 py-8 lg:grid-cols-[1.2fr_0.8fr] lg:px-8 lg:py-10">
        <div>
          <p class="text-sm font-semibold uppercase tracking-[0.28em] text-amber-700">
            电商导购 Agent · 第一版骨架
          </p>
          <h1 class="mt-4 text-4xl font-semibold tracking-tight text-ink sm:text-5xl">
            中文化、响应式、可持续迭代的 AI 导购项目基座
          </h1>
          <p class="mt-5 max-w-3xl text-base leading-8 text-slate-600">
            这一版的重点不是直接把所有能力做完，而是先把页面结构、业务模块和技术边界搭清楚。你现在看到的搜索区、导购区、对比区和
            FAQ 区，都是后续真实后端接口和 LangGraph 工作流的承载位置。
          </p>

          <div class="mt-6 flex flex-wrap gap-3">
            <span class="chip bg-amber-100 text-amber-800">Vue 3</span>
            <span class="chip bg-sky-100 text-sky-800">Tailwind CSS</span>
            <span class="chip bg-emerald-100 text-emerald-800">FastAPI</span>
            <span class="chip bg-violet-100 text-violet-800">LangGraph 预留</span>
          </div>
        </div>

        <div class="rounded-[28px] bg-ink p-6 text-white">
          <p class="text-sm font-semibold uppercase tracking-[0.24em] text-amber-300">
            第一版模块清单
          </p>
          <ul class="mt-5 space-y-4 text-sm leading-7 text-slate-200">
            <li>1. 结构化搜索区：未来承接商品搜索接口</li>
            <li>2. 智能导购区：未来承接 LangGraph 主工作流</li>
            <li>3. 商品结果区：展示搜索结果与推荐候选</li>
            <li>4. 商品对比区：展示多商品差异分析</li>
            <li>5. FAQ 区：展示售前知识条目与答案来源</li>
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
        :categories="categories"
        :brands="brands"
        @update="updateFilters"
        @reset="resetFilters"
      />
      <AgentPromptPanel :result="agentResult" @submit="runAgentPrompt" />
    </section>

    <section class="grid gap-6 2xl:grid-cols-[1.1fr_0.9fr]">
      <ProductGrid
        :products="filteredProducts"
        :selected-ids="selectedProductIds"
        @toggle-compare="toggleCompare"
      />
      <ComparePanel :selected-products="selectedProducts" />
    </section>

    <FaqPanel :entries="mockFaqEntries" />
  </main>
</template>

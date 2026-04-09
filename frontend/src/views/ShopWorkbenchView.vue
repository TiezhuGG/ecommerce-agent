<script setup lang="ts">
import type { CompareResponse } from "../api/contracts/compare";
import AgentPromptPanel from "../components/AgentPromptPanel.vue";
import AgentRunHistoryCard from "../components/AgentRunHistoryCard.vue";
import ComparePanel from "../components/ComparePanel.vue";
import FaqPanel from "../components/FaqPanel.vue";
import ProductGrid from "../components/ProductGrid.vue";
import SearchFiltersPanel from "../components/SearchFiltersPanel.vue";
import type {
  AgentConversationTurn,
  AgentResult,
  AgentRunHistory,
  AgentThreadDetail,
  AgentThreadHistory,
} from "../types/agent";
import type { Product, SearchFilters } from "../types/catalog";
import type { FaqAskResult } from "../types/faq";

type CatalogPanelState = {
  filters: SearchFilters;
  categories: string[];
  brands: string[];
  products: Product[];
  productsLoading: boolean;
  productsErrorMessage: string;
  appliedFilters: string[];
  selectedProductIds: string[];
  recommendedProductIds: string[];
  selectedProducts: Product[];
  compareResult: CompareResponse | null;
  compareLoading: boolean;
  compareErrorMessage: string;
  showComparePanel: boolean;
};

type AgentPanelState = {
  result: AgentResult | null;
  loading: boolean;
  errorMessage: string;
  currentThreadId: string | null;
  conversationContext: AgentConversationTurn[];
};

type FaqPanelState = {
  suggestedQuestions: string[];
  result: FaqAskResult | null;
  loading: boolean;
  errorMessage: string;
};

type HistoryPanelState = {
  visible: boolean;
  history: AgentRunHistory | null;
  threadHistory: AgentThreadHistory | null;
  threadDetail: AgentThreadDetail | null;
  loading: boolean;
  errorMessage: string;
  selectedRunId: string | null;
  selectedThreadId: string | null;
  currentThreadId: string | null;
  threadDetailLoading: boolean;
  detailLoading: boolean;
  threadDetailErrorMessage: string;
  detailErrorMessage: string;
};

defineProps<{
  catalog: CatalogPanelState;
  agent: AgentPanelState;
  faq: FaqPanelState;
  historyPanel: HistoryPanelState;
  updateFilters: (filters: SearchFilters) => void;
  resetFilters: () => void;
  submitAgentPrompt: (query: string) => void | Promise<void>;
  applyAgentFilters: () => void;
  applyAgentFaqResult: () => void;
  applyAgentCompareResult: () => void;
  clearAgentConversation: () => void;
  toggleCompare: (productId: string) => void;
  submitFaq: (question: string) => void | Promise<void>;
  refreshHistory: () => void | Promise<void>;
  inspectAgentThread: (threadId: string) => void | Promise<void>;
  inspectAgentRun: (runId: string) => void | Promise<void>;
  resumeAgentThread: (runId: string) => void | Promise<void>;
  showDevPanels: boolean;
  goToAdminSystem: () => void;
  goToAdminKnowledge: () => void;
  goToAdminCatalog: () => void;
}>();
</script>

<template>
  <section class="space-y-6">
    <section class="panel overflow-hidden">
      <div class="grid gap-8 px-6 py-8 lg:grid-cols-[1.15fr_0.85fr] lg:px-8 lg:py-10">
        <div>
          <p class="text-sm font-semibold uppercase tracking-[0.28em] text-amber-700">
            Shopper Guide
          </p>
          <h1 class="mt-4 text-4xl font-semibold tracking-tight text-ink sm:text-5xl">
            先筛商品，再让 AI 帮你缩小范围
          </h1>
          <p class="mt-5 max-w-3xl text-base leading-8 text-slate-600">
            现在首页只保留普通用户真正会用到的主链路：先筛条件，再描述需求，再看商品结果，
            必要时做对比，最后查询售前问题。
          </p>

          <div class="mt-6 grid gap-3 sm:grid-cols-3">
            <div class="rounded-3xl bg-slate-50 p-4">
              <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
                第一步
              </p>
              <p class="mt-2 text-base font-semibold text-slate-900">
                先缩小预算、分类和品牌范围
              </p>
            </div>
            <div class="rounded-3xl bg-slate-50 p-4">
              <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
                第二步
              </p>
              <p class="mt-2 text-base font-semibold text-slate-900">
                直接告诉 AI 你的使用场景
              </p>
            </div>
            <div class="rounded-3xl bg-slate-50 p-4">
              <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
                第三步
              </p>
              <p class="mt-2 text-base font-semibold text-slate-900">
                选择商品做对比并继续追问
              </p>
            </div>
          </div>
        </div>

        <div class="rounded-[28px] bg-ink p-6 text-white">
          <p class="text-sm font-semibold uppercase tracking-[0.24em] text-amber-300">
            当前导购概况
          </p>

          <div class="mt-5 grid gap-4 sm:grid-cols-2">
            <div class="rounded-3xl bg-white/10 p-4">
              <p class="text-xs uppercase tracking-[0.18em] text-slate-300">商品数量</p>
              <p class="mt-2 text-2xl font-semibold text-white">{{ catalog.products.length }}</p>
            </div>
            <div class="rounded-3xl bg-white/10 p-4">
              <p class="text-xs uppercase tracking-[0.18em] text-slate-300">已选对比</p>
              <p class="mt-2 text-2xl font-semibold text-white">
                {{ catalog.selectedProductIds.length }}
              </p>
            </div>
          </div>

          <div class="mt-5 flex flex-wrap gap-2">
            <span class="chip bg-amber-100 text-amber-900">搜索</span>
            <span class="chip bg-sky-100 text-sky-900">AI 推荐</span>
            <span class="chip bg-emerald-100 text-emerald-900">商品对比</span>
            <span class="chip bg-violet-100 text-violet-900">知识问答</span>
          </div>

          <p class="mt-5 text-sm leading-7 text-slate-200">
            {{
              agent.currentThreadId
                ? "当前已有进行中的会话，你可以继续追问，不需要从头重说一遍。"
                : "还没有进行中的会话，直接输入需求即可开始。"
            }}
          </p>
        </div>
      </div>
    </section>

    <section class="space-y-4">
      <div class="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h2 class="text-2xl font-semibold text-ink">核心操作区</h2>
          <p class="mt-1 text-sm leading-6 text-slate-600">
            普通用户只看这里，就可以完成一次完整导购。
          </p>
        </div>

        <div class="flex flex-wrap gap-2">
          <span v-if="agent.currentThreadId" class="chip bg-emerald-100 text-emerald-800">
            会话进行中
          </span>
          <span
            v-if="catalog.recommendedProductIds.length"
            class="chip bg-amber-100 text-amber-800"
          >
            AI 已推荐 {{ catalog.recommendedProductIds.length }} 件商品
          </span>
        </div>
      </div>

      <div class="grid gap-6 xl:grid-cols-[0.94fr_1.06fr]">
        <SearchFiltersPanel
          :filters="catalog.filters"
          :categories="catalog.categories"
          :brands="catalog.brands"
          @update="updateFilters"
          @reset="resetFilters"
        />

        <AgentPromptPanel
          :result="agent.result"
          :loading="agent.loading"
          :error-message="agent.errorMessage"
          :current-thread-id="agent.currentThreadId"
          :conversation-context="agent.conversationContext"
          @submit="submitAgentPrompt"
          @apply-filters="applyAgentFilters"
          @apply-faq="applyAgentFaqResult"
          @apply-compare="applyAgentCompareResult"
          @clear-conversation="clearAgentConversation"
        />
      </div>
    </section>

    <section class="space-y-4">
      <div>
        <h2 class="text-2xl font-semibold text-ink">商品与对比</h2>
        <p class="mt-1 text-sm leading-6 text-slate-600">
          先看商品结果，再决定是否加入对比。商品区当前只保留约 4 张卡片的首屏高度，其余向下滚动查看。
        </p>
      </div>

      <div class="grid gap-6 2xl:grid-cols-[1.08fr_0.92fr]">
        <ProductGrid
          :products="catalog.products"
          :selected-ids="catalog.selectedProductIds"
          :recommended-ids="catalog.recommendedProductIds"
          :loading="catalog.productsLoading"
          :error-message="catalog.productsErrorMessage"
          :applied-filters="catalog.appliedFilters"
          @toggle-compare="toggleCompare"
        />

        <ComparePanel
          v-if="catalog.showComparePanel"
          :selected-products="catalog.selectedProducts"
          :result="catalog.compareResult"
          :loading="catalog.compareLoading"
          :error-message="catalog.compareErrorMessage"
        />

        <section v-else class="panel p-6">
          <div class="flex h-full flex-col justify-between gap-5">
            <div>
              <h3 class="panel-title">对比区尚未激活</h3>
              <p class="muted-copy mt-2">
                从左侧商品列表里勾选 2 到 3 件商品后，这里会自动生成横向对比结果。
              </p>
            </div>

            <div class="rounded-3xl bg-slate-50 p-5">
              <p class="text-sm font-semibold text-slate-800">建议操作</p>
              <ul class="mt-3 space-y-2 text-sm leading-7 text-slate-600">
                <li>1. 先在左侧缩小筛选范围。</li>
                <li>2. 不确定时，先让 AI 给出推荐理由。</li>
                <li>3. 最后挑 2 到 3 件商品做横向对比。</li>
              </ul>
            </div>
          </div>
        </section>
      </div>
    </section>

    <section class="space-y-4">
      <div>
        <h2 class="text-2xl font-semibold text-ink">售前问答</h2>
        <p class="mt-1 text-sm leading-6 text-slate-600">
          发票、发货、质保、企业采购等问题，统一从知识库入口查询。
        </p>
      </div>

      <FaqPanel
        :suggested-questions="faq.suggestedQuestions"
        :result="faq.result"
        :loading="faq.loading"
        :error-message="faq.errorMessage"
        @submit="submitFaq"
      />
    </section>

    <section v-if="historyPanel.visible" class="space-y-4">
      <details class="group" :open="Boolean(historyPanel.currentThreadId)">
        <summary
          class="panel flex cursor-pointer list-none items-center justify-between gap-4 px-6 py-5"
        >
          <div>
            <h2 class="text-2xl font-semibold text-ink">继续上次会话</h2>
            <p class="mt-1 text-sm leading-6 text-slate-600">
              这里放线程历史和运行时间线，首屏不再默认展开。
            </p>
          </div>
          <span class="chip bg-slate-100 text-slate-700 group-open:bg-amber-100 group-open:text-amber-800">
            {{ historyPanel.currentThreadId ? "已展开当前会话" : "展开历史" }}
          </span>
        </summary>

        <div class="mt-4">
          <AgentRunHistoryCard
            :history="historyPanel.history"
            :thread-history="historyPanel.threadHistory"
            :thread-detail="historyPanel.threadDetail"
            :loading="historyPanel.loading"
            :error-message="historyPanel.errorMessage"
            :selected-run-id="historyPanel.selectedRunId"
            :selected-thread-id="historyPanel.selectedThreadId"
            :current-thread-id="historyPanel.currentThreadId"
            :thread-detail-loading="historyPanel.threadDetailLoading"
            :detail-loading="historyPanel.detailLoading"
            :thread-detail-error-message="historyPanel.threadDetailErrorMessage"
            :detail-error-message="historyPanel.detailErrorMessage"
            @refresh="refreshHistory"
            @inspect-thread="inspectAgentThread"
            @inspect="inspectAgentRun"
            @resume="resumeAgentThread"
          />
        </div>
      </details>
    </section>

    <section class="space-y-4">
      <section v-if="showDevPanels" class="panel p-5">
        <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p class="text-sm font-semibold text-slate-900">后台工作区已独立</p>
            <p class="mt-1 text-sm leading-6 text-slate-600">
              开发与运营模块已经从首页移出，并由正式路由管理。
            </p>
          </div>

          <div class="flex flex-wrap gap-2">
            <button
              type="button"
              class="rounded-full border border-slate-200 px-4 py-2 text-sm text-slate-700 transition hover:border-slate-300 hover:bg-slate-50"
              @click="goToAdminSystem"
            >
              系统
            </button>
            <button
              type="button"
              class="rounded-full border border-slate-200 px-4 py-2 text-sm text-slate-700 transition hover:border-slate-300 hover:bg-slate-50"
              @click="goToAdminKnowledge"
            >
              知识库
            </button>
            <button
              type="button"
              class="rounded-full bg-ink px-4 py-2 text-sm font-medium text-white transition hover:bg-slate-800"
              @click="goToAdminCatalog"
            >
              商品目录
            </button>
          </div>
        </div>
      </section>

      <section v-else class="panel p-5">
        <p class="text-sm leading-7 text-slate-600">
          当前是用户视角，后台工作区默认隐藏。如需在生产环境开放，可在 `frontend/.env`
          中显式设置 `VITE_SHOW_DEV_PANELS=true`。
        </p>
      </section>
    </section>
  </section>
</template>

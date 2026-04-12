<script setup lang="ts">
import type { CompareResponse } from "../api/contracts/compare";
import AgentPromptPanel from "../components/AgentPromptPanel.vue";
import ComparePanel from "../components/ComparePanel.vue";
import ConversationResumePanel from "../components/ConversationResumePanel.vue";
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
            先缩小范围，再让 AI 帮你挑
          </h1>
          <p class="mt-5 max-w-3xl text-base leading-8 text-slate-600">
            首页只保留普通用户真正会用到的导购流程：先筛预算、分类和品牌，再告诉 AI 你的使用场景，
            最后看商品结果、做对比，必要时再查售前问题。
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
                选商品做对比并继续追问
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
                ? "当前已有进行中的会话，你可以继续追问，不需要从头再说一遍。"
                : "还没有进行中的会话，直接输入需求就可以开始。"
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
            普通用户主要看这里，就可以完成一次完整导购。
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
          :show-dev-details="showDevPanels"
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
          <div class="flex h-full flex-col justify-between gap-6">
            <div>
              <span class="chip bg-slate-100 text-slate-700">等待加入对比</span>
              <h3 class="mt-4 text-2xl font-semibold text-ink">对比区还没有内容</h3>
              <p class="mt-3 max-w-2xl text-sm leading-7 text-slate-600">
                从左侧商品结果里勾选 2 到 3 件你真正想比较的商品，这里就会自动展开横向对比，
                帮你集中看差异、适合场景和推荐理由。
              </p>
            </div>

            <div class="grid gap-3 sm:grid-cols-3">
              <article class="rounded-3xl bg-slate-50 p-4">
                <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
                  Step 1
                </p>
                <p class="mt-2 text-sm font-semibold text-slate-900">
                  先用左侧筛选缩小预算、分类和品牌范围。
                </p>
              </article>
              <article class="rounded-3xl bg-slate-50 p-4">
                <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
                  Step 2
                </p>
                <p class="mt-2 text-sm font-semibold text-slate-900">
                  不确定时，先让 AI 给出推荐理由和候选商品。
                </p>
              </article>
              <article class="rounded-3xl bg-slate-50 p-4">
                <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
                  Step 3
                </p>
                <p class="mt-2 text-sm font-semibold text-slate-900">
                  最后挑 2 到 3 件商品加入对比，再看关键差异。
                </p>
              </article>
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
      <ConversationResumePanel
        :history="historyPanel.threadHistory"
        :loading="historyPanel.loading"
        :error-message="historyPanel.errorMessage"
        :current-thread-id="historyPanel.currentThreadId"
        @refresh="refreshHistory"
        @resume="resumeAgentThread"
      />
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
          当前是普通用户视角，后台工作区默认隐藏。如需在生产环境开放，可在
          <code>frontend/.env</code> 中显式设置 <code>VITE_SHOW_DEV_PANELS=true</code>。
        </p>
      </section>
    </section>
  </section>
</template>

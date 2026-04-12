<script setup lang="ts">
import { computed } from "vue";

import type { AgentConversationTurn, AgentResult, AgentRoute, AgentToolCall } from "../types/agent";

const props = defineProps<{
  result: AgentResult | null;
  loading: boolean;
  errorMessage: string;
  selectedRunId: string | null;
}>();

const currentThreadState = computed(() => props.result?.threadState ?? null);

const detailTitle = computed(() => {
  return props.selectedRunId ? "当前选中运行详情" : "最近一次加载的运行详情";
});

const rememberedFilters = computed(() => {
  const filters = props.result?.parsedIntent?.searchFilters ?? currentThreadState.value?.searchFilters;
  if (!filters) {
    return [] as string[];
  }

  const items: string[] = [];
  if (filters.category) {
    items.push(`分类: ${filters.category}`);
  }
  if (filters.brand) {
    items.push(`品牌: ${filters.brand}`);
  }
  if (filters.maxPrice !== null) {
    items.push(`预算上限: CNY ${filters.maxPrice}`);
  }
  if (filters.keyword) {
    items.push(`关键词: ${filters.keyword}`);
  }
  return items;
});

const providerRows = computed(() => {
  if (!props.result) {
    return [] as Array<{ label: string; value: string }>;
  }

  return [
    { label: "Route Provider", value: props.result.providers.routeProvider || "not-recorded" },
    { label: "Intent Provider", value: props.result.providers.intentProvider || "not-recorded" },
    { label: "Answer Provider", value: props.result.providers.answerProvider || "not-recorded" },
    { label: "Retrieval Provider", value: props.result.providers.retrievalProvider || "not-recorded" },
  ];
});

function formatTimestamp(value: string | null): string {
  if (!value) {
    return "未记录";
  }

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }

  return parsed.toLocaleString("zh-CN", {
    hour12: false,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

function formatRouteLabel(route: AgentRoute | ""): string {
  if (route === "faq") {
    return "知识问答";
  }

  if (route === "compare") {
    return "商品对比";
  }

  if (route === "shopping") {
    return "AI 导购";
  }

  return "未分类";
}

function formatOriginLabel(origin: AgentResult["origin"]): string {
  return origin === "history" ? "来自历史记录" : "来自最新运行";
}

function formatJson(value: Record<string, unknown>): string {
  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return "{}";
  }
}

function hasPayload(toolCall: AgentToolCall): boolean {
  return Object.keys(toolCall.inputPayload).length > 0 || Object.keys(toolCall.outputPayload).length > 0;
}

function contextTurnLabel(turn: AgentConversationTurn, index: number): string {
  return `${index + 1}. ${formatRouteLabel(turn.route)}`;
}
</script>

<template>
  <section class="panel p-6">
    <div class="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
      <div class="max-w-3xl">
        <p class="text-sm font-semibold uppercase tracking-[0.24em] text-amber-700">
          Run Detail
        </p>
        <h2 class="mt-3 text-3xl font-semibold tracking-tight text-ink">
          {{ detailTitle }}
        </h2>
        <p class="mt-3 text-sm leading-7 text-slate-600">
          这里承接后台系统区里“查看详情”的正文落点。重点不是再重复历史列表，而是把当前这次
          Agent 运行的输入、决策、工具调用、线程状态和业务结果连成一条可复盘的诊断链路。
        </p>
      </div>

      <span v-if="selectedRunId" class="chip bg-sky-100 text-sky-800">
        run: {{ selectedRunId }}
      </span>
    </div>

    <div
      v-if="loading"
      class="mt-5 rounded-3xl bg-slate-50 px-5 py-10 text-center text-sm text-slate-600"
    >
      正在加载运行详情...
    </div>

    <p
      v-else-if="errorMessage && !result"
      class="mt-5 rounded-2xl bg-rose-50 px-4 py-3 text-sm text-rose-700"
    >
      运行详情加载失败：{{ errorMessage }}
    </p>

    <div
      v-else-if="!result"
      class="mt-5 rounded-3xl bg-slate-50 px-5 py-10 text-center text-sm leading-7 text-slate-600"
    >
      这里会展示某次运行的完整诊断正文。先在上方运行历史里选择一条记录，再回到这里查看详情。
    </div>

    <div v-else class="mt-6 space-y-5">
      <section class="rounded-[28px] bg-slate-50 p-5">
        <div class="flex flex-wrap gap-2">
          <span class="chip bg-emerald-100 text-emerald-800">
            {{ formatRouteLabel(result.route) }}
          </span>
          <span
            class="chip"
            :class="result.origin === 'history' ? 'bg-slate-100 text-slate-700' : 'bg-sky-100 text-sky-800'"
          >
            {{ formatOriginLabel(result.origin) }}
          </span>
          <span class="chip bg-violet-100 text-violet-800">{{ result.provider }}</span>
          <span class="chip bg-slate-100 text-slate-700">{{ result.model }}</span>
          <span
            class="chip"
            :class="result.persisted ? 'bg-amber-100 text-amber-800' : 'bg-slate-100 text-slate-700'"
          >
            {{ result.persisted ? "已持久化" : "未持久化" }}
          </span>
        </div>

        <div class="mt-5 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
          <article class="rounded-2xl bg-white p-4">
            <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">运行时间</p>
            <p class="mt-2 text-sm leading-6 text-slate-900">{{ formatTimestamp(result.createdAt) }}</p>
          </article>
          <article class="rounded-2xl bg-white p-4">
            <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Run ID</p>
            <p class="mt-2 text-sm leading-6 text-slate-900 break-all">{{ result.runId ?? "未记录" }}</p>
          </article>
          <article class="rounded-2xl bg-white p-4">
            <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Thread ID</p>
            <p class="mt-2 text-sm leading-6 text-slate-900 break-all">{{ result.threadId }}</p>
          </article>
          <article class="rounded-2xl bg-white p-4">
            <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Graph Runtime</p>
            <p class="mt-2 text-sm leading-6 text-slate-900">{{ result.graphRuntime }}</p>
          </article>
        </div>
      </section>

      <div class="grid gap-5 xl:grid-cols-[1.08fr_0.92fr]">
        <section class="rounded-[28px] bg-slate-50 p-5">
          <p class="text-sm font-semibold text-slate-800">用户输入</p>
          <p class="mt-3 whitespace-pre-line text-sm leading-7 text-slate-700">{{ result.message }}</p>

          <p class="mt-6 text-sm font-semibold text-slate-800">最终回答</p>
          <p class="mt-3 whitespace-pre-line text-sm leading-7 text-slate-700">
            {{ result.finalAnswer }}
          </p>
        </section>

        <section class="rounded-[28px] bg-slate-50 p-5">
          <p class="text-sm font-semibold text-slate-800">提供方拆解</p>
          <div class="mt-4 space-y-3">
            <article
              v-for="row in providerRows"
              :key="row.label"
              class="rounded-2xl bg-white p-4"
            >
              <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">{{ row.label }}</p>
              <p class="mt-2 text-sm leading-6 text-slate-700">{{ row.value }}</p>
            </article>
          </div>
        </section>
      </div>

      <section
        v-if="result.routeReasoning || result.parsedIntent"
        class="rounded-[28px] bg-slate-50 p-5"
      >
        <div>
          <p class="text-sm font-semibold text-slate-800">路由与意图理解</p>
          <p class="mt-2 text-sm leading-6 text-slate-600">
            用于回看这次运行为什么走到当前 route，以及解析出了哪些导购筛选条件。
          </p>
        </div>

        <p v-if="result.routeReasoning" class="mt-4 text-sm leading-7 text-slate-700">
          {{ result.routeReasoning }}
        </p>

        <div v-if="result.parsedIntent" class="mt-5 grid gap-4 xl:grid-cols-[1.04fr_0.96fr]">
          <article class="rounded-2xl bg-white p-4">
            <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">场景与优先级</p>
            <p class="mt-2 text-sm leading-6 text-slate-700">
              {{ result.parsedIntent.scenario || "未记录场景说明" }}
            </p>
            <div v-if="result.parsedIntent.priorities.length" class="mt-3 flex flex-wrap gap-2">
              <span
                v-for="item in result.parsedIntent.priorities"
                :key="item"
                class="chip bg-violet-100 text-violet-800"
              >
                {{ item }}
              </span>
            </div>
            <p class="mt-3 text-sm leading-7 text-slate-600">
              {{ result.parsedIntent.reasoningSummary }}
            </p>
          </article>

          <article class="rounded-2xl bg-white p-4">
            <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">筛选条件</p>
            <div v-if="rememberedFilters.length" class="mt-3 flex flex-wrap gap-2">
              <span
                v-for="item in rememberedFilters"
                :key="item"
                class="chip bg-amber-100 text-amber-800"
              >
                {{ item }}
              </span>
            </div>
            <div v-if="result.parsedIntent.appliedFilters.length" class="mt-3 flex flex-wrap gap-2">
              <span
                v-for="item in result.parsedIntent.appliedFilters"
                :key="'applied-' + item"
                class="chip bg-sky-100 text-sky-800"
              >
                {{ item }}
              </span>
            </div>
            <p
              v-if="!rememberedFilters.length && !result.parsedIntent.appliedFilters.length"
              class="mt-3 text-sm leading-6 text-slate-500"
            >
              本次运行没有留下可展示的筛选条件。
            </p>
          </article>
        </div>
      </section>

      <section class="grid gap-5 xl:grid-cols-2">
        <article class="rounded-[28px] bg-slate-50 p-5">
          <p class="text-sm font-semibold text-slate-800">运行提醒</p>
          <div v-if="result.warnings.length" class="mt-4 flex flex-wrap gap-2">
            <span
              v-for="warning in result.warnings"
              :key="warning"
              class="chip bg-amber-100 text-amber-800"
            >
              {{ warning }}
            </span>
          </div>
          <p v-else class="mt-4 text-sm leading-6 text-slate-500">
            本次运行没有额外 warning。
          </p>
        </article>

        <article class="rounded-[28px] bg-slate-50 p-5">
          <p class="text-sm font-semibold text-slate-800">商品轨迹</p>

          <div v-if="result.recommendedProductIds.length" class="mt-4">
            <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Recommended</p>
            <div class="mt-2 flex flex-wrap gap-2">
              <span
                v-for="productId in result.recommendedProductIds"
                :key="productId"
                class="chip bg-sky-100 text-sky-800"
              >
                {{ productId }}
              </span>
            </div>
          </div>

          <div v-if="result.selectedProductIds.length" class="mt-4">
            <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Selected</p>
            <div class="mt-2 flex flex-wrap gap-2">
              <span
                v-for="productId in result.selectedProductIds"
                :key="'selected-' + productId"
                class="chip bg-emerald-100 text-emerald-800"
              >
                {{ productId }}
              </span>
            </div>
          </div>

          <p
            v-if="!result.recommendedProductIds.length && !result.selectedProductIds.length"
            class="mt-4 text-sm leading-6 text-slate-500"
          >
            本次运行没有留下商品轨迹信息。
          </p>
        </article>
      </section>

      <section
        v-if="result.conversationContext.length || currentThreadState"
        class="grid gap-5 xl:grid-cols-[0.96fr_1.04fr]"
      >
        <article v-if="currentThreadState" class="rounded-[28px] bg-slate-50 p-5">
          <p class="text-sm font-semibold text-slate-800">线程状态快照</p>
          <div class="mt-4 grid gap-3 md:grid-cols-2">
            <article class="rounded-2xl bg-white p-4">
              <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Last Run</p>
              <p class="mt-2 text-sm leading-6 text-slate-700 break-all">{{ currentThreadState.lastRunId }}</p>
            </article>
            <article class="rounded-2xl bg-white p-4">
              <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Last Route</p>
              <p class="mt-2 text-sm leading-6 text-slate-700">
                {{ formatRouteLabel(currentThreadState.lastRoute) }}
              </p>
            </article>
            <article class="rounded-2xl bg-white p-4">
              <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Candidate Count</p>
              <p class="mt-2 text-2xl font-semibold text-slate-900">
                {{ currentThreadState.candidateProductIds.length }}
              </p>
            </article>
            <article class="rounded-2xl bg-white p-4">
              <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Selected Count</p>
              <p class="mt-2 text-2xl font-semibold text-slate-900">
                {{ currentThreadState.selectedProductIds.length }}
              </p>
            </article>
          </div>

          <div v-if="currentThreadState.candidateProductIds.length" class="mt-4">
            <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Candidate Products</p>
            <div class="mt-2 flex flex-wrap gap-2">
              <span
                v-for="productId in currentThreadState.candidateProductIds"
                :key="'candidate-' + productId"
                class="chip bg-white text-slate-700"
              >
                {{ productId }}
              </span>
            </div>
          </div>
        </article>

        <article v-if="result.conversationContext.length" class="rounded-[28px] bg-slate-50 p-5">
          <p class="text-sm font-semibold text-slate-800">会话上下文</p>
          <p class="mt-2 text-sm leading-6 text-slate-600">
            用于回看本次运行继承了哪些历史对话上下文，判断恢复续聊时是否带上了正确记忆。
          </p>

          <div class="mt-4 space-y-3">
            <article
              v-for="(turn, index) in result.conversationContext"
              :key="turn.userMessage + '-' + index"
              class="rounded-2xl bg-white p-4"
            >
              <div class="flex flex-wrap gap-2">
                <span class="chip bg-slate-100 text-slate-700">{{ contextTurnLabel(turn, index) }}</span>
              </div>
              <p class="mt-3 text-sm font-semibold leading-6 text-slate-900">{{ turn.userMessage }}</p>
              <p class="mt-2 line-clamp-4 whitespace-pre-line text-sm leading-6 text-slate-600">
                {{ turn.agentAnswer }}
              </p>
            </article>
          </div>
        </article>
      </section>

      <section v-if="result.faqResult || result.compareResult" class="grid gap-5 xl:grid-cols-2">
        <article v-if="result.faqResult" class="rounded-[28px] bg-slate-50 p-5">
          <p class="text-sm font-semibold text-slate-800">FAQ 命中结果</p>
          <div class="mt-4 flex flex-wrap gap-2">
            <span class="chip bg-sky-100 text-sky-800">{{ result.faqResult.sourceLabel }}</span>
            <span class="chip bg-slate-100 text-slate-700">
              citations: {{ result.faqResult.citations.length }}
            </span>
          </div>
          <p class="mt-4 whitespace-pre-line text-sm leading-7 text-slate-700">
            {{ result.faqResult.answer }}
          </p>

          <div v-if="result.faqResult.citations.length" class="mt-4 space-y-3">
            <article
              v-for="citation in result.faqResult.citations"
              :key="citation.entryId + '-' + citation.title"
              class="rounded-2xl bg-white p-4"
            >
              <p class="text-sm font-semibold text-slate-900">{{ citation.title }}</p>
              <p class="mt-2 text-sm leading-6 text-slate-600">{{ citation.snippet }}</p>
            </article>
          </div>

          <div v-if="result.faqResult.suggestions.length" class="mt-4 flex flex-wrap gap-2">
            <span
              v-for="item in result.faqResult.suggestions"
              :key="item"
              class="chip bg-violet-100 text-violet-800"
            >
              {{ item }}
            </span>
          </div>
        </article>

        <article v-if="result.compareResult" class="rounded-[28px] bg-slate-50 p-5">
          <p class="text-sm font-semibold text-slate-800">商品对比结果</p>
          <div class="mt-4 flex flex-wrap gap-2">
            <span class="chip bg-emerald-100 text-emerald-800">
              {{ result.compareResult.compared_products.length }} 件商品
            </span>
            <span class="chip bg-slate-100 text-slate-700">
              价差: CNY {{ result.compareResult.price_gap }}
            </span>
          </div>
          <p class="mt-4 whitespace-pre-line text-sm leading-7 text-slate-700">
            {{ result.compareResult.summary }}
          </p>
          <div v-if="result.compareResult.highlights.length" class="mt-4 flex flex-wrap gap-2">
            <span
              v-for="item in result.compareResult.highlights"
              :key="item"
              class="chip bg-amber-100 text-amber-800"
            >
              {{ item }}
            </span>
          </div>
        </article>
      </section>

      <section class="rounded-[28px] bg-slate-50 p-5">
        <div class="flex items-center justify-between gap-3">
          <div>
            <p class="text-sm font-semibold text-slate-800">工具调用详情</p>
            <p class="mt-1 text-sm leading-6 text-slate-600">
              用于回看本次运行依次调用了哪些工具、每一步状态如何，以及输入输出载荷是否合理。
            </p>
          </div>
          <span class="chip bg-violet-100 text-violet-800">
            {{ result.toolCalls.length }} 次调用
          </span>
        </div>

        <div v-if="result.toolCalls.length" class="mt-4 space-y-3">
          <article
            v-for="(toolCall, index) in result.toolCalls"
            :key="toolCall.toolName + '-' + index"
            class="rounded-2xl bg-white p-4"
          >
            <div class="flex flex-wrap items-center gap-2">
              <span class="chip bg-slate-100 text-slate-700">#{{ index + 1 }}</span>
              <span class="chip bg-sky-100 text-sky-800">{{ toolCall.toolName }}</span>
              <span class="chip bg-amber-100 text-amber-800">{{ toolCall.status }}</span>
            </div>

            <p class="mt-3 text-sm leading-7 text-slate-700">{{ toolCall.summary }}</p>

            <details v-if="hasPayload(toolCall)" class="mt-3 rounded-2xl bg-slate-50 p-4">
              <summary class="cursor-pointer text-sm font-medium text-slate-700">
                查看输入输出载荷
              </summary>

              <div class="mt-4 grid gap-4 xl:grid-cols-2">
                <div>
                  <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Input</p>
                  <pre class="mt-2 overflow-x-auto rounded-2xl bg-white p-3 text-xs leading-6 text-slate-700">{{ formatJson(toolCall.inputPayload) }}</pre>
                </div>

                <div>
                  <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Output</p>
                  <pre class="mt-2 overflow-x-auto rounded-2xl bg-white p-3 text-xs leading-6 text-slate-700">{{ formatJson(toolCall.outputPayload) }}</pre>
                </div>
              </div>
            </details>
          </article>
        </div>

        <p v-else class="mt-4 text-sm leading-6 text-slate-500">
          本次运行没有记录工具调用。
        </p>
      </section>
    </div>
  </section>
</template>

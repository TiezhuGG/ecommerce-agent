<script setup lang="ts">
import { computed, ref } from "vue";

import type { AgentConversationTurn, AgentResult, AgentRoute } from "../types/agent";

const props = defineProps<{
  result: AgentResult | null;
  loading: boolean;
  errorMessage: string;
  currentThreadId: string | null;
  conversationContext: AgentConversationTurn[];
  showDevDetails: boolean;
}>();

const emit = defineEmits<{
  submit: [query: string];
  applyFilters: [];
  applyFaq: [];
  applyCompare: [];
  clearConversation: [];
}>();

const prompt = ref("帮我推荐 2000 元以内、适合通勤和开会的蓝牙耳机，优先考虑降噪和佩戴舒适。");
const starterPrompts = [
  "预算 3000 元左右，想买一台适合 MacBook 办公的显示器，优先轻薄和护眼。",
  "帮我推荐适合出差的蓝牙耳机，预算 1500 元以内，重点看降噪和佩戴舒适。",
  "家里客厅想买一台电视，预算 5000 元左右，主要看电影和游戏体验。",
];

const usedConversationContext = computed(
  () => props.result?.conversationContext ?? props.conversationContext,
);

const currentThreadState = computed(() => props.result?.threadState ?? null);

const rememberedFilters = computed(() => {
  const state = currentThreadState.value;
  if (!state?.searchFilters) {
    return [] as string[];
  }

  const items: string[] = [];
  if (state.searchFilters.category) {
    items.push(`分类: ${state.searchFilters.category}`);
  }
  if (state.searchFilters.brand) {
    items.push(`品牌: ${state.searchFilters.brand}`);
  }
  if (state.searchFilters.maxPrice !== null) {
    items.push(`预算上限: CNY ${state.searchFilters.maxPrice}`);
  }
  if (state.searchFilters.keyword) {
    items.push(`关键词: ${state.searchFilters.keyword}`);
  }
  return items;
});

function submitPrompt() {
  const query = prompt.value.trim();
  if (!query) {
    return;
  }

  emit("submit", query);
}

function formatRoute(route: AgentRoute | ""): string {
  if (route === "shopping") {
    return "商品推荐";
  }
  if (route === "faq") {
    return "售前问答";
  }
  if (route === "compare") {
    return "商品对比";
  }
  return "未分类";
}
</script>

<template>
  <section class="panel p-6">
    <div class="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
      <div class="max-w-3xl">
        <p class="text-sm font-semibold uppercase tracking-[0.24em] text-amber-700">
          AI Guide
        </p>
        <h2 class="mt-3 text-2xl font-semibold text-ink">告诉 AI 你的需求</h2>
        <p class="mt-3 text-sm leading-7 text-slate-600">
          直接描述预算、使用场景和偏好，或者基于上一轮结果继续追问，比如“换个品牌”“预算放宽一点”或“把刚才那两款再比较一下”。
        </p>
      </div>
      <span class="chip bg-violet-100 text-violet-800">支持连续追问</span>
    </div>

    <div class="mt-5 rounded-3xl bg-slate-50 p-5">
      <div class="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p class="text-sm font-semibold text-slate-800">当前会话</p>
          <p class="mt-2 text-sm leading-7 text-slate-600">
            系统会自动带上最近几轮上下文，适合连续追问，不需要每次都把前情重新说一遍。
          </p>
        </div>

        <div class="flex flex-wrap items-center gap-2">
          <span v-if="currentThreadId" class="chip bg-emerald-100 text-emerald-800">
            会话进行中
          </span>
          <span class="chip bg-slate-100 text-slate-700">
            已记住 {{ usedConversationContext.length }} 轮
          </span>
          <button
            type="button"
            class="rounded-full border border-slate-200 px-4 py-2 text-sm text-slate-700 transition hover:border-slate-300 hover:bg-white disabled:cursor-not-allowed disabled:opacity-50"
            :disabled="!usedConversationContext.length"
            @click="emit('clearConversation')"
          >
            开始新会话
          </button>
        </div>
      </div>

      <div v-if="rememberedFilters.length" class="mt-4 flex flex-wrap gap-2">
        <span
          v-for="item in rememberedFilters"
          :key="item"
          class="chip bg-amber-100 text-amber-800"
        >
          {{ item }}
        </span>
      </div>

      <div
        v-if="usedConversationContext.length"
        class="mt-4 max-h-[320px] space-y-3 overflow-y-auto pr-1"
      >
        <article
          v-for="(turn, index) in usedConversationContext"
          :key="index + '-' + turn.userMessage"
          class="rounded-2xl border border-slate-200 bg-white p-4"
        >
          <div class="flex flex-wrap items-center gap-2">
            <span class="chip bg-slate-100 text-slate-700">第 {{ index + 1 }} 轮</span>
            <span v-if="turn.route" class="chip bg-emerald-100 text-emerald-800">
              {{ formatRoute(turn.route) }}
            </span>
          </div>
          <p class="mt-3 text-sm font-semibold leading-6 text-slate-900">{{ turn.userMessage }}</p>
          <p class="mt-2 line-clamp-3 whitespace-pre-line text-sm leading-7 text-slate-600">
            {{ turn.agentAnswer }}
          </p>
        </article>
      </div>

      <div
        v-else
        class="mt-4 rounded-2xl border border-dashed border-slate-300 bg-white px-4 py-8 text-center text-sm text-slate-600"
      >
        还没有历史上下文。直接输入你的需求就可以开始。
      </div>
    </div>

    <textarea
      v-model="prompt"
      rows="5"
      class="field-input mt-6 resize-none"
      placeholder="例如: 给我找一款适合 MacBook 办公、预算 3000 元左右、最好轻一点的显示器。"
      @keydown.ctrl.enter="submitPrompt"
    />

    <div class="mt-4 flex flex-wrap gap-3">
      <button
        type="button"
        class="rounded-full bg-amber-500 px-5 py-2.5 text-sm font-medium text-white transition hover:bg-amber-600 disabled:cursor-wait disabled:opacity-70"
        :disabled="loading"
        @click="submitPrompt"
      >
        {{ loading ? "AI 正在整理建议..." : "让 AI 开始推荐" }}
      </button>
      <span class="chip bg-slate-100 text-slate-700">支持 Ctrl + Enter 快速提交</span>
    </div>

    <div
      v-if="errorMessage"
      class="mt-6 rounded-3xl border border-rose-200 bg-rose-50 p-5"
    >
      <span class="chip bg-rose-100 text-rose-700">本次推荐没有成功</span>
      <p class="mt-4 text-lg font-semibold text-rose-900">AI 暂时没能完成这次整理</p>
      <p class="mt-3 text-sm leading-7 text-rose-800">
        你可以先把需求写得更具体一点，比如补充预算、使用场景或品牌偏好，再试一次。
      </p>
      <p class="mt-4 rounded-2xl bg-white/80 px-4 py-3 text-sm text-rose-700">
        {{ errorMessage }}
      </p>
    </div>

    <div
      v-else-if="loading && !result"
      class="mt-6 rounded-3xl border border-amber-200 bg-amber-50 p-5"
    >
      <div class="flex flex-wrap items-center gap-2">
        <span class="chip bg-amber-100 text-amber-800">AI 正在整理建议</span>
        <span class="chip bg-white text-slate-700">通常只需要几秒</span>
      </div>

      <p class="mt-4 text-lg font-semibold text-amber-950">正在理解你的需求并筛选候选商品</p>
      <div class="mt-4 grid gap-3 sm:grid-cols-3">
        <article class="rounded-3xl bg-white/90 p-4">
          <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">步骤 1</p>
          <p class="mt-2 text-sm font-semibold text-slate-900">提取预算、场景和偏好重点</p>
        </article>
        <article class="rounded-3xl bg-white/90 p-4">
          <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">步骤 2</p>
          <p class="mt-2 text-sm font-semibold text-slate-900">匹配商品事实和可用知识</p>
        </article>
        <article class="rounded-3xl bg-white/90 p-4">
          <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">步骤 3</p>
          <p class="mt-2 text-sm font-semibold text-slate-900">生成推荐理由和下一步建议</p>
        </article>
      </div>
    </div>

    <div v-else-if="result" class="mt-6 space-y-5">
      <div class="rounded-3xl bg-slate-50 p-5">
        <div class="flex flex-wrap gap-2">
          <span class="chip bg-emerald-100 text-emerald-800">
            本次任务: {{ formatRoute(result.route) }}
          </span>
          <span
            class="chip"
            :class="result.origin === 'history' ? 'bg-slate-100 text-slate-700' : 'bg-emerald-100 text-emerald-800'"
          >
            {{ result.origin === "history" ? "来自历史记录" : "本次最新结果" }}
          </span>
          <span v-if="result.threadId" class="chip bg-sky-100 text-sky-800">
            可继续追问
          </span>
        </div>

        <div class="mt-5">
          <p class="text-sm font-semibold text-slate-700">AI 给你的建议</p>
          <p class="mt-2 whitespace-pre-line text-sm leading-7 text-slate-700">
            {{ result.finalAnswer }}
          </p>
        </div>
      </div>

      <div v-if="result.parsedIntent" class="rounded-3xl bg-slate-50 p-5">
        <p class="text-sm font-semibold text-slate-700">AI 理解到的需求</p>

        <div v-if="result.parsedIntent.appliedFilters.length" class="mt-4 flex flex-wrap gap-2">
          <span
            v-for="item in result.parsedIntent.appliedFilters"
            :key="item"
            class="chip bg-sky-100 text-sky-800"
          >
            {{ item }}
          </span>
        </div>

        <p v-if="result.parsedIntent.scenario" class="mt-4 text-sm leading-7 text-slate-700">
          使用场景: {{ result.parsedIntent.scenario }}
        </p>

        <div v-if="result.parsedIntent.priorities.length" class="mt-4 flex flex-wrap gap-2">
          <span
            v-for="item in result.parsedIntent.priorities"
            :key="item"
            class="chip bg-violet-100 text-violet-800"
          >
            {{ item }}
          </span>
        </div>

        <p class="mt-4 text-sm leading-7 text-slate-700">
          {{ result.parsedIntent.reasoningSummary }}
        </p>

        <div class="mt-4">
          <button
            type="button"
            class="rounded-full border border-sky-200 px-4 py-2 text-sm text-sky-700 transition hover:bg-sky-50"
            @click="emit('applyFilters')"
          >
            把这些条件同步到筛选区
          </button>
        </div>
      </div>

      <div
        v-if="result.faqResult"
        class="rounded-3xl border border-sky-200 bg-sky-50/70 p-5"
      >
        <div class="flex flex-wrap items-center gap-2">
          <span class="chip bg-sky-100 text-sky-800">已查到售前答案</span>
          <span class="chip bg-emerald-100 text-emerald-800">
            {{ result.faqResult.sourceLabel }}
          </span>
        </div>

        <p class="mt-4 text-sm font-semibold text-slate-700">答案摘要</p>
        <p class="mt-2 whitespace-pre-line text-sm leading-7 text-slate-700">
          {{ result.faqResult.answer }}
        </p>

        <div class="mt-4">
          <button
            type="button"
            class="rounded-full border border-sky-200 px-4 py-2 text-sm text-sky-700 transition hover:bg-sky-50"
            @click="emit('applyFaq')"
          >
            同步到售前问答区
          </button>
        </div>
      </div>

      <div
        v-if="result.compareResult"
        class="rounded-3xl border border-emerald-200 bg-emerald-50/70 p-5"
      >
        <div class="flex flex-wrap items-center gap-2">
          <span class="chip bg-emerald-100 text-emerald-800">已生成商品对比</span>
          <span class="chip bg-slate-100 text-slate-700">
            {{ result.compareResult.compared_products.length }} 件商品
          </span>
        </div>

        <p class="mt-4 text-sm font-semibold text-slate-700">对比摘要</p>
        <p class="mt-2 whitespace-pre-line text-sm leading-7 text-slate-700">
          {{ result.compareResult.summary }}
        </p>

        <div class="mt-4">
          <button
            type="button"
            class="rounded-full border border-emerald-200 px-4 py-2 text-sm text-emerald-700 transition hover:bg-emerald-50"
            @click="emit('applyCompare')"
          >
            同步到对比区
          </button>
        </div>
      </div>

      <div v-if="result.warnings.length" class="rounded-3xl bg-amber-50 p-5">
        <p class="text-sm font-semibold text-amber-900">本次提醒</p>
        <div class="mt-3 flex flex-wrap gap-2">
          <span
            v-for="warning in result.warnings"
            :key="warning"
            class="chip bg-amber-100 text-amber-800"
          >
            {{ warning }}
          </span>
        </div>
      </div>

      <details v-if="showDevDetails" class="rounded-3xl bg-slate-50 p-5">
        <summary class="cursor-pointer text-sm font-semibold text-slate-700">
          查看分析过程与详细信息
        </summary>

        <div class="mt-5 space-y-5">
          <div class="flex flex-wrap gap-2">
            <span class="chip bg-slate-100 text-slate-700">route: {{ result.route }}</span>
            <span class="chip bg-sky-100 text-sky-800">{{ result.provider }}</span>
            <span class="chip bg-amber-100 text-amber-800">{{ result.model }}</span>
            <span class="chip bg-violet-100 text-violet-800">{{ result.graphRuntime }}</span>
            <span
              class="chip"
              :class="result.persisted ? 'bg-emerald-100 text-emerald-800' : 'bg-slate-100 text-slate-700'"
            >
              {{ result.persisted ? "已持久化" : "未持久化" }}
            </span>
          </div>

          <div v-if="result.runId || result.createdAt" class="rounded-2xl bg-white p-4">
            <p class="text-sm font-semibold text-slate-700">运行信息</p>
            <p v-if="result.runId" class="mt-2 text-sm text-slate-600">run_id: {{ result.runId }}</p>
            <p v-if="result.createdAt" class="mt-1 text-sm text-slate-600">
              created_at: {{ result.createdAt }}
            </p>
          </div>

          <div v-if="currentThreadState" class="rounded-2xl bg-white p-4">
            <p class="text-sm font-semibold text-slate-700">线程状态快照</p>
            <div class="mt-3 flex flex-wrap gap-2">
              <span v-if="currentThreadState.lastRoute" class="chip bg-slate-100 text-slate-700">
                last_route: {{ currentThreadState.lastRoute }}
              </span>
              <span v-if="currentThreadState.lastRunId" class="chip bg-slate-100 text-slate-700">
                last_run: {{ currentThreadState.lastRunId }}
              </span>
              <span
                v-for="item in rememberedFilters"
                :key="'remembered-' + item"
                class="chip bg-amber-100 text-amber-800"
              >
                {{ item }}
              </span>
            </div>

            <div v-if="currentThreadState.candidateProductIds.length" class="mt-4">
              <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
                Candidate Products
              </p>
              <div class="mt-2 flex flex-wrap gap-2">
                <span
                  v-for="productId in currentThreadState.candidateProductIds"
                  :key="'thread-candidate-' + productId"
                  class="chip bg-violet-100 text-violet-800"
                >
                  {{ productId }}
                </span>
              </div>
            </div>
          </div>

          <div v-if="usedConversationContext.length" class="rounded-2xl bg-white p-4">
            <p class="text-sm font-semibold text-slate-700">本次参考的会话上下文</p>
            <div class="mt-4 space-y-3">
              <article
                v-for="(turn, index) in usedConversationContext"
                :key="turn.userMessage + '-' + index"
                class="rounded-2xl border border-slate-200 bg-slate-50 p-4"
              >
                <div class="flex flex-wrap items-center gap-2">
                  <span class="chip bg-slate-100 text-slate-700">第 {{ index + 1 }} 轮</span>
                  <span v-if="turn.route" class="chip bg-emerald-100 text-emerald-800">
                    {{ formatRoute(turn.route) }}
                  </span>
                </div>
                <p class="mt-3 text-sm font-semibold leading-6 text-slate-900">
                  {{ turn.userMessage }}
                </p>
                <p class="mt-2 line-clamp-3 whitespace-pre-line text-sm leading-7 text-slate-600">
                  {{ turn.agentAnswer }}
                </p>
              </article>
            </div>
          </div>

          <div
            v-if="result.recommendedProductIds.length || result.selectedProductIds.length"
            class="rounded-2xl bg-white p-4"
          >
            <p class="text-sm font-semibold text-slate-700">商品 ID 轨迹</p>

            <div v-if="result.recommendedProductIds.length" class="mt-3">
              <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
                Recommended
              </p>
              <div class="mt-2 flex flex-wrap gap-2">
                <span
                  v-for="productId in result.recommendedProductIds"
                  :key="productId"
                  class="chip bg-amber-100 text-amber-800"
                >
                  {{ productId }}
                </span>
              </div>
            </div>

            <div v-if="result.selectedProductIds.length" class="mt-4">
              <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
                Selected
              </p>
              <div class="mt-2 flex flex-wrap gap-2">
                <span
                  v-for="productId in result.selectedProductIds"
                  :key="'selected-' + productId"
                  class="chip bg-sky-100 text-sky-800"
                >
                  {{ productId }}
                </span>
              </div>
            </div>
          </div>

          <div v-if="result.toolCalls.length" class="rounded-2xl bg-white p-4">
            <p class="text-sm font-semibold text-slate-700">工具调用摘要</p>
            <div class="mt-4 space-y-3">
              <article
                v-for="(toolCall, index) in result.toolCalls"
                :key="toolCall.toolName + '-' + index"
                class="rounded-2xl border border-slate-200 bg-slate-50 p-4"
              >
                <div class="flex flex-wrap gap-2">
                  <span class="chip bg-slate-100 text-slate-700">#{{ index + 1 }}</span>
                  <span class="chip bg-sky-100 text-sky-800">{{ toolCall.toolName }}</span>
                  <span class="chip bg-amber-100 text-amber-800">{{ toolCall.status }}</span>
                </div>
                <p class="mt-3 text-sm leading-7 text-slate-700">{{ toolCall.summary }}</p>
              </article>
            </div>
          </div>
        </div>
      </details>
    </div>

    <div
      v-else
      class="mt-6 rounded-3xl border border-dashed border-slate-300 bg-slate-50 p-6"
    >
      <span class="chip bg-slate-100 text-slate-700">还没有生成推荐</span>
      <h3 class="mt-4 text-2xl font-semibold text-ink">先把你的需求告诉 AI</h3>
      <p class="mt-3 max-w-3xl text-sm leading-7 text-slate-600">
        写得越接近真实购买场景，AI 给出的推荐就越实用。你可以直接说明预算、用途、在意的参数，
        也可以先点下面的示例句式，再按自己的需要改一改。
      </p>

      <div class="mt-5 grid gap-3 lg:grid-cols-3">
        <button
          v-for="item in starterPrompts"
          :key="item"
          type="button"
          class="rounded-3xl border border-slate-200 bg-white p-4 text-left transition hover:border-slate-300 hover:bg-slate-50"
          @click="prompt = item"
        >
          <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
            示例问法
          </p>
          <p class="mt-3 text-sm leading-7 text-slate-800">{{ item }}</p>
        </button>
      </div>
    </div>
  </section>
</template>

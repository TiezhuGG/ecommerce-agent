<script setup lang="ts">
import { ref } from "vue";

import type { AgentResult } from "../types/agent";

defineProps<{
  result: AgentResult | null;
  loading: boolean;
  errorMessage: string;
}>();

const emit = defineEmits<{
  submit: [query: string];
  applyFilters: [];
  applyFaq: [];
  applyCompare: [];
}>();

const prompt = ref(
  "帮我推荐 2000 元以内、适合通勤和开会的蓝牙耳机，优先考虑降噪和佩戴舒适。",
);

function submitPrompt() {
  const query = prompt.value.trim();
  if (!query) {
    return;
  }

  emit("submit", query);
}
</script>

<template>
  <section class="panel p-6">
    <div class="flex items-start justify-between gap-4">
      <div>
        <h2 class="panel-title">Agent 工作台</h2>
        <p class="muted-copy mt-2">
          这里是统一的 Agent 入口。你输入一句自然语言后，后端会先做路由判断，再按场景调用商品搜索、知识库问答、商品对比等工具，
          最后把执行轨迹和结果一起返回给前端。当前工作台默认只展示 Agent 结果，不会自动改写搜索、FAQ 或对比面板。
        </p>
      </div>
      <span class="chip bg-violet-100 text-violet-800">LangGraph 单 Agent</span>
    </div>

    <textarea
      v-model="prompt"
      rows="5"
      class="field-input mt-6 resize-none"
      placeholder="例如：对比一下 Sony WF-1000XM5 和 Apple AirPods Pro 2，看谁更适合通勤。"
      @keydown.ctrl.enter="submitPrompt"
    />

    <div class="mt-4 flex flex-wrap gap-3">
      <button
        type="button"
        class="rounded-full bg-amber-500 px-5 py-2.5 text-sm font-medium text-white transition hover:bg-amber-600 disabled:cursor-wait disabled:opacity-70"
        :disabled="loading"
        @click="submitPrompt"
      >
        {{ loading ? "Agent 执行中..." : "提交给 Agent" }}
      </button>
      <span class="chip bg-slate-100 text-slate-700">支持 Ctrl + Enter 快速提交</span>
    </div>

    <p
      v-if="errorMessage"
      class="mt-4 rounded-2xl bg-rose-50 px-4 py-3 text-sm text-rose-700"
    >
      Agent 执行失败：{{ errorMessage }}
    </p>

    <div v-else-if="result" class="mt-6 space-y-5">
      <div class="rounded-3xl bg-slate-50 p-5">
        <div class="flex flex-wrap gap-2">
          <span class="chip bg-emerald-100 text-emerald-800">路由：{{ result.route }}</span>
          <span
            class="chip"
            :class="result.origin === 'history' ? 'bg-slate-100 text-slate-700' : 'bg-emerald-100 text-emerald-800'"
          >
            {{ result.origin === "history" ? "历史运行详情" : "当前运行结果" }}
          </span>
          <span class="chip bg-sky-100 text-sky-800">{{ result.provider }}</span>
          <span class="chip bg-amber-100 text-amber-800">{{ result.model }}</span>
          <span class="chip bg-violet-100 text-violet-800">{{ result.graphRuntime }}</span>
          <span
            class="chip"
            :class="result.persisted ? 'bg-emerald-100 text-emerald-800' : 'bg-slate-100 text-slate-700'"
          >
            {{ result.persisted ? "日志已持久化" : "日志未持久化" }}
          </span>
        </div>

        <p v-if="result.runId" class="mt-3 text-xs text-slate-500">run_id：{{ result.runId }}</p>
        <p v-if="result.createdAt" class="mt-2 text-xs text-slate-500">
          创建时间：{{ result.createdAt }}
        </p>

        <div class="mt-5">
          <p class="text-sm font-semibold text-slate-700">最终回答</p>
          <p class="mt-2 whitespace-pre-line text-sm leading-7 text-slate-700">
            {{ result.finalAnswer }}
          </p>
        </div>

        <div class="mt-5">
          <p class="text-sm font-semibold text-slate-700">为什么走这条路由</p>
          <p class="mt-2 text-sm leading-7 text-slate-700">{{ result.routeReasoning }}</p>
        </div>

        <div class="mt-5">
          <p class="text-sm font-semibold text-slate-700">阶段来源</p>
          <div class="mt-3 flex flex-wrap gap-2">
            <span v-if="result.providers.routeProvider" class="chip bg-slate-100 text-slate-700">
              route：{{ result.providers.routeProvider }}
            </span>
            <span v-if="result.providers.intentProvider" class="chip bg-sky-100 text-sky-800">
              intent：{{ result.providers.intentProvider }}
            </span>
            <span v-if="result.providers.answerProvider" class="chip bg-amber-100 text-amber-800">
              answer：{{ result.providers.answerProvider }}
            </span>
            <span
              v-if="result.providers.retrievalProvider"
              class="chip bg-violet-100 text-violet-800"
            >
              retrieval：{{ result.providers.retrievalProvider }}
            </span>
          </div>
        </div>

        <div v-if="result.recommendedProductIds.length" class="mt-5">
          <p class="text-sm font-semibold text-slate-700">推荐商品 ID</p>
          <div class="mt-3 flex flex-wrap gap-2">
            <span
              v-for="productId in result.recommendedProductIds"
              :key="productId"
              class="chip bg-amber-100 text-amber-800"
            >
              {{ productId }}
            </span>
          </div>
        </div>

        <div v-if="result.selectedProductIds.length" class="mt-5">
          <p class="text-sm font-semibold text-slate-700">本轮携带的已选商品</p>
          <div class="mt-3 flex flex-wrap gap-2">
            <span
              v-for="productId in result.selectedProductIds"
              :key="`selected-${productId}`"
              class="chip bg-slate-100 text-slate-700"
            >
              {{ productId }}
            </span>
          </div>
        </div>
      </div>

      <div v-if="result.warnings.length" class="rounded-3xl bg-amber-50 p-5">
        <p class="text-sm font-semibold text-amber-900">执行警告</p>
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

      <div v-if="result.parsedIntent" class="rounded-3xl bg-slate-50 p-5">
        <p class="text-sm font-semibold text-slate-700">意图解析结果</p>
        <p class="mt-2 text-sm leading-7 text-slate-600">
          这一块展示的是 Agent 在导购场景下调用意图解析工具后得到的结构化条件。
          它的意义不是直接给用户看，而是把自然语言翻译成系统可执行的筛选参数。
        </p>

        <div class="mt-4 flex flex-wrap gap-2">
          <span
            v-for="item in result.parsedIntent.appliedFilters"
            :key="item"
            class="chip bg-sky-100 text-sky-800"
          >
            {{ item }}
          </span>
        </div>

        <p v-if="result.parsedIntent.scenario" class="mt-4 text-sm text-slate-700">
          使用场景：{{ result.parsedIntent.scenario }}
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
            应用到搜索筛选区
          </button>
        </div>
      </div>

      <div
        v-if="result.faqResult"
        class="rounded-3xl border border-sky-200 bg-sky-50/70 p-5"
      >
        <div class="flex flex-wrap items-center gap-2">
          <span class="chip bg-sky-100 text-sky-800">知识库结果可同步</span>
          <span class="chip bg-violet-100 text-violet-800">
            {{ result.faqResult.retrievalMode }}
          </span>
          <span class="chip bg-slate-100 text-slate-700">
            {{ result.faqResult.retrievalProvider }}
          </span>
          <span class="chip bg-amber-100 text-amber-800">
            {{ result.faqResult.answerProvider }}
          </span>
          <span class="chip bg-emerald-100 text-emerald-800">
            {{ result.faqResult.sourceLabel }}
          </span>
        </div>

        <p class="mt-4 text-sm font-semibold text-slate-700">知识库回答</p>
        <p class="mt-2 whitespace-pre-line text-sm leading-7 text-slate-700">
          {{ result.faqResult.answer }}
        </p>

        <div v-if="result.faqResult.citations.length" class="mt-4 grid gap-3">
          <article
            v-for="citation in result.faqResult.citations"
            :key="`${citation.entryId}-${citation.title}`"
            class="rounded-2xl border border-sky-200 bg-white p-4"
          >
            <div class="flex flex-wrap gap-2">
              <span class="chip bg-slate-100 text-slate-700">{{ citation.title }}</span>
              <span class="chip bg-amber-100 text-amber-800">
                得分：{{ citation.score.toFixed(2) }}
              </span>
            </div>
            <p class="mt-2 text-sm text-slate-600">{{ citation.sourceLabel }}</p>
            <p class="mt-3 whitespace-pre-line text-sm leading-7 text-slate-700">
              {{ citation.snippet }}
            </p>
          </article>
        </div>

        <div class="mt-4">
          <button
            type="button"
            class="rounded-full border border-sky-200 px-4 py-2 text-sm text-sky-700 transition hover:bg-sky-50"
            @click="emit('applyFaq')"
          >
            同步到知识库面板
          </button>
        </div>
      </div>

      <div
        v-if="result.compareResult"
        class="rounded-3xl border border-emerald-200 bg-emerald-50/70 p-5"
      >
        <div class="flex flex-wrap items-center gap-2">
          <span class="chip bg-emerald-100 text-emerald-800">商品对比结果可应用</span>
          <span class="chip bg-slate-100 text-slate-700">
            {{ result.compareResult.compared_products.length }} 个商品
          </span>
          <span class="chip bg-amber-100 text-amber-800">
            价差：￥{{ result.compareResult.price_gap }}
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
            同步到对比面板
          </button>
        </div>
      </div>

      <div class="rounded-3xl bg-slate-50 p-5">
        <p class="text-sm font-semibold text-slate-700">工具调用轨迹</p>
        <div class="mt-4 grid gap-3">
          <article
            v-for="toolCall in result.toolCalls"
            :key="`${toolCall.toolName}-${toolCall.summary}`"
            class="rounded-2xl border border-slate-200 bg-white p-4"
          >
            <div class="flex flex-wrap items-center gap-2">
              <span class="chip bg-slate-100 text-slate-700">{{ toolCall.toolName }}</span>
              <span
                class="chip"
                :class="
                  toolCall.status === 'completed'
                    ? 'bg-emerald-100 text-emerald-800'
                    : toolCall.status === 'failed'
                      ? 'bg-rose-100 text-rose-700'
                      : 'bg-amber-100 text-amber-800'
                "
              >
                {{ toolCall.status }}
              </span>
            </div>

            <p class="mt-3 text-sm leading-7 text-slate-700">{{ toolCall.summary }}</p>

            <div class="mt-3 grid gap-3 md:grid-cols-2">
              <div>
                <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
                  输入
                </p>
                <pre class="mt-2 overflow-x-auto rounded-2xl bg-slate-50 p-3 text-xs text-slate-600">{{
                  JSON.stringify(toolCall.inputPayload, null, 2)
                }}</pre>
              </div>
              <div>
                <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
                  输出
                </p>
                <pre class="mt-2 overflow-x-auto rounded-2xl bg-slate-50 p-3 text-xs text-slate-600">{{
                  JSON.stringify(toolCall.outputPayload, null, 2)
                }}</pre>
              </div>
            </div>
          </article>
        </div>
      </div>
    </div>
  </section>
</template>

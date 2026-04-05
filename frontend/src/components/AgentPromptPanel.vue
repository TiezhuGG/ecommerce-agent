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
}>();

const prompt = ref("帮我推荐 2000 元以内、适合通勤和开会的蓝牙耳机，优先考虑降噪和佩戴舒适。");

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
          这里已经不只是“意图解析演示框”了，而是统一的 Agent 工作台。
          你输入一句自然语言后，后端会先做路由判断，再按场景去调用商品搜索、FAQ、商品对比等工具，
          最后把执行结果组织成一段可直接展示给用户的话。
        </p>
      </div>
      <span class="chip bg-violet-100 text-violet-800">LangGraph 单 Agent</span>
    </div>

    <textarea
      v-model="prompt"
      rows="5"
      class="field-input mt-6 resize-none"
      placeholder="例如：对比一下 Sony WF-1000XM5 和 Apple AirPods Pro 2，看看谁更适合我通勤。"
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
          <span class="chip bg-sky-100 text-sky-800">{{ result.provider }}</span>
          <span class="chip bg-amber-100 text-amber-800">{{ result.model }}</span>
          <span class="chip bg-violet-100 text-violet-800">{{ result.graphRuntime }}</span>
        </div>

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
          这部分展示的是 Agent 在导购场景下调用意图解析工具后得到的结构化条件。
          它的作用不是直接展示给用户，而是把自然语言翻译成系统可执行的筛选参数。
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

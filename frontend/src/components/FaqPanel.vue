<script setup lang="ts">
import { ref, watch } from "vue";

import type { FaqAskResult } from "../types/faq";

const props = defineProps<{
  suggestedQuestions: string[];
  result: FaqAskResult | null;
  loading: boolean;
  errorMessage: string;
}>();

const emit = defineEmits<{
  submit: [question: string];
}>();

const question = ref(props.suggestedQuestions[0] ?? "");

watch(
  () => props.suggestedQuestions,
  (next) => {
    if (!question.value && next.length) {
      question.value = next[0];
    }
  },
  { immediate: true },
);

function submitFaq() {
  if (!question.value.trim()) {
    return;
  }

  emit("submit", question.value.trim());
}
</script>

<template>
  <section class="panel p-6">
    <div class="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
      <div>
        <h2 class="panel-title">售前问答</h2>
        <p class="muted-copy mt-2 max-w-3xl">
          发票、发货、质保、退换货、企业采购等问题，统一在这里问。你也可以先点左侧常见问题，再按需追问。
        </p>
      </div>
      <span class="chip bg-sky-100 text-sky-800">知识库检索</span>
    </div>

    <div class="mt-6 grid gap-4 xl:grid-cols-[0.88fr_1.12fr]">
      <div class="space-y-3">
        <button
          v-for="item in suggestedQuestions"
          :key="item"
          type="button"
          class="w-full rounded-2xl border border-slate-200 bg-white px-4 py-4 text-left transition hover:border-slate-300 hover:bg-slate-50"
          @click="question = item"
        >
          <p class="text-sm font-medium text-slate-900">{{ item }}</p>
        </button>
      </div>

      <div class="rounded-3xl bg-slate-50 p-5">
        <label class="field-label">输入售前问题</label>
        <textarea
          v-model="question"
          rows="4"
          class="field-input resize-none"
          placeholder="例如：企业采购可以开专票吗？保修期多久？"
        />

        <button
          type="button"
          class="mt-4 rounded-full bg-ink px-5 py-2.5 text-sm font-medium text-white transition hover:bg-slate-800 disabled:cursor-wait disabled:opacity-70"
          :disabled="loading"
          @click="submitFaq"
        >
          {{ loading ? "正在查询..." : "查询答案" }}
        </button>

        <p
          v-if="errorMessage"
          class="mt-4 rounded-2xl bg-rose-50 px-4 py-3 text-sm text-rose-700"
        >
          查询失败：{{ errorMessage }}
        </p>

        <div v-else-if="result" class="mt-6 space-y-5">
          <div>
            <p class="text-sm font-semibold text-slate-700">你的问题</p>
            <p class="mt-2 text-base text-slate-900">{{ result.question }}</p>
          </div>

          <div>
            <p class="text-sm font-semibold text-slate-700">答案</p>
            <p class="mt-2 whitespace-pre-line text-sm leading-7 text-slate-700">
              {{ result.answer }}
            </p>
          </div>

          <div class="flex flex-wrap gap-2">
            <span class="chip bg-sky-100 text-sky-800">来源：{{ result.sourceLabel }}</span>
            <span
              v-if="result.matchedEntry"
              class="chip bg-emerald-100 text-emerald-800"
            >
              主题：{{ result.matchedEntry.topic }}
            </span>
          </div>

          <div v-if="result.citations.length" class="rounded-3xl bg-white p-4">
            <p class="text-sm font-semibold text-slate-700">命中的知识片段</p>
            <div class="mt-4 grid gap-3">
              <article
                v-for="citation in result.citations"
                :key="`${citation.entryId}-${citation.title}-${citation.score}`"
                class="rounded-2xl border border-slate-200 bg-slate-50 p-4"
              >
                <div class="flex flex-wrap items-center gap-2">
                  <span class="chip bg-slate-100 text-slate-700">{{ citation.title }}</span>
                  <span class="chip bg-sky-100 text-sky-800">{{ citation.sourceLabel }}</span>
                </div>
                <p class="mt-3 whitespace-pre-line text-sm leading-7 text-slate-700">
                  {{ citation.snippet }}
                </p>
              </article>
            </div>
          </div>

          <div v-if="result.suggestions.length">
            <p class="text-sm font-semibold text-slate-700">你还可以继续问</p>
            <div class="mt-3 flex flex-wrap gap-2">
              <button
                v-for="item in result.suggestions"
                :key="item"
                type="button"
                class="chip bg-amber-100 text-amber-800"
                @click="question = item"
              >
                {{ item }}
              </button>
            </div>
          </div>

          <details class="rounded-3xl bg-white p-4">
            <summary class="cursor-pointer text-sm font-semibold text-slate-700">
              查看检索细节
            </summary>
            <div class="mt-4 flex flex-wrap gap-2">
              <span class="chip bg-violet-100 text-violet-800">
                检索模式：{{ result.retrievalMode }}
              </span>
              <span class="chip bg-slate-100 text-slate-700">
                检索来源：{{ result.retrievalProvider }}
              </span>
              <span class="chip bg-amber-100 text-amber-800">
                回答来源：{{ result.answerProvider }}
              </span>
            </div>
          </details>
        </div>
      </div>
    </div>
  </section>
</template>

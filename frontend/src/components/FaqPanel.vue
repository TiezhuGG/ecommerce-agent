<script setup lang="ts">
import { ref, watch } from "vue";

import type { FaqAskResponse } from "../api/contracts/faq";

const props = defineProps<{
  suggestedQuestions: string[];
  result: FaqAskResponse | null;
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
    <h2 class="panel-title">售前 FAQ 区</h2>
    <p class="muted-copy mt-2">
      这块已经接入真实后端接口。它和商品搜索一样，都是后续 Agent 可以调用的业务工具，
      只是它专门回答规则、政策和售前说明类问题。
    </p>

    <div class="mt-6 grid gap-4 xl:grid-cols-[0.9fr_1.1fr]">
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
          placeholder="例如：耳机进水还能保修吗？"
        />

        <button
          type="button"
          class="mt-4 rounded-full bg-ink px-5 py-2.5 text-sm font-medium text-white transition hover:bg-slate-800 disabled:cursor-wait disabled:opacity-70"
          :disabled="loading"
          @click="submitFaq"
        >
          {{ loading ? "查询中..." : "查询 FAQ" }}
        </button>

        <p
          v-if="errorMessage"
          class="mt-4 rounded-2xl bg-rose-50 px-4 py-3 text-sm text-rose-700"
        >
          FAQ 查询失败：{{ errorMessage }}
        </p>

        <div v-else-if="result" class="mt-6 space-y-4">
          <div>
            <p class="text-sm font-semibold text-slate-700">问题</p>
            <p class="mt-2 text-base text-slate-900">{{ result.question }}</p>
          </div>

          <div>
            <p class="text-sm font-semibold text-slate-700">答案</p>
            <p class="mt-2 text-sm leading-7 text-slate-700">{{ result.answer }}</p>
          </div>

          <div>
            <span class="chip bg-sky-100 text-sky-800">来源：{{ result.source_label }}</span>
          </div>

          <div v-if="result.suggestions.length">
            <p class="text-sm font-semibold text-slate-700">可继续追问</p>
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
        </div>
      </div>
    </div>
  </section>
</template>

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
    <div class="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
      <div class="max-w-3xl">
        <p class="text-sm font-semibold uppercase tracking-[0.24em] text-amber-700">
          FAQ
        </p>
        <h2 class="mt-3 text-2xl font-semibold text-ink">售前问答</h2>
        <p class="mt-3 text-sm leading-7 text-slate-600">
          发票、发货、质保、退换货、企业采购等问题统一在这里查询。你也可以先点左侧常见问题，再继续追问更细的内容。
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
          placeholder="例如: 企业采购可以开增值税专用发票吗? 保修期多久?"
        />

        <button
          type="button"
          class="mt-4 rounded-full bg-ink px-5 py-2.5 text-sm font-medium text-white transition hover:bg-slate-800 disabled:cursor-wait disabled:opacity-70"
          :disabled="loading"
          @click="submitFaq"
        >
          {{ loading ? "正在查询..." : "查询答案" }}
        </button>

        <div
          v-if="errorMessage"
          class="mt-6 rounded-3xl border border-rose-200 bg-rose-50 p-5"
        >
          <span class="chip bg-rose-100 text-rose-700">这次没有查到答案</span>
          <p class="mt-4 text-lg font-semibold text-rose-900">售前问答暂时没有成功返回结果</p>
          <p class="mt-3 text-sm leading-7 text-rose-800">
            可以先把问题写得更具体一点，比如补充“企业采购”“发票类型”“保修期”这类关键词，
            或者直接点击左侧常见问题后再试一次。
          </p>
          <p class="mt-4 rounded-2xl bg-white/80 px-4 py-3 text-sm text-rose-700">
            {{ errorMessage }}
          </p>
        </div>

        <div
          v-else-if="loading && !result"
          class="mt-6 rounded-3xl border border-sky-200 bg-sky-50 p-5"
        >
          <div class="flex flex-wrap items-center gap-2">
            <span class="chip bg-sky-100 text-sky-800">正在查询答案</span>
            <span class="chip bg-white text-slate-700">通常只需要几秒</span>
          </div>
          <p class="mt-4 text-lg font-semibold text-sky-950">系统正在整理知识库里的相关内容</p>
          <div class="mt-4 grid gap-3 sm:grid-cols-3">
            <article class="rounded-3xl bg-white/90 p-4">
              <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">步骤 1</p>
              <p class="mt-2 text-sm font-semibold text-slate-900">匹配最相关的问题主题</p>
            </article>
            <article class="rounded-3xl bg-white/90 p-4">
              <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">步骤 2</p>
              <p class="mt-2 text-sm font-semibold text-slate-900">提取命中的知识片段</p>
            </article>
            <article class="rounded-3xl bg-white/90 p-4">
              <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">步骤 3</p>
              <p class="mt-2 text-sm font-semibold text-slate-900">生成可继续追问的答案</p>
            </article>
          </div>
        </div>

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
            <span class="chip bg-sky-100 text-sky-800">来源: {{ result.sourceLabel }}</span>
            <span
              v-if="result.matchedEntry"
              class="chip bg-emerald-100 text-emerald-800"
            >
              主题: {{ result.matchedEntry.topic }}
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
                检索模式: {{ result.retrievalMode }}
              </span>
              <span class="chip bg-slate-100 text-slate-700">
                检索来源: {{ result.retrievalProvider }}
              </span>
              <span class="chip bg-amber-100 text-amber-800">
                回答来源: {{ result.answerProvider }}
              </span>
            </div>
          </details>
        </div>

        <div
          v-else
          class="mt-6 rounded-3xl border border-dashed border-slate-300 bg-white p-6"
        >
          <span class="chip bg-slate-100 text-slate-700">还没有开始查询</span>
          <h3 class="mt-4 text-2xl font-semibold text-ink">先问一个售前问题</h3>
          <p class="mt-3 text-sm leading-7 text-slate-600">
            这里适合查询发票、发货、保修、退换货、企业采购这些购买前最常见的问题。
            你可以直接输入问题，也可以先从左侧常见问法里选一个，再按自己的情况改一改。
          </p>

          <div class="mt-5 flex flex-wrap gap-2">
            <span class="chip bg-sky-100 text-sky-800">发票与报销</span>
            <span class="chip bg-emerald-100 text-emerald-800">发货与物流</span>
            <span class="chip bg-amber-100 text-amber-800">保修与退换货</span>
            <span class="chip bg-violet-100 text-violet-800">企业采购</span>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

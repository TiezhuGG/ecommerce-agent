<script setup lang="ts">
import { ref } from "vue";

import type { AgentResult } from "../types";

defineProps<{
  result: AgentResult | null;
}>();

const emit = defineEmits<{
  submit: [query: string];
}>();

const prompt = ref("帮我找 500 元以内、适合通勤和开会的蓝牙耳机，优先考虑续航和佩戴舒适。");

function submitPrompt() {
  emit("submit", prompt.value.trim());
}
</script>

<template>
  <section class="panel p-6">
    <h2 class="panel-title">智能导购入口</h2>
    <p class="muted-copy mt-2">
      未来这里会接 LangGraph。当前先用前端演示版模拟“自然语言输入 -> 条件解析 ->
      推荐摘要”的链路，让你先看懂业务流。
    </p>

    <textarea
      v-model="prompt"
      rows="5"
      class="field-input mt-6 resize-none"
      placeholder="例如：我想买 300 到 500 元的机械键盘，主要办公用，希望尽量安静。"
    />

    <div class="mt-4 flex flex-wrap gap-3">
      <button
        type="button"
        class="rounded-full bg-amber-500 px-5 py-2.5 text-sm font-medium text-white transition hover:bg-amber-600"
        @click="submitPrompt"
      >
        生成导购建议
      </button>
      <span class="chip bg-amber-100 text-amber-800">当前为前端演示模式</span>
    </div>

    <div v-if="result" class="mt-6 rounded-3xl bg-slate-50 p-5">
      <p class="text-sm font-semibold text-slate-500">推荐主题</p>
      <h3 class="mt-2 text-xl font-semibold text-slate-900">{{ result.title }}</h3>
      <p class="mt-3 text-sm leading-7 text-slate-700">{{ result.answer }}</p>

      <div class="mt-5">
        <p class="text-sm font-semibold text-slate-700">解析出的条件</p>
        <div class="mt-3 flex flex-wrap gap-2">
          <span
            v-for="item in result.appliedFilters"
            :key="item"
            class="chip bg-sky-100 text-sky-800"
          >
            {{ item }}
          </span>
        </div>
      </div>

      <div class="mt-5">
        <p class="text-sm font-semibold text-slate-700">执行摘要</p>
        <ol class="mt-3 space-y-2 text-sm text-slate-600">
          <li v-for="step in result.executionSteps" :key="step">
            {{ step }}
          </li>
        </ol>
      </div>
    </div>
  </section>
</template>

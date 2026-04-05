<script setup lang="ts">
import { ref } from "vue";

import type { AgentResult } from "../types/agent";

defineProps<{
  result: AgentResult | null;
}>();

const emit = defineEmits<{
  submit: [query: string];
}>();

const prompt = ref("帮我找 2000 元以内、适合通勤和开会的蓝牙耳机，优先考虑降噪和佩戴舒适。");

function submitPrompt() {
  emit("submit", prompt.value.trim());
}
</script>

<template>
  <section class="panel p-6">
    <h2 class="panel-title">智能导购入口</h2>
    <p class="muted-copy mt-2">
      这里仍然是前端演示逻辑，但它已经建立在真实后端商品检索结果之上。后续接入
      LangGraph 时，这里会从“演示推荐”升级为真正的 Agent 入口。
    </p>

    <textarea
      v-model="prompt"
      rows="5"
      class="field-input mt-6 resize-none"
      placeholder="例如：我想买一款 2000 元以内的降噪耳机，通勤和视频会议都要用。"
    />

    <div class="mt-4 flex flex-wrap gap-3">
      <button
        type="button"
        class="rounded-full bg-amber-500 px-5 py-2.5 text-sm font-medium text-white transition hover:bg-amber-600"
        @click="submitPrompt"
      >
        生成导购建议
      </button>
      <span class="chip bg-amber-100 text-amber-800">当前仍为前端演示逻辑</span>
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

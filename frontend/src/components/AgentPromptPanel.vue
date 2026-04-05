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

const prompt = ref("帮我找 2000 元以内、适合通勤和开会的蓝牙耳机，优先考虑降噪和佩戴舒适。");

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
        <h2 class="panel-title">AI 导购意图解析</h2>
        <p class="muted-copy mt-2">
          这个模块现在会真实调用后端的 `/intent/parse` 接口。模型只负责把自然语言理解成结构化条件，
          不直接产出商品事实；真正的商品结果仍然来自下方的商品搜索接口。
        </p>
      </div>
      <span class="chip bg-amber-100 text-amber-800">AI 只做理解，不做编造</span>
    </div>

    <textarea
      v-model="prompt"
      rows="5"
      class="field-input mt-6 resize-none"
      placeholder="例如：我想买一款 2000 元以内的降噪耳机，通勤和视频会议都要用。"
      @keydown.ctrl.enter="submitPrompt"
    />

    <div class="mt-4 flex flex-wrap gap-3">
      <button
        type="button"
        class="rounded-full bg-amber-500 px-5 py-2.5 text-sm font-medium text-white transition hover:bg-amber-600 disabled:cursor-wait disabled:opacity-70"
        :disabled="loading"
        @click="submitPrompt"
      >
        {{ loading ? "解析中..." : "解析导购需求" }}
      </button>
      <span class="chip bg-slate-100 text-slate-700">按下 Ctrl + Enter 也可以提交</span>
    </div>

    <p
      v-if="errorMessage"
      class="mt-4 rounded-2xl bg-rose-50 px-4 py-3 text-sm text-rose-700"
    >
      意图解析失败：{{ errorMessage }}
    </p>

    <div v-else-if="result" class="mt-6 rounded-3xl bg-slate-50 p-5">
      <div class="flex flex-wrap items-center gap-3">
        <span class="chip bg-emerald-100 text-emerald-800">{{ result.provider }}</span>
        <span class="chip bg-sky-100 text-sky-800">{{ result.model }}</span>
      </div>

      <div class="mt-5">
        <p class="text-sm font-semibold text-slate-700">原始需求</p>
        <p class="mt-2 text-sm leading-7 text-slate-700">{{ result.query }}</p>
      </div>

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

      <div v-if="result.scenario" class="mt-5">
        <p class="text-sm font-semibold text-slate-700">识别出的使用场景</p>
        <p class="mt-2 text-sm text-slate-700">{{ result.scenario }}</p>
      </div>

      <div v-if="result.priorities.length" class="mt-5">
        <p class="text-sm font-semibold text-slate-700">优先级关注点</p>
        <div class="mt-3 flex flex-wrap gap-2">
          <span
            v-for="item in result.priorities"
            :key="item"
            class="chip bg-amber-100 text-amber-800"
          >
            {{ item }}
          </span>
        </div>
      </div>

      <div class="mt-5">
        <p class="text-sm font-semibold text-slate-700">AI 解析说明</p>
        <p class="mt-2 text-sm leading-7 text-slate-700">{{ result.reasoningSummary }}</p>
      </div>

      <div class="mt-5 rounded-2xl bg-white px-4 py-4 text-sm leading-7 text-slate-600">
        上面的结果会自动回填到搜索筛选区，然后重新请求商品列表。
        这就是一个很典型的企业级分层：LLM 做意图理解，业务接口做事实检索。
      </div>
    </div>
  </section>
</template>

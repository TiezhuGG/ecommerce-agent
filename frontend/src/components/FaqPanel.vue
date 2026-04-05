<script setup lang="ts">
import { ref } from "vue";

import type { FaqEntry } from "../types/faq";

const props = defineProps<{
  entries: FaqEntry[];
}>();

const activeId = ref(props.entries[0]?.id ?? "");
</script>

<template>
  <section class="panel p-6">
    <h2 class="panel-title">售前 FAQ 区</h2>
    <p class="muted-copy mt-2">
      FAQ 仍保留静态演示数据。这样你可以直观看到：商品搜索已经进入真实接口阶段，而 FAQ
      还没有迁移，后面我们会单独把它做成后端工具。
    </p>

    <div class="mt-6 grid gap-4 xl:grid-cols-[0.9fr_1.1fr]">
      <div class="space-y-3">
        <button
          v-for="entry in entries"
          :key="entry.id"
          type="button"
          class="w-full rounded-2xl border px-4 py-4 text-left transition"
          :class="
            activeId === entry.id
              ? 'border-amber-300 bg-amber-50'
              : 'border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50'
          "
          @click="activeId = entry.id"
        >
          <p class="text-xs uppercase tracking-[0.18em] text-slate-500">{{ entry.topic }}</p>
          <p class="mt-2 text-sm font-medium text-slate-900">{{ entry.question }}</p>
        </button>
      </div>

      <div class="rounded-3xl bg-slate-50 p-5">
        <template v-for="entry in entries" :key="entry.id">
          <div v-if="entry.id === activeId">
            <p class="text-sm font-semibold text-slate-700">问题</p>
            <p class="mt-2 text-base text-slate-900">{{ entry.question }}</p>

            <p class="mt-5 text-sm font-semibold text-slate-700">答案</p>
            <p class="mt-2 text-sm leading-7 text-slate-700">{{ entry.answer }}</p>

            <div class="mt-5">
              <span class="chip bg-sky-100 text-sky-800">来源：{{ entry.sourceLabel }}</span>
            </div>
          </div>
        </template>
      </div>
    </div>
  </section>
</template>

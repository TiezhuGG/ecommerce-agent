<script setup lang="ts">
import type { AgentThreadHistory } from "../types/agent";

defineProps<{
  history: AgentThreadHistory | null;
  loading: boolean;
  errorMessage: string;
  currentThreadId: string | null;
}>();

const emit = defineEmits<{
  refresh: [];
  resume: [runId: string];
}>();

function formatTimestamp(value: string): string {
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }

  return parsed.toLocaleString("zh-CN", {
    hour12: false,
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function formatRoute(route: string): string {
  if (route === "shopping") {
    return "商品推荐";
  }

  if (route === "compare") {
    return "商品对比";
  }

  if (route === "faq") {
    return "售前问答";
  }

  return "最近会话";
}
</script>

<template>
  <section class="panel p-6">
    <div class="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
      <div class="max-w-3xl">
        <p class="text-sm font-semibold uppercase tracking-[0.24em] text-amber-700">
          Resume
        </p>
        <h2 class="mt-3 text-2xl font-semibold text-ink">继续上次会话</h2>
        <p class="mt-3 text-sm leading-7 text-slate-600">
          这里只保留普通用户真正需要的历史信息: 你之前问过什么、系统最后给了什么建议，以及一键继续聊。
        </p>
      </div>

      <button
        type="button"
        class="rounded-full border border-slate-200 px-4 py-2 text-sm text-slate-700 transition hover:border-slate-300 hover:bg-slate-50"
        :disabled="loading"
        @click="emit('refresh')"
      >
        {{ loading ? "刷新中..." : "刷新会话" }}
      </button>
    </div>

    <div
      v-if="errorMessage"
      class="mt-6 rounded-3xl border border-rose-200 bg-rose-50 p-5"
    >
      <span class="chip bg-rose-100 text-rose-700">历史会话暂时不可用</span>
      <p class="mt-4 text-lg font-semibold text-rose-900">这次没有成功加载最近会话</p>
      <p class="mt-3 text-sm leading-7 text-rose-800">
        不影响你继续发起新的导购。稍后刷新一次，或者先直接开始新会话即可。
      </p>
      <p class="mt-4 rounded-2xl bg-white/80 px-4 py-3 text-sm text-rose-700">
        {{ errorMessage }}
      </p>
    </div>

    <div
      v-else-if="loading && !(history?.items.length ?? 0)"
      class="mt-6 rounded-3xl border border-slate-200 bg-slate-50 p-5"
    >
      <div class="flex flex-wrap items-center gap-2">
        <span class="chip bg-sky-100 text-sky-800">正在加载最近会话</span>
        <span class="chip bg-white text-slate-700">只展示普通用户真正需要的内容</span>
      </div>
      <p class="mt-4 text-sm leading-7 text-slate-600">
        系统正在整理你最近问过的问题、上次的推荐结果，以及可以一键继续聊的入口。
      </p>
    </div>

    <div v-else-if="history?.items.length" class="mt-6 grid gap-3">
      <article
        v-for="item in history.items"
        :key="item.threadId"
        class="rounded-3xl border bg-white p-5"
        :class="
          currentThreadId === item.threadId
            ? 'border-emerald-300 shadow-sm shadow-emerald-100/80'
            : 'border-slate-200'
        "
      >
        <div class="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <div class="flex flex-wrap items-center gap-2">
              <span class="chip bg-sky-100 text-sky-800">
                {{ formatRoute(item.latestRoute) }}
              </span>
              <span
                v-if="currentThreadId === item.threadId"
                class="chip bg-emerald-100 text-emerald-800"
              >
                当前正在继续
              </span>
              <span class="chip bg-slate-100 text-slate-700">
                {{ formatTimestamp(item.latestCreatedAt) }}
              </span>
            </div>

            <p class="mt-4 text-sm font-semibold leading-7 text-slate-900">
              {{ item.latestMessage }}
            </p>
            <p class="mt-2 text-sm leading-7 text-slate-600">
              {{ item.latestFinalAnswerPreview }}
            </p>

            <div v-if="item.recommendedProductIds.length" class="mt-3 flex flex-wrap gap-2">
              <span
                v-for="productId in item.recommendedProductIds.slice(0, 3)"
                :key="`${item.threadId}-${productId}`"
                class="chip bg-amber-100 text-amber-800"
              >
                推荐商品 {{ productId }}
              </span>
              <span
                v-if="item.recommendedProductIds.length > 3"
                class="chip bg-slate-100 text-slate-700"
              >
                +{{ item.recommendedProductIds.length - 3 }}
              </span>
            </div>
          </div>

          <button
            type="button"
            class="rounded-full bg-ink px-4 py-2 text-sm font-medium text-white transition hover:bg-slate-800"
            @click="emit('resume', item.latestRunId)"
          >
            从这里继续
          </button>
        </div>
      </article>
    </div>

    <div
      v-else
      class="mt-6 rounded-3xl border border-dashed border-slate-300 bg-slate-50 px-6 py-10 text-center"
    >
      <span class="chip bg-slate-100 text-slate-700">还没有历史会话</span>
      <p class="mt-4 text-xl font-semibold text-slate-900">第一次导购后，这里会自动保存最近会话</p>
      <p class="mt-3 text-sm leading-7 text-slate-600">
        你下次回来时，可以直接从上一次的推荐结果继续追问，不需要把前情重新再说一遍。
      </p>
      <div class="mt-5 flex flex-wrap justify-center gap-2">
        <span class="chip bg-white text-slate-700">记住最近问题</span>
        <span class="chip bg-white text-slate-700">保留推荐结果</span>
        <span class="chip bg-white text-slate-700">一键继续会话</span>
      </div>
    </div>
  </section>
</template>

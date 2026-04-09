<script setup lang="ts">
import type { AgentRunHistory } from "../types/agent";

defineProps<{
  history: AgentRunHistory | null;
  loading: boolean;
  errorMessage: string;
  selectedRunId: string | null;
  detailLoading: boolean;
  detailErrorMessage: string;
}>();

const emit = defineEmits<{
  refresh: [];
  inspect: [runId: string];
  resume: [runId: string];
}>();

function formatTimestamp(value: string): string {
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }

  return parsed.toLocaleString("zh-CN", {
    hour12: false,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}
</script>

<template>
  <section class="panel p-6">
    <div class="flex items-start justify-between gap-4">
      <div>
        <h2 class="panel-title">最近持久化运行</h2>
        <p class="muted-copy mt-2">
          这里展示最近写入数据库的 Agent 运行摘要。除了查看详情，你现在也可以直接从某条历史运行恢复会话，继续沿着原线程追问。
        </p>
      </div>

      <button
        type="button"
        class="rounded-full border border-slate-200 px-4 py-2 text-sm text-slate-700 transition hover:border-slate-300 hover:bg-slate-50"
        :disabled="loading"
        @click="emit('refresh')"
      >
        {{ loading ? "刷新中..." : "刷新历史" }}
      </button>
    </div>

    <p
      v-if="errorMessage"
      class="mt-4 rounded-2xl bg-rose-50 px-4 py-3 text-sm text-rose-700"
    >
      历史记录加载失败：{{ errorMessage }}
    </p>

    <p
      v-if="detailErrorMessage"
      class="mt-4 rounded-2xl bg-rose-50 px-4 py-3 text-sm text-rose-700"
    >
      运行详情加载失败：{{ detailErrorMessage }}
    </p>

    <template v-if="history">
      <div class="mt-6 rounded-3xl bg-slate-50 p-5">
        <p class="text-sm font-semibold text-slate-800">存储后端</p>
        <p class="mt-2 text-sm leading-7 text-slate-600">{{ history.backend }}</p>
      </div>

      <div
        v-if="history.backend === 'disabled'"
        class="mt-5 rounded-3xl bg-amber-50 p-5 text-sm leading-7 text-amber-900"
      >
        当前未启用数据库日志存储，所以这里只会显示空列表。配置可用的 `DATABASE_URL`
        后，这里会展示最近的 Agent 运行历史。
      </div>

      <div v-else-if="history.items.length" class="mt-5 grid gap-3">
        <article
          v-for="item in history.items"
          :key="item.runId"
          class="rounded-2xl border bg-white p-4"
          :class="
            selectedRunId === item.runId ? 'border-sky-300 shadow-sm shadow-sky-100/80' : 'border-slate-200'
          "
        >
          <div class="flex items-start justify-between gap-4">
            <div class="flex flex-wrap items-center gap-2">
              <span class="chip bg-emerald-100 text-emerald-800">{{ item.route }}</span>
              <span class="chip bg-sky-100 text-sky-800">{{ item.provider }}</span>
              <span class="chip bg-slate-100 text-slate-700">{{ item.model }}</span>
            </div>

            <div class="flex flex-wrap gap-2">
              <button
                type="button"
                class="rounded-full border border-slate-200 px-3 py-1.5 text-xs text-slate-700 transition hover:border-slate-300 hover:bg-slate-50"
                :disabled="detailLoading && selectedRunId === item.runId"
                @click="emit('inspect', item.runId)"
              >
                {{
                  detailLoading && selectedRunId === item.runId
                    ? "加载中..."
                    : selectedRunId === item.runId
                      ? "重新加载"
                      : "查看详情"
                }}
              </button>
              <button
                type="button"
                class="rounded-full border border-emerald-200 px-3 py-1.5 text-xs text-emerald-700 transition hover:border-emerald-300 hover:bg-emerald-50"
                :disabled="detailLoading"
                @click="emit('resume', item.runId)"
              >
                恢复会话
              </button>
            </div>
          </div>

          <p class="mt-3 text-xs text-slate-500">
            {{ formatTimestamp(item.createdAt) }} · run_id：{{ item.runId }}
          </p>
          <p class="mt-2 text-xs text-slate-500">thread_id：{{ item.threadId }}</p>
          <p class="mt-3 text-sm font-semibold leading-7 text-slate-900">{{ item.message }}</p>
          <p class="mt-2 text-sm leading-7 text-slate-600">{{ item.finalAnswerPreview }}</p>

          <div class="mt-3 flex flex-wrap gap-2">
            <span class="chip bg-amber-100 text-amber-800">
              warnings：{{ item.warningCount }}
            </span>
            <span class="chip bg-violet-100 text-violet-800">
              tool_calls：{{ item.toolCallCount }}
            </span>
          </div>

          <div v-if="item.recommendedProductIds.length" class="mt-3 flex flex-wrap gap-2">
            <span
              v-for="productId in item.recommendedProductIds"
              :key="`${item.runId}-${productId}`"
              class="chip bg-sky-100 text-sky-800"
            >
              {{ productId }}
            </span>
          </div>
        </article>
      </div>

      <div
        v-else
        class="mt-5 rounded-3xl bg-slate-50 p-5 text-sm leading-7 text-slate-600"
      >
        数据库已启用，但目前还没有可展示的 Agent 运行记录。
      </div>
    </template>
  </section>
</template>

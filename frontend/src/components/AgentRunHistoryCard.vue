<script setup lang="ts">
import { computed, ref } from "vue";

import type {
  AgentRunHistory,
  AgentThreadDetail,
  AgentThreadHistory,
} from "../types/agent";

const props = defineProps<{
  history: AgentRunHistory | null;
  threadHistory: AgentThreadHistory | null;
  threadDetail: AgentThreadDetail | null;
  loading: boolean;
  errorMessage: string;
  selectedRunId: string | null;
  selectedThreadId: string | null;
  currentThreadId: string | null;
  threadDetailLoading: boolean;
  detailLoading: boolean;
  threadDetailErrorMessage: string;
  detailErrorMessage: string;
}>();

const emit = defineEmits<{
  refresh: [];
  inspectThread: [threadId: string];
  inspect: [runId: string];
  resume: [runId: string];
}>();

const viewMode = ref<"threads" | "runs">("threads");

const hasRunItems = computed(() => (props.history?.items.length ?? 0) > 0);
const hasThreadItems = computed(() => (props.threadHistory?.items.length ?? 0) > 0);
const currentBackend = computed(() => props.threadHistory?.backend ?? props.history?.backend ?? "disabled");

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
        <h2 class="panel-title">Agent 历史与线程</h2>
        <p class="muted-copy mt-2">
          这里同时提供运行视角和线程视角。运行视角适合排查单次执行，线程视角适合看连续会话时间线，并从任意节点恢复续聊。
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

    <div class="mt-5 flex flex-wrap items-center gap-3">
      <div class="inline-flex rounded-full bg-slate-100 p-1">
        <button
          type="button"
          class="rounded-full px-4 py-2 text-sm transition"
          :class="
            viewMode === 'threads'
              ? 'bg-white text-slate-900 shadow-sm'
              : 'text-slate-600 hover:text-slate-900'
          "
          @click="viewMode = 'threads'"
        >
          线程视角
        </button>
        <button
          type="button"
          class="rounded-full px-4 py-2 text-sm transition"
          :class="
            viewMode === 'runs'
              ? 'bg-white text-slate-900 shadow-sm'
              : 'text-slate-600 hover:text-slate-900'
          "
          @click="viewMode = 'runs'"
        >
          运行视角
        </button>
      </div>

      <span v-if="currentThreadId" class="chip bg-emerald-100 text-emerald-800">
        当前活跃线程：{{ currentThreadId }}
      </span>
    </div>

    <p
      v-if="errorMessage"
      class="mt-4 rounded-2xl bg-rose-50 px-4 py-3 text-sm text-rose-700"
    >
      历史记录加载失败：{{ errorMessage }}
    </p>

    <p
      v-if="threadDetailErrorMessage"
      class="mt-4 rounded-2xl bg-rose-50 px-4 py-3 text-sm text-rose-700"
    >
      线程时间线加载失败：{{ threadDetailErrorMessage }}
    </p>

    <p
      v-if="detailErrorMessage"
      class="mt-4 rounded-2xl bg-rose-50 px-4 py-3 text-sm text-rose-700"
    >
      运行详情加载失败：{{ detailErrorMessage }}
    </p>

    <div class="mt-6 rounded-3xl bg-slate-50 p-5">
      <p class="text-sm font-semibold text-slate-800">存储后端</p>
      <p class="mt-2 text-sm leading-7 text-slate-600">{{ currentBackend }}</p>
    </div>

    <div
      v-if="currentBackend === 'disabled'"
      class="mt-5 rounded-3xl bg-amber-50 p-5 text-sm leading-7 text-amber-900"
    >
      当前未启用数据库日志存储，因此这里不会展示历史运行与线程。配置可用的 `DATABASE_URL` 后，这里会自动展示最近的会话记录。
    </div>

    <template v-else-if="viewMode === 'threads'">
      <div v-if="hasThreadItems" class="mt-5 grid gap-3">
        <article
          v-for="item in threadHistory?.items ?? []"
          :key="item.threadId"
          class="rounded-2xl border bg-white p-4"
          :class="
            currentThreadId === item.threadId
              ? 'border-emerald-300 shadow-sm shadow-emerald-100/80'
              : selectedThreadId === item.threadId
                ? 'border-sky-300 shadow-sm shadow-sky-100/80'
                : 'border-slate-200'
          "
        >
          <div class="flex items-start justify-between gap-4">
            <div class="flex flex-wrap items-center gap-2">
              <span class="chip bg-violet-100 text-violet-800">{{ item.latestRoute }}</span>
              <span class="chip bg-sky-100 text-sky-800">{{ item.provider }}</span>
              <span class="chip bg-slate-100 text-slate-700">{{ item.model }}</span>
              <span class="chip bg-amber-100 text-amber-800">{{ item.runCount }} 次运行</span>
            </div>

            <div class="flex flex-wrap gap-2">
              <button
                type="button"
                class="rounded-full border border-slate-200 px-3 py-1.5 text-xs text-slate-700 transition hover:border-slate-300 hover:bg-slate-50"
                :disabled="threadDetailLoading"
                @click="emit('inspectThread', item.threadId)"
              >
                {{
                  threadDetailLoading && selectedThreadId === item.threadId
                    ? "加载时间线..."
                    : selectedThreadId === item.threadId
                      ? "收起时间线"
                      : "展开时间线"
                }}
              </button>
              <button
                type="button"
                class="rounded-full border border-slate-200 px-3 py-1.5 text-xs text-slate-700 transition hover:border-slate-300 hover:bg-slate-50"
                :disabled="detailLoading && selectedRunId === item.latestRunId"
                @click="emit('inspect', item.latestRunId)"
              >
                {{
                  detailLoading && selectedRunId === item.latestRunId
                    ? "加载中..."
                    : "查看最新一次"
                }}
              </button>
              <button
                type="button"
                class="rounded-full border border-emerald-200 px-3 py-1.5 text-xs text-emerald-700 transition hover:border-emerald-300 hover:bg-emerald-50"
                :disabled="detailLoading"
                @click="emit('resume', item.latestRunId)"
              >
                恢复该线程
              </button>
            </div>
          </div>

          <p class="mt-3 text-xs text-slate-500">
            {{ formatTimestamp(item.latestCreatedAt) }} · latest_run_id：{{ item.latestRunId }}
          </p>
          <p class="mt-2 text-xs text-slate-500">thread_id：{{ item.threadId }}</p>
          <p class="mt-3 text-sm font-semibold leading-7 text-slate-900">{{ item.latestMessage }}</p>
          <p class="mt-2 text-sm leading-7 text-slate-600">{{ item.latestFinalAnswerPreview }}</p>

          <div class="mt-3 flex flex-wrap gap-2">
            <span
              v-for="route in item.routes"
              :key="`${item.threadId}-${route}`"
              class="chip bg-slate-100 text-slate-700"
            >
              {{ route }}
            </span>
          </div>

          <div v-if="item.recommendedProductIds.length" class="mt-3 flex flex-wrap gap-2">
            <span
              v-for="productId in item.recommendedProductIds"
              :key="`${item.threadId}-${productId}`"
              class="chip bg-sky-100 text-sky-800"
            >
              {{ productId }}
            </span>
          </div>

          <div
            v-if="selectedThreadId === item.threadId && threadDetail"
            class="mt-5 rounded-3xl bg-slate-50 p-4"
          >
            <div class="flex flex-wrap items-center justify-between gap-3">
              <div>
                <p class="text-sm font-semibold text-slate-800">线程时间线</p>
                <p class="mt-1 text-xs text-slate-500">
                  共 {{ threadDetail.runCount }} 次运行，当前展示最近 {{ threadDetail.items.length }} 次。
                </p>
              </div>
              <span class="chip bg-emerald-100 text-emerald-800">
                latest_run：{{ threadDetail.latestRunId }}
              </span>
            </div>

            <div class="mt-4 space-y-3">
              <article
                v-for="run in threadDetail.items"
                :key="run.runId"
                class="rounded-2xl border border-slate-200 bg-white p-4"
              >
                <div class="flex items-start justify-between gap-4">
                  <div class="flex flex-wrap items-center gap-2">
                    <span class="chip bg-emerald-100 text-emerald-800">{{ run.route }}</span>
                    <span class="chip bg-slate-100 text-slate-700">{{ run.model }}</span>
                    <span v-if="run.runId === threadDetail.latestRunId" class="chip bg-sky-100 text-sky-800">
                      最新一次
                    </span>
                  </div>

                  <div class="flex flex-wrap gap-2">
                    <button
                      type="button"
                      class="rounded-full border border-slate-200 px-3 py-1.5 text-xs text-slate-700 transition hover:border-slate-300 hover:bg-slate-50"
                      :disabled="detailLoading && selectedRunId === run.runId"
                      @click="emit('inspect', run.runId)"
                    >
                      {{
                        detailLoading && selectedRunId === run.runId
                          ? "加载中..."
                          : "查看详情"
                      }}
                    </button>
                    <button
                      type="button"
                      class="rounded-full border border-emerald-200 px-3 py-1.5 text-xs text-emerald-700 transition hover:border-emerald-300 hover:bg-emerald-50"
                      :disabled="detailLoading"
                      @click="emit('resume', run.runId)"
                    >
                      从此节点恢复
                    </button>
                  </div>
                </div>

                <p class="mt-3 text-xs text-slate-500">
                  {{ formatTimestamp(run.createdAt) }} · run_id：{{ run.runId }}
                </p>
                <p class="mt-2 text-sm font-semibold leading-7 text-slate-900">{{ run.message }}</p>
                <p class="mt-2 text-sm leading-7 text-slate-600">{{ run.finalAnswerPreview }}</p>
              </article>
            </div>
          </div>
        </article>
      </div>

      <div
        v-else
        class="mt-5 rounded-3xl bg-slate-50 p-5 text-sm leading-7 text-slate-600"
      >
        数据库已启用，但目前还没有可展示的会话线程。
      </div>
    </template>

    <template v-else>
      <div v-if="hasRunItems" class="mt-5 grid gap-3">
        <article
          v-for="item in history?.items ?? []"
          :key="item.runId"
          class="rounded-2xl border bg-white p-4"
          :class="
            selectedRunId === item.runId
              ? 'border-sky-300 shadow-sm shadow-sky-100/80'
              : 'border-slate-200'
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
            <span class="chip bg-amber-100 text-amber-800">warnings：{{ item.warningCount }}</span>
            <span class="chip bg-violet-100 text-violet-800">tool_calls：{{ item.toolCallCount }}</span>
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

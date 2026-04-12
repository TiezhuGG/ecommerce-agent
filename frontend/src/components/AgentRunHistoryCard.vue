<script setup lang="ts">
import { computed, ref } from "vue";

import type {
  AgentRoute,
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

const threadItems = computed(() => props.threadHistory?.items ?? []);
const runItems = computed(() => props.history?.items ?? []);
const currentBackend = computed(() => props.threadHistory?.backend ?? props.history?.backend ?? "disabled");
const hasThreadItems = computed(() => threadItems.value.length > 0);
const hasRunItems = computed(() => runItems.value.length > 0);
const activeThreadLabel = computed(() => props.currentThreadId ?? "当前没有活跃会话");

const totalThreads = computed(() => threadItems.value.length);
const totalRuns = computed(() => runItems.value.length);
const totalProviders = computed(() => {
  return new Set(
    [...threadItems.value.map((item) => item.provider), ...runItems.value.map((item) => item.provider)].filter(
      Boolean,
    ),
  ).size;
});

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

function formatRouteLabel(route: AgentRoute): string {
  if (route === "faq") {
    return "知识问答";
  }

  if (route === "compare") {
    return "商品对比";
  }

  return "导购推荐";
}

function formatBackendLabel(value: string): string {
  if (value === "disabled") {
    return "未启用";
  }

  if (value === "sqlite") {
    return "SQLite";
  }

  if (value === "postgresql") {
    return "PostgreSQL";
  }

  return value;
}

function shortenId(value: string): string {
  if (value.length <= 18) {
    return value;
  }

  return `${value.slice(0, 8)}...${value.slice(-6)}`;
}

function hasSelectedThread(itemThreadId: string): boolean {
  return props.selectedThreadId === itemThreadId;
}

function hasSelectedRun(runId: string): boolean {
  return props.selectedRunId === runId;
}
</script>

<template>
  <section class="panel p-6">
    <div class="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
      <div class="max-w-3xl">
        <p class="text-sm font-semibold uppercase tracking-[0.24em] text-amber-700">
          Agent Diagnostics
        </p>
        <h2 class="mt-3 text-3xl font-semibold tracking-tight text-ink">
          运行诊断工作台
        </h2>
        <p class="mt-3 text-sm leading-7 text-slate-600">
          这里集中查看最近的 Agent 线程、运行记录和恢复入口。前台首页已经不再展示这些技术细节，
          它们统一回收到后台系统区，方便排查问题、追踪会话和恢复历史节点。
        </p>
      </div>

      <button
        type="button"
        class="rounded-full border border-slate-200 px-4 py-2 text-sm text-slate-700 transition hover:border-slate-300 hover:bg-slate-50"
        :disabled="loading"
        @click="emit('refresh')"
      >
        {{ loading ? "刷新中..." : "刷新记录" }}
      </button>
    </div>

    <div class="mt-6 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
      <article class="rounded-3xl bg-slate-50 p-4">
        <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">存储后端</p>
        <p class="mt-2 text-xl font-semibold text-slate-900">{{ formatBackendLabel(currentBackend) }}</p>
        <p class="mt-2 text-sm leading-6 text-slate-600">
          本地开发阶段默认使用 SQLite，上线后再切换 PostgreSQL。
        </p>
      </article>

      <article class="rounded-3xl bg-slate-50 p-4">
        <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">最近线程数</p>
        <p class="mt-2 text-xl font-semibold text-slate-900">{{ totalThreads }}</p>
        <p class="mt-2 text-sm leading-6 text-slate-600">
          用于从会话维度查看一段连续对话的演进过程。
        </p>
      </article>

      <article class="rounded-3xl bg-slate-50 p-4">
        <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">最近运行数</p>
        <p class="mt-2 text-xl font-semibold text-slate-900">{{ totalRuns }}</p>
        <p class="mt-2 text-sm leading-6 text-slate-600">
          用于从单次执行维度排查模型、工具调用和返回摘要。
        </p>
      </article>

      <article class="rounded-3xl bg-slate-50 p-4">
        <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">活跃会话</p>
        <p class="mt-2 text-base font-semibold text-slate-900">{{ shortenId(activeThreadLabel) }}</p>
        <p class="mt-2 text-sm leading-6 text-slate-600">
          已覆盖 {{ totalProviders }} 个模型提供方来源。
        </p>
      </article>
    </div>

    <div class="mt-6 flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
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

      <div class="flex flex-wrap gap-2">
        <span v-if="currentThreadId" class="chip bg-emerald-100 text-emerald-800">
          当前活跃线程：{{ shortenId(currentThreadId) }}
        </span>
        <span v-if="selectedThreadId" class="chip bg-sky-100 text-sky-800">
          已展开线程：{{ shortenId(selectedThreadId) }}
        </span>
        <span v-if="selectedRunId" class="chip bg-amber-100 text-amber-800">
          已选运行：{{ shortenId(selectedRunId) }}
        </span>
      </div>
    </div>

    <div class="mt-4 space-y-3">
      <p
        v-if="errorMessage"
        class="rounded-2xl bg-rose-50 px-4 py-3 text-sm text-rose-700"
      >
        历史记录加载失败：{{ errorMessage }}
      </p>

      <p
        v-if="threadDetailErrorMessage"
        class="rounded-2xl bg-rose-50 px-4 py-3 text-sm text-rose-700"
      >
        线程时间线加载失败：{{ threadDetailErrorMessage }}
      </p>

      <p
        v-if="detailErrorMessage"
        class="rounded-2xl bg-rose-50 px-4 py-3 text-sm text-rose-700"
      >
        运行详情加载失败：{{ detailErrorMessage }}
      </p>
    </div>

    <div
      v-if="currentBackend === 'disabled'"
      class="mt-5 rounded-3xl bg-amber-50 p-5 text-sm leading-7 text-amber-900"
    >
      当前还没有启用 Agent 历史存储，因此这里只能看到空态说明。配置可用的
      <code>DATABASE_URL</code> 后，后台系统区会自动接入最近线程与运行记录。
    </div>

    <template v-else-if="viewMode === 'threads'">
      <div v-if="hasThreadItems" class="mt-5 grid gap-4">
        <article
          v-for="item in threadItems"
          :key="item.threadId"
          class="rounded-[28px] border bg-white p-5"
          :class="
            currentThreadId === item.threadId
              ? 'border-emerald-300 shadow-sm shadow-emerald-100/80'
              : hasSelectedThread(item.threadId)
                ? 'border-sky-300 shadow-sm shadow-sky-100/80'
                : 'border-slate-200'
          "
        >
          <div class="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
            <div class="space-y-3">
              <div class="flex flex-wrap items-center gap-2">
                <span class="chip bg-violet-100 text-violet-800">
                  {{ formatRouteLabel(item.latestRoute) }}
                </span>
                <span class="chip bg-sky-100 text-sky-800">{{ item.provider }}</span>
                <span class="chip bg-slate-100 text-slate-700">{{ item.model }}</span>
                <span class="chip bg-amber-100 text-amber-800">{{ item.runCount }} 次运行</span>
                <span
                  v-if="currentThreadId === item.threadId"
                  class="chip bg-emerald-100 text-emerald-800"
                >
                  当前会话
                </span>
              </div>

              <div>
                <p class="text-xs text-slate-500">
                  最近更新时间：{{ formatTimestamp(item.latestCreatedAt) }}
                </p>
                <p class="mt-1 text-xs text-slate-500">
                  thread_id：{{ item.threadId }}
                </p>
                <p class="mt-1 text-xs text-slate-500">
                  latest_run_id：{{ item.latestRunId }}
                </p>
              </div>
            </div>

            <div class="flex flex-wrap gap-2">
              <button
                type="button"
                class="rounded-full border border-slate-200 px-3 py-1.5 text-xs text-slate-700 transition hover:border-slate-300 hover:bg-slate-50"
                :disabled="threadDetailLoading"
                @click="emit('inspectThread', item.threadId)"
              >
                {{
                  threadDetailLoading && hasSelectedThread(item.threadId)
                    ? "加载时间线..."
                    : hasSelectedThread(item.threadId)
                      ? "收起时间线"
                      : "展开时间线"
                }}
              </button>
              <button
                type="button"
                class="rounded-full border border-slate-200 px-3 py-1.5 text-xs text-slate-700 transition hover:border-slate-300 hover:bg-slate-50"
                :disabled="detailLoading && hasSelectedRun(item.latestRunId)"
                @click="emit('inspect', item.latestRunId)"
              >
                {{
                  detailLoading && hasSelectedRun(item.latestRunId)
                    ? "加载详情..."
                    : "查看最近一次"
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

          <div class="mt-4 grid gap-4 xl:grid-cols-[1.2fr_0.8fr]">
            <div>
              <p class="text-sm font-semibold leading-7 text-slate-900">{{ item.latestMessage }}</p>
              <p class="mt-2 text-sm leading-7 text-slate-600">{{ item.latestFinalAnswerPreview }}</p>
            </div>

            <div class="rounded-3xl bg-slate-50 p-4">
              <p class="text-sm font-semibold text-slate-800">线程摘要</p>
              <div class="mt-3 flex flex-wrap gap-2">
                <span
                  v-for="route in item.routes"
                  :key="`${item.threadId}-${route}`"
                  class="chip bg-white text-slate-700"
                >
                  {{ formatRouteLabel(route) }}
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
              <p v-else class="mt-3 text-sm leading-6 text-slate-500">
                当前线程没有留存推荐商品编号。
              </p>
            </div>
          </div>

          <div
            v-if="hasSelectedThread(item.threadId) && threadDetail"
            class="mt-5 rounded-[28px] bg-slate-50 p-5"
          >
            <div class="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
              <div>
                <p class="text-lg font-semibold text-slate-900">线程时间线</p>
                <p class="mt-1 text-sm leading-6 text-slate-600">
                  共 {{ threadDetail.runCount }} 次运行，当前展开最近 {{ threadDetail.items.length }} 次。
                  可以从任意节点恢复继续对话。
                </p>
              </div>

              <div class="flex flex-wrap gap-2">
                <span class="chip bg-white text-slate-700">
                  latest_run：{{ shortenId(threadDetail.latestRunId) }}
                </span>
                <span v-if="threadDetail.threadState" class="chip bg-emerald-100 text-emerald-800">
                  已保存线程状态
                </span>
              </div>
            </div>

            <div v-if="threadDetail.threadState" class="mt-4 grid gap-3 lg:grid-cols-3">
              <article class="rounded-2xl bg-white p-4">
                <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">筛选状态</p>
                <p class="mt-2 text-sm leading-6 text-slate-700">
                  {{
                    threadDetail.threadState.searchFilters
                      ? "该线程已保存商品筛选条件，可用于恢复导购上下文。"
                      : "该线程没有保存商品筛选条件。"
                  }}
                </p>
              </article>

              <article class="rounded-2xl bg-white p-4">
                <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">已选商品</p>
                <p class="mt-2 text-2xl font-semibold text-slate-900">
                  {{ threadDetail.threadState.selectedProductIds.length }}
                </p>
              </article>

              <article class="rounded-2xl bg-white p-4">
                <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">候选商品</p>
                <p class="mt-2 text-2xl font-semibold text-slate-900">
                  {{ threadDetail.threadState.candidateProductIds.length }}
                </p>
              </article>
            </div>

            <div class="mt-4 space-y-3">
              <article
                v-for="run in threadDetail.items"
                :key="run.runId"
                class="rounded-2xl border border-slate-200 bg-white p-4"
                :class="hasSelectedRun(run.runId) ? 'border-sky-300 shadow-sm shadow-sky-100/80' : ''"
              >
                <div class="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                  <div>
                    <div class="flex flex-wrap items-center gap-2">
                      <span class="chip bg-emerald-100 text-emerald-800">
                        {{ formatRouteLabel(run.route) }}
                      </span>
                      <span class="chip bg-slate-100 text-slate-700">{{ run.model }}</span>
                      <span
                        v-if="run.runId === threadDetail.latestRunId"
                        class="chip bg-sky-100 text-sky-800"
                      >
                        最新一次
                      </span>
                    </div>

                    <p class="mt-3 text-xs text-slate-500">
                      {{ formatTimestamp(run.createdAt) }} / run_id：{{ run.runId }}
                    </p>
                  </div>

                  <div class="flex flex-wrap gap-2">
                    <button
                      type="button"
                      class="rounded-full border border-slate-200 px-3 py-1.5 text-xs text-slate-700 transition hover:border-slate-300 hover:bg-slate-50"
                      :disabled="detailLoading && hasSelectedRun(run.runId)"
                      @click="emit('inspect', run.runId)"
                    >
                      {{
                        detailLoading && hasSelectedRun(run.runId)
                          ? "加载详情..."
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

                <p class="mt-3 text-sm font-semibold leading-7 text-slate-900">{{ run.message }}</p>
                <p class="mt-2 text-sm leading-7 text-slate-600">{{ run.finalAnswerPreview }}</p>

                <div class="mt-3 flex flex-wrap gap-2">
                  <span class="chip bg-amber-100 text-amber-800">warnings：{{ run.warningCount }}</span>
                  <span class="chip bg-violet-100 text-violet-800">tool calls：{{ run.toolCallCount }}</span>
                </div>
              </article>
            </div>
          </div>
        </article>
      </div>

      <div
        v-else
        class="mt-5 rounded-3xl bg-slate-50 p-5 text-sm leading-7 text-slate-600"
      >
        数据库已经启用，但当前还没有可展示的线程记录。先在前台跑几次导购对话，这里就会开始出现最近会话时间线。
      </div>
    </template>

    <template v-else>
      <div v-if="hasRunItems" class="mt-5 grid gap-4">
        <article
          v-for="item in runItems"
          :key="item.runId"
          class="rounded-[28px] border bg-white p-5"
          :class="hasSelectedRun(item.runId) ? 'border-sky-300 shadow-sm shadow-sky-100/80' : 'border-slate-200'"
        >
          <div class="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
            <div class="space-y-3">
              <div class="flex flex-wrap items-center gap-2">
                <span class="chip bg-emerald-100 text-emerald-800">{{ formatRouteLabel(item.route) }}</span>
                <span class="chip bg-sky-100 text-sky-800">{{ item.provider }}</span>
                <span class="chip bg-slate-100 text-slate-700">{{ item.model }}</span>
                <span v-if="hasSelectedRun(item.runId)" class="chip bg-amber-100 text-amber-800">
                  当前选中
                </span>
              </div>

              <div>
                <p class="text-xs text-slate-500">
                  运行时间：{{ formatTimestamp(item.createdAt) }}
                </p>
                <p class="mt-1 text-xs text-slate-500">run_id：{{ item.runId }}</p>
                <p class="mt-1 text-xs text-slate-500">thread_id：{{ item.threadId }}</p>
              </div>
            </div>

            <div class="flex flex-wrap gap-2">
              <button
                type="button"
                class="rounded-full border border-slate-200 px-3 py-1.5 text-xs text-slate-700 transition hover:border-slate-300 hover:bg-slate-50"
                :disabled="detailLoading && hasSelectedRun(item.runId)"
                @click="emit('inspect', item.runId)"
              >
                {{
                  detailLoading && hasSelectedRun(item.runId)
                    ? "加载详情..."
                    : hasSelectedRun(item.runId)
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

          <div class="mt-4 grid gap-4 xl:grid-cols-[1.2fr_0.8fr]">
            <div>
              <p class="text-sm font-semibold leading-7 text-slate-900">{{ item.message }}</p>
              <p class="mt-2 text-sm leading-7 text-slate-600">{{ item.finalAnswerPreview }}</p>
            </div>

            <div class="rounded-3xl bg-slate-50 p-4">
              <p class="text-sm font-semibold text-slate-800">诊断摘要</p>
              <div class="mt-3 flex flex-wrap gap-2">
                <span class="chip bg-amber-100 text-amber-800">warnings：{{ item.warningCount }}</span>
                <span class="chip bg-violet-100 text-violet-800">tool calls：{{ item.toolCallCount }}</span>
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
              <p v-else class="mt-3 text-sm leading-6 text-slate-500">
                本次运行没有留存推荐商品编号。
              </p>
            </div>
          </div>
        </article>
      </div>

      <div
        v-else
        class="mt-5 rounded-3xl bg-slate-50 p-5 text-sm leading-7 text-slate-600"
      >
        数据库已经启用，但当前还没有可展示的运行记录。等前台产生新的 Agent 执行后，这里会按时间倒序列出最近记录。
      </div>
    </template>
  </section>
</template>

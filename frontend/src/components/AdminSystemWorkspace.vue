<script setup lang="ts">
import { computed, ref } from "vue";

import type {
  AgentPrecheck,
  AgentResult,
  AgentRunHistory,
  AgentThreadDetail,
  AgentThreadHistory,
} from "../types/agent";
import type { DatabaseSmokeReport, HealthResponse } from "../types/system";

import AdminAgentRunDetailPanel from "./AdminAgentRunDetailPanel.vue";
import AgentPrecheckCard from "./AgentPrecheckCard.vue";
import AgentRunHistoryCard from "./AgentRunHistoryCard.vue";
import DatabaseSmokeCheckCard from "./DatabaseSmokeCheckCard.vue";
import HealthStatusCard from "./HealthStatusCard.vue";

type SystemSubsection = "overview" | "health" | "precheck" | "diagnostics";

const props = defineProps<{
  health: HealthResponse | null;
  healthLoading: boolean;
  healthErrorMessage: string;
  onRefreshHealth: () => void;
  agentPrecheck: AgentPrecheck | null;
  agentPrecheckLoading: boolean;
  agentPrecheckErrorMessage: string;
  onRefreshPrecheck: () => void;
  databaseSmokeReport: DatabaseSmokeReport | null;
  databaseSmokeLoading: boolean;
  databaseSmokeErrorMessage: string;
  onRunDatabaseSmoke: () => void;
  history: AgentRunHistory | null;
  threadHistory: AgentThreadHistory | null;
  threadDetail: AgentThreadDetail | null;
  selectedAgentResult: AgentResult | null;
  historyLoading: boolean;
  historyErrorMessage: string;
  selectedRunId: string | null;
  selectedThreadId: string | null;
  currentThreadId: string | null;
  threadDetailLoading: boolean;
  detailLoading: boolean;
  threadDetailErrorMessage: string;
  detailErrorMessage: string;
  onRefreshHistory: () => void;
  onInspectThread: (threadId: string) => void;
  onInspectRun: (runId: string) => void;
  onResumeThread: (runId: string) => void;
}>();

const currentSubsection = ref<SystemSubsection>("overview");

const runCount = computed(() => props.history?.items.length ?? 0);
const threadCount = computed(() => props.threadHistory?.items.length ?? 0);

const healthState = computed(() => {
  if (props.healthLoading) {
    return "检测中";
  }

  if (props.healthErrorMessage) {
    return "异常";
  }

  return props.health?.status ?? "未检查";
});

const precheckState = computed(() => {
  if (props.agentPrecheckLoading) {
    return "检查中";
  }

  if (props.agentPrecheckErrorMessage) {
    return "失败";
  }

  return props.agentPrecheck?.status ?? "未检查";
});

const diagnosticsState = computed(() => {
  if (props.historyLoading) {
    return "加载中";
  }

  if (props.historyErrorMessage) {
    return "异常";
  }

  if (runCount.value > 0 || threadCount.value > 0) {
    return "有记录";
  }

  return "暂无记录";
});

function selectSubsection(next: SystemSubsection) {
  currentSubsection.value = next;
}
</script>

<template>
  <section class="space-y-6">
    <section class="panel p-6">
      <div class="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
        <div class="max-w-3xl">
          <p class="text-sm font-semibold uppercase tracking-[0.24em] text-amber-700">
            System Workspace
          </p>
          <h2 class="mt-3 text-3xl font-semibold tracking-tight text-ink">
            系统联调工作台
          </h2>
          <p class="mt-3 text-sm leading-7 text-slate-600">
            后台系统区不再只是把卡片堆在一起，而是按排查顺序拆成三层：先看基础环境，再看运行前预检，最后进入运行后诊断。
          </p>
        </div>

        <div class="grid gap-3 sm:grid-cols-3">
          <article class="rounded-3xl bg-slate-50 p-4">
            <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">基础环境</p>
            <p class="mt-2 text-lg font-semibold text-slate-900">{{ healthState }}</p>
          </article>
          <article class="rounded-3xl bg-slate-50 p-4">
            <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">运行前预检</p>
            <p class="mt-2 text-lg font-semibold text-slate-900">{{ precheckState }}</p>
          </article>
          <article class="rounded-3xl bg-slate-50 p-4">
            <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">运行后诊断</p>
            <p class="mt-2 text-lg font-semibold text-slate-900">{{ diagnosticsState }}</p>
          </article>
        </div>
      </div>

      <div class="mt-6 flex flex-wrap gap-2">
        <button
          type="button"
          class="rounded-full px-4 py-2 text-sm transition"
          :class="
            currentSubsection === 'overview'
              ? 'bg-ink text-white'
              : 'border border-slate-200 text-slate-700 hover:border-slate-300 hover:bg-slate-50'
          "
          @click="selectSubsection('overview')"
        >
          概览
        </button>
        <button
          type="button"
          class="rounded-full px-4 py-2 text-sm transition"
          :class="
            currentSubsection === 'health'
              ? 'bg-ink text-white'
              : 'border border-slate-200 text-slate-700 hover:border-slate-300 hover:bg-slate-50'
          "
          @click="selectSubsection('health')"
        >
          基础环境
        </button>
        <button
          type="button"
          class="rounded-full px-4 py-2 text-sm transition"
          :class="
            currentSubsection === 'precheck'
              ? 'bg-ink text-white'
              : 'border border-slate-200 text-slate-700 hover:border-slate-300 hover:bg-slate-50'
          "
          @click="selectSubsection('precheck')"
        >
          运行前预检
        </button>
        <button
          type="button"
          class="rounded-full px-4 py-2 text-sm transition"
          :class="
            currentSubsection === 'diagnostics'
              ? 'bg-ink text-white'
              : 'border border-slate-200 text-slate-700 hover:border-slate-300 hover:bg-slate-50'
          "
          @click="selectSubsection('diagnostics')"
        >
          运行后诊断
        </button>
      </div>
    </section>

    <section v-if="currentSubsection === 'overview'" class="space-y-6">
      <div class="grid gap-6 xl:grid-cols-3">
        <article class="panel p-6">
          <p class="text-sm font-semibold text-slate-900">第一层：基础环境</p>
          <p class="mt-3 text-sm leading-7 text-slate-600">
            先确认前后端链路是否通畅，当前服务是否在线，运行环境和阶段是否符合预期。
          </p>
          <div class="mt-5 flex flex-wrap gap-2">
            <span class="chip bg-slate-100 text-slate-700">{{ healthState }}</span>
            <span class="chip bg-sky-100 text-sky-800">{{ props.health?.environment ?? "未知环境" }}</span>
          </div>
          <button
            type="button"
            class="mt-5 rounded-full border border-slate-200 px-4 py-2 text-sm text-slate-700 transition hover:border-slate-300 hover:bg-slate-50"
            @click="selectSubsection('health')"
          >
            进入基础环境
          </button>
        </article>

        <article class="panel p-6">
          <p class="text-sm font-semibold text-slate-900">第二层：运行前预检</p>
          <p class="mt-3 text-sm leading-7 text-slate-600">
            再确认模型配置、API 风格、工具状态和数据后端是否可用，避免问题拖到用户触发时才暴露。
          </p>
          <div class="mt-5 flex flex-wrap gap-2">
            <span class="chip bg-slate-100 text-slate-700">{{ precheckState }}</span>
            <span class="chip bg-amber-100 text-amber-800">
              {{ props.agentPrecheck?.catalogTotal ?? 0 }} 件商品
            </span>
          </div>
          <button
            type="button"
            class="mt-5 rounded-full border border-slate-200 px-4 py-2 text-sm text-slate-700 transition hover:border-slate-300 hover:bg-slate-50"
            @click="selectSubsection('precheck')"
          >
            进入运行前预检
          </button>
        </article>

        <article class="panel p-6">
          <p class="text-sm font-semibold text-slate-900">第三层：运行后诊断</p>
          <p class="mt-3 text-sm leading-7 text-slate-600">
            最后从线程、运行记录和当前选中详情中排查实际执行过程，必要时从任意节点恢复继续会话。
          </p>
          <div class="mt-5 flex flex-wrap gap-2">
            <span class="chip bg-slate-100 text-slate-700">{{ diagnosticsState }}</span>
            <span class="chip bg-sky-100 text-sky-800">{{ threadCount }} 条线程</span>
            <span class="chip bg-violet-100 text-violet-800">{{ runCount }} 条运行</span>
          </div>
          <button
            type="button"
            class="mt-5 rounded-full border border-slate-200 px-4 py-2 text-sm text-slate-700 transition hover:border-slate-300 hover:bg-slate-50"
            @click="selectSubsection('diagnostics')"
          >
            进入运行后诊断
          </button>
        </article>
      </div>

      <section class="panel p-6">
        <div class="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <h3 class="text-xl font-semibold text-ink">数据库真实写入验证</h3>
            <p class="mt-2 text-sm leading-7 text-slate-600">
              这一层会真正执行一轮数据库自检，不只是看数据库状态，而是验证商品、FAQ 和 Agent 日志是否能真实写入后再读回。
            </p>
          </div>

          <div class="flex flex-wrap gap-2">
            <span
              class="chip"
              :class="
                props.databaseSmokeReport?.persistenceEnabled
                  ? 'bg-emerald-100 text-emerald-800'
                  : props.databaseSmokeErrorMessage
                    ? 'bg-rose-100 text-rose-700'
                    : 'bg-slate-100 text-slate-700'
              "
            >
              {{
                props.databaseSmokeReport?.persistenceEnabled
                  ? '最近一次通过'
                  : props.databaseSmokeErrorMessage
                    ? '最近一次失败'
                    : '尚未执行'
              }}
            </span>
            <span class="chip bg-sky-100 text-sky-800">
              {{ props.health?.database_configured_backend ?? props.agentPrecheck?.databaseConfiguredBackend ?? "not-configured" }}
            </span>
            <button
              type="button"
              class="rounded-full border border-slate-200 px-4 py-2 text-sm text-slate-700 transition hover:border-slate-300 hover:bg-slate-50 disabled:cursor-wait disabled:opacity-70"
              :disabled="props.databaseSmokeLoading"
              @click="props.onRunDatabaseSmoke"
            >
              {{ props.databaseSmokeLoading ? "自检中..." : "运行一次自检" }}
            </button>
          </div>
        </div>
      </section>

      <section class="panel p-6">
        <h3 class="text-xl font-semibold text-ink">推荐排查顺序</h3>
        <div class="mt-4 grid gap-4 lg:grid-cols-3">
          <article class="rounded-3xl bg-slate-50 p-4">
            <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Step 1</p>
            <p class="mt-2 text-sm font-semibold text-slate-900">先看基础环境</p>
            <p class="mt-2 text-sm leading-6 text-slate-600">
              如果健康检查就异常，后面的预检和诊断都没有意义。
            </p>
          </article>
          <article class="rounded-3xl bg-slate-50 p-4">
            <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Step 2</p>
            <p class="mt-2 text-sm font-semibold text-slate-900">再看运行前预检</p>
            <p class="mt-2 text-sm leading-6 text-slate-600">
              这里负责把模型、工具和数据依赖问题提前拦住。
            </p>
          </article>
          <article class="rounded-3xl bg-slate-50 p-4">
            <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Step 3</p>
            <p class="mt-2 text-sm font-semibold text-slate-900">最后做运行后诊断</p>
            <p class="mt-2 text-sm leading-6 text-slate-600">
              结合线程时间线、工具调用和当前运行详情做最终排查。
            </p>
          </article>
        </div>
      </section>
    </section>

    <section v-else-if="currentSubsection === 'health'" class="space-y-4">
      <div>
        <h3 class="text-2xl font-semibold text-ink">基础环境</h3>
        <p class="mt-1 text-sm leading-6 text-slate-600">
          用于确认服务在线状态、运行环境和当前阶段，优先判断问题是不是出在最基础的链路上。
        </p>
      </div>

      <HealthStatusCard
        :health="health"
        :loading="healthLoading"
        :error-message="healthErrorMessage"
        :on-refresh="onRefreshHealth"
      />

      <DatabaseSmokeCheckCard
        :report="databaseSmokeReport"
        :loading="databaseSmokeLoading"
        :error-message="databaseSmokeErrorMessage"
        :configured-backend="health?.database_configured_backend ?? agentPrecheck?.databaseConfiguredBackend ?? ''"
        @run="onRunDatabaseSmoke"
      />
    </section>

    <section v-else-if="currentSubsection === 'precheck'" class="space-y-4">
      <div>
        <h3 class="text-2xl font-semibold text-ink">运行前预检</h3>
        <p class="mt-1 text-sm leading-6 text-slate-600">
          用于确认 Agent 运行前的模型、工具和数据依赖是否已经就绪。
        </p>
      </div>

      <AgentPrecheckCard
        :precheck="agentPrecheck"
        :loading="agentPrecheckLoading"
        :error-message="agentPrecheckErrorMessage"
        @refresh="onRefreshPrecheck"
      />
    </section>

    <section v-else class="space-y-4">
      <div>
        <h3 class="text-2xl font-semibold text-ink">运行后诊断</h3>
        <p class="mt-1 text-sm leading-6 text-slate-600">
          从线程时间线、运行列表和当前选中详情三个层次回看 Agent 真正是怎么跑的。
        </p>
      </div>

      <AgentRunHistoryCard
        :history="history"
        :thread-history="threadHistory"
        :thread-detail="threadDetail"
        :loading="historyLoading"
        :error-message="historyErrorMessage"
        :selected-run-id="selectedRunId"
        :selected-thread-id="selectedThreadId"
        :current-thread-id="currentThreadId"
        :thread-detail-loading="threadDetailLoading"
        :detail-loading="detailLoading"
        :thread-detail-error-message="threadDetailErrorMessage"
        :detail-error-message="detailErrorMessage"
        @refresh="onRefreshHistory"
        @inspect-thread="onInspectThread"
        @inspect="onInspectRun"
        @resume="onResumeThread"
      />

      <AdminAgentRunDetailPanel
        :result="selectedAgentResult"
        :loading="detailLoading"
        :error-message="detailErrorMessage"
        :selected-run-id="selectedRunId"
      />
    </section>
  </section>
</template>

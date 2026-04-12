<script setup lang="ts">
import { computed } from "vue";

import type {
  AgentPrecheck,
  AgentResult,
  AgentRunHistory,
  AgentThreadDetail,
  AgentThreadHistory,
} from "../types/agent";
import type { DatabaseSmokeReport, HealthResponse } from "../types/system";

import AdminSystemWorkspace from "./AdminSystemWorkspace.vue";
import KnowledgeBaseAdminPanel from "./KnowledgeBaseAdminPanel.vue";
import ProductCatalogAdminPanel from "./ProductCatalogAdminPanel.vue";

type AdminSection = "system" | "knowledge" | "catalog";

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
  entryLabel: string;
  activeSection: AdminSection;
}>();

const emit = defineEmits<{
  navigateSection: [section: AdminSection];
}>();

const sectionTitle = computed(() => {
  if (props.activeSection === "knowledge") {
    return "知识库管理";
  }

  if (props.activeSection === "catalog") {
    return "商品目录管理";
  }

  return "系统联调与诊断";
});

const sectionDescription = computed(() => {
  if (props.activeSection === "knowledge") {
    return "集中维护 FAQ 与知识文档，后续可以继续扩展为审核、导入和发布流程。";
  }

  if (props.activeSection === "catalog") {
    return "集中维护商品目录和示例数据，本地阶段继续使用 SQLite，后续上线再切换 PostgreSQL。";
  }

  return "用于联调、预检和诊断系统状态。系统区现在已经拆成更明确的二级结构，不再把所有模块平铺在同一页。";
});
</script>

<template>
  <section class="space-y-6">
    <section class="panel overflow-hidden">
      <div class="grid gap-6 px-6 py-8 lg:grid-cols-[1.12fr_0.88fr] lg:px-8">
        <div>
          <p class="text-sm font-semibold uppercase tracking-[0.24em] text-amber-700">
            Admin Workspace
          </p>
          <h1 class="mt-4 text-4xl font-semibold tracking-tight text-ink sm:text-5xl">
            后台工作区
          </h1>
          <p class="mt-5 max-w-3xl text-base leading-8 text-slate-600">
            后台已经和前台导购页分离。这里专门承接系统联调、运行诊断、知识维护和商品运营，
            后续可以继续演进为更正式的 <code>/admin</code> 工作区。
          </p>

          <div class="mt-6 flex flex-wrap gap-2">
            <button
              type="button"
              class="rounded-full px-4 py-2 text-sm transition"
              :class="
                activeSection === 'system'
                  ? 'bg-ink text-white'
                  : 'border border-slate-200 text-slate-700 hover:border-slate-300 hover:bg-slate-50'
              "
              @click="emit('navigateSection', 'system')"
            >
              系统
            </button>
            <button
              type="button"
              class="rounded-full px-4 py-2 text-sm transition"
              :class="
                activeSection === 'knowledge'
                  ? 'bg-ink text-white'
                  : 'border border-slate-200 text-slate-700 hover:border-slate-300 hover:bg-slate-50'
              "
              @click="emit('navigateSection', 'knowledge')"
            >
              知识库
            </button>
            <button
              type="button"
              class="rounded-full px-4 py-2 text-sm transition"
              :class="
                activeSection === 'catalog'
                  ? 'bg-ink text-white'
                  : 'border border-slate-200 text-slate-700 hover:border-slate-300 hover:bg-slate-50'
              "
              @click="emit('navigateSection', 'catalog')"
            >
              商品目录
            </button>
          </div>
        </div>

        <div class="rounded-[28px] bg-ink p-6 text-white">
          <p class="text-sm font-semibold uppercase tracking-[0.24em] text-amber-300">
            当前分区
          </p>
          <p class="mt-4 text-2xl font-semibold text-white">{{ sectionTitle }}</p>
          <p class="mt-4 text-sm leading-7 text-slate-200">
            {{ sectionDescription }}
          </p>

          <div class="mt-5 rounded-3xl bg-white/10 p-4">
            <p class="text-xs uppercase tracking-[0.18em] text-slate-300">入口策略</p>
            <p class="mt-2 text-sm leading-7 text-white">
              {{ entryLabel }}
            </p>
          </div>
        </div>
      </div>
    </section>

    <AdminSystemWorkspace
      v-if="activeSection === 'system'"
      :health="health"
      :health-loading="healthLoading"
      :health-error-message="healthErrorMessage"
      :on-refresh-health="onRefreshHealth"
      :agent-precheck="agentPrecheck"
      :agent-precheck-loading="agentPrecheckLoading"
      :agent-precheck-error-message="agentPrecheckErrorMessage"
      :on-refresh-precheck="onRefreshPrecheck"
      :database-smoke-report="databaseSmokeReport"
      :database-smoke-loading="databaseSmokeLoading"
      :database-smoke-error-message="databaseSmokeErrorMessage"
      :on-run-database-smoke="onRunDatabaseSmoke"
      :history="history"
      :thread-history="threadHistory"
      :thread-detail="threadDetail"
      :selected-agent-result="selectedAgentResult"
      :history-loading="historyLoading"
      :history-error-message="historyErrorMessage"
      :selected-run-id="selectedRunId"
      :selected-thread-id="selectedThreadId"
      :current-thread-id="currentThreadId"
      :thread-detail-loading="threadDetailLoading"
      :detail-loading="detailLoading"
      :thread-detail-error-message="threadDetailErrorMessage"
      :detail-error-message="detailErrorMessage"
      :on-refresh-history="onRefreshHistory"
      :on-inspect-thread="onInspectThread"
      :on-inspect-run="onInspectRun"
      :on-resume-thread="onResumeThread"
    />

    <KnowledgeBaseAdminPanel v-else-if="activeSection === 'knowledge'" />

    <ProductCatalogAdminPanel v-else />
  </section>
</template>

<script setup lang="ts">
import AdminAccessGate from "../components/AdminAccessGate.vue";
import AdminWorkbench from "../components/AdminWorkbench.vue";
import type {
  AgentPrecheck,
  AgentResult,
  AgentRunHistory,
  AgentThreadDetail,
  AgentThreadHistory,
} from "../types/agent";
import type { DatabaseSmokeReport, HealthResponse } from "../types/system";

type AdminSection = "system" | "knowledge" | "catalog";

const props = defineProps<{
  health: HealthResponse | null;
  healthLoading: boolean;
  healthErrorMessage: string;
  refreshHealth: () => void | Promise<void>;
  agentPrecheck: AgentPrecheck | null;
  agentPrecheckLoading: boolean;
  agentPrecheckErrorMessage: string;
  refreshPrecheck: () => void | Promise<void>;
  databaseSmokeReport: DatabaseSmokeReport | null;
  databaseSmokeLoading: boolean;
  databaseSmokeErrorMessage: string;
  runDatabaseSmoke: () => void | Promise<void>;
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
  refreshHistory: () => void | Promise<void>;
  inspectAgentThread: (threadId: string) => void | Promise<void>;
  inspectAgentRun: (runId: string) => void | Promise<void>;
  resumeAgentThread: (runId: string) => void | Promise<void>;
  entryLabel: string;
  activeSection: AdminSection;
  navigateSection: (section: AdminSection) => void;
}>();

async function refreshAdminWorkspace() {
  await Promise.all([props.refreshHealth(), props.refreshPrecheck(), props.refreshHistory()]);
}
</script>

<template>
  <AdminAccessGate :on-unlock="refreshAdminWorkspace">
    <AdminWorkbench
      :health="health"
      :health-loading="healthLoading"
      :health-error-message="healthErrorMessage"
      :on-refresh-health="refreshHealth"
      :agent-precheck="agentPrecheck"
      :agent-precheck-loading="agentPrecheckLoading"
      :agent-precheck-error-message="agentPrecheckErrorMessage"
      :on-refresh-precheck="refreshPrecheck"
      :database-smoke-report="databaseSmokeReport"
      :database-smoke-loading="databaseSmokeLoading"
      :database-smoke-error-message="databaseSmokeErrorMessage"
      :on-run-database-smoke="runDatabaseSmoke"
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
      :on-refresh-history="refreshHistory"
      :on-inspect-thread="inspectAgentThread"
      :on-inspect-run="inspectAgentRun"
      :on-resume-thread="resumeAgentThread"
      :entry-label="entryLabel"
      :active-section="activeSection"
      @navigate-section="navigateSection"
    />
  </AdminAccessGate>
</template>

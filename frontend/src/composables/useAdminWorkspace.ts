import { computed, ref } from "vue";

import { fetchAgentPrecheck } from "../api/agent";
import { runDatabaseSmokeCheck } from "../api/admin";
import { requestJson } from "../api/client";
import { devPanelsEntryLabel } from "../config/runtime";
import type { AgentPrecheck } from "../types/agent";
import type { DatabaseSmokeReport, HealthResponse } from "../types/system";

export function useAdminWorkspace() {
  const health = ref<HealthResponse | null>(null);
  const healthLoading = ref(false);
  const healthErrorMessage = ref("");

  const agentPrecheck = ref<AgentPrecheck | null>(null);
  const agentPrecheckLoading = ref(false);
  const agentPrecheckErrorMessage = ref("");

  const databaseSmokeReport = ref<DatabaseSmokeReport | null>(null);
  const databaseSmokeLoading = ref(false);
  const databaseSmokeErrorMessage = ref("");

  async function loadHealth() {
    healthLoading.value = true;
    healthErrorMessage.value = "";

    try {
      health.value = await requestJson<HealthResponse>("/health");
    } catch (error) {
      healthErrorMessage.value =
        error instanceof Error ? error.message : "未知错误，无法访问后端健康检查接口。";
    } finally {
      healthLoading.value = false;
    }
  }

  async function loadAgentPrecheck() {
    agentPrecheckLoading.value = true;
    agentPrecheckErrorMessage.value = "";

    try {
      agentPrecheck.value = await fetchAgentPrecheck();
    } catch (error) {
      agentPrecheck.value = null;
      agentPrecheckErrorMessage.value =
        error instanceof Error ? error.message : "未知错误，无法完成 Agent 预检。";
    } finally {
      agentPrecheckLoading.value = false;
    }
  }

  async function runDatabaseSmoke() {
    databaseSmokeLoading.value = true;
    databaseSmokeErrorMessage.value = "";

    try {
      const configuredBackend =
        agentPrecheck.value?.databaseConfiguredBackend || health.value?.database_configured_backend || "";
      const expectBackend =
        configuredBackend === "sqlite" || configuredBackend === "postgresql"
          ? configuredBackend
          : undefined;

      databaseSmokeReport.value = await runDatabaseSmokeCheck(
        expectBackend,
      );
      await Promise.all([loadHealth(), loadAgentPrecheck()]);
    } catch (error) {
      databaseSmokeErrorMessage.value =
        error instanceof Error ? error.message : "未知错误，无法完成数据库自检。";
    } finally {
      databaseSmokeLoading.value = false;
    }
  }

  const viewModel = computed(() => ({
    health: health.value,
    healthLoading: healthLoading.value,
    healthErrorMessage: healthErrorMessage.value,
    refreshHealth: loadHealth,
    agentPrecheck: agentPrecheck.value,
    agentPrecheckLoading: agentPrecheckLoading.value,
    agentPrecheckErrorMessage: agentPrecheckErrorMessage.value,
    refreshPrecheck: loadAgentPrecheck,
    databaseSmokeReport: databaseSmokeReport.value,
    databaseSmokeLoading: databaseSmokeLoading.value,
    databaseSmokeErrorMessage: databaseSmokeErrorMessage.value,
    runDatabaseSmoke,
    entryLabel: devPanelsEntryLabel,
  }));

  return {
    viewModel,
  };
}

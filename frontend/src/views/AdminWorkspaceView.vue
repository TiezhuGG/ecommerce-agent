<script setup lang="ts">
import AdminWorkbench from "../components/AdminWorkbench.vue";
import type { AgentPrecheck } from "../types/agent";
import type { HealthResponse } from "../types/system";

type AdminSection = "system" | "knowledge" | "catalog";

defineProps<{
  health: HealthResponse | null;
  healthLoading: boolean;
  healthErrorMessage: string;
  refreshHealth: () => void | Promise<void>;
  agentPrecheck: AgentPrecheck | null;
  agentPrecheckLoading: boolean;
  agentPrecheckErrorMessage: string;
  refreshPrecheck: () => void | Promise<void>;
  entryLabel: string;
  activeSection: AdminSection;
  navigateSection: (section: AdminSection) => void;
}>();
</script>

<template>
  <AdminWorkbench
    :health="health"
    :health-loading="healthLoading"
    :health-error-message="healthErrorMessage"
    :on-refresh-health="refreshHealth"
    :agent-precheck="agentPrecheck"
    :agent-precheck-loading="agentPrecheckLoading"
    :agent-precheck-error-message="agentPrecheckErrorMessage"
    :on-refresh-precheck="refreshPrecheck"
    :entry-label="entryLabel"
    :active-section="activeSection"
    @navigate-section="navigateSection"
  />
</template>

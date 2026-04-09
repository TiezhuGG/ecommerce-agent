<script setup lang="ts">
import { computed } from "vue";

import type { AgentPrecheck } from "../types/agent";
import type { HealthResponse } from "../types/system";

import AgentPrecheckCard from "./AgentPrecheckCard.vue";
import HealthStatusCard from "./HealthStatusCard.vue";
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

  return "系统联调与预检";
});

const sectionDescription = computed(() => {
  if (props.activeSection === "knowledge") {
    return "集中维护 FAQ 与知识文档，后续可以继续扩展为知识审核、导入审批和发布流。";
  }

  if (props.activeSection === "catalog") {
    return "集中维护商品目录和示例数据，当前仍然服务 SQLite 本地开发数据源。";
  }

  return "用于联调、诊断和确认系统运行状态，不再与前台导购链路混在一起。";
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
            后台已从前台导购页独立出来。这里专门承接联调、排障、知识维护和商品运营，
            后续可以继续扩展为真正的 `/admin` 体系。
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
            当前区域
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

    <div v-if="activeSection === 'system'" class="grid gap-6 xl:grid-cols-2">
      <HealthStatusCard
        :health="health"
        :loading="healthLoading"
        :error-message="healthErrorMessage"
        :on-refresh="onRefreshHealth"
      />

      <AgentPrecheckCard
        :precheck="agentPrecheck"
        :loading="agentPrecheckLoading"
        :error-message="agentPrecheckErrorMessage"
        @refresh="onRefreshPrecheck"
      />
    </div>

    <KnowledgeBaseAdminPanel v-else-if="activeSection === 'knowledge'" />

    <ProductCatalogAdminPanel v-else />
  </section>
</template>

<script setup lang="ts">
import { computed } from "vue";

import type { AgentPrecheck } from "../types/agent";

const props = defineProps<{
  precheck: AgentPrecheck | null;
  loading: boolean;
  errorMessage: string;
}>();

const emit = defineEmits<{
  refresh: [];
}>();

const summaryRows = computed(() => {
  if (!props.precheck) {
    return [] as Array<{ label: string; value: string | number }>;
  }

  return [
    { label: "整体状态", value: props.precheck.status },
    { label: "当前模型", value: props.precheck.model },
    { label: "API 风格", value: props.precheck.apiStyle },
    { label: "商品总数", value: props.precheck.catalogTotal },
    { label: "数据后端", value: props.precheck.dataBackend },
    { label: "配置目标", value: props.precheck.databaseConfiguredBackend },
    { label: "日志后端", value: props.precheck.agentLogBackend },
  ];
});

const runtimeRows = computed(() => {
  if (!props.precheck) {
    return [] as Array<{ label: string; value: string }>;
  }

  return [
    {
      label: "OpenAI SDK",
      value: props.precheck.openaiSdkAvailable ? "可用" : "不可用",
    },
    {
      label: "LangGraph",
      value: props.precheck.langgraphAvailable ? "可用" : "不可用",
    },
    {
      label: "Base URL",
      value: props.precheck.baseUrl ?? "使用 SDK 默认地址",
    },
    {
      label: "数据库状态",
      value: props.precheck.databaseRuntimeStatus,
    },
    {
      label: "持久化",
      value: props.precheck.databasePersistenceEnabled ? "已启用" : "未启用",
    },
  ];
});
</script>

<template>
  <section class="panel p-6">
    <div class="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
      <div class="max-w-3xl">
        <p class="text-sm font-semibold uppercase tracking-[0.24em] text-amber-700">
          Agent Precheck
        </p>
        <h2 class="mt-3 text-2xl font-semibold text-ink">运行前预检</h2>
        <p class="mt-3 text-sm leading-7 text-slate-600">
          这一层用于在真正发起 Agent 对话前，先确认模型配置、API 风格、运行框架、数据后端和工具依赖是否已经就绪。
          它的价值不是展示技术参数本身，而是把“运行前就能发现的问题”提前拦住。
        </p>
      </div>

      <button
        type="button"
        class="rounded-full border border-slate-200 px-4 py-2 text-sm text-slate-700 transition hover:border-slate-300 hover:bg-slate-50"
        :disabled="loading"
        @click="emit('refresh')"
      >
        {{ loading ? "检查中..." : "重新检查" }}
      </button>
    </div>

    <p
      v-if="errorMessage"
      class="mt-4 rounded-2xl bg-rose-50 px-4 py-3 text-sm text-rose-700"
    >
      预检失败：{{ errorMessage }}
    </p>

    <div
      v-else-if="loading && !precheck"
      class="mt-5 rounded-3xl bg-slate-50 px-5 py-10 text-center text-sm text-slate-600"
    >
      正在检查运行前依赖...
    </div>

    <div
      v-else-if="!precheck"
      class="mt-5 rounded-3xl bg-slate-50 px-5 py-10 text-center text-sm leading-7 text-slate-600"
    >
      这里会展示 Agent 运行前的关键依赖状态。点击上方“重新检查”后可以拉取最新预检结果。
    </div>

    <template v-else>
      <div class="mt-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        <article
          v-for="row in summaryRows"
          :key="row.label"
          class="rounded-3xl bg-slate-50 p-4"
        >
          <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">{{ row.label }}</p>
          <p class="mt-2 text-sm leading-6 font-semibold text-slate-900">{{ row.value }}</p>
        </article>
      </div>

      <div class="mt-6 grid gap-5 xl:grid-cols-[1.02fr_0.98fr]">
        <section class="rounded-[28px] bg-slate-50 p-5">
          <p class="text-sm font-semibold text-slate-800">预检摘要</p>
          <p class="mt-3 text-sm leading-7 text-slate-700">{{ precheck.summary }}</p>

          <div class="mt-4 rounded-2xl bg-white p-4">
            <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
              数据库运行态
            </p>
            <p class="mt-2 text-sm leading-7 text-slate-700">
              {{ precheck.databaseRuntimeMessage }}
            </p>
          </div>

          <div class="mt-5 grid gap-3 md:grid-cols-3">
            <article
              v-for="row in runtimeRows"
              :key="row.label"
              class="rounded-2xl bg-white p-4"
            >
              <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">{{ row.label }}</p>
              <p class="mt-2 text-sm leading-6 text-slate-700">{{ row.value }}</p>
            </article>
          </div>
        </section>

        <section class="rounded-[28px] bg-slate-50 p-5">
          <p class="text-sm font-semibold text-slate-800">工具状态</p>
          <p class="mt-2 text-sm leading-6 text-slate-600">
            这里聚焦“当前能不能调得起来”，而不是工具说明本身。
          </p>

          <div class="mt-4 space-y-3">
            <article
              v-for="tool in precheck.tools"
              :key="tool.name"
              class="rounded-2xl bg-white p-4"
            >
              <div class="flex items-center justify-between gap-3">
                <p class="text-sm font-semibold text-slate-900">{{ tool.name }}</p>
                <span
                  class="chip"
                  :class="tool.enabled ? 'bg-emerald-100 text-emerald-800' : 'bg-rose-100 text-rose-700'"
                >
                  {{ tool.enabled ? "可用" : "不可用" }}
                </span>
              </div>
              <p class="mt-2 text-sm leading-6 text-slate-600">{{ tool.description }}</p>
            </article>
          </div>
        </section>
      </div>

      <section v-if="precheck.warnings.length" class="mt-6 rounded-[28px] bg-slate-50 p-5">
        <p class="text-sm font-semibold text-slate-800">风险提示</p>
        <div class="mt-4 flex flex-wrap gap-2">
          <span
            v-for="warning in precheck.warnings"
            :key="warning"
            class="chip bg-amber-100 text-amber-800"
          >
            {{ warning }}
          </span>
        </div>
      </section>

      <section class="mt-6 grid gap-4 lg:grid-cols-3">
        <article class="rounded-3xl bg-slate-50 p-4">
          <p class="text-sm font-semibold text-slate-900">这个区域解决什么问题</p>
          <p class="mt-2 text-sm leading-6 text-slate-600">
            判断当前环境是否已经具备发起一次完整 Agent 运行所需的依赖条件。
          </p>
        </article>
        <article class="rounded-3xl bg-slate-50 p-4">
          <p class="text-sm font-semibold text-slate-900">适合什么时候看</p>
          <p class="mt-2 text-sm leading-6 text-slate-600">
            当 Agent 无法启动、工具调用异常、模型配置怀疑未生效时，优先看这里。
          </p>
        </article>
        <article class="rounded-3xl bg-slate-50 p-4">
          <p class="text-sm font-semibold text-slate-900">和后续链路的关系</p>
          <p class="mt-2 text-sm leading-6 text-slate-600">
            只有这里通过，后面的历史诊断和运行详情才有意义，否则问题往往出在运行前依赖层。
          </p>
        </article>
      </section>
    </template>
  </section>
</template>

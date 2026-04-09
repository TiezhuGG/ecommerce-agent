<script setup lang="ts">
import type { AgentPrecheck } from "../types/agent";

defineProps<{
  precheck: AgentPrecheck | null;
  loading: boolean;
  errorMessage: string;
}>();

const emit = defineEmits<{
  refresh: [];
}>();
</script>

<template>
  <section class="panel p-6">
    <div class="flex items-start justify-between gap-4">
      <div>
        <h2 class="panel-title">Agent 运行预检</h2>
        <p class="muted-copy mt-2">
          这个模块用于在真正发起 Agent 对话前，先检查 LangGraph、模型配置和业务工具是否可用。
          企业项目里这类“预检”很重要，因为它能把环境问题提前暴露出来，而不是等到用户点击后才报错。
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

    <template v-else-if="precheck">
      <div class="mt-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <div class="rounded-2xl bg-slate-50 p-4">
          <p class="text-xs text-slate-500">整体状态</p>
          <p class="mt-2 text-base font-semibold text-slate-900">{{ precheck.status }}</p>
        </div>
        <div class="rounded-2xl bg-slate-50 p-4">
          <p class="text-xs text-slate-500">当前模型</p>
          <p class="mt-2 text-base font-semibold text-slate-900">{{ precheck.model }}</p>
        </div>
        <div class="rounded-2xl bg-slate-50 p-4">
          <p class="text-xs text-slate-500">API 风格</p>
          <p class="mt-2 text-base font-semibold text-slate-900">{{ precheck.apiStyle }}</p>
        </div>
        <div class="rounded-2xl bg-slate-50 p-4">
          <p class="text-xs text-slate-500">商品数量</p>
          <p class="mt-2 text-base font-semibold text-slate-900">{{ precheck.catalogTotal }}</p>
        </div>
      </div>

      <div class="mt-5 rounded-3xl bg-slate-50 p-5">
        <p class="text-sm font-semibold text-slate-800">预检摘要</p>
        <p class="mt-2 text-sm leading-7 text-slate-600">{{ precheck.summary }}</p>
        <p class="mt-3 text-xs text-slate-500">
          base_url：{{ precheck.baseUrl ?? "使用 SDK 默认地址" }}
        </p>
        <p class="mt-2 text-xs text-slate-500">
          data_backend：{{ precheck.dataBackend }}
        </p>
        <p class="mt-2 text-xs text-slate-500">
          agent_log_backend：{{ precheck.agentLogBackend }}
        </p>
      </div>

      <div class="mt-5">
        <p class="text-sm font-semibold text-slate-800">工具状态</p>
        <div class="mt-3 grid gap-3 md:grid-cols-2">
          <div
            v-for="tool in precheck.tools"
            :key="tool.name"
            class="rounded-2xl border border-slate-200 bg-white p-4"
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
          </div>
        </div>
      </div>

      <div v-if="precheck.warnings.length" class="mt-5">
        <p class="text-sm font-semibold text-slate-800">风险提示</p>
        <div class="mt-3 flex flex-wrap gap-2">
          <span
            v-for="warning in precheck.warnings"
            :key="warning"
            class="chip bg-amber-100 text-amber-800"
          >
            {{ warning }}
          </span>
        </div>
      </div>
    </template>
  </section>
</template>

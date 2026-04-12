<script setup lang="ts">
import { computed } from "vue";

import type { HealthResponse } from "../types/system";

const props = defineProps<{
  health: HealthResponse | null;
  loading: boolean;
  errorMessage: string;
  onRefresh: () => void;
}>();

const statusLabel = computed(() => {
  if (props.loading) {
    return "检测中";
  }
  if (props.errorMessage) {
    return "异常";
  }
  return props.health?.status ?? "未检测";
});

const healthRows = computed(() => {
  return [
    { label: "服务名", value: props.health?.service ?? "等待后端响应" },
    { label: "运行环境", value: props.health?.environment ?? "未记录" },
    { label: "当前阶段", value: props.health?.phase ?? "phase-unknown" },
    { label: "数据后端", value: props.health?.data_backend ?? "not-recorded" },
    { label: "配置目标", value: props.health?.database_configured_backend ?? "not-configured" },
    {
      label: "持久化",
      value: props.health?.database_persistence_enabled ? "已启用" : "未启用",
    },
  ];
});
</script>

<template>
  <section class="panel p-6">
    <div class="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
      <div class="max-w-3xl">
        <p class="text-sm font-semibold uppercase tracking-[0.24em] text-amber-700">
          System Health
        </p>
        <h2 class="mt-3 text-2xl font-semibold text-ink">
          基础服务联通状态
        </h2>
        <p class="mt-3 text-sm leading-7 text-slate-600">
          这一层只负责回答最基础的问题：前端当前还能不能访问后端、后端运行在什么环境、现在的项目阶段和数据后端是什么。
          如果这里就异常，后面的预检和运行诊断都不值得继续看。
        </p>
      </div>

      <button
        type="button"
        class="rounded-full bg-ink px-4 py-2 text-sm font-medium text-white transition hover:bg-slate-800 disabled:cursor-wait disabled:opacity-70"
        :disabled="loading"
        @click="onRefresh"
      >
        {{ loading ? "检测中..." : "刷新状态" }}
      </button>
    </div>

    <div class="mt-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      <article class="rounded-3xl bg-slate-50 p-4">
        <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">整体状态</p>
        <p class="mt-2 text-lg font-semibold text-slate-900">{{ statusLabel }}</p>
      </article>
      <article
        v-for="row in healthRows"
        :key="row.label"
        class="rounded-3xl bg-slate-50 p-4"
      >
        <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">{{ row.label }}</p>
        <p class="mt-2 text-sm leading-6 text-slate-900">{{ row.value }}</p>
      </article>
    </div>

    <p
      v-if="errorMessage"
      class="mt-4 rounded-2xl bg-rose-50 px-4 py-3 text-sm text-rose-700"
    >
      当前无法连接后端：{{ errorMessage }}
    </p>

    <section v-else-if="health" class="mt-6 rounded-[28px] bg-slate-50 p-5">
      <div class="flex flex-wrap items-center gap-2">
        <span class="chip bg-slate-100 text-slate-700">
          数据库状态: {{ health.database_runtime_status ?? "unknown" }}
        </span>
        <span
          class="chip"
          :class="
            health.database_persistence_enabled
              ? 'bg-emerald-100 text-emerald-800'
              : 'bg-amber-100 text-amber-800'
          "
        >
          {{ health.database_persistence_enabled ? "当前写入会保留" : "当前写入不会保留" }}
        </span>
      </div>
      <p class="mt-4 text-sm leading-7 text-slate-700">
        {{ health.database_runtime_message ?? "数据库运行状态未记录。" }}
      </p>
    </section>

    <section class="mt-6 grid gap-4 lg:grid-cols-3">
      <article class="rounded-3xl bg-slate-50 p-4">
        <p class="text-sm font-semibold text-slate-900">这个区域解决什么问题</p>
        <p class="mt-2 text-sm leading-6 text-slate-600">
          先确认系统是否在线，避免把网络、服务启动或环境配置问题误判成 Agent 逻辑问题。
        </p>
      </article>
      <article class="rounded-3xl bg-slate-50 p-4">
        <p class="text-sm font-semibold text-slate-900">适合什么时候看</p>
        <p class="mt-2 text-sm leading-6 text-slate-600">
          当前台接口全都异常、后台无响应，或者你怀疑环境切换后没有真正生效时，优先看这里。
        </p>
      </article>
      <article class="rounded-3xl bg-slate-50 p-4">
        <p class="text-sm font-semibold text-slate-900">和后续链路的关系</p>
        <p class="mt-2 text-sm leading-6 text-slate-600">
          商品搜索、FAQ、对比和 Agent 都依赖同一套后端可达性，所以这是整个系统区的第一层入口。
        </p>
      </article>
    </section>
  </section>
</template>

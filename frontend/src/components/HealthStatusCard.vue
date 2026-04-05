<script setup lang="ts">
import type { HealthResponse } from "../types/system";

defineProps<{
  health: HealthResponse | null;
  loading: boolean;
  errorMessage: string;
  onRefresh: () => void;
}>();
</script>

<template>
  <section class="panel p-6">
    <div class="flex items-start justify-between gap-4">
      <div>
        <p class="text-sm font-semibold uppercase tracking-[0.24em] text-amber-700">
          系统联通状态
        </p>
        <h2 class="mt-3 text-2xl font-semibold text-ink">基础后端已接通</h2>
        <p class="mt-3 max-w-2xl text-sm leading-7 text-slate-600">
          这个模块只负责验证前端是否能正常访问 FastAPI。后续商品搜索、FAQ、对比分析和 Agent 工作流
          都会复用同一套前后端通信基础，所以这里相当于整个项目的“系统体检入口”。
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
      <div class="rounded-2xl bg-slate-50 p-4">
        <p class="text-xs text-slate-500">状态</p>
        <p class="mt-2 text-base font-semibold text-slate-900">
          {{ errorMessage ? "异常" : health?.status ?? "未知" }}
        </p>
      </div>
      <div class="rounded-2xl bg-slate-50 p-4">
        <p class="text-xs text-slate-500">服务名</p>
        <p class="mt-2 text-base font-semibold text-slate-900">
          {{ health?.service ?? "等待后端响应" }}
        </p>
      </div>
      <div class="rounded-2xl bg-slate-50 p-4">
        <p class="text-xs text-slate-500">运行环境</p>
        <p class="mt-2 text-base font-semibold text-slate-900">
          {{ health?.environment ?? "未知" }}
        </p>
      </div>
      <div class="rounded-2xl bg-slate-50 p-4">
        <p class="text-xs text-slate-500">当前阶段</p>
        <p class="mt-2 text-base font-semibold text-slate-900">
          {{ health?.phase ?? "phase-unknown" }}
        </p>
      </div>
    </div>

    <p
      v-if="errorMessage"
      class="mt-4 rounded-2xl bg-rose-50 px-4 py-3 text-sm text-rose-700"
    >
      当前无法连接后端：{{ errorMessage }}
    </p>
  </section>
</template>

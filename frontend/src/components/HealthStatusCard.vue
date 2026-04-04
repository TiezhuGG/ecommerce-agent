<script setup lang="ts">
import type { HealthResponse } from "../types";

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
        <h2 class="mt-3 text-2xl font-semibold text-ink">基础后端已接入</h2>
        <p class="mt-3 max-w-2xl text-sm leading-7 text-slate-600">
          这个区域只负责验证前后端链路是否通畅。你可以把它理解成整个项目的基础设施探针：
          `/health` 正常，说明前端至少能访问 FastAPI；后续搜索、FAQ、Agent 接口都会复用同一条链路。
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
          {{ health?.phase ?? "phase-1" }}
        </p>
      </div>
    </div>

    <p v-if="errorMessage" class="mt-4 rounded-2xl bg-rose-50 px-4 py-3 text-sm text-rose-700">
      当前无法连接后端：{{ errorMessage }}
    </p>
  </section>
</template>

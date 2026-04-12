<script setup lang="ts">
import type { DatabaseSmokeReport } from "../types/system";

const props = defineProps<{
  report: DatabaseSmokeReport | null;
  loading: boolean;
  errorMessage: string;
  configuredBackend: string;
}>();

const emit = defineEmits<{
  run: [];
}>();
</script>

<template>
  <section class="panel p-6">
    <div class="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
      <div class="max-w-3xl">
        <p class="text-sm font-semibold uppercase tracking-[0.24em] text-amber-700">
          Database Smoke
        </p>
        <h2 class="mt-3 text-2xl font-semibold text-ink">数据库自检</h2>
        <p class="mt-3 text-sm leading-7 text-slate-600">
          这一步不是只看数据库“能不能连上”，而是实际验证初始化、seed、商品目录、知识库条目和
          Agent 日志是否都能真正写入当前数据库。
        </p>
      </div>

      <button
        type="button"
        class="rounded-full bg-ink px-4 py-2 text-sm font-medium text-white transition hover:bg-slate-800 disabled:cursor-wait disabled:opacity-70"
        :disabled="loading"
        @click="emit('run')"
      >
        {{ loading ? "自检中..." : "运行数据库自检" }}
      </button>
    </div>

    <div class="mt-6 flex flex-wrap gap-2">
      <span class="chip bg-slate-100 text-slate-700">
        配置目标: {{ configuredBackend || "not-configured" }}
      </span>
      <span
        class="chip"
        :class="
          report?.persistenceEnabled
            ? 'bg-emerald-100 text-emerald-800'
            : 'bg-amber-100 text-amber-800'
        "
      >
        {{ report?.persistenceEnabled ? "最近一次自检已验证持久化" : "尚未验证持久化" }}
      </span>
    </div>

    <div
      v-if="errorMessage"
      class="mt-6 rounded-3xl border border-rose-200 bg-rose-50 p-5"
    >
      <span class="chip bg-rose-100 text-rose-700">数据库自检失败</span>
      <p class="mt-4 text-lg font-semibold text-rose-900">当前数据库链路还没有通过真实写入验证</p>
      <p class="mt-3 text-sm leading-7 text-rose-800">
        先确认后台系统区里的数据库运行态是否为 ready，再检查 Docker、DATABASE_URL 和目标数据库是否真的可用。
      </p>
      <p class="mt-4 rounded-2xl bg-white/80 px-4 py-3 text-sm text-rose-700">
        {{ errorMessage }}
      </p>
    </div>

    <div
      v-else-if="loading && !report"
      class="mt-6 rounded-3xl border border-slate-200 bg-slate-50 p-5"
    >
      <div class="flex flex-wrap items-center gap-2">
        <span class="chip bg-sky-100 text-sky-800">正在运行数据库自检</span>
        <span class="chip bg-white text-slate-700">会临时写入并自动清理测试数据</span>
      </div>
      <p class="mt-4 text-sm leading-7 text-slate-600">
        系统正在验证数据库初始化、seed 数据读取、商品目录 CRUD、知识库条目 CRUD 和 Agent
        日志写入链路。
      </p>
    </div>

    <div v-else-if="report" class="mt-6 space-y-5">
      <div class="rounded-3xl border border-emerald-200 bg-emerald-50 p-5">
        <div class="flex flex-wrap items-center gap-2">
          <span class="chip bg-emerald-100 text-emerald-800">数据库自检通过</span>
          <span class="chip bg-white text-slate-700">{{ report.runtimeBackend }}</span>
          <span class="chip bg-white text-slate-700">状态: {{ report.runtimeStatus }}</span>
        </div>
        <p class="mt-4 text-sm leading-7 text-emerald-950">
          {{ report.runtimeMessage }}
        </p>
      </div>

      <div class="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
        <article class="rounded-3xl bg-slate-50 p-4">
          <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">商品总数</p>
          <p class="mt-2 text-lg font-semibold text-slate-900">{{ report.productTotal }}</p>
        </article>
        <article class="rounded-3xl bg-slate-50 p-4">
          <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">FAQ 总数</p>
          <p class="mt-2 text-lg font-semibold text-slate-900">{{ report.faqTotal }}</p>
        </article>
        <article class="rounded-3xl bg-slate-50 p-4">
          <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">临时商品</p>
          <p class="mt-2 text-sm leading-6 text-slate-900 break-all">{{ report.createdProductId }}</p>
        </article>
        <article class="rounded-3xl bg-slate-50 p-4">
          <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">临时 FAQ</p>
          <p class="mt-2 text-sm leading-6 text-slate-900 break-all">{{ report.createdFaqEntryId }}</p>
        </article>
        <article class="rounded-3xl bg-slate-50 p-4">
          <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">临时日志</p>
          <p class="mt-2 text-sm leading-6 text-slate-900 break-all">{{ report.persistedRunId }}</p>
        </article>
      </div>

      <section class="grid gap-4 lg:grid-cols-3">
        <article class="rounded-3xl bg-slate-50 p-4">
          <p class="text-sm font-semibold text-slate-900">这个区域解决什么问题</p>
          <p class="mt-2 text-sm leading-6 text-slate-600">
            把“能连上数据库”和“真的能持久化业务数据”这两件事彻底区分开。
          </p>
        </article>
        <article class="rounded-3xl bg-slate-50 p-4">
          <p class="text-sm font-semibold text-slate-900">适合什么时候看</p>
          <p class="mt-2 text-sm leading-6 text-slate-600">
            刚切换 SQLite / PostgreSQL、准备上线前验证，或者怀疑数据库已经 fallback 到 seed 时。
          </p>
        </article>
        <article class="rounded-3xl bg-slate-50 p-4">
          <p class="text-sm font-semibold text-slate-900">和后续链路的关系</p>
          <p class="mt-2 text-sm leading-6 text-slate-600">
            只有数据库自检通过，后台管理改动和 Agent 运行日志才真的具备可复盘价值。
          </p>
        </article>
      </section>
    </div>

    <div
      v-else
      class="mt-6 rounded-3xl border border-dashed border-slate-300 bg-slate-50 p-5"
    >
      <span class="chip bg-slate-100 text-slate-700">还没有运行数据库自检</span>
      <p class="mt-4 text-lg font-semibold text-slate-900">先执行一次真实写入验证</p>
      <p class="mt-3 text-sm leading-7 text-slate-600">
        这一步会临时写入一条商品、一条 FAQ 和一条 Agent 日志，再自动清理，用于确认当前数据库不是“看起来可用”，而是真的能持久化。
      </p>
    </div>
  </section>
</template>

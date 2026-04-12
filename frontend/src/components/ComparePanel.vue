<script setup lang="ts">
import type { CompareResponse } from "../api/contracts/compare";
import type { Product } from "../types/catalog";

defineProps<{
  selectedProducts: Product[];
  result: CompareResponse | null;
  loading: boolean;
  errorMessage: string;
}>();
</script>

<template>
  <section class="panel p-6">
    <div class="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
      <div class="max-w-3xl">
        <p class="text-sm font-semibold uppercase tracking-[0.24em] text-amber-700">
          Compare
        </p>
        <h2 class="mt-3 text-2xl font-semibold text-ink">商品对比</h2>
        <p class="mt-3 text-sm leading-7 text-slate-600">
          这里会把你选中的商品并排展示，并给出价格与重点差异总结，方便快速判断哪一款更适合自己。
        </p>
      </div>

      <span class="chip bg-slate-100 text-slate-700">已选 {{ selectedProducts.length }} 件</span>
    </div>

    <div class="mt-6 grid gap-4 lg:grid-cols-3">
      <article
        v-for="product in selectedProducts"
        :key="product.id"
        class="rounded-3xl bg-slate-50 p-5"
      >
        <p class="text-sm text-slate-500">{{ product.brand }} / {{ product.category }}</p>
        <h3 class="mt-2 text-base font-semibold text-slate-900">{{ product.name }}</h3>
        <p class="mt-3 text-2xl font-semibold text-slate-900">CNY {{ product.price }}</p>
        <ul class="mt-4 space-y-2 text-sm text-slate-600">
          <li v-for="spec in product.specs" :key="spec">- {{ spec }}</li>
        </ul>
      </article>

      <div
        v-if="selectedProducts.length === 0"
        class="rounded-3xl border border-dashed border-slate-300 bg-slate-50 p-6 text-sm leading-7 text-slate-600 lg:col-span-3"
      >
        先从商品结果里勾选你想比较的商品。选中后，这里会自动显示并排对比结果。
      </div>
    </div>

    <div
      v-if="loading"
      class="mt-6 rounded-3xl border border-emerald-200 bg-emerald-50 p-5"
    >
      <div class="flex flex-wrap items-center gap-2">
        <span class="chip bg-emerald-100 text-emerald-800">正在生成商品对比</span>
        <span class="chip bg-white text-slate-700">会自动总结关键差异</span>
      </div>
      <p class="mt-4 text-sm leading-7 text-emerald-900">
        系统正在对价格、重点参数、适用场景和推荐理由做横向整理，通常只需要几秒。
      </p>
    </div>
    <div
      v-else-if="errorMessage"
      class="mt-6 rounded-3xl border border-rose-200 bg-rose-50 p-5"
    >
      <span class="chip bg-rose-100 text-rose-700">商品对比暂时不可用</span>
      <p class="mt-4 text-lg font-semibold text-rose-900">这次没有成功生成对比结论</p>
      <p class="mt-3 text-sm leading-7 text-rose-800">
        可以先减少对比商品数量，或者回到左侧重新挑选更明确的候选商品，再试一次。
      </p>
      <p class="mt-4 rounded-2xl bg-white/80 px-4 py-3 text-sm text-rose-700">
        {{ errorMessage }}
      </p>
    </div>

    <div
      v-else-if="result"
      class="mt-6 space-y-4 rounded-3xl bg-amber-50 p-5 text-sm leading-7 text-amber-900"
    >
      <p class="text-base font-semibold text-amber-950">关键结论</p>
      <p>{{ result.summary }}</p>

      <ul class="space-y-2">
        <li v-for="item in result.highlights" :key="item">- {{ item }}</li>
      </ul>
    </div>

    <div
      v-else-if="selectedProducts.length"
      class="mt-6 rounded-3xl border border-dashed border-slate-300 bg-slate-50 p-5"
    >
      <span class="chip bg-slate-100 text-slate-700">等待生成结论</span>
      <p class="mt-4 text-lg font-semibold text-slate-900">已选商品，马上就能开始对比</p>
      <p class="mt-3 text-sm leading-7 text-slate-600">
        当前商品卡片已经就位。系统会根据已选商品给出价格差异、适合场景和推荐理由总结。
      </p>
    </div>
  </section>
</template>

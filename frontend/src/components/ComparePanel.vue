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
    <div class="flex items-center justify-between gap-4">
      <div>
        <h2 class="panel-title">商品对比区</h2>
        <p class="muted-copy mt-2">
          这里已经接入真实后端接口。它和商品搜索、FAQ 一样，都是后续 Agent 可以直接复用的业务工具。
          当前对比结论仍然由后端规则逻辑生成，还没有交给模型总结。
        </p>
      </div>
      <span class="chip bg-slate-100 text-slate-700">已选 {{ selectedProducts.length }} 件</span>
    </div>

    <div class="mt-6 grid gap-4 lg:grid-cols-3">
      <div
        v-for="product in selectedProducts"
        :key="product.id"
        class="rounded-3xl bg-slate-50 p-5"
      >
        <p class="text-sm text-slate-500">{{ product.brand }} · {{ product.category }}</p>
        <h3 class="mt-2 text-base font-semibold text-slate-900">{{ product.name }}</h3>
        <p class="mt-3 text-2xl font-semibold text-slate-900">¥{{ product.price }}</p>
        <ul class="mt-4 space-y-2 text-sm text-slate-600">
          <li v-for="spec in product.specs" :key="spec">- {{ spec }}</li>
        </ul>
      </div>

      <div
        v-if="selectedProducts.length === 0"
        class="rounded-3xl border border-dashed border-slate-300 bg-slate-50 p-6 text-sm text-slate-600 lg:col-span-3"
      >
        先从商品列表中选择要比较的商品。
      </div>
    </div>

    <p v-if="loading" class="mt-6 text-sm text-slate-600">正在生成商品对比结果...</p>
    <p
      v-else-if="errorMessage"
      class="mt-6 rounded-2xl bg-rose-50 px-4 py-3 text-sm text-rose-700"
    >
      商品对比失败：{{ errorMessage }}
    </p>

    <div
      v-else-if="result"
      class="mt-6 space-y-4 rounded-3xl bg-amber-50 p-5 text-sm leading-7 text-amber-900"
    >
      <p>{{ result.summary }}</p>

      <ul class="space-y-2">
        <li v-for="item in result.highlights" :key="item">- {{ item }}</li>
      </ul>
    </div>
  </section>
</template>

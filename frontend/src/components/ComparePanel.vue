<script setup lang="ts">
import { computed } from "vue";

import type { Product } from "../types";

const props = defineProps<{
  selectedProducts: Product[];
}>();

const comparisonSummary = computed(() => {
  if (props.selectedProducts.length < 2) {
    return "至少选择 2 个商品后，这里会给出价格差异、适用人群和购买建议。下一轮我们会把它迁到后端接口。";
  }

  const cheapest = [...props.selectedProducts].sort((a, b) => a.price - b.price)[0];
  const expensive = [...props.selectedProducts].sort((a, b) => b.price - a.price)[0];

  return `当前对比中，${cheapest.name} 的参考价更低，${expensive.name} 的定位更高。后续这里会接真实对比接口，并明确区分“数据事实”和“AI 总结”。`;
});
</script>

<template>
  <section class="panel p-6">
    <div class="flex items-center justify-between gap-4">
      <div>
        <h2 class="panel-title">商品对比区</h2>
        <p class="muted-copy mt-2">
          这一块暂时还保留前端演示逻辑。它的意义是先把“选中商品 ->
          生成对比结论”的业务链路摆出来，下一轮再迁到后端接口。
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
          <li v-for="spec in product.specs" :key="spec">• {{ spec }}</li>
        </ul>
      </div>

      <div
        v-if="selectedProducts.length === 0"
        class="rounded-3xl border border-dashed border-slate-300 bg-slate-50 p-6 text-sm text-slate-600 lg:col-span-3"
      >
        先从商品列表中选择要比较的商品。
      </div>
    </div>

    <div class="mt-6 rounded-3xl bg-amber-50 p-5 text-sm leading-7 text-amber-900">
      {{ comparisonSummary }}
    </div>
  </section>
</template>

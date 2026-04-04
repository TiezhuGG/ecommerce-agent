<script setup lang="ts">
import type { Product } from "../types";

defineProps<{
  products: Product[];
  selectedIds: string[];
}>();

const emit = defineEmits<{
  toggleCompare: [productId: string];
}>();
</script>

<template>
  <section class="panel p-6">
    <div class="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <h2 class="panel-title">商品结果区</h2>
        <p class="muted-copy mt-2">
          这里当前展示的是前端静态商品数据。等第二轮迭代开始，会改为真实后端搜索接口返回的数据。
        </p>
      </div>
      <span class="chip bg-slate-100 text-slate-700">当前结果 {{ products.length }} 条</span>
    </div>

    <div
      v-if="products.length"
      class="mt-6 grid gap-4 sm:grid-cols-2 2xl:grid-cols-3"
    >
      <article
        v-for="product in products"
        :key="product.id"
        class="rounded-3xl border border-slate-200 bg-white p-5 transition hover:-translate-y-0.5 hover:shadow-lg"
      >
        <div class="flex items-start justify-between gap-4">
          <div>
            <p class="text-sm font-medium text-amber-700">{{ product.category }}</p>
            <h3 class="mt-2 text-lg font-semibold text-slate-900">{{ product.name }}</h3>
          </div>
          <span class="rounded-full bg-slate-100 px-3 py-1 text-xs text-slate-600">
            {{ product.brand }}
          </span>
        </div>

        <p class="mt-4 text-3xl font-semibold text-slate-900">¥{{ product.price }}</p>
        <p class="mt-3 text-sm leading-7 text-slate-600">{{ product.summary }}</p>
        <p class="mt-3 text-sm text-slate-500">适用场景：{{ product.scenario }}</p>

        <div class="mt-4 flex flex-wrap gap-2">
          <span
            v-for="tag in product.tags"
            :key="tag"
            class="chip bg-amber-100 text-amber-800"
          >
            {{ tag }}
          </span>
        </div>

        <ul class="mt-5 space-y-2 text-sm text-slate-600">
          <li v-for="spec in product.specs" :key="spec">• {{ spec }}</li>
        </ul>

        <button
          type="button"
          class="mt-5 w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm font-medium text-slate-800 transition hover:border-slate-300 hover:bg-slate-50"
          @click="emit('toggleCompare', product.id)"
        >
          {{ selectedIds.includes(product.id) ? "移出对比" : "加入对比" }}
        </button>
      </article>
    </div>

    <div
      v-else
      class="mt-6 rounded-3xl border border-dashed border-slate-300 bg-slate-50 px-6 py-10 text-center"
    >
      <p class="text-base font-medium text-slate-900">当前没有命中商品</p>
      <p class="mt-2 text-sm text-slate-600">
        这就是未来真实搜索接口需要覆盖的一个典型场景。第一版先只展示空状态，不做复杂兜底。
      </p>
    </div>
  </section>
</template>

<script setup lang="ts">
import type { Product } from "../types/catalog";

defineProps<{
  products: Product[];
  selectedIds: string[];
  recommendedIds: string[];
  loading: boolean;
  errorMessage: string;
  appliedFilters: string[];
}>();

const emit = defineEmits<{
  toggleCompare: [productId: string];
}>();
</script>

<template>
  <section class="panel p-6">
    <div class="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <h2 class="panel-title">商品结果</h2>
        <p class="muted-copy mt-2">
          这里只保留最需要的信息。当前窗口最多同时展示 4 张卡片，其余商品向下滚动查看。
        </p>
      </div>
      <span class="chip bg-slate-100 text-slate-700">当前共 {{ products.length }} 件</span>
    </div>

    <div v-if="appliedFilters.length" class="mt-4 flex flex-wrap gap-2">
      <span
        v-for="filter in appliedFilters"
        :key="filter"
        class="chip bg-sky-100 text-sky-800"
      >
        {{ filter }}
      </span>
    </div>

    <p v-if="loading" class="mt-6 text-sm text-slate-600">正在加载商品列表...</p>
    <p
      v-else-if="errorMessage"
      class="mt-6 rounded-2xl bg-rose-50 px-4 py-3 text-sm text-rose-700"
    >
      商品加载失败：{{ errorMessage }}
    </p>

    <div
      v-else-if="products.length"
      class="mt-6 max-h-[1320px] overflow-y-auto pr-2 xl:max-h-[880px]"
    >
      <div class="grid gap-4 xl:grid-cols-2">
        <article
          v-for="product in products"
          :key="product.id"
          class="rounded-3xl border bg-white p-5 transition hover:-translate-y-0.5 hover:shadow-lg"
          :class="
            selectedIds.includes(product.id)
              ? 'border-sky-300 shadow-[0_18px_40px_rgba(14,165,233,0.14)]'
              : recommendedIds.includes(product.id)
                ? 'border-amber-300 shadow-[0_18px_40px_rgba(245,158,11,0.14)]'
                : 'border-slate-200'
          "
        >
          <div class="flex items-start justify-between gap-4">
            <div>
              <div class="flex flex-wrap items-center gap-2">
                <span class="chip bg-slate-100 text-slate-700">{{ product.category }}</span>
                <span
                  v-if="recommendedIds.includes(product.id)"
                  class="chip bg-amber-100 text-amber-800"
                >
                  AI 推荐
                </span>
                <span
                  v-if="selectedIds.includes(product.id)"
                  class="chip bg-sky-100 text-sky-800"
                >
                  已加入对比
                </span>
              </div>
              <h3 class="mt-3 text-lg font-semibold text-slate-900">{{ product.name }}</h3>
            </div>

            <span class="rounded-full bg-slate-100 px-3 py-1 text-xs text-slate-600">
              {{ product.brand }}
            </span>
          </div>

          <p class="mt-4 text-3xl font-semibold text-slate-900">￥{{ product.price }}</p>
          <p class="mt-1 text-xs text-slate-500">{{ product.price_note }}</p>

          <p class="mt-4 line-clamp-2 text-sm leading-7 text-slate-700">
            {{ product.summary }}
          </p>
          <p class="mt-2 line-clamp-1 text-sm text-slate-500">
            适用场景：{{ product.scenario }}
          </p>

          <div class="mt-4 flex flex-wrap gap-2">
            <span
              v-for="tag in product.tags.slice(0, 3)"
              :key="tag"
              class="chip bg-amber-100 text-amber-800"
            >
              {{ tag }}
            </span>
            <span
              v-if="product.tags.length > 3"
              class="chip bg-slate-100 text-slate-700"
            >
              +{{ product.tags.length - 3 }}
            </span>
          </div>

          <div class="mt-5 rounded-2xl bg-slate-50 p-4">
            <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
              重点参数
            </p>
            <ul class="mt-3 space-y-2 text-sm text-slate-700">
              <li v-for="spec in product.specs.slice(0, 2)" :key="spec">- {{ spec }}</li>
              <li v-if="product.specs.length > 2" class="text-slate-500">
                还有 {{ product.specs.length - 2 }} 条参数可在官网查看
              </li>
            </ul>
          </div>

          <div class="mt-5 grid gap-3 sm:grid-cols-2">
            <button
              type="button"
              class="rounded-2xl border border-slate-200 px-4 py-3 text-sm font-medium text-slate-800 transition hover:border-slate-300 hover:bg-slate-50"
              @click="emit('toggleCompare', product.id)"
            >
              {{ selectedIds.includes(product.id) ? "移出对比" : "加入对比" }}
            </button>

            <a
              :href="product.official_url"
              target="_blank"
              rel="noreferrer"
              class="rounded-2xl border border-slate-200 px-4 py-3 text-center text-sm font-medium text-slate-700 transition hover:border-slate-300 hover:bg-slate-50"
            >
              查看官网
            </a>
          </div>
        </article>
      </div>
    </div>

    <div
      v-else
      class="mt-6 rounded-3xl border border-dashed border-slate-300 bg-slate-50 px-6 py-10 text-center"
    >
      <p class="text-base font-medium text-slate-900">当前没有命中商品</p>
      <p class="mt-2 text-sm text-slate-600">
        试着放宽预算、清空品牌限制，或者直接让 AI 帮你重新推荐。
      </p>
    </div>
  </section>
</template>

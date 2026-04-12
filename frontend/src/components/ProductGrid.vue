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
    <div class="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
      <div class="max-w-3xl">
        <p class="text-sm font-semibold uppercase tracking-[0.24em] text-amber-700">
          Product Results
        </p>
        <h2 class="mt-3 text-2xl font-semibold text-ink">商品结果</h2>
        <p class="mt-3 text-sm leading-7 text-slate-600">
          这里只保留对决策最有帮助的信息。当前窗口会优先展示前 4 张左右的卡片，其余结果向下滚动查看，避免首页被商品列表完全占满。
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

    <div v-if="loading" class="mt-6 space-y-4">
      <div class="rounded-3xl border border-slate-200 bg-slate-50 p-5">
        <div class="flex flex-wrap items-center gap-2">
          <span class="chip bg-sky-100 text-sky-800">正在加载商品结果</span>
          <span class="chip bg-white text-slate-700">结果区会自动刷新</span>
        </div>
        <p class="mt-4 text-sm leading-7 text-slate-600">
          系统正在根据当前筛选条件整理商品结果。你可以继续调整左侧筛选，或者稍等几秒查看结果。
        </p>
      </div>

      <div class="grid gap-4 xl:grid-cols-2">
        <article
          v-for="item in 4"
          :key="item"
          class="rounded-3xl border border-slate-200 bg-white p-5 animate-pulse"
        >
          <div class="flex items-start justify-between gap-4">
            <div class="space-y-3">
              <div class="h-6 w-20 rounded-full bg-slate-200" />
              <div class="h-6 w-48 rounded-2xl bg-slate-200" />
            </div>
            <div class="h-8 w-20 rounded-full bg-slate-200" />
          </div>
          <div class="mt-5 h-8 w-32 rounded-2xl bg-slate-200" />
          <div class="mt-5 h-20 rounded-3xl bg-slate-100" />
          <div class="mt-5 h-24 rounded-3xl bg-slate-100" />
          <div class="mt-5 grid gap-3 sm:grid-cols-2">
            <div class="h-12 rounded-2xl bg-slate-100" />
            <div class="h-12 rounded-2xl bg-slate-100" />
          </div>
        </article>
      </div>
    </div>
    <div
      v-else-if="errorMessage"
      class="mt-6 rounded-3xl border border-rose-200 bg-rose-50 p-5"
    >
      <span class="chip bg-rose-100 text-rose-700">商品结果暂时不可用</span>
      <p class="mt-4 text-lg font-semibold text-rose-900">这次没有成功加载商品结果</p>
      <p class="mt-3 text-sm leading-7 text-rose-800">
        可以先放宽预算、清空品牌限制，或者回到 AI 推荐区重新描述需求，再试一轮。
      </p>
      <p class="mt-4 rounded-2xl bg-white/80 px-4 py-3 text-sm text-rose-700">
        {{ errorMessage }}
      </p>
    </div>

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

          <p class="mt-4 text-3xl font-semibold text-slate-900">CNY {{ product.price }}</p>
          <p class="mt-1 text-xs text-slate-500">{{ product.price_note }}</p>

          <p class="mt-4 line-clamp-2 text-sm leading-7 text-slate-700">
            {{ product.summary }}
          </p>
          <p class="mt-2 line-clamp-1 text-sm text-slate-500">
            适用场景: {{ product.scenario }}
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
                还有 {{ product.specs.length - 2 }} 条参数可在官网继续查看
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
      <span class="chip bg-slate-100 text-slate-700">没有找到匹配商品</span>
      <p class="mt-4 text-xl font-semibold text-slate-900">当前筛选条件下还没有命中结果</p>
      <p class="mt-3 text-sm leading-7 text-slate-600">
        可以先放宽预算、清空品牌限制，或者直接让 AI 帮你重新推荐一轮。
      </p>
      <div class="mt-5 flex flex-wrap justify-center gap-2">
        <span class="chip bg-white text-slate-700">放宽预算</span>
        <span class="chip bg-white text-slate-700">减少筛选条件</span>
        <span class="chip bg-white text-slate-700">重新让 AI 推荐</span>
      </div>
    </div>
  </section>
</template>

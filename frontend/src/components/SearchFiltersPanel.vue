<script setup lang="ts">
import type { SearchFilters } from "../types/catalog";

const props = defineProps<{
  filters: SearchFilters;
  categories: string[];
  brands: string[];
}>();

const emit = defineEmits<{
  update: [filters: SearchFilters];
  reset: [];
}>();

function updateField<K extends keyof SearchFilters>(field: K, value: SearchFilters[K]) {
  emit("update", {
    ...props.filters,
    [field]: value,
  });
}
</script>

<template>
  <section class="panel p-6">
    <div class="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
      <div class="max-w-3xl">
        <p class="text-sm font-semibold uppercase tracking-[0.24em] text-amber-700">
          Search Filters
        </p>
        <h2 class="mt-3 text-2xl font-semibold text-ink">先缩小商品范围</h2>
        <p class="mt-3 text-sm leading-7 text-slate-600">
          如果你已经知道大致预算、分类或品牌，可以先在这里缩一轮范围。右侧 AI 推荐和下方商品结果都会直接复用这些条件。
        </p>
      </div>

      <button
        type="button"
        class="rounded-full border border-slate-200 px-4 py-2 text-sm text-slate-700 transition hover:border-slate-300 hover:bg-slate-50"
        @click="emit('reset')"
      >
        清空筛选
      </button>
    </div>

    <div class="mt-5 flex flex-wrap gap-2">
      <span class="chip bg-slate-100 text-slate-700">支持关键词、分类、品牌、预算</span>
      <span class="chip bg-amber-100 text-amber-800">修改后会自动刷新商品结果</span>
    </div>

    <div class="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      <label>
        <span class="field-label">关键词</span>
        <input
          :value="filters.keyword"
          type="text"
          class="field-input"
          placeholder="例如: 降噪耳机, 4K 显示器, 移动 SSD"
          @input="updateField('keyword', ($event.target as HTMLInputElement).value)"
        />
      </label>

      <label>
        <span class="field-label">商品分类</span>
        <select
          :value="filters.category"
          class="field-input"
          @change="updateField('category', ($event.target as HTMLSelectElement).value)"
        >
          <option value="">全部分类</option>
          <option v-for="category in categories" :key="category" :value="category">
            {{ category }}
          </option>
        </select>
      </label>

      <label>
        <span class="field-label">品牌</span>
        <select
          :value="filters.brand"
          class="field-input"
          @change="updateField('brand', ($event.target as HTMLSelectElement).value)"
        >
          <option value="">全部品牌</option>
          <option v-for="brand in brands" :key="brand" :value="brand">
            {{ brand }}
          </option>
        </select>
      </label>

      <label>
        <span class="field-label">预算上限</span>
        <input
          :value="filters.maxPrice ?? ''"
          type="number"
          min="0"
          class="field-input"
          placeholder="例如: 1500"
          @input="
            updateField(
              'maxPrice',
              ($event.target as HTMLInputElement).value
                ? Number(($event.target as HTMLInputElement).value)
                : null,
            )
          "
        />
      </label>
    </div>
  </section>
</template>

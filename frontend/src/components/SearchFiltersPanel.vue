<script setup lang="ts">
import type { SearchFilters } from "../types";

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
    <div class="flex items-center justify-between gap-4">
      <div>
        <h2 class="panel-title">结构化商品搜索</h2>
        <p class="muted-copy mt-2">
          这一块现在已经开始对接真实后端接口。你在这里输入的条件，会被转换成查询参数发送给
          FastAPI 的商品搜索接口，而不是继续在前端本地过滤静态数组。
        </p>
      </div>
      <button
        type="button"
        class="rounded-full border border-slate-200 px-4 py-2 text-sm text-slate-700 transition hover:border-slate-300 hover:bg-slate-50"
        @click="emit('reset')"
      >
        重置筛选
      </button>
    </div>

    <div class="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      <label>
        <span class="field-label">关键词</span>
        <input
          :value="filters.keyword"
          type="text"
          class="field-input"
          placeholder="例如：降噪耳机、4K 显示器、办公键盘"
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
          placeholder="例如：1500"
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

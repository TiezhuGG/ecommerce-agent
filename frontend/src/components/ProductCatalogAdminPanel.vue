<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import { createProduct, deleteProduct, fetchAdminProducts, updateProduct } from "../api/products";
import type { Product, ProductCatalogAdminResult, ProductInput } from "../types/catalog";

type ProductDraft = {
  name: string;
  category: string;
  brand: string;
  price: number | null;
  priceNote: string;
  summary: string;
  scenario: string;
  tagsText: string;
  specsText: string;
  officialUrl: string;
};

const listState = ref<ProductCatalogAdminResult | null>(null);
const loading = ref(false);
const saving = ref(false);
const deleting = ref(false);
const errorMessage = ref("");
const successMessage = ref("");
const selectedProductId = ref<string | null>(null);
const draft = ref<ProductDraft>(createEmptyDraft());
const filterKeyword = ref("");
const filterCategory = ref("");
const filterBrand = ref("");

const selectedProduct = computed(
  () => listState.value?.items.find((item) => item.id === selectedProductId.value) ?? null,
);

const availableCategories = computed(() => {
  const categories = new Set((listState.value?.items ?? []).map((item) => item.category));
  return Array.from(categories).sort((left, right) => left.localeCompare(right, "zh-CN"));
});

const availableBrands = computed(() => {
  const brands = new Set((listState.value?.items ?? []).map((item) => item.brand));
  return Array.from(brands).sort((left, right) => left.localeCompare(right, "zh-CN"));
});

const filteredProducts = computed(() => {
  const keyword = filterKeyword.value.trim().toLowerCase();
  const category = filterCategory.value.trim();
  const brand = filterBrand.value.trim();

  return (listState.value?.items ?? []).filter((item) => {
    if (category && item.category !== category) {
      return false;
    }
    if (brand && item.brand !== brand) {
      return false;
    }
    if (!keyword) {
      return true;
    }

    const haystacks = [
      item.id,
      item.name,
      item.category,
      item.brand,
      item.summary,
      item.scenario,
      item.price_note,
      item.official_url,
      ...item.tags,
      ...item.specs,
    ];
    return haystacks.some((value) => value.toLowerCase().includes(keyword));
  });
});

function createEmptyDraft(): ProductDraft {
  return {
    name: "",
    category: "",
    brand: "",
    price: null,
    priceNote: "",
    summary: "",
    scenario: "",
    tagsText: "",
    specsText: "",
    officialUrl: "",
  };
}

function mapProductToDraft(product: Product): ProductDraft {
  return {
    name: product.name,
    category: product.category,
    brand: product.brand,
    price: product.price,
    priceNote: product.price_note,
    summary: product.summary,
    scenario: product.scenario,
    tagsText: product.tags.join("，"),
    specsText: product.specs.join("\n"),
    officialUrl: product.official_url,
  };
}

function parseList(value: string) {
  return value
    .split(/[\n,，]/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function buildInputFromDraft(): ProductInput | null {
  if (
    !draft.value.name.trim() ||
    !draft.value.category.trim() ||
    !draft.value.brand.trim() ||
    draft.value.price === null ||
    Number.isNaN(draft.value.price) ||
    draft.value.price < 0 ||
    !draft.value.priceNote.trim() ||
    !draft.value.summary.trim() ||
    !draft.value.scenario.trim() ||
    !draft.value.officialUrl.trim()
  ) {
    return null;
  }

  return {
    name: draft.value.name.trim(),
    category: draft.value.category.trim(),
    brand: draft.value.brand.trim(),
    price: Math.round(draft.value.price),
    price_note: draft.value.priceNote.trim(),
    summary: draft.value.summary.trim(),
    scenario: draft.value.scenario.trim(),
    tags: parseList(draft.value.tagsText),
    specs: parseList(draft.value.specsText),
    official_url: draft.value.officialUrl.trim(),
  };
}

function startCreate() {
  selectedProductId.value = null;
  draft.value = createEmptyDraft();
  errorMessage.value = "";
  successMessage.value = "";
}

function selectProduct(product: Product) {
  selectedProductId.value = product.id;
  draft.value = mapProductToDraft(product);
  errorMessage.value = "";
  successMessage.value = "";
}

async function loadProducts() {
  loading.value = true;
  errorMessage.value = "";

  try {
    const result = await fetchAdminProducts();
    listState.value = result;

    if (selectedProductId.value) {
      const nextSelected = result.items.find((item) => item.id === selectedProductId.value);
      if (nextSelected) {
        draft.value = mapProductToDraft(nextSelected);
      } else {
        startCreate();
      }
    }
  } catch (error) {
    errorMessage.value =
      error instanceof Error ? error.message : "未知错误，无法加载商品目录。";
  } finally {
    loading.value = false;
  }
}

async function saveProduct() {
  const input = buildInputFromDraft();
  if (!input) {
    errorMessage.value = "名称、分类、品牌、价格、价格说明、摘要、场景和官方链接为必填项。";
    return;
  }

  const editingProductId = selectedProductId.value;
  saving.value = true;
  errorMessage.value = "";
  successMessage.value = "";

  try {
    const saved = editingProductId
      ? await updateProduct(editingProductId, input)
      : await createProduct(input);

    await loadProducts();
    selectProduct(saved);
    successMessage.value = editingProductId ? "商品已更新。" : "商品已创建。";
  } catch (error) {
    errorMessage.value =
      error instanceof Error ? error.message : "未知错误，无法保存商品。";
  } finally {
    saving.value = false;
  }
}

async function removeProduct() {
  if (!selectedProductId.value) {
    return;
  }

  deleting.value = true;
  errorMessage.value = "";
  successMessage.value = "";

  try {
    await deleteProduct(selectedProductId.value);
    await loadProducts();
    startCreate();
    successMessage.value = "商品已删除。";
  } catch (error) {
    errorMessage.value =
      error instanceof Error ? error.message : "未知错误，无法删除商品。";
  } finally {
    deleting.value = false;
  }
}

onMounted(() => {
  void loadProducts();
});
</script>

<template>
  <section class="panel p-6">
    <div class="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
      <div>
        <h2 class="panel-title">商品目录管理台</h2>
        <p class="muted-copy mt-2 max-w-3xl">
          这里直接管理本地 SQLite 里的商品目录。新增或修改后，商品搜索、商品对比和 Agent
          推荐会复用同一份商品事实数据。
        </p>
      </div>

      <div class="flex flex-wrap gap-2">
        <button
          type="button"
          class="rounded-full border border-slate-200 px-4 py-2 text-sm text-slate-700 transition hover:border-slate-300 hover:bg-slate-50"
          :disabled="loading"
          @click="loadProducts"
        >
          {{ loading ? "刷新中..." : "刷新商品" }}
        </button>
        <button
          type="button"
          class="rounded-full bg-ink px-4 py-2 text-sm text-white transition hover:bg-slate-800"
          @click="startCreate"
        >
          新建商品
        </button>
      </div>
    </div>

    <p
      v-if="errorMessage"
      class="mt-4 rounded-2xl bg-rose-50 px-4 py-3 text-sm text-rose-700"
    >
      {{ errorMessage }}
    </p>

    <p
      v-if="successMessage"
      class="mt-4 rounded-2xl bg-emerald-50 px-4 py-3 text-sm text-emerald-800"
    >
      {{ successMessage }}
    </p>

    <div class="mt-6 grid gap-4 xl:grid-cols-[0.84fr_1.16fr]">
      <div class="rounded-3xl bg-slate-50 p-4">
        <div class="flex items-center justify-between gap-3">
          <p class="text-sm font-semibold text-slate-800">商品列表</p>
          <span class="chip bg-slate-100 text-slate-700">
            {{ listState?.backend ?? "未加载" }} / {{ listState?.items.length ?? 0 }} 条
          </span>
        </div>

        <div class="mt-4 grid gap-3 md:grid-cols-3">
          <div>
            <label class="field-label">按分类过滤</label>
            <select v-model="filterCategory" class="field-input">
              <option value="">全部分类</option>
              <option v-for="category in availableCategories" :key="category" :value="category">
                {{ category }}
              </option>
            </select>
          </div>
          <div>
            <label class="field-label">按品牌过滤</label>
            <select v-model="filterBrand" class="field-input">
              <option value="">全部品牌</option>
              <option v-for="brand in availableBrands" :key="brand" :value="brand">
                {{ brand }}
              </option>
            </select>
          </div>
          <div>
            <label class="field-label">按关键词过滤</label>
            <input
              v-model="filterKeyword"
              class="field-input"
              placeholder="搜索名称、分类、品牌、标签"
            />
          </div>
        </div>

        <div class="mt-4 max-h-[720px] space-y-3 overflow-y-auto pr-1">
          <button
            v-for="product in filteredProducts"
            :key="product.id"
            type="button"
            class="w-full rounded-2xl border px-4 py-4 text-left transition"
            :class="
              selectedProductId === product.id
                ? 'border-amber-300 bg-amber-50'
                : 'border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50'
            "
            @click="selectProduct(product)"
          >
            <div class="flex flex-wrap gap-2">
              <span class="chip bg-slate-100 text-slate-700">{{ product.category }}</span>
              <span class="chip bg-sky-100 text-sky-800">{{ product.brand }}</span>
            </div>
            <div class="mt-3 flex items-start justify-between gap-3">
              <p class="text-sm font-semibold leading-6 text-slate-900">{{ product.name }}</p>
              <span class="text-sm font-semibold text-amber-700">￥{{ product.price }}</span>
            </div>
            <p class="mt-2 line-clamp-2 text-sm leading-6 text-slate-600">{{ product.summary }}</p>
          </button>

          <div
            v-if="!loading && !filteredProducts.length"
            class="rounded-2xl border border-dashed border-slate-300 bg-white px-4 py-8 text-center text-sm text-slate-600"
          >
            当前筛选条件下没有命中的商品。
          </div>
        </div>
      </div>

      <div class="rounded-3xl bg-slate-50 p-5">
        <div class="flex flex-wrap items-center gap-2">
          <span class="chip bg-amber-100 text-amber-800">
            {{ selectedProduct ? "编辑商品" : "新增商品" }}
          </span>
          <span v-if="selectedProduct" class="chip bg-slate-100 text-slate-700">
            {{ selectedProduct.id }}
          </span>
        </div>

        <div class="mt-5 grid gap-4 md:grid-cols-2">
          <div>
            <label class="field-label">商品名称</label>
            <input v-model="draft.name" class="field-input" placeholder="例如：Sony WF-1000XM5" />
          </div>
          <div>
            <label class="field-label">分类</label>
            <input v-model="draft.category" class="field-input" placeholder="例如：蓝牙耳机" />
          </div>
        </div>

        <div class="mt-4 grid gap-4 md:grid-cols-2">
          <div>
            <label class="field-label">品牌</label>
            <input v-model="draft.brand" class="field-input" placeholder="例如：Sony" />
          </div>
          <div>
            <label class="field-label">价格</label>
            <input
              v-model.number="draft.price"
              type="number"
              min="0"
              class="field-input"
              placeholder="例如：1599"
            />
          </div>
        </div>

        <div class="mt-4 grid gap-4 md:grid-cols-2">
          <div>
            <label class="field-label">价格说明</label>
            <input
              v-model="draft.priceNote"
              class="field-input"
              placeholder="例如：演示参考价，非实时电商价格"
            />
          </div>
          <div>
            <label class="field-label">适用场景</label>
            <input
              v-model="draft.scenario"
              class="field-input"
              placeholder="例如：通勤 / 办公 / 降噪"
            />
          </div>
        </div>

        <div class="mt-4">
          <label class="field-label">商品摘要</label>
          <textarea
            v-model="draft.summary"
            rows="3"
            class="field-input resize-none"
            placeholder="用于商品卡片展示与 Agent 推荐说明"
          />
        </div>

        <div class="mt-4 grid gap-4 md:grid-cols-2">
          <div>
            <label class="field-label">标签</label>
            <input
              v-model="draft.tagsText"
              class="field-input"
              placeholder="用中文逗号、英文逗号或换行分隔"
            />
          </div>
          <div>
            <label class="field-label">官方链接</label>
            <input
              v-model="draft.officialUrl"
              class="field-input"
              placeholder="https://..."
            />
          </div>
        </div>

        <div class="mt-4">
          <label class="field-label">规格要点</label>
          <textarea
            v-model="draft.specsText"
            rows="4"
            class="field-input resize-none"
            placeholder="建议每行一个规格点，也支持逗号分隔"
          />
        </div>

        <div class="mt-6 flex flex-wrap gap-3">
          <button
            type="button"
            class="rounded-full bg-amber-500 px-5 py-3 text-sm font-medium text-white transition hover:bg-amber-600 disabled:cursor-not-allowed disabled:bg-amber-300"
            :disabled="saving"
            @click="saveProduct"
          >
            {{ saving ? "保存中..." : selectedProduct ? "保存修改" : "创建商品" }}
          </button>
          <button
            type="button"
            class="rounded-full border border-slate-200 px-5 py-3 text-sm font-medium text-slate-700 transition hover:border-slate-300 hover:bg-white"
            @click="startCreate"
          >
            清空表单
          </button>
          <button
            type="button"
            class="rounded-full border border-rose-200 px-5 py-3 text-sm font-medium text-rose-700 transition hover:border-rose-300 hover:bg-rose-50 disabled:cursor-not-allowed disabled:opacity-50"
            :disabled="!selectedProduct || deleting"
            @click="removeProduct"
          >
            {{ deleting ? "删除中..." : "删除商品" }}
          </button>
        </div>
      </div>
    </div>
  </section>
</template>

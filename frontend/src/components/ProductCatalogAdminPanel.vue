<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import {
  createProduct,
  deleteProduct,
  exportAdminProducts,
  fetchAdminProducts,
  importAdminProducts,
  updateProduct,
} from "../api/products";
import type {
  Product,
  ProductCatalogAdminResult,
  ProductImportMode,
  ProductInput,
} from "../types/catalog";

type ProductDraft = {
  name: string;
  category: string;
  brand: string;
  price: number | null;
  priceNote: string;
  summary: string;
  scenario: string;
  aliasesText: string;
  tagsText: string;
  specsText: string;
  officialUrl: string;
};

type CatalogSubsection = "overview" | "products" | "import-export";

const listState = ref<ProductCatalogAdminResult | null>(null);
const loading = ref(false);
const saving = ref(false);
const deleting = ref(false);
const importing = ref(false);
const exporting = ref(false);
const errorMessage = ref("");
const successMessage = ref("");
const selectedProductId = ref<string | null>(null);
const draft = ref<ProductDraft>(createEmptyDraft());
const filterKeyword = ref("");
const filterCategory = ref("");
const filterBrand = ref("");
const importMode = ref<ProductImportMode>("upsert");
const importJson = ref("");
const currentSubsection = ref<CatalogSubsection>("overview");

const selectedProduct = computed(
  () => listState.value?.items.find((item) => item.id === selectedProductId.value) ?? null,
);

const totalProducts = computed(() => listState.value?.items.length ?? 0);
const currentBackend = computed(() => listState.value?.backend ?? "not-loaded");
const availableCategories = computed(() => {
  const categories = new Set((listState.value?.items ?? []).map((item) => item.category));
  return Array.from(categories).sort((left, right) => left.localeCompare(right, "zh-CN"));
});
const availableBrands = computed(() => {
  const brands = new Set((listState.value?.items ?? []).map((item) => item.brand));
  return Array.from(brands).sort((left, right) => left.localeCompare(right, "zh-CN"));
});
const totalCategories = computed(() => availableCategories.value.length);
const totalBrands = computed(() => availableBrands.value.length);

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
      ...item.aliases,
      ...item.tags,
      ...item.specs,
    ];
    return haystacks.some((value) => String(value).toLowerCase().includes(keyword));
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
    aliasesText: "",
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
    aliasesText: product.aliases.join(", "),
    tagsText: product.tags.join(", "),
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
    aliases: parseList(draft.value.aliasesText),
    tags: parseList(draft.value.tagsText),
    specs: parseList(draft.value.specsText),
    official_url: draft.value.officialUrl.trim(),
  };
}

function clearMessages() {
  errorMessage.value = "";
  successMessage.value = "";
}

function startCreate() {
  selectedProductId.value = null;
  draft.value = createEmptyDraft();
  clearMessages();
  currentSubsection.value = "products";
}

function selectProduct(product: Product) {
  selectedProductId.value = product.id;
  draft.value = mapProductToDraft(product);
  clearMessages();
  currentSubsection.value = "products";
}

function selectSubsection(next: CatalogSubsection) {
  currentSubsection.value = next;
}

async function loadProducts() {
  loading.value = true;
  errorMessage.value = "";

  try {
    const result = await fetchAdminProducts();
    listState.value = result;

    if (!selectedProductId.value) {
      return;
    }

    const nextSelected = result.items.find((item) => item.id === selectedProductId.value);
    if (nextSelected) {
      draft.value = mapProductToDraft(nextSelected);
      return;
    }

    selectedProductId.value = null;
    draft.value = createEmptyDraft();
  } catch (error) {
    errorMessage.value =
      error instanceof Error ? error.message : "未能加载商品目录，请稍后重试。";
  } finally {
    loading.value = false;
  }
}

async function saveProduct() {
  const input = buildInputFromDraft();
  if (!input) {
    errorMessage.value = "商品名称、分类、品牌、价格、价格说明、摘要、适用场景和官方链接为必填项。";
    return;
  }

  const editingProductId = selectedProductId.value;
  saving.value = true;
  clearMessages();

  try {
    const saved = editingProductId
      ? await updateProduct(editingProductId, input)
      : await createProduct(input);

    await loadProducts();
    selectProduct(saved);
    successMessage.value = editingProductId ? "商品已更新。" : "商品已创建。";
  } catch (error) {
    errorMessage.value =
      error instanceof Error ? error.message : "未能保存商品，请稍后重试。";
  } finally {
    saving.value = false;
  }
}

async function removeProduct() {
  if (!selectedProductId.value) {
    return;
  }

  deleting.value = true;
  clearMessages();

  try {
    await deleteProduct(selectedProductId.value);
    await loadProducts();
    selectedProductId.value = null;
    draft.value = createEmptyDraft();
    successMessage.value = "商品已删除。";
  } catch (error) {
    errorMessage.value =
      error instanceof Error ? error.message : "未能删除商品，请稍后重试。";
  } finally {
    deleting.value = false;
  }
}

async function handleExport() {
  exporting.value = true;
  clearMessages();

  try {
    const result = await exportAdminProducts();
    const content = JSON.stringify(result.items, null, 2);
    importJson.value = content;

    const blob = new Blob([content], { type: "application/json;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = "product-catalog-export.json";
    anchor.click();
    URL.revokeObjectURL(url);

    successMessage.value = `已导出 ${result.items.length} 条商品记录。`;
    currentSubsection.value = "import-export";
  } catch (error) {
    errorMessage.value =
      error instanceof Error ? error.message : "未能导出商品目录，请稍后重试。";
  } finally {
    exporting.value = false;
  }
}

function buildImportedProducts(raw: string): Product[] {
  const parsed = JSON.parse(raw) as unknown;
  if (!Array.isArray(parsed)) {
    throw new Error("导入内容必须是 JSON 数组。");
  }

  return parsed.map((item, index) => {
    if (!item || typeof item !== "object") {
      throw new Error(`第 ${index + 1} 条导入数据不是对象。`);
    }

    const candidate = item as Record<string, unknown>;
    const price = Number(candidate.price ?? NaN);
    if (!Number.isFinite(price) || price < 0) {
      throw new Error(`第 ${index + 1} 条导入数据的 price 非法。`);
    }

    const product: Product = {
      id: typeof candidate.id === "string" ? candidate.id : "",
      name: String(candidate.name ?? "").trim(),
      category: String(candidate.category ?? "").trim(),
      brand: String(candidate.brand ?? "").trim(),
      price: Math.round(price),
      price_note: String(candidate.price_note ?? candidate.priceNote ?? "").trim(),
      summary: String(candidate.summary ?? "").trim(),
      scenario: String(candidate.scenario ?? "").trim(),
      aliases: Array.isArray(candidate.aliases) ? candidate.aliases.map((value) => String(value)) : [],
      tags: Array.isArray(candidate.tags) ? candidate.tags.map((value) => String(value)) : [],
      specs: Array.isArray(candidate.specs) ? candidate.specs.map((value) => String(value)) : [],
      official_url: String(candidate.official_url ?? candidate.officialUrl ?? "").trim(),
    };

    if (
      !product.name ||
      !product.category ||
      !product.brand ||
      !product.price_note ||
      !product.summary ||
      !product.scenario ||
      !product.official_url
    ) {
      throw new Error(`第 ${index + 1} 条导入数据缺少必填字段。`);
    }

    return product;
  });
}

async function handleImport() {
  importing.value = true;
  clearMessages();

  try {
    const items = buildImportedProducts(importJson.value);
    const result = await importAdminProducts(items, importMode.value);
    await loadProducts();
    successMessage.value = `导入完成：共 ${result.importedCount} 条，新增 ${result.createdCount} 条，更新 ${result.updatedCount} 条。`;
    currentSubsection.value = "import-export";
  } catch (error) {
    errorMessage.value =
      error instanceof Error ? error.message : "未能导入商品目录，请稍后重试。";
  } finally {
    importing.value = false;
  }
}

async function handleImportFileChange(event: Event) {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  if (!file) {
    return;
  }

  try {
    importJson.value = await file.text();
    clearMessages();
    successMessage.value = `已读取文件：${file.name}`;
    currentSubsection.value = "import-export";
  } catch {
    errorMessage.value = "读取文件失败，请改用粘贴 JSON。";
  } finally {
    input.value = "";
  }
}

onMounted(() => {
  void loadProducts();
});
</script>

<template>
  <section class="space-y-6">
    <section class="panel p-6">
      <div class="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
        <div class="max-w-3xl">
          <p class="text-sm font-semibold uppercase tracking-[0.24em] text-amber-700">
            Catalog Workspace
          </p>
          <h2 class="mt-3 text-3xl font-semibold tracking-tight text-ink">
            商品目录工作台
          </h2>
          <p class="mt-3 text-sm leading-7 text-slate-600">
            这里集中维护前台搜索、商品推荐、商品对比会共用的商品事实数据。本地阶段继续使用
            SQLite，后续上线再切换 PostgreSQL，但管理流程先统一下来。
          </p>
        </div>

        <div class="grid gap-3 sm:grid-cols-3">
          <article class="rounded-3xl bg-slate-50 p-4">
            <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">数据后端</p>
            <p class="mt-2 text-lg font-semibold text-slate-900">{{ currentBackend }}</p>
          </article>
          <article class="rounded-3xl bg-slate-50 p-4">
            <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">商品总数</p>
            <p class="mt-2 text-lg font-semibold text-slate-900">{{ totalProducts }}</p>
          </article>
          <article class="rounded-3xl bg-slate-50 p-4">
            <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">分类 / 品牌</p>
            <p class="mt-2 text-lg font-semibold text-slate-900">
              {{ totalCategories }} / {{ totalBrands }}
            </p>
          </article>
        </div>
      </div>

      <div class="mt-6 flex flex-wrap gap-2">
        <button
          type="button"
          class="rounded-full px-4 py-2 text-sm transition"
          :class="
            currentSubsection === 'overview'
              ? 'bg-ink text-white'
              : 'border border-slate-200 text-slate-700 hover:border-slate-300 hover:bg-slate-50'
          "
          @click="selectSubsection('overview')"
        >
          概览
        </button>
        <button
          type="button"
          class="rounded-full px-4 py-2 text-sm transition"
          :class="
            currentSubsection === 'products'
              ? 'bg-ink text-white'
              : 'border border-slate-200 text-slate-700 hover:border-slate-300 hover:bg-slate-50'
          "
          @click="selectSubsection('products')"
        >
          商品维护
        </button>
        <button
          type="button"
          class="rounded-full px-4 py-2 text-sm transition"
          :class="
            currentSubsection === 'import-export'
              ? 'bg-ink text-white'
              : 'border border-slate-200 text-slate-700 hover:border-slate-300 hover:bg-slate-50'
          "
          @click="selectSubsection('import-export')"
        >
          批量迁移
        </button>
      </div>

      <div class="mt-6 flex flex-wrap gap-2">
        <button
          type="button"
          class="rounded-full border border-slate-200 px-4 py-2 text-sm text-slate-700 transition hover:border-slate-300 hover:bg-slate-50"
          :disabled="loading"
          @click="loadProducts"
        >
          {{ loading ? "刷新中..." : "刷新目录" }}
        </button>
        <button
          type="button"
          class="rounded-full bg-ink px-4 py-2 text-sm text-white transition hover:bg-slate-800"
          @click="startCreate"
        >
          新建商品
        </button>
        <button
          type="button"
          class="rounded-full border border-slate-200 px-4 py-2 text-sm text-slate-700 transition hover:border-slate-300 hover:bg-slate-50"
          :disabled="exporting"
          @click="handleExport"
        >
          {{ exporting ? "导出中..." : "导出 JSON" }}
        </button>
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
    </section>

    <section v-if="currentSubsection === 'overview'" class="space-y-6">
      <div class="grid gap-6 xl:grid-cols-3">
        <article class="panel p-6">
          <p class="text-sm font-semibold text-slate-900">商品维护</p>
          <p class="mt-3 text-sm leading-7 text-slate-600">
            适合日常新增、编辑和删除单个商品。这里维护的字段会直接影响前台结果卡片、Agent
            推荐摘要和对比内容。
          </p>
          <div class="mt-5 flex flex-wrap gap-2">
            <span class="chip bg-sky-100 text-sky-800">{{ totalProducts }} 条商品</span>
            <span class="chip bg-slate-100 text-slate-700">{{ filteredProducts.length }} 条可见</span>
          </div>
          <button
            type="button"
            class="mt-5 rounded-full border border-slate-200 px-4 py-2 text-sm text-slate-700 transition hover:border-slate-300 hover:bg-slate-50"
            @click="selectSubsection('products')"
          >
            进入商品维护
          </button>
        </article>

        <article class="panel p-6">
          <p class="text-sm font-semibold text-slate-900">目录结构</p>
          <p class="mt-3 text-sm leading-7 text-slate-600">
            当前目录已覆盖 {{ totalCategories }} 个分类和 {{ totalBrands }} 个品牌。品牌与分类越清晰，筛选器和
            Agent 意图映射越稳定。
          </p>
          <div class="mt-5 flex flex-wrap gap-2">
            <span class="chip bg-amber-100 text-amber-800">{{ totalCategories }} 个分类</span>
            <span class="chip bg-violet-100 text-violet-800">{{ totalBrands }} 个品牌</span>
          </div>
          <button
            type="button"
            class="mt-5 rounded-full border border-slate-200 px-4 py-2 text-sm text-slate-700 transition hover:border-slate-300 hover:bg-slate-50"
            @click="loadProducts"
          >
            重新统计目录
          </button>
        </article>

        <article class="panel p-6">
          <p class="text-sm font-semibold text-slate-900">批量迁移</p>
          <p class="mt-3 text-sm leading-7 text-slate-600">
            适合从种子数据迁移到更完整的商品池，或在不同环境之间同步目录。支持增量 upsert 和全量 replace 两种模式。
          </p>
          <div class="mt-5 flex flex-wrap gap-2">
            <span class="chip bg-slate-100 text-slate-700">JSON 导入导出</span>
            <span class="chip bg-emerald-100 text-emerald-800">SQLite 先行</span>
          </div>
          <button
            type="button"
            class="mt-5 rounded-full border border-slate-200 px-4 py-2 text-sm text-slate-700 transition hover:border-slate-300 hover:bg-slate-50"
            @click="selectSubsection('import-export')"
          >
            进入批量迁移
          </button>
        </article>
      </div>

      <section class="panel p-6">
        <h3 class="text-xl font-semibold text-ink">推荐使用顺序</h3>
        <div class="mt-4 grid gap-4 lg:grid-cols-3">
          <article class="rounded-3xl bg-slate-50 p-4">
            <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Step 1</p>
            <p class="mt-2 text-sm font-semibold text-slate-900">先看目录规模</p>
            <p class="mt-2 text-sm leading-6 text-slate-600">
              先确认商品数、分类数和品牌数是否符合预期，避免前台筛选和推荐的可选项过少。
            </p>
          </article>
          <article class="rounded-3xl bg-slate-50 p-4">
            <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Step 2</p>
            <p class="mt-2 text-sm font-semibold text-slate-900">再做单品维护</p>
            <p class="mt-2 text-sm leading-6 text-slate-600">
              单个商品的标题、摘要、场景和规格字段，是普通用户在页面上最直接能感知到的内容。
            </p>
          </article>
          <article class="rounded-3xl bg-slate-50 p-4">
            <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Step 3</p>
            <p class="mt-2 text-sm font-semibold text-slate-900">最后做批量同步</p>
            <p class="mt-2 text-sm leading-6 text-slate-600">
              当需要扩容或迁移环境时，再使用 JSON 批量导入导出，减少手工录入的维护成本。
            </p>
          </article>
        </div>
      </section>
    </section>

    <section
      v-else-if="currentSubsection === 'products'"
      class="grid gap-6 xl:grid-cols-[0.84fr_1.16fr]"
    >
      <section class="panel p-5">
        <div class="flex items-center justify-between gap-3">
          <div>
            <h3 class="text-2xl font-semibold text-ink">商品列表</h3>
            <p class="mt-1 text-sm leading-6 text-slate-600">
              先筛选，再进入右侧编辑区维护单个商品。
            </p>
          </div>
          <span class="chip bg-slate-100 text-slate-700">
            {{ filteredProducts.length }} / {{ totalProducts }}
          </span>
        </div>

        <div class="mt-5 grid gap-3 md:grid-cols-3">
          <div>
            <label class="field-label">分类筛选</label>
            <select v-model="filterCategory" class="field-input">
              <option value="">全部分类</option>
              <option v-for="category in availableCategories" :key="category" :value="category">
                {{ category }}
              </option>
            </select>
          </div>
          <div>
            <label class="field-label">品牌筛选</label>
            <select v-model="filterBrand" class="field-input">
              <option value="">全部品牌</option>
              <option v-for="brand in availableBrands" :key="brand" :value="brand">
                {{ brand }}
              </option>
            </select>
          </div>
          <div>
            <label class="field-label">关键词</label>
            <input
              v-model="filterKeyword"
              class="field-input"
              placeholder="搜索名称、别名、分类、品牌、标签"
            />
          </div>
        </div>

        <div class="mt-5 max-h-[760px] space-y-3 overflow-y-auto pr-1">
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
              <span class="text-sm font-semibold text-amber-700">CNY {{ product.price }}</span>
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
      </section>

      <section class="panel p-5">
        <div class="flex flex-wrap items-center gap-2">
          <span class="chip bg-amber-100 text-amber-800">
            {{ selectedProduct ? "编辑商品" : "新建商品" }}
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
              placeholder="例如：展示参考价，非实时成交价"
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
            placeholder="用于结果卡片、Agent 推荐摘要和对比说明"
          />
        </div>

        <div class="mt-4 grid gap-4 md:grid-cols-2">
          <div>
            <label class="field-label">别名 / 型号简称</label>
            <input
              v-model="draft.aliasesText"
              class="field-input"
              placeholder="例如：索尼 XM5, WF1000XM5, AirPods Pro 2"
            />
          </div>
          <div>
            <label class="field-label">标签</label>
            <input
              v-model="draft.tagsText"
              class="field-input"
              placeholder="支持中文逗号、英文逗号或换行分隔"
            />
          </div>
        </div>

        <div class="mt-4 grid gap-4 md:grid-cols-2">
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
            class="rounded-full border border-slate-200 px-5 py-3 text-sm font-medium text-slate-700 transition hover:border-slate-300 hover:bg-slate-50"
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
      </section>
    </section>

    <section v-else class="space-y-6">
      <div class="grid gap-6 xl:grid-cols-[0.92fr_1.08fr]">
        <section class="panel p-6">
          <div>
            <h3 class="text-2xl font-semibold text-ink">批量迁移</h3>
            <p class="mt-2 text-sm leading-7 text-slate-600">
              用于在不同环境之间同步商品目录，或一次性扩充更完整的演示数据。导出后会自动生成 JSON 文件，也会把内容回填到右侧文本框。
            </p>
          </div>

          <div class="mt-6 rounded-3xl bg-slate-50 p-4">
            <p class="text-sm font-semibold text-slate-900">导入模式</p>
            <div class="mt-3 flex flex-wrap gap-2">
              <button
                type="button"
                class="rounded-full px-4 py-2 text-sm transition"
                :class="
                  importMode === 'upsert'
                    ? 'bg-ink text-white'
                    : 'border border-slate-200 bg-white text-slate-700 hover:border-slate-300 hover:bg-slate-50'
                "
                @click="importMode = 'upsert'"
              >
                upsert
              </button>
              <button
                type="button"
                class="rounded-full px-4 py-2 text-sm transition"
                :class="
                  importMode === 'replace'
                    ? 'bg-ink text-white'
                    : 'border border-slate-200 bg-white text-slate-700 hover:border-slate-300 hover:bg-slate-50'
                "
                @click="importMode = 'replace'"
              >
                replace
              </button>
            </div>
            <p class="mt-3 text-sm leading-6 text-slate-600">
              `upsert` 会按商品 ID 增量更新。`replace` 会先清空当前目录，再按导入内容重建。
            </p>
          </div>

          <div class="mt-6 flex flex-wrap gap-3">
            <button
              type="button"
              class="rounded-full bg-ink px-5 py-3 text-sm text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-400"
              :disabled="exporting"
              @click="handleExport"
            >
              {{ exporting ? "导出中..." : "导出当前目录" }}
            </button>
            <label
              class="cursor-pointer rounded-full border border-slate-200 px-5 py-3 text-sm text-slate-700 transition hover:border-slate-300 hover:bg-slate-50"
            >
              选择 JSON 文件
              <input
                type="file"
                accept=".json,application/json"
                class="hidden"
                @change="handleImportFileChange"
              />
            </label>
          </div>

          <div class="mt-6 grid gap-4 md:grid-cols-2">
            <article class="rounded-3xl bg-slate-50 p-4">
              <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">适用场景</p>
              <p class="mt-2 text-sm leading-6 text-slate-700">
                演示数据扩容、环境迁移、批量修订商品摘要或规格字段。
              </p>
            </article>
            <article class="rounded-3xl bg-slate-50 p-4">
              <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">当前后端</p>
              <p class="mt-2 text-sm leading-6 text-slate-700">
                {{ currentBackend }}
              </p>
            </article>
          </div>
        </section>

        <section class="panel p-6">
          <div class="flex items-center justify-between gap-3">
            <div>
              <h3 class="text-2xl font-semibold text-ink">JSON 内容</h3>
              <p class="mt-2 text-sm leading-7 text-slate-600">
                可以直接粘贴数组 JSON，也可以先选择本地文件。导入前请确认必填字段完整。
              </p>
            </div>
            <span class="chip bg-slate-100 text-slate-700">{{ importMode }}</span>
          </div>

          <textarea
            v-model="importJson"
            rows="20"
            class="field-input mt-5 font-mono text-sm"
            placeholder='[{"id":"product-demo-001","name":"示例商品","category":"蓝牙耳机","brand":"Demo","price":999,"price_note":"展示参考价","summary":"一句话摘要","scenario":"通勤 / 办公","aliases":["Demo One","示例一代"],"tags":["降噪","长续航"],"specs":["40mm 单元","蓝牙 5.3"],"official_url":"https://example.com"}]'
          />

          <div class="mt-5 flex flex-wrap gap-3">
            <button
              type="button"
              class="rounded-full bg-amber-500 px-5 py-3 text-sm font-medium text-white transition hover:bg-amber-600 disabled:cursor-not-allowed disabled:bg-amber-300"
              :disabled="importing"
              @click="handleImport"
            >
              {{ importing ? "导入中..." : "开始导入" }}
            </button>
            <button
              type="button"
              class="rounded-full border border-slate-200 px-5 py-3 text-sm font-medium text-slate-700 transition hover:border-slate-300 hover:bg-slate-50"
              @click="importJson = ''"
            >
              清空内容
            </button>
          </div>
        </section>
      </div>

      <section class="panel p-6">
        <h3 class="text-xl font-semibold text-ink">导入数据要求</h3>
        <div class="mt-4 grid gap-4 lg:grid-cols-3">
          <article class="rounded-3xl bg-slate-50 p-4">
            <p class="text-sm font-semibold text-slate-900">必填字段</p>
            <p class="mt-2 text-sm leading-6 text-slate-600">
              `name`、`category`、`brand`、`price`、`price_note`、`summary`、`scenario`、`official_url` 为必填。
            </p>
          </article>
          <article class="rounded-3xl bg-slate-50 p-4">
            <p class="text-sm font-semibold text-slate-900">数组字段</p>
            <p class="mt-2 text-sm leading-6 text-slate-600">
              `aliases`、`tags` 和 `specs` 需要是字符串数组，导入时会自动去重并清理空白项。
            </p>
          </article>
          <article class="rounded-3xl bg-slate-50 p-4">
            <p class="text-sm font-semibold text-slate-900">ID 规则</p>
            <p class="mt-2 text-sm leading-6 text-slate-600">
              没有传 `id` 时系统会自动生成；`upsert` 模式下传入已有 `id` 会覆盖原商品。
            </p>
          </article>
        </div>
      </section>
    </section>
  </section>
</template>

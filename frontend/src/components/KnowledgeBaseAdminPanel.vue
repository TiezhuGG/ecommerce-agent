<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import {
  createFaqEntry,
  deleteFaqEntry,
  exportFaqEntries,
  fetchFaqEntries,
  importFaqEntries,
  updateFaqEntry,
} from "../api/faq";
import type { FaqEntry, FaqEntryImportResult, FaqEntryInput, FaqEntryListResult, FaqImportMode } from "../types/faq";

type EntryDraft = {
  topic: string;
  question: string;
  answer: string;
  sourceLabel: string;
  keywordsText: string;
  body: string;
};

const listState = ref<FaqEntryListResult | null>(null);
const loading = ref(false);
const saving = ref(false);
const deleting = ref(false);
const importing = ref(false);
const exporting = ref(false);
const errorMessage = ref("");
const successMessage = ref("");
const selectedEntryId = ref<string | null>(null);
const draft = ref<EntryDraft>(createEmptyDraft());
const filterKeyword = ref("");
const filterTopic = ref("");
const importMode = ref<FaqImportMode>("upsert");
const importJson = ref("");

const selectedEntry = computed(() =>
  listState.value?.items.find((item) => item.id === selectedEntryId.value) ?? null,
);

const availableTopics = computed(() => {
  const topics = new Set((listState.value?.items ?? []).map((item) => item.topic));
  return Array.from(topics).sort((left, right) => left.localeCompare(right, "zh-CN"));
});

const filteredEntries = computed(() => {
  const keyword = filterKeyword.value.trim().toLowerCase();
  const topic = filterTopic.value.trim();

  return (listState.value?.items ?? []).filter((item) => {
    if (topic && item.topic !== topic) {
      return false;
    }
    if (!keyword) {
      return true;
    }

    const haystacks = [
      item.id,
      item.topic,
      item.question,
      item.answer,
      item.sourceLabel,
      item.body,
      ...item.keywords,
    ];
    return haystacks.some((value) => value.toLowerCase().includes(keyword));
  });
});

function createEmptyDraft(): EntryDraft {
  return {
    topic: "",
    question: "",
    answer: "",
    sourceLabel: "",
    keywordsText: "",
    body: "",
  };
}

function mapEntryToDraft(entry: FaqEntry): EntryDraft {
  return {
    topic: entry.topic,
    question: entry.question,
    answer: entry.answer,
    sourceLabel: entry.sourceLabel,
    keywordsText: entry.keywords.join("，"),
    body: entry.body,
  };
}

function buildInputFromDraft(): FaqEntryInput {
  const keywords = draft.value.keywordsText
    .split(/[\n,，、]/)
    .map((item) => item.trim())
    .filter(Boolean);

  return {
    topic: draft.value.topic.trim(),
    question: draft.value.question.trim(),
    answer: draft.value.answer.trim(),
    sourceLabel: draft.value.sourceLabel.trim(),
    keywords,
    body: draft.value.body.trim(),
  };
}

function startCreate() {
  selectedEntryId.value = null;
  draft.value = createEmptyDraft();
  errorMessage.value = "";
  successMessage.value = "";
}

function selectEntry(entry: FaqEntry) {
  selectedEntryId.value = entry.id;
  draft.value = mapEntryToDraft(entry);
  errorMessage.value = "";
  successMessage.value = "";
}

async function loadEntries() {
  loading.value = true;
  errorMessage.value = "";

  try {
    const result = await fetchFaqEntries();
    listState.value = result;

    if (selectedEntryId.value) {
      const nextSelected = result.items.find((item) => item.id === selectedEntryId.value);
      if (nextSelected) {
        draft.value = mapEntryToDraft(nextSelected);
      } else {
        startCreate();
      }
    }
  } catch (error) {
    errorMessage.value =
      error instanceof Error ? error.message : "未知错误，无法加载知识库条目。";
  } finally {
    loading.value = false;
  }
}

async function saveEntry() {
  const input = buildInputFromDraft();
  if (!input.topic || !input.question || !input.answer || !input.sourceLabel) {
    errorMessage.value = "主题、问题、短答案和来源标签为必填项。";
    return;
  }

  saving.value = true;
  errorMessage.value = "";
  successMessage.value = "";

  try {
    const saved = selectedEntryId.value
      ? await updateFaqEntry(selectedEntryId.value, input)
      : await createFaqEntry(input);

    await loadEntries();
    selectEntry(saved);
    successMessage.value = selectedEntryId.value ? "知识库条目已更新。" : "知识库条目已创建。";
  } catch (error) {
    errorMessage.value =
      error instanceof Error ? error.message : "未知错误，无法保存知识库条目。";
  } finally {
    saving.value = false;
  }
}

async function removeEntry() {
  if (!selectedEntryId.value) {
    return;
  }

  deleting.value = true;
  errorMessage.value = "";
  successMessage.value = "";

  try {
    await deleteFaqEntry(selectedEntryId.value);
    await loadEntries();
    startCreate();
    successMessage.value = "知识库条目已删除。";
  } catch (error) {
    errorMessage.value =
      error instanceof Error ? error.message : "未知错误，无法删除知识库条目。";
  } finally {
    deleting.value = false;
  }
}

async function handleExport() {
  exporting.value = true;
  errorMessage.value = "";
  successMessage.value = "";

  try {
    const result = await exportFaqEntries();
    const content = JSON.stringify(result.items, null, 2);
    importJson.value = content;

    const blob = new Blob([content], { type: "application/json;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = "knowledge-base-export.json";
    anchor.click();
    URL.revokeObjectURL(url);
    successMessage.value = `已导出 ${result.items.length} 条知识文档。`;
  } catch (error) {
    errorMessage.value =
      error instanceof Error ? error.message : "未知错误，无法导出知识库条目。";
  } finally {
    exporting.value = false;
  }
}

async function handleImport() {
  importing.value = true;
  errorMessage.value = "";
  successMessage.value = "";

  try {
    const parsed = JSON.parse(importJson.value) as unknown;
    if (!Array.isArray(parsed)) {
      throw new Error("导入内容必须是 JSON 数组。");
    }

    const items = parsed.map((item) => {
      if (!item || typeof item !== "object") {
        throw new Error("导入数组中存在非法条目。");
      }
      const candidate = item as Record<string, unknown>;
      return {
        id: typeof candidate.id === "string" ? candidate.id : "",
        topic: String(candidate.topic ?? ""),
        question: String(candidate.question ?? ""),
        answer: String(candidate.answer ?? ""),
        sourceLabel: String(candidate.sourceLabel ?? candidate.source_label ?? ""),
        keywords: Array.isArray(candidate.keywords)
          ? candidate.keywords.map((value) => String(value))
          : [],
        body: String(candidate.body ?? ""),
      } satisfies FaqEntry;
    });

    const result: FaqEntryImportResult = await importFaqEntries(items, importMode.value);
    await loadEntries();
    successMessage.value = `导入完成：${result.importedCount} 条，新增 ${result.createdCount} 条，更新 ${result.updatedCount} 条。`;
  } catch (error) {
    errorMessage.value =
      error instanceof Error ? error.message : "未知错误，无法导入知识库条目。";
  } finally {
    importing.value = false;
  }
}

onMounted(() => {
  void loadEntries();
});
</script>

<template>
  <section class="panel p-6">
    <div class="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
      <div>
        <h2 class="panel-title">知识库管理台</h2>
        <p class="muted-copy mt-2 max-w-3xl">
          这里直接管理本地 SQLite 里的知识文档。新增或修改后，FAQ 检索和 Agent 知识库路由会直接复用这些条目。
        </p>
      </div>

      <div class="flex flex-wrap gap-2">
        <button
          type="button"
          class="rounded-full border border-slate-200 px-4 py-2 text-sm text-slate-700 transition hover:border-slate-300 hover:bg-slate-50"
          :disabled="loading"
          @click="loadEntries"
        >
          {{ loading ? "刷新中..." : "刷新条目" }}
        </button>
        <button
          type="button"
          class="rounded-full bg-ink px-4 py-2 text-sm text-white transition hover:bg-slate-800"
          @click="startCreate"
        >
          新建条目
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

    <div class="mt-6 grid gap-4 xl:grid-cols-[0.82fr_1.18fr]">
      <div class="rounded-3xl bg-slate-50 p-4">
        <div class="flex items-center justify-between gap-3">
          <p class="text-sm font-semibold text-slate-800">知识文档列表</p>
          <span class="chip bg-slate-100 text-slate-700">
            {{ listState?.backend ?? "未加载" }} / {{ listState?.items.length ?? 0 }} 条
          </span>
        </div>

        <div class="mt-4 grid gap-3">
          <div>
            <label class="field-label">按主题过滤</label>
            <select v-model="filterTopic" class="field-input">
              <option value="">全部主题</option>
              <option v-for="topic in availableTopics" :key="topic" :value="topic">
                {{ topic }}
              </option>
            </select>
          </div>
          <div>
            <label class="field-label">按关键词过滤</label>
            <input
              v-model="filterKeyword"
              class="field-input"
              placeholder="搜索问题、答案、关键词、来源标签"
            />
          </div>
        </div>

        <div class="mt-4 max-h-[720px] overflow-y-auto space-y-3 pr-1">
          <button
            v-for="entry in filteredEntries"
            :key="entry.id"
            type="button"
            class="w-full rounded-2xl border px-4 py-4 text-left transition"
            :class="
              selectedEntryId === entry.id
                ? 'border-amber-300 bg-amber-50'
                : 'border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50'
            "
            @click="selectEntry(entry)"
          >
            <div class="flex flex-wrap gap-2">
              <span class="chip bg-slate-100 text-slate-700">{{ entry.topic }}</span>
              <span class="chip bg-sky-100 text-sky-800">{{ entry.sourceLabel }}</span>
            </div>
            <p class="mt-3 text-sm font-semibold leading-6 text-slate-900">{{ entry.question }}</p>
            <p class="mt-2 line-clamp-2 text-sm leading-6 text-slate-600">{{ entry.answer }}</p>
          </button>

          <div
            v-if="!loading && !filteredEntries.length"
            class="rounded-2xl border border-dashed border-slate-300 bg-white px-4 py-8 text-center text-sm text-slate-600"
          >
            当前筛选条件下没有命中的知识文档。
          </div>
        </div>
      </div>

      <div class="rounded-3xl bg-slate-50 p-5">
        <div class="flex flex-wrap items-center gap-2">
          <span class="chip bg-amber-100 text-amber-800">
            {{ selectedEntry ? "编辑条目" : "新增条目" }}
          </span>
          <span v-if="selectedEntry" class="chip bg-slate-100 text-slate-700">
            {{ selectedEntry.id }}
          </span>
        </div>

        <div class="mt-5 grid gap-4 md:grid-cols-2">
          <div>
            <label class="field-label">主题</label>
            <input v-model="draft.topic" class="field-input" placeholder="例如：配送" />
          </div>
          <div>
            <label class="field-label">来源标签</label>
            <input
              v-model="draft.sourceLabel"
              class="field-input"
              placeholder="例如：配送说明 V2"
            />
          </div>
        </div>

        <div class="mt-4">
          <label class="field-label">标准问题</label>
          <input
            v-model="draft.question"
            class="field-input"
            placeholder="例如：签收时发现外包装破损怎么办？"
          />
        </div>

        <div class="mt-4">
          <label class="field-label">短答案</label>
          <textarea
            v-model="draft.answer"
            rows="3"
            class="field-input resize-none"
            placeholder="用于摘要回答和检索首屏展示"
          />
        </div>

        <div class="mt-4">
          <label class="field-label">关键词</label>
          <input
            v-model="draft.keywordsText"
            class="field-input"
            placeholder="用中文逗号、英文逗号或换行分隔"
          />
        </div>

        <div class="mt-4">
          <label class="field-label">知识正文</label>
          <textarea
            v-model="draft.body"
            rows="10"
            class="field-input resize-y"
            placeholder="用于切片检索的正文内容"
          />
        </div>

        <div class="mt-5 flex flex-wrap gap-3">
          <button
            type="button"
            class="rounded-full bg-amber-500 px-5 py-2.5 text-sm font-medium text-white transition hover:bg-amber-600 disabled:cursor-wait disabled:opacity-70"
            :disabled="saving"
            @click="saveEntry"
          >
            {{ saving ? "保存中..." : selectedEntry ? "保存修改" : "创建条目" }}
          </button>

          <button
            type="button"
            class="rounded-full border border-slate-200 px-5 py-2.5 text-sm text-slate-700 transition hover:border-slate-300 hover:bg-slate-50"
            @click="startCreate"
          >
            清空表单
          </button>

          <button
            v-if="selectedEntry"
            type="button"
            class="rounded-full border border-rose-200 px-5 py-2.5 text-sm text-rose-700 transition hover:bg-rose-50 disabled:cursor-wait disabled:opacity-70"
            :disabled="deleting"
            @click="removeEntry"
          >
            {{ deleting ? "删除中..." : "删除条目" }}
          </button>
        </div>

        <div class="mt-8 border-t border-slate-200 pt-6">
          <div class="flex flex-wrap items-center gap-2">
            <span class="chip bg-sky-100 text-sky-800">JSON 导入导出</span>
            <span class="chip bg-slate-100 text-slate-700">
              支持 upsert / replace
            </span>
          </div>

          <div class="mt-4 flex flex-wrap gap-3">
            <button
              type="button"
              class="rounded-full border border-slate-200 px-5 py-2.5 text-sm text-slate-700 transition hover:border-slate-300 hover:bg-slate-50 disabled:cursor-wait disabled:opacity-70"
              :disabled="exporting"
              @click="handleExport"
            >
              {{ exporting ? "导出中..." : "导出 JSON" }}
            </button>

            <label class="text-sm text-slate-600">
              导入模式
              <select v-model="importMode" class="field-input mt-2 min-w-[180px]">
                <option value="upsert">upsert：按 id 更新或新增</option>
                <option value="replace">replace：清空后重建</option>
              </select>
            </label>
          </div>

          <div class="mt-4">
            <label class="field-label">导入 / 导出 JSON</label>
            <textarea
              v-model="importJson"
              rows="12"
              class="field-input resize-y font-mono text-xs leading-6"
              placeholder="这里可以粘贴导出的知识文档 JSON 数组"
            />
          </div>

          <div class="mt-4">
            <button
              type="button"
              class="rounded-full bg-sky-600 px-5 py-2.5 text-sm font-medium text-white transition hover:bg-sky-700 disabled:cursor-wait disabled:opacity-70"
              :disabled="importing"
              @click="handleImport"
            >
              {{ importing ? "导入中..." : "导入 JSON" }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

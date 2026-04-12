<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import {
  askFaq,
  createFaqEntry,
  deleteFaqEntry,
  exportFaqEntries,
  fetchFaqEntries,
  importFaqEntries,
  updateFaqEntry,
} from "../api/faq";
import type {
  FaqAskResult,
  FaqEntry,
  FaqEntryImportResult,
  FaqEntryInput,
  FaqEntryListResult,
  FaqImportMode,
} from "../types/faq";

type EntryDraft = {
  topic: string;
  question: string;
  answer: string;
  sourceLabel: string;
  questionAliasesText: string;
  keywordsText: string;
  body: string;
};

type KnowledgeSubsection = "overview" | "entries" | "import-export";
type DraftDiagnosticSignal = {
  kind: string;
  label: string;
  matchedValue: string;
  detail: string;
};

type DiagnosticCompareCard = {
  title: string;
  badge: string;
  question: string;
  sourceLabel: string;
  aliases: string[];
  keywords: string[];
  bodySnippet: string;
};

type DiagnosticActionSuggestion = {
  aliasSuggestions: string[];
  keywordSuggestions: string[];
  bodySuggestion: string;
};

type AppliedSuggestionSnapshot = {
  aliases: string[];
  keywords: string[];
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
const currentSubsection = ref<KnowledgeSubsection>("overview");
const diagnosticQuestion = ref("");
const diagnosticLoading = ref(false);
const diagnosticErrorMessage = ref("");
const diagnosticResult = ref<FaqAskResult | null>(null);
const applyingSuggestions = ref(false);
const lastAppliedSuggestions = ref<AppliedSuggestionSnapshot>({
  aliases: [],
  keywords: [],
  body: "",
});

const selectedEntry = computed(
  () => listState.value?.items.find((item) => item.id === selectedEntryId.value) ?? null,
);

const totalEntries = computed(() => listState.value?.items.length ?? 0);
const availableTopics = computed(() => {
  const topics = new Set((listState.value?.items ?? []).map((item) => item.topic));
  return Array.from(topics).sort((left, right) => left.localeCompare(right, "zh-CN"));
});
const totalTopics = computed(() => availableTopics.value.length);
const currentBackend = computed(() => listState.value?.backend ?? "未加载");

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
      ...item.questionAliases,
      ...item.keywords,
    ];

    return haystacks.some((value) => value.toLowerCase().includes(keyword));
  });
});

const diagnosticMatchedCurrentEntry = computed(() => {
  if (!selectedEntry.value || !diagnosticResult.value?.matchedEntry) {
    return null;
  }

  return diagnosticResult.value.matchedEntry.id === selectedEntry.value.id;
});

const currentDraftDiagnosticSignals = computed(() => {
  const question = diagnosticQuestion.value.trim();
  const canonicalQuestion = draft.value.question.trim();
  const topic = draft.value.topic.trim();
  const aliases = splitDraftList(draft.value.questionAliasesText);
  const keywords = splitDraftList(draft.value.keywordsText);
  const signals: DraftDiagnosticSignal[] = [];

  if (!question || !canonicalQuestion) {
    return signals;
  }

  const normalizedQuestion = normalizeDiagnosticText(question);
  const normalizedCanonicalQuestion = normalizeDiagnosticText(canonicalQuestion);
  const normalizedTopic = normalizeDiagnosticText(topic);
  const bodySnippet = extractBodySnippet(draft.value.body);
  const bodyOverlap = calculateBigramOverlap(question, bodySnippet);

  if (
    normalizedCanonicalQuestion &&
    (normalizedQuestion.includes(normalizedCanonicalQuestion) ||
      normalizedCanonicalQuestion.includes(normalizedQuestion))
  ) {
    signals.push({
      kind: "canonical_question",
      label: "标准问题",
      matchedValue: canonicalQuestion,
      detail: "当前草稿的标准问题与用户问法足够接近。",
    });
  }

  for (const alias of aliases) {
    const normalizedAlias = normalizeDiagnosticText(alias);
    if (
      normalizedAlias &&
      (normalizedQuestion.includes(normalizedAlias) || normalizedAlias.includes(normalizedQuestion))
    ) {
      signals.push({
        kind: "question_alias",
        label: "问法别名",
        matchedValue: alias,
        detail: "当前草稿里已经存在与用户问法接近的问法别名。",
      });
    }
  }

  for (const keyword of keywords) {
    const normalizedKeyword = normalizeDiagnosticText(keyword);
    if (normalizedKeyword && normalizedQuestion.includes(normalizedKeyword)) {
      signals.push({
        kind: "keyword",
        label: "关键词",
        matchedValue: keyword,
        detail: "用户问法中已经出现当前草稿的检索关键词。",
      });
    }
  }

  if (normalizedTopic && normalizedQuestion.includes(normalizedTopic)) {
    signals.push({
      kind: "topic",
      label: "主题",
      matchedValue: topic,
      detail: "用户问法里直接出现了当前草稿的主题词。",
    });
  }

  if (bodySnippet && bodyOverlap > 0) {
    signals.push({
      kind: "body_snippet",
      label: "正文片段",
      matchedValue: bodySnippet,
      detail: `当前草稿正文与问法存在字词重合，重合片段数 ${bodyOverlap}。`,
    });
  }

  return deduplicateDraftSignals(signals);
});

const currentDraftDiagnosticGaps = computed(() => {
  const question = diagnosticQuestion.value.trim();
  const canonicalQuestion = draft.value.question.trim();
  if (!question || !canonicalQuestion) {
    return [];
  }

  const gaps: string[] = [];
  const signalKinds = new Set(currentDraftDiagnosticSignals.value.map((item) => item.kind));
  const matchedSignalKinds = new Set(diagnosticResult.value?.matchSignals.map((item) => item.kind) ?? []);

  if (!signalKinds.has("canonical_question") && !signalKinds.has("question_alias")) {
    gaps.push("当前条目缺少与这句用户问法足够接近的标准问题或问法别名。");
  }

  if (!signalKinds.has("keyword")) {
    gaps.push("当前条目没有命中明显关键词，可以补更贴近用户说法的关键词。");
  }

  if (!signalKinds.has("body_snippet")) {
    gaps.push("当前条目正文与这句问法的重合度偏弱，可以补更具体的场景描述或规则表述。");
  }

  if (diagnosticResult.value?.matchedEntry && diagnosticMatchedCurrentEntry.value === false) {
    if (matchedSignalKinds.has("question_alias") && !signalKinds.has("question_alias")) {
      gaps.push("实际命中条目依赖问法别名，而当前条目还没有覆盖这类自然问法。");
    }
    if (matchedSignalKinds.has("keyword") && !signalKinds.has("keyword")) {
      gaps.push("实际命中条目已经抓住了关键词，当前条目关键词表达仍偏弱。");
    }
    if (matchedSignalKinds.has("canonical_question") && !signalKinds.has("canonical_question")) {
      gaps.push("实际命中条目的标准问题与用户问法更接近，当前标题可能还不够口语化。");
    }
  }

  return Array.from(new Set(gaps));
});

const diagnosticComparisonCards = computed<DiagnosticCompareCard[]>(() => {
  const matchedEntry = diagnosticResult.value?.matchedEntry;
  if (!matchedEntry || diagnosticMatchedCurrentEntry.value !== false || !draft.value.question.trim()) {
    return [];
  }

  return [
    {
      title: "当前草稿条目",
      badge: selectedEntry.value?.id ?? "unsaved-draft",
      question: draft.value.question.trim() || "未填写",
      sourceLabel: draft.value.sourceLabel.trim() || "未填写",
      aliases: splitDraftList(draft.value.questionAliasesText),
      keywords: splitDraftList(draft.value.keywordsText),
      bodySnippet: extractBodySnippet(draft.value.body) || "未填写正文",
    },
    {
      title: "实际命中条目",
      badge: matchedEntry.id,
      question: matchedEntry.question,
      sourceLabel: matchedEntry.sourceLabel,
      aliases: matchedEntry.questionAliases,
      keywords: matchedEntry.keywords,
      bodySnippet: extractBodySnippet(matchedEntry.body || matchedEntry.answer),
    },
  ];
});

const diagnosticComparisonInsights = computed(() => {
  const matchedEntry = diagnosticResult.value?.matchedEntry;
  if (!matchedEntry || diagnosticMatchedCurrentEntry.value !== false || !draft.value.question.trim()) {
    return [];
  }

  const question = diagnosticQuestion.value.trim();
  const draftAliases = splitDraftList(draft.value.questionAliasesText);
  const draftKeywords = splitDraftList(draft.value.keywordsText);
  const draftBodySnippet = extractBodySnippet(draft.value.body);
  const matchedBodySnippet = extractBodySnippet(matchedEntry.body || matchedEntry.answer);
  const draftBodyOverlap = calculateBigramOverlap(question, draftBodySnippet);
  const matchedBodyOverlap = calculateBigramOverlap(question, matchedBodySnippet);
  const insights: string[] = [];

  if (draftAliases.length < matchedEntry.questionAliases.length) {
    insights.push(
      `实际命中条目有 ${matchedEntry.questionAliases.length} 条问法别名，当前草稿只有 ${draftAliases.length} 条，别名覆盖面偏弱。`,
    );
  }

  if (draftKeywords.length < matchedEntry.keywords.length) {
    insights.push(
      `实际命中条目有 ${matchedEntry.keywords.length} 个关键词，当前草稿只有 ${draftKeywords.length} 个，关键词抓词能力更弱。`,
    );
  }

  if (draftBodyOverlap < matchedBodyOverlap) {
    insights.push(
      `实际命中条目的正文片段与当前问法重合更高（${matchedBodyOverlap} vs ${draftBodyOverlap}），正文表达更贴近用户说法。`,
    );
  }

  const draftQuestionNormalized = normalizeDiagnosticText(draft.value.question);
  const matchedQuestionNormalized = normalizeDiagnosticText(matchedEntry.question);
  const questionNormalized = normalizeDiagnosticText(question);
  const draftQuestionMatched =
    draftQuestionNormalized &&
    (questionNormalized.includes(draftQuestionNormalized) ||
      draftQuestionNormalized.includes(questionNormalized));
  const matchedQuestionMatched =
    matchedQuestionNormalized &&
    (questionNormalized.includes(matchedQuestionNormalized) ||
      matchedQuestionNormalized.includes(questionNormalized));

  if (!draftQuestionMatched && matchedQuestionMatched) {
    insights.push("实际命中条目的标准问题更接近用户原话，当前标题还可以再口语化一些。");
  }

  return Array.from(new Set(insights));
});

const diagnosticActionSuggestions = computed<DiagnosticActionSuggestion>(() => {
  const question = diagnosticQuestion.value.trim();
  if (!question || !draft.value.question.trim()) {
    return {
      aliasSuggestions: [],
      keywordSuggestions: [],
      bodySuggestion: "",
    };
  }

  const draftAliases = splitDraftList(draft.value.questionAliasesText);
  const draftKeywords = splitDraftList(draft.value.keywordsText);
  const matchedEntry = diagnosticResult.value?.matchedEntry ?? null;
  const aliasSuggestions: string[] = [];
  const keywordSuggestions: string[] = [];
  const normalizedDraftQuestion = normalizeDiagnosticText(draft.value.question);

  if (!hasNormalizedValue([draft.value.question, ...draftAliases], question)) {
    aliasSuggestions.push(question);
  }

  for (const signal of diagnosticResult.value?.matchSignals ?? []) {
    if (
      signal.kind === "question_alias" &&
      !hasNormalizedValue([draft.value.question, ...draftAliases, ...aliasSuggestions], signal.matchedValue)
    ) {
      aliasSuggestions.push(signal.matchedValue);
    }

    if (
      (signal.kind === "keyword" || signal.kind === "topic") &&
      !hasNormalizedValue([...draftKeywords, ...keywordSuggestions], signal.matchedValue)
    ) {
      keywordSuggestions.push(signal.matchedValue);
    }
  }

  if (matchedEntry && diagnosticMatchedCurrentEntry.value === false) {
    for (const keyword of matchedEntry.keywords) {
      if (
        normalizeDiagnosticText(question).includes(normalizeDiagnosticText(keyword)) &&
        !hasNormalizedValue([...draftKeywords, ...keywordSuggestions], keyword)
      ) {
        keywordSuggestions.push(keyword);
      }
    }
  }

  const bodySuggestion =
    matchedEntry && diagnosticMatchedCurrentEntry.value === false
      ? `用户常问“${question}”。可补一句更贴近用户原话的说明：${matchedEntry.answer}`
      : currentDraftDiagnosticGaps.value.some((item) => item.includes("正文"))
        ? `用户常问“${question}”。建议在正文里补一条直接回应这句问法的规则说明。`
        : "";

  return {
    aliasSuggestions: aliasSuggestions
      .filter((item) => normalizeDiagnosticText(item) !== normalizedDraftQuestion)
      .slice(0, 3),
    keywordSuggestions: keywordSuggestions.slice(0, 4),
    bodySuggestion,
  };
});

function createEmptyDraft(): EntryDraft {
  return {
    topic: "",
    question: "",
    answer: "",
    sourceLabel: "",
    questionAliasesText: "",
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
    questionAliasesText: entry.questionAliases.join("，"),
    keywordsText: entry.keywords.join("，"),
    body: entry.body,
  };
}

function splitDraftList(value: string): string[] {
  return value
    .split(/[\n,，、]/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function normalizeDiagnosticText(value: string): string {
  return value.trim().toLowerCase().replace(/\s+/g, "");
}

function buildBigrams(value: string): string[] {
  const normalized = normalizeDiagnosticText(value);
  if (!normalized) {
    return [];
  }
  if (normalized.length < 2) {
    return [normalized];
  }

  const result: string[] = [];
  for (let index = 0; index < normalized.length - 1; index += 1) {
    result.push(normalized.slice(index, index + 2));
  }
  return result;
}

function calculateBigramOverlap(left: string, right: string): number {
  const leftSet = new Set(buildBigrams(left));
  const rightSet = new Set(buildBigrams(right));
  let overlap = 0;

  for (const value of leftSet) {
    if (rightSet.has(value)) {
      overlap += 1;
    }
  }

  return overlap;
}

function extractBodySnippet(body: string): string {
  return (
    body
      .split(/\n+/)
      .map((item) => item.trim())
      .find(Boolean) ?? ""
  );
}

function deduplicateDraftSignals(signals: DraftDiagnosticSignal[]): DraftDiagnosticSignal[] {
  const seen = new Set<string>();
  return signals.filter((item) => {
    const key = `${item.kind}:${item.matchedValue.toLowerCase()}`;
    if (seen.has(key)) {
      return false;
    }
    seen.add(key);
    return true;
  });
}

function hasNormalizedValue(values: string[], candidate: string): boolean {
  const normalizedCandidate = normalizeDiagnosticText(candidate);
  if (!normalizedCandidate) {
    return false;
  }

  return values.some((item) => normalizeDiagnosticText(item) === normalizedCandidate);
}

function buildInputFromDraft(): FaqEntryInput {
  return {
    topic: draft.value.topic.trim(),
    question: draft.value.question.trim(),
    answer: draft.value.answer.trim(),
    sourceLabel: draft.value.sourceLabel.trim(),
    questionAliases: splitDraftList(draft.value.questionAliasesText),
    keywords: splitDraftList(draft.value.keywordsText),
    body: draft.value.body.trim(),
  };
}

function clearMessages() {
  errorMessage.value = "";
  successMessage.value = "";
}

function resetAppliedSuggestions() {
  lastAppliedSuggestions.value = {
    aliases: [],
    keywords: [],
    body: "",
  };
}

function buildUpdatedDraftListField(
  currentValue: string,
  additions: string[],
): { nextValue: string; appended: string[] } {
  const merged = [...splitDraftList(currentValue)];
  const appended: string[] = [];

  for (const item of additions) {
    const value = item.trim();
    if (!value || hasNormalizedValue(merged, value)) {
      continue;
    }
    merged.push(value);
    appended.push(value);
  }

  return {
    nextValue: merged.join("，"),
    appended,
  };
}

async function rerunDiagnosticAfterApply() {
  if (!diagnosticQuestion.value.trim()) {
    return;
  }

  await runDiagnostic();
}

async function applyAliasSuggestions() {
  if (applyingSuggestions.value) {
    return;
  }

  const additions = diagnosticActionSuggestions.value.aliasSuggestions;
  if (!additions.length) {
    return;
  }

  applyingSuggestions.value = true;
  clearMessages();
  resetAppliedSuggestions();

  try {
    const result = buildUpdatedDraftListField(draft.value.questionAliasesText, additions);
    if (!result.appended.length) {
      successMessage.value = "建议问法别名已存在，无需重复追加。";
      return;
    }

    draft.value.questionAliasesText = result.nextValue;
    lastAppliedSuggestions.value.aliases = result.appended;
    successMessage.value = `已追加 ${result.appended.length} 个建议问法别名。`;
    await rerunDiagnosticAfterApply();
  } finally {
    applyingSuggestions.value = false;
  }
}

async function applyKeywordSuggestions() {
  if (applyingSuggestions.value) {
    return;
  }

  const additions = diagnosticActionSuggestions.value.keywordSuggestions;
  if (!additions.length) {
    return;
  }

  applyingSuggestions.value = true;
  clearMessages();
  resetAppliedSuggestions();

  try {
    const result = buildUpdatedDraftListField(draft.value.keywordsText, additions);
    if (!result.appended.length) {
      successMessage.value = "建议关键词已存在，无需重复追加。";
      return;
    }

    draft.value.keywordsText = result.nextValue;
    lastAppliedSuggestions.value.keywords = result.appended;
    successMessage.value = `已追加 ${result.appended.length} 个建议关键词。`;
    await rerunDiagnosticAfterApply();
  } finally {
    applyingSuggestions.value = false;
  }
}

async function applyBodySuggestion() {
  if (applyingSuggestions.value) {
    return;
  }

  const suggestion = diagnosticActionSuggestions.value.bodySuggestion.trim();
  if (!suggestion) {
    return;
  }

  applyingSuggestions.value = true;
  clearMessages();
  resetAppliedSuggestions();

  try {
    const currentBody = draft.value.body.trim();
    const normalizedSuggestion = normalizeDiagnosticText(suggestion);

    if (
      currentBody &&
      normalizedSuggestion &&
      normalizeDiagnosticText(currentBody).includes(normalizedSuggestion)
    ) {
      successMessage.value = "正文里已经包含相近说明，无需重复追加。";
      return;
    }

    draft.value.body = currentBody ? `${currentBody}\n\n${suggestion}` : suggestion;
    lastAppliedSuggestions.value.body = suggestion;
    successMessage.value = "已将建议正文说明追加到当前条目。";
    await rerunDiagnosticAfterApply();
  } finally {
    applyingSuggestions.value = false;
  }
}

async function applyAllSuggestions() {
  if (applyingSuggestions.value) {
    return;
  }

  applyingSuggestions.value = true;
  clearMessages();
  resetAppliedSuggestions();

  try {
    const aliasResult = buildUpdatedDraftListField(
      draft.value.questionAliasesText,
      diagnosticActionSuggestions.value.aliasSuggestions,
    );
    if (aliasResult.appended.length) {
      draft.value.questionAliasesText = aliasResult.nextValue;
      lastAppliedSuggestions.value.aliases = aliasResult.appended;
    }

    const keywordResult = buildUpdatedDraftListField(
      draft.value.keywordsText,
      diagnosticActionSuggestions.value.keywordSuggestions,
    );
    if (keywordResult.appended.length) {
      draft.value.keywordsText = keywordResult.nextValue;
      lastAppliedSuggestions.value.keywords = keywordResult.appended;
    }

    const bodySuggestion = diagnosticActionSuggestions.value.bodySuggestion.trim();
    const currentBody = draft.value.body.trim();
    const normalizedSuggestion = normalizeDiagnosticText(bodySuggestion);
    const shouldAppendBody =
      bodySuggestion &&
      (!currentBody ||
        !normalizedSuggestion ||
        !normalizeDiagnosticText(currentBody).includes(normalizedSuggestion));

    if (shouldAppendBody) {
      draft.value.body = currentBody ? `${currentBody}\n\n${bodySuggestion}` : bodySuggestion;
      lastAppliedSuggestions.value.body = bodySuggestion;
    }

    const summaryParts: string[] = [];
    if (lastAppliedSuggestions.value.aliases.length) {
      summaryParts.push(`问法别名 ${lastAppliedSuggestions.value.aliases.length} 条`);
    }
    if (lastAppliedSuggestions.value.keywords.length) {
      summaryParts.push(`关键词 ${lastAppliedSuggestions.value.keywords.length} 条`);
    }
    if (lastAppliedSuggestions.value.body) {
      summaryParts.push("正文说明 1 条");
    }

    if (!summaryParts.length) {
      successMessage.value = "建议内容已存在，无需重复采纳。";
      return;
    }

    successMessage.value = `已一键采纳：${summaryParts.join("、")}。`;
    await rerunDiagnosticAfterApply();
  } finally {
    applyingSuggestions.value = false;
  }
}

function seedDiagnosticQuestionFromDraft() {
  diagnosticQuestion.value = draft.value.question.trim();
  diagnosticErrorMessage.value = "";
}

async function runDiagnostic() {
  const question = diagnosticQuestion.value.trim();
  if (!question) {
    diagnosticErrorMessage.value = "请输入要诊断的用户问法。";
    diagnosticResult.value = null;
    return;
  }

  diagnosticLoading.value = true;
  diagnosticErrorMessage.value = "";

  try {
    diagnosticResult.value = await askFaq(question);
  } catch (error) {
    diagnosticResult.value = null;
    diagnosticErrorMessage.value =
      error instanceof Error ? error.message : "未知错误，无法完成问法诊断。";
  } finally {
    diagnosticLoading.value = false;
  }
}

function startCreate() {
  selectedEntryId.value = null;
  draft.value = createEmptyDraft();
  diagnosticQuestion.value = "";
  diagnosticResult.value = null;
  diagnosticErrorMessage.value = "";
  resetAppliedSuggestions();
  clearMessages();
  currentSubsection.value = "entries";
}

function selectEntry(entry: FaqEntry) {
  selectedEntryId.value = entry.id;
  draft.value = mapEntryToDraft(entry);
  diagnosticQuestion.value = entry.question;
  diagnosticResult.value = null;
  diagnosticErrorMessage.value = "";
  resetAppliedSuggestions();
  clearMessages();
  currentSubsection.value = "entries";
}

function selectSubsection(next: KnowledgeSubsection) {
  currentSubsection.value = next;
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
        selectedEntryId.value = null;
        draft.value = createEmptyDraft();
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

  const editingEntryId = selectedEntryId.value;
  saving.value = true;
  clearMessages();

  try {
    const saved = editingEntryId
      ? await updateFaqEntry(editingEntryId, input)
      : await createFaqEntry(input);

    await loadEntries();
    selectEntry(saved);
    successMessage.value = editingEntryId ? "知识库条目已更新。" : "知识库条目已创建。";
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
  clearMessages();

  try {
    await deleteFaqEntry(selectedEntryId.value);
    await loadEntries();
    selectedEntryId.value = null;
    draft.value = createEmptyDraft();
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
  clearMessages();

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
    currentSubsection.value = "import-export";
  } catch (error) {
    errorMessage.value =
      error instanceof Error ? error.message : "未知错误，无法导出知识库条目。";
  } finally {
    exporting.value = false;
  }
}

async function handleImport() {
  importing.value = true;
  clearMessages();

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
      const rawQuestionAliases = candidate.questionAliases ?? candidate.question_aliases;
      return {
        id: typeof candidate.id === "string" ? candidate.id : "",
        topic: String(candidate.topic ?? ""),
        question: String(candidate.question ?? ""),
        answer: String(candidate.answer ?? ""),
        sourceLabel: String(candidate.sourceLabel ?? candidate.source_label ?? ""),
        questionAliases: Array.isArray(rawQuestionAliases)
          ? rawQuestionAliases.map((value) => String(value))
          : [],
        keywords: Array.isArray(candidate.keywords)
          ? candidate.keywords.map((value) => String(value))
          : [],
        body: String(candidate.body ?? ""),
      } satisfies FaqEntry;
    });

    const result: FaqEntryImportResult = await importFaqEntries(items, importMode.value);
    await loadEntries();
    successMessage.value = `导入完成：共 ${result.importedCount} 条，新增 ${result.createdCount} 条，更新 ${result.updatedCount} 条。`;
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
  <section class="space-y-6">
    <section class="panel p-6">
      <div class="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
        <div class="max-w-3xl">
          <p class="text-sm font-semibold uppercase tracking-[0.24em] text-amber-700">
            Knowledge Workspace
          </p>
          <h2 class="mt-3 text-3xl font-semibold tracking-tight text-ink">
            知识库工作台
          </h2>
          <p class="mt-3 text-sm leading-7 text-slate-600">
            这里直接维护本地 SQLite 里的 FAQ 与知识文档。新增、编辑、导入或替换后，
            FAQ 检索和 Agent 知识路由都会复用同一份事实数据。
          </p>
        </div>

        <div class="grid gap-3 sm:grid-cols-3">
          <article class="rounded-3xl bg-slate-50 p-4">
            <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">数据后端</p>
            <p class="mt-2 text-lg font-semibold text-slate-900">{{ currentBackend }}</p>
          </article>
          <article class="rounded-3xl bg-slate-50 p-4">
            <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">文档总数</p>
            <p class="mt-2 text-lg font-semibold text-slate-900">{{ totalEntries }}</p>
          </article>
          <article class="rounded-3xl bg-slate-50 p-4">
            <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">主题数</p>
            <p class="mt-2 text-lg font-semibold text-slate-900">{{ totalTopics }}</p>
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
            currentSubsection === 'entries'
              ? 'bg-ink text-white'
              : 'border border-slate-200 text-slate-700 hover:border-slate-300 hover:bg-slate-50'
          "
          @click="selectSubsection('entries')"
        >
          条目维护
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
          导入导出
        </button>
      </div>

      <div class="mt-6 flex flex-wrap gap-2">
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
          <p class="text-sm font-semibold text-slate-900">条目维护</p>
          <p class="mt-3 text-sm leading-7 text-slate-600">
            用于日常编辑 FAQ 条目、短答案、关键词和知识正文，是知识库最常用的工作入口。
          </p>
          <div class="mt-5 flex flex-wrap gap-2">
            <span class="chip bg-sky-100 text-sky-800">{{ totalEntries }} 条条目</span>
            <span class="chip bg-slate-100 text-slate-700">{{ totalTopics }} 个主题</span>
          </div>
          <button
            type="button"
            class="mt-5 rounded-full border border-slate-200 px-4 py-2 text-sm text-slate-700 transition hover:border-slate-300 hover:bg-slate-50"
            @click="selectSubsection('entries')"
          >
            进入条目维护
          </button>
        </article>

        <article class="panel p-6">
          <p class="text-sm font-semibold text-slate-900">导入导出</p>
          <p class="mt-3 text-sm leading-7 text-slate-600">
            用于批量迁移知识文档，支持 `upsert` 增量更新，也支持 `replace` 清空后重建。
          </p>
          <div class="mt-5 flex flex-wrap gap-2">
            <span class="chip bg-amber-100 text-amber-800">upsert</span>
            <span class="chip bg-rose-100 text-rose-700">replace</span>
          </div>
          <button
            type="button"
            class="mt-5 rounded-full border border-slate-200 px-4 py-2 text-sm text-slate-700 transition hover:border-slate-300 hover:bg-slate-50"
            @click="selectSubsection('import-export')"
          >
            进入导入导出
          </button>
        </article>

        <article class="panel p-6">
          <p class="text-sm font-semibold text-slate-900">数据去向</p>
          <p class="mt-3 text-sm leading-7 text-slate-600">
            前台售前问答和 Agent 的知识检索都复用同一份知识事实，避免出现“问答一套、Agent 一套”的数据分裂。
          </p>
          <div class="mt-5 flex flex-wrap gap-2">
            <span class="chip bg-violet-100 text-violet-800">FAQ 检索</span>
            <span class="chip bg-emerald-100 text-emerald-800">Agent 路由</span>
          </div>
        </article>
      </div>

      <section class="panel p-6">
        <h3 class="text-xl font-semibold text-ink">推荐维护顺序</h3>
        <div class="mt-4 grid gap-4 lg:grid-cols-3">
          <article class="rounded-3xl bg-slate-50 p-4">
            <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Step 1</p>
            <p class="mt-2 text-sm font-semibold text-slate-900">先筛选或定位条目</p>
            <p class="mt-2 text-sm leading-6 text-slate-600">
              按主题和关键词找到当前要维护的知识条目。
            </p>
          </article>
          <article class="rounded-3xl bg-slate-50 p-4">
            <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Step 2</p>
            <p class="mt-2 text-sm font-semibold text-slate-900">再编辑短答案和正文</p>
            <p class="mt-2 text-sm leading-6 text-slate-600">
              短答案负责首屏回答，正文负责检索命中和知识切片。
            </p>
          </article>
          <article class="rounded-3xl bg-slate-50 p-4">
            <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Step 3</p>
            <p class="mt-2 text-sm font-semibold text-slate-900">批量迁移时再用导入导出</p>
            <p class="mt-2 text-sm leading-6 text-slate-600">
              单条编辑走维护区，批量同步或替换再进入导入导出区。
            </p>
          </article>
        </div>
      </section>
    </section>

    <section v-else-if="currentSubsection === 'entries'" class="space-y-6">
      <div>
        <h3 class="text-2xl font-semibold text-ink">条目维护</h3>
        <p class="mt-1 text-sm leading-6 text-slate-600">
          在这里筛选、编辑和删除单条知识文档，适合日常维护和快速修订。
        </p>
      </div>

      <div class="grid gap-4 xl:grid-cols-[0.82fr_1.18fr]">
        <div class="rounded-3xl bg-slate-50 p-4">
          <div class="flex items-center justify-between gap-3">
            <p class="text-sm font-semibold text-slate-800">知识文档列表</p>
            <span class="chip bg-slate-100 text-slate-700">
              {{ currentBackend }} / {{ totalEntries }} 条
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

          <div class="mt-4 max-h-[720px] space-y-3 overflow-y-auto pr-1">
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
              placeholder="用于首屏回答摘要和检索结果展示"
            />
          </div>

          <div class="mt-4">
            <label class="field-label">问法别名</label>
            <input
              v-model="draft.questionAliasesText"
              class="field-input"
              placeholder="支持中文逗号、英文逗号或换行分隔，例如：能开发票吗，发票怎么开"
            />
          </div>

          <div class="mt-4">
            <label class="field-label">关键词</label>
            <input
              v-model="draft.keywordsText"
              class="field-input"
              placeholder="支持中文逗号、英文逗号或换行分隔"
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
        </div>
      </div>

      <section class="panel p-6">
        <div class="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
          <div class="max-w-3xl">
            <h4 class="text-lg font-semibold text-ink">问法诊断</h4>
            <p class="mt-2 text-sm leading-6 text-slate-600">
              输入一句用户真实会说的话，直接查看当前知识库命中了哪条 FAQ，以及是靠标准问题、问法别名、关键词还是正文片段命中的。
            </p>
          </div>
          <div class="flex flex-wrap gap-2">
            <button
              type="button"
              class="rounded-full border border-slate-200 px-4 py-2 text-sm text-slate-700 transition hover:border-slate-300 hover:bg-slate-50"
              :disabled="!draft.question.trim()"
              @click="seedDiagnosticQuestionFromDraft"
            >
              使用当前标准问题
            </button>
            <button
              type="button"
              class="rounded-full bg-slate-900 px-4 py-2 text-sm text-white transition hover:bg-slate-800 disabled:cursor-wait disabled:opacity-70"
              :disabled="diagnosticLoading"
              @click="runDiagnostic"
            >
              {{ diagnosticLoading ? "诊断中..." : "开始诊断" }}
            </button>
          </div>
        </div>

        <div class="mt-4">
          <label class="field-label">用户问法</label>
          <textarea
            v-model="diagnosticQuestion"
            rows="3"
            class="field-input resize-none"
            placeholder="例如：发票抬头写错了还能改吗；退货运费谁出；下单后还能取消吗"
          />
        </div>

        <p
          v-if="diagnosticErrorMessage"
          class="mt-4 rounded-2xl bg-rose-50 px-4 py-3 text-sm text-rose-700"
        >
          {{ diagnosticErrorMessage }}
        </p>

        <div v-else-if="diagnosticResult" class="mt-5 space-y-4">
          <div class="flex flex-wrap gap-2">
            <span class="chip bg-sky-100 text-sky-800">
              命中条目: {{ diagnosticResult.matchedEntry?.question ?? "未命中" }}
            </span>
            <span
              v-if="diagnosticResult.matchedEntry"
              class="chip bg-slate-100 text-slate-700"
            >
              {{ diagnosticResult.matchedEntry.id }}
            </span>
            <span
              v-if="diagnosticMatchedCurrentEntry === true"
              class="chip bg-emerald-100 text-emerald-800"
            >
              已命中当前编辑条目
            </span>
            <span
              v-else-if="diagnosticMatchedCurrentEntry === false"
              class="chip bg-amber-100 text-amber-800"
            >
              未命中当前编辑条目
            </span>
          </div>

          <div
            v-if="diagnosticResult.matchSignals.length"
            class="rounded-3xl bg-slate-50 p-4"
          >
            <p class="text-sm font-semibold text-slate-800">命中原因</p>
            <div class="mt-3 grid gap-3 md:grid-cols-2">
              <article
                v-for="signal in diagnosticResult.matchSignals"
                :key="`${signal.kind}-${signal.matchedValue}`"
                class="rounded-2xl border border-slate-200 bg-white p-4"
              >
                <div class="flex flex-wrap items-center gap-2">
                  <span class="chip bg-violet-100 text-violet-800">{{ signal.label }}</span>
                  <span class="chip bg-slate-100 text-slate-700">{{ signal.matchedValue }}</span>
                </div>
                <p v-if="signal.detail" class="mt-3 text-sm leading-6 text-slate-600">
                  {{ signal.detail }}
                </p>
              </article>
            </div>
          </div>

          <div
            v-if="draft.question.trim()"
            class="rounded-3xl bg-white p-4"
          >
            <div class="flex flex-wrap items-center gap-2">
              <p class="text-sm font-semibold text-slate-800">当前条目对比诊断</p>
              <span
                v-if="diagnosticMatchedCurrentEntry === true"
                class="chip bg-emerald-100 text-emerald-800"
              >
                当前条目已命中
              </span>
              <span
                v-else-if="diagnosticMatchedCurrentEntry === false"
                class="chip bg-amber-100 text-amber-800"
              >
                当前条目未命中
              </span>
            </div>

            <div
              v-if="currentDraftDiagnosticSignals.length"
              class="mt-4 grid gap-3 md:grid-cols-2"
            >
              <article
                v-for="signal in currentDraftDiagnosticSignals"
                :key="`draft-${signal.kind}-${signal.matchedValue}`"
                class="rounded-2xl border border-slate-200 bg-slate-50 p-4"
              >
                <div class="flex flex-wrap items-center gap-2">
                  <span class="chip bg-emerald-100 text-emerald-800">{{ signal.label }}</span>
                  <span class="chip bg-slate-100 text-slate-700">{{ signal.matchedValue }}</span>
                </div>
                <p class="mt-3 text-sm leading-6 text-slate-600">{{ signal.detail }}</p>
              </article>
            </div>
            <p
              v-else
              class="mt-4 rounded-2xl bg-slate-50 px-4 py-3 text-sm text-slate-600"
            >
              当前草稿与这句用户问法之间还没有明显命中点。
            </p>

            <div
              v-if="currentDraftDiagnosticGaps.length"
              class="mt-4 rounded-2xl border border-dashed border-amber-300 bg-amber-50 px-4 py-4"
            >
              <p class="text-sm font-semibold text-amber-900">下一步可优化点</p>
              <ul class="mt-3 space-y-2 text-sm leading-6 text-amber-900">
                <li
                  v-for="item in currentDraftDiagnosticGaps"
                  :key="item"
                >
                  {{ item }}
                </li>
              </ul>
            </div>

            <div
              v-if="diagnosticComparisonCards.length"
              class="mt-4 rounded-2xl border border-slate-200 bg-slate-50 p-4"
            >
              <p class="text-sm font-semibold text-slate-800">当前条目 vs 实际命中条目</p>
              <div class="mt-4 grid gap-4 xl:grid-cols-2">
                <article
                  v-for="card in diagnosticComparisonCards"
                  :key="card.title"
                  class="rounded-2xl border border-slate-200 bg-white p-4"
                >
                  <div class="flex flex-wrap items-center gap-2">
                    <span class="chip bg-sky-100 text-sky-800">{{ card.title }}</span>
                    <span class="chip bg-slate-100 text-slate-700">{{ card.badge }}</span>
                  </div>
                  <div class="mt-4 space-y-3 text-sm text-slate-700">
                    <div>
                      <p class="font-medium text-slate-900">标准问题</p>
                      <p class="mt-1 leading-6">{{ card.question }}</p>
                    </div>
                    <div>
                      <p class="font-medium text-slate-900">来源标签</p>
                      <p class="mt-1 leading-6">{{ card.sourceLabel }}</p>
                    </div>
                    <div>
                      <p class="font-medium text-slate-900">问法别名</p>
                      <div class="mt-2 flex flex-wrap gap-2">
                        <span
                          v-for="alias in card.aliases.slice(0, 6)"
                          :key="alias"
                          class="chip bg-emerald-100 text-emerald-800"
                        >
                          {{ alias }}
                        </span>
                        <span
                          v-if="!card.aliases.length"
                          class="chip bg-slate-100 text-slate-700"
                        >
                          暂无
                        </span>
                      </div>
                    </div>
                    <div>
                      <p class="font-medium text-slate-900">关键词</p>
                      <div class="mt-2 flex flex-wrap gap-2">
                        <span
                          v-for="keyword in card.keywords.slice(0, 6)"
                          :key="keyword"
                          class="chip bg-amber-100 text-amber-800"
                        >
                          {{ keyword }}
                        </span>
                        <span
                          v-if="!card.keywords.length"
                          class="chip bg-slate-100 text-slate-700"
                        >
                          暂无
                        </span>
                      </div>
                    </div>
                    <div>
                      <p class="font-medium text-slate-900">正文片段</p>
                      <p class="mt-1 leading-6">{{ card.bodySnippet }}</p>
                    </div>
                  </div>
                </article>
              </div>

              <div
                v-if="diagnosticComparisonInsights.length"
                class="mt-4 rounded-2xl border border-dashed border-sky-300 bg-sky-50 px-4 py-4"
              >
                <p class="text-sm font-semibold text-sky-900">对比结论</p>
                <ul class="mt-3 space-y-2 text-sm leading-6 text-sky-900">
                  <li
                    v-for="item in diagnosticComparisonInsights"
                    :key="item"
                  >
                    {{ item }}
                  </li>
                </ul>
              </div>
            </div>

            <div
              v-if="
                diagnosticActionSuggestions.aliasSuggestions.length ||
                diagnosticActionSuggestions.keywordSuggestions.length ||
                diagnosticActionSuggestions.bodySuggestion ||
                lastAppliedSuggestions.aliases.length ||
                lastAppliedSuggestions.keywords.length ||
                lastAppliedSuggestions.body
              "
              class="mt-4 rounded-2xl border border-emerald-300 bg-emerald-50 px-4 py-4"
            >
              <div class="flex flex-wrap items-center justify-between gap-3">
                <p class="text-sm font-semibold text-emerald-900">可直接补到当前条目的建议</p>
                <button
                  v-if="
                    diagnosticActionSuggestions.aliasSuggestions.length ||
                    diagnosticActionSuggestions.keywordSuggestions.length ||
                    diagnosticActionSuggestions.bodySuggestion
                  "
                  type="button"
                  class="rounded-full border border-emerald-400 px-4 py-1.5 text-xs font-medium text-emerald-900 transition hover:bg-emerald-100 disabled:cursor-not-allowed disabled:opacity-60"
                  :disabled="applyingSuggestions"
                  @click="applyAllSuggestions"
                >
                  {{ applyingSuggestions ? "采纳中..." : "一键全部采纳" }}
                </button>
              </div>

              <div
                v-if="
                  diagnosticActionSuggestions.aliasSuggestions.length ||
                  lastAppliedSuggestions.aliases.length
                "
                class="mt-4"
              >
                <div class="flex flex-wrap items-center gap-2">
                  <p class="text-sm font-medium text-emerald-900">建议新增问法别名</p>
                  <button
                    v-if="diagnosticActionSuggestions.aliasSuggestions.length"
                    type="button"
                    class="rounded-full border border-emerald-300 px-3 py-1 text-xs text-emerald-800 transition hover:bg-emerald-100 disabled:cursor-not-allowed disabled:opacity-60"
                    :disabled="applyingSuggestions"
                    @click="applyAliasSuggestions"
                  >
                    {{ applyingSuggestions ? "处理中..." : "一键追加" }}
                  </button>
                </div>
                <div
                  v-if="diagnosticActionSuggestions.aliasSuggestions.length"
                  class="mt-2 flex flex-wrap gap-2"
                >
                  <span
                    v-for="item in diagnosticActionSuggestions.aliasSuggestions"
                    :key="item"
                    class="chip bg-white text-emerald-800"
                  >
                    {{ item }}
                  </span>
                </div>
                <div
                  v-if="lastAppliedSuggestions.aliases.length"
                  class="mt-3 rounded-2xl border border-emerald-200 bg-white/80 px-3 py-3"
                >
                  <p class="text-xs font-medium text-emerald-900">最近自动追加的问法别名</p>
                  <div class="mt-2 flex flex-wrap gap-2">
                    <span
                      v-for="item in lastAppliedSuggestions.aliases"
                      :key="`applied-alias-${item}`"
                      class="chip bg-emerald-100 text-emerald-900"
                    >
                      {{ item }}
                    </span>
                  </div>
                </div>
              </div>

              <div
                v-if="
                  diagnosticActionSuggestions.keywordSuggestions.length ||
                  lastAppliedSuggestions.keywords.length
                "
                class="mt-4"
              >
                <div class="flex flex-wrap items-center gap-2">
                  <p class="text-sm font-medium text-emerald-900">建议补充关键词</p>
                  <button
                    v-if="diagnosticActionSuggestions.keywordSuggestions.length"
                    type="button"
                    class="rounded-full border border-emerald-300 px-3 py-1 text-xs text-emerald-800 transition hover:bg-emerald-100 disabled:cursor-not-allowed disabled:opacity-60"
                    :disabled="applyingSuggestions"
                    @click="applyKeywordSuggestions"
                  >
                    {{ applyingSuggestions ? "处理中..." : "一键追加" }}
                  </button>
                </div>
                <div
                  v-if="diagnosticActionSuggestions.keywordSuggestions.length"
                  class="mt-2 flex flex-wrap gap-2"
                >
                  <span
                    v-for="item in diagnosticActionSuggestions.keywordSuggestions"
                    :key="item"
                    class="chip bg-white text-emerald-800"
                  >
                    {{ item }}
                  </span>
                </div>
                <div
                  v-if="lastAppliedSuggestions.keywords.length"
                  class="mt-3 rounded-2xl border border-emerald-200 bg-white/80 px-3 py-3"
                >
                  <p class="text-xs font-medium text-emerald-900">最近自动追加的关键词</p>
                  <div class="mt-2 flex flex-wrap gap-2">
                    <span
                      v-for="item in lastAppliedSuggestions.keywords"
                      :key="`applied-keyword-${item}`"
                      class="chip bg-emerald-100 text-emerald-900"
                    >
                      {{ item }}
                    </span>
                  </div>
                </div>
              </div>

              <div
                v-if="diagnosticActionSuggestions.bodySuggestion || lastAppliedSuggestions.body"
                class="mt-4"
              >
                <div class="flex flex-wrap items-center gap-2">
                  <p class="text-sm font-medium text-emerald-900">建议补一条正文说明</p>
                  <button
                    v-if="diagnosticActionSuggestions.bodySuggestion"
                    type="button"
                    class="rounded-full border border-emerald-300 px-3 py-1 text-xs text-emerald-800 transition hover:bg-emerald-100 disabled:cursor-not-allowed disabled:opacity-60"
                    :disabled="applyingSuggestions"
                    @click="applyBodySuggestion"
                  >
                    {{ applyingSuggestions ? "处理中..." : "一键追加" }}
                  </button>
                </div>
                <p
                  v-if="diagnosticActionSuggestions.bodySuggestion"
                  class="mt-2 rounded-2xl bg-white px-4 py-3 text-sm leading-6 text-emerald-900"
                >
                  {{ diagnosticActionSuggestions.bodySuggestion }}
                </p>
                <div
                  v-if="lastAppliedSuggestions.body"
                  class="mt-3 rounded-2xl border border-emerald-200 bg-white/80 px-3 py-3"
                >
                  <p class="text-xs font-medium text-emerald-900">最近自动追加的正文说明</p>
                  <p class="mt-2 text-sm leading-6 text-emerald-900">
                    {{ lastAppliedSuggestions.body }}
                  </p>
                </div>
              </div>
            </div>
          </div>

          <div
            v-if="diagnosticResult.citations.length"
            class="rounded-3xl bg-slate-50 p-4"
          >
            <p class="text-sm font-semibold text-slate-800">命中片段</p>
            <div class="mt-3 grid gap-3">
              <article
                v-for="citation in diagnosticResult.citations"
                :key="`${citation.entryId}-${citation.score}`"
                class="rounded-2xl border border-slate-200 bg-white p-4"
              >
                <div class="flex flex-wrap gap-2">
                  <span class="chip bg-slate-100 text-slate-700">{{ citation.title }}</span>
                  <span class="chip bg-sky-100 text-sky-800">{{ citation.sourceLabel }}</span>
                </div>
                <p class="mt-3 text-sm leading-6 text-slate-600">{{ citation.snippet }}</p>
              </article>
            </div>
          </div>
        </div>
      </section>
    </section>

    <section v-else class="space-y-6">
      <div>
        <h3 class="text-2xl font-semibold text-ink">导入导出</h3>
        <p class="mt-1 text-sm leading-6 text-slate-600">
          适合批量迁移、备份或替换知识库内容。单条编辑请回到“条目维护”区。
        </p>
      </div>

      <section class="panel p-6">
        <div class="flex flex-wrap items-center gap-2">
          <span class="chip bg-sky-100 text-sky-800">JSON 导入导出</span>
          <span class="chip bg-slate-100 text-slate-700">支持 upsert / replace</span>
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
          <div class="mt-4 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-600">
            <p class="font-medium text-slate-800">导入字段说明</p>
            <p class="mt-2 leading-6">
              建议至少包含 <code>topic</code>、<code>question</code>、<code>answer</code>、
              <code>sourceLabel</code> 或 <code>source_label</code>。
            </p>
            <p class="mt-2 leading-6">
              问法别名同时支持 <code>questionAliases</code> 和 <code>question_aliases</code>；
              当前导出结果默认使用前端 camelCase 字段。
            </p>
          </div>
          <textarea
            v-model="importJson"
            rows="14"
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
      </section>
    </section>
  </section>
</template>

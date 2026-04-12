export type FaqEntry = {
  id: string;
  topic: string;
  question: string;
  answer: string;
  sourceLabel: string;
  questionAliases: string[];
  keywords: string[];
  body: string;
};

export type FaqCitation = {
  entryId: string;
  title: string;
  snippet: string;
  sourceLabel: string;
  score: number;
};

export type FaqMatchSignal = {
  kind: string;
  label: string;
  matchedValue: string;
  detail: string;
};

export type FaqAskResult = {
  question: string;
  answer: string;
  matchedEntry: FaqEntry | null;
  sourceLabel: string;
  suggestions: string[];
  citations: FaqCitation[];
  matchSignals: FaqMatchSignal[];
  retrievalMode: string;
  retrievalProvider: string;
  answerProvider: string;
};

export type FaqEntryInput = {
  topic: string;
  question: string;
  answer: string;
  sourceLabel: string;
  questionAliases: string[];
  keywords: string[];
  body: string;
};

export type FaqEntryListResult = {
  backend: string;
  items: FaqEntry[];
};

export type FaqImportMode = "upsert" | "replace";

export type FaqEntryImportResult = {
  mode: FaqImportMode;
  importedCount: number;
  createdCount: number;
  updatedCount: number;
  backend: string;
};

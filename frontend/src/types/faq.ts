export type FaqEntry = {
  id: string;
  topic: string;
  question: string;
  answer: string;
  sourceLabel: string;
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

export type FaqAskResult = {
  question: string;
  answer: string;
  matchedEntry: FaqEntry | null;
  sourceLabel: string;
  suggestions: string[];
  citations: FaqCitation[];
  retrievalMode: string;
};

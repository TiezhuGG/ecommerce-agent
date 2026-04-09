export type FaqEntryResponse = {
  id: string;
  topic: string;
  question: string;
  answer: string;
  source_label: string;
  keywords: string[];
  body: string;
};

export type FaqCitationResponse = {
  entry_id: string;
  title: string;
  snippet: string;
  source_label: string;
  score: number;
};

export type FaqAskResponse = {
  question: string;
  answer: string;
  matched_entry: FaqEntryResponse | null;
  source_label: string;
  suggestions: string[];
  citations: FaqCitationResponse[];
  retrieval_mode: string;
};

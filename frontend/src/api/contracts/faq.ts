import type { FaqEntry } from "../../types/faq";

export type FaqAskResponse = {
  question: string;
  answer: string;
  matched_entry: FaqEntry | null;
  source_label: string;
  suggestions: string[];
};

import { requestJson } from "./client";
import type {
  FaqAskResponse,
  FaqCitationResponse,
  FaqEntryResponse,
} from "./contracts/faq";
import type { FaqAskResult, FaqCitation, FaqEntry } from "../types/faq";


function mapFaqEntry(entry: FaqEntryResponse): FaqEntry {
  return {
    id: entry.id,
    topic: entry.topic,
    question: entry.question,
    answer: entry.answer,
    sourceLabel: entry.source_label,
    keywords: entry.keywords,
    body: entry.body,
  };
}


function mapFaqCitation(citation: FaqCitationResponse): FaqCitation {
  return {
    entryId: citation.entry_id,
    title: citation.title,
    snippet: citation.snippet,
    sourceLabel: citation.source_label,
    score: citation.score,
  };
}


export function mapFaqAskResponse(response: FaqAskResponse): FaqAskResult {
  return {
    question: response.question,
    answer: response.answer,
    matchedEntry: response.matched_entry ? mapFaqEntry(response.matched_entry) : null,
    sourceLabel: response.source_label,
    suggestions: response.suggestions,
    citations: response.citations.map(mapFaqCitation),
    retrievalMode: response.retrieval_mode,
  };
}


export async function askFaq(question: string): Promise<FaqAskResult> {
  const response = await requestJson<FaqAskResponse>("/faq/ask", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ question }),
  });

  return mapFaqAskResponse(response);
}

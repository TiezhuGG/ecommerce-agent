import { requestJson } from "./client";
import type {
  FaqAskResponse,
  FaqCitationResponse,
  FaqDeleteResponse,
  FaqEntryResponse,
  FaqEntryImportResponse,
  FaqEntryListResponse,
} from "./contracts/faq";
import type {
  FaqAskResult,
  FaqCitation,
  FaqEntry,
  FaqEntryImportResult,
  FaqEntryInput,
  FaqEntryListResult,
  FaqImportMode,
} from "../types/faq";


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
    retrievalProvider: response.retrieval_provider,
    answerProvider: response.answer_provider,
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


function mapFaqEntryInput(input: FaqEntryInput) {
  return {
    topic: input.topic,
    question: input.question,
    answer: input.answer,
    source_label: input.sourceLabel,
    keywords: input.keywords,
    body: input.body,
  };
}


export async function fetchFaqEntries(): Promise<FaqEntryListResult> {
  const response = await requestJson<FaqEntryListResponse>("/faq/entries");
  return {
    backend: response.backend,
    items: response.items.map(mapFaqEntry),
  };
}


export async function createFaqEntry(input: FaqEntryInput): Promise<FaqEntry> {
  const response = await requestJson<FaqEntryResponse>("/faq/entries", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(mapFaqEntryInput(input)),
  });

  return mapFaqEntry(response);
}


export async function updateFaqEntry(entryId: string, input: FaqEntryInput): Promise<FaqEntry> {
  const response = await requestJson<FaqEntryResponse>(`/faq/entries/${entryId}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(mapFaqEntryInput(input)),
  });

  return mapFaqEntry(response);
}


export async function deleteFaqEntry(entryId: string): Promise<FaqDeleteResponse> {
  return requestJson<FaqDeleteResponse>(`/faq/entries/${entryId}`, {
    method: "DELETE",
  });
}


export async function exportFaqEntries(): Promise<FaqEntryListResult> {
  const response = await requestJson<FaqEntryListResponse>("/faq/entries/export");
  return {
    backend: response.backend,
    items: response.items.map(mapFaqEntry),
  };
}


export async function importFaqEntries(
  items: FaqEntry[],
  mode: FaqImportMode,
): Promise<FaqEntryImportResult> {
  const response = await requestJson<FaqEntryImportResponse>("/faq/entries/import", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      mode,
      items: items.map((item) => ({
        id: item.id,
        topic: item.topic,
        question: item.question,
        answer: item.answer,
        source_label: item.sourceLabel,
        keywords: item.keywords,
        body: item.body,
      })),
    }),
  });

  return {
    mode: response.mode,
    importedCount: response.imported_count,
    createdCount: response.created_count,
    updatedCount: response.updated_count,
    backend: response.backend,
  };
}

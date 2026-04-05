import type { AgentResult } from "../types/agent";
import { requestJson } from "./client";
import type { IntentParseResponse } from "./contracts/intent";


export async function parseIntent(query: string): Promise<AgentResult> {
  const response = await requestJson<IntentParseResponse>("/intent/parse", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ query }),
  });

  return {
    query: response.query,
    searchFilters: {
      keyword: response.search_filters.keyword,
      category: response.search_filters.category,
      brand: response.search_filters.brand,
      maxPrice: response.search_filters.max_price,
    },
    scenario: response.scenario,
    priorities: response.priorities,
    appliedFilters: response.applied_filters,
    reasoningSummary: response.reasoning_summary,
    provider: response.provider,
    model: response.model,
  };
}

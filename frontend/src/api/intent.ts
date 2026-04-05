import type { ParsedIntentResult } from "../types/agent";
import { requestJson } from "./client";
import type { IntentParseResponse } from "./contracts/intent";


// 这个文件保留为“单独调用意图解析工具”的低层 API。
// 即使现在页面主入口已经升级成 Agent 工作台，这个能力依然可以被单独复用。
export async function parseIntent(query: string): Promise<ParsedIntentResult> {
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

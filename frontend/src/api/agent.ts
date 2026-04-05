import type {
  AgentChatResponse,
  AgentPrecheckResponse,
  AgentToolCallResponse,
  AgentToolStatusResponse,
} from "./contracts/agent";
import { requestJson } from "./client";
import type {
  AgentPrecheck,
  AgentResult,
  AgentToolCall,
  AgentToolStatus,
} from "../types/agent";
import type { SearchFilters } from "../types/catalog";


function mapAgentToolStatus(tool: AgentToolStatusResponse): AgentToolStatus {
  return {
    name: tool.name,
    enabled: tool.enabled,
    description: tool.description,
  };
}


function mapAgentToolCall(toolCall: AgentToolCallResponse): AgentToolCall {
  return {
    toolName: toolCall.tool_name,
    status: toolCall.status,
    summary: toolCall.summary,
    inputPayload: toolCall.input_payload,
    outputPayload: toolCall.output_payload,
  };
}


function mapSearchFilters(
  response: AgentChatResponse["parsed_intent"],
): SearchFilters | null {
  if (!response) {
    return null;
  }

  return {
    keyword: response.search_filters.keyword,
    category: response.search_filters.category,
    brand: response.search_filters.brand,
    maxPrice: response.search_filters.max_price,
  };
}


export async function fetchAgentPrecheck(): Promise<AgentPrecheck> {
  const response = await requestJson<AgentPrecheckResponse>("/agent/precheck");

  return {
    status: response.status,
    summary: response.summary,
    model: response.model,
    baseUrl: response.base_url,
    apiStyle: response.api_style,
    openaiSdkAvailable: response.openai_sdk_available,
    langgraphAvailable: response.langgraph_available,
    catalogTotal: response.catalog_total,
    warnings: response.warnings,
    tools: response.tools.map(mapAgentToolStatus),
  };
}


export async function chatWithAgent(
  message: string,
  selectedProductIds: string[],
): Promise<AgentResult> {
  const response = await requestJson<AgentChatResponse>("/agent/chat", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      message,
      selected_product_ids: selectedProductIds,
    }),
  });

  return {
    message: response.message,
    route: response.route,
    routeReasoning: response.route_reasoning,
    finalAnswer: response.final_answer,
    warnings: response.warnings,
    toolCalls: response.tool_calls.map(mapAgentToolCall),
    parsedIntent: response.parsed_intent
      ? {
          query: response.parsed_intent.query,
          searchFilters: mapSearchFilters(response.parsed_intent) ?? {
            keyword: "",
            category: "",
            brand: "",
            maxPrice: null,
          },
          scenario: response.parsed_intent.scenario,
          priorities: response.parsed_intent.priorities,
          appliedFilters: response.parsed_intent.applied_filters,
          reasoningSummary: response.parsed_intent.reasoning_summary,
          provider: response.parsed_intent.provider,
          model: response.parsed_intent.model,
        }
      : null,
    recommendedProductIds: response.recommended_product_ids,
    faqResult: response.faq_result,
    compareResult: response.compare_result,
    provider: response.provider,
    model: response.model,
    graphRuntime: response.graph_runtime,
  };
}

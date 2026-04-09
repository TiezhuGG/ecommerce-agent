import type {
  AgentChatResponse,
  AgentConversationTurnResponse,
  AgentProvidersResponse,
  AgentRunDetailResponse,
  AgentPrecheckResponse,
  AgentRunListResponse,
  AgentRunSummaryResponse,
  AgentToolCallResponse,
  AgentToolStatusResponse,
} from "./contracts/agent";
import { requestJson } from "./client";
import { mapFaqAskResponse } from "./faq";
import type {
  AgentConversationTurn,
  AgentPrecheck,
  AgentProviders,
  AgentRunHistory,
  AgentResult,
  AgentRunSummary,
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


function mapAgentProviders(providers: AgentProvidersResponse): AgentProviders {
  return {
    routeProvider: providers.route_provider,
    intentProvider: providers.intent_provider,
    answerProvider: providers.answer_provider,
    retrievalProvider: providers.retrieval_provider,
  };
}


function mapConversationTurn(turn: AgentConversationTurnResponse): AgentConversationTurn {
  return {
    userMessage: turn.user_message,
    agentAnswer: turn.agent_answer,
    route: turn.route,
    selectedProductIds: turn.selected_product_ids,
    recommendedProductIds: turn.recommended_product_ids,
  };
}


function mapAgentRunSummary(item: AgentRunSummaryResponse): AgentRunSummary {
  return {
    runId: item.run_id,
    createdAt: item.created_at,
    message: item.message,
    route: item.route,
    finalAnswerPreview: item.final_answer_preview,
    warningCount: item.warning_count,
    toolCallCount: item.tool_call_count,
    selectedProductIds: item.selected_product_ids,
    recommendedProductIds: item.recommended_product_ids,
    providers: {
      routeProvider: "",
      intentProvider: "",
      answerProvider: item.provider,
      retrievalProvider: "",
    },
    provider: item.provider,
    model: item.model,
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


function mapAgentResultFromResponse(
  response: AgentChatResponse | AgentRunDetailResponse,
  options: {
    origin: "live" | "history";
    createdAt: string | null;
  },
): AgentResult {
  return {
    origin: options.origin,
    createdAt: options.createdAt,
    message: response.message,
    selectedProductIds: response.selected_product_ids,
    conversationContext: response.conversation_context.map(mapConversationTurn),
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
    faqResult: response.faq_result ? mapFaqAskResponse(response.faq_result) : null,
    compareResult: response.compare_result,
    providers: mapAgentProviders(response.providers),
    provider: response.provider,
    model: response.model,
    graphRuntime: response.graph_runtime,
    runId: "run_id" in response ? response.run_id : null,
    persisted: response.persisted,
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
    dataBackend: response.data_backend,
    agentLogBackend: response.agent_log_backend,
    catalogTotal: response.catalog_total,
    warnings: response.warnings,
    tools: response.tools.map(mapAgentToolStatus),
  };
}


export async function chatWithAgent(
  message: string,
  selectedProductIds: string[],
  conversationContext: AgentConversationTurn[],
): Promise<AgentResult> {
  const response = await requestJson<AgentChatResponse>("/agent/chat", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      message,
      selected_product_ids: selectedProductIds,
      conversation_context: conversationContext.map((turn) => ({
        user_message: turn.userMessage,
        agent_answer: turn.agentAnswer,
        route: turn.route,
        selected_product_ids: turn.selectedProductIds,
        recommended_product_ids: turn.recommendedProductIds,
      })),
    }),
  });

  return mapAgentResultFromResponse(response, {
    origin: "live",
    createdAt: null,
  });
}


export async function fetchAgentRunDetail(runId: string): Promise<AgentResult> {
  const response = await requestJson<AgentRunDetailResponse>(`/agent/runs/${runId}`);
  return mapAgentResultFromResponse(response, {
    origin: "history",
    createdAt: response.created_at,
  });
}


export async function fetchRecentAgentRuns(limit = 10): Promise<AgentRunHistory> {
  const response = await requestJson<AgentRunListResponse>(`/agent/runs?limit=${limit}`);

  return {
    backend: response.backend,
    items: response.items.map(mapAgentRunSummary),
  };
}

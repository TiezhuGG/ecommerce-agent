import type { CompareResponse } from "./compare";
import type { FaqAskResponse } from "./faq";
import type { IntentParseResponse } from "./intent";


export type AgentToolStatusResponse = {
  name: string;
  enabled: boolean;
  description: string;
};

export type AgentPrecheckResponse = {
  status: string;
  summary: string;
  model: string;
  base_url: string | null;
  api_style: string;
  openai_sdk_available: boolean;
  langgraph_available: boolean;
  data_backend: string;
  agent_log_backend: string;
  catalog_total: number;
  warnings: string[];
  tools: AgentToolStatusResponse[];
};

export type AgentToolCallResponse = {
  tool_name: string;
  status: string;
  summary: string;
  input_payload: Record<string, unknown>;
  output_payload: Record<string, unknown>;
};

export type AgentProvidersResponse = {
  route_provider: string;
  intent_provider: string;
  answer_provider: string;
  retrieval_provider: string;
};

export type AgentConversationTurnResponse = {
  user_message: string;
  agent_answer: string;
  route: "shopping" | "faq" | "compare" | "";
  selected_product_ids: string[];
  recommended_product_ids: string[];
};

export type AgentChatResponse = {
  message: string;
  thread_id: string;
  selected_product_ids: string[];
  conversation_context: AgentConversationTurnResponse[];
  route: "shopping" | "faq" | "compare";
  route_reasoning: string;
  final_answer: string;
  warnings: string[];
  tool_calls: AgentToolCallResponse[];
  parsed_intent: IntentParseResponse | null;
  recommended_product_ids: string[];
  faq_result: FaqAskResponse | null;
  compare_result: CompareResponse | null;
  providers: AgentProvidersResponse;
  provider: string;
  model: string;
  graph_runtime: string;
  run_id: string | null;
  persisted: boolean;
};

export type AgentRunDetailResponse = {
  run_id: string;
  thread_id: string;
  created_at: string;
  message: string;
  selected_product_ids: string[];
  conversation_context: AgentConversationTurnResponse[];
  route: "shopping" | "faq" | "compare";
  route_reasoning: string;
  final_answer: string;
  warnings: string[];
  tool_calls: AgentToolCallResponse[];
  parsed_intent: IntentParseResponse | null;
  recommended_product_ids: string[];
  faq_result: FaqAskResponse | null;
  compare_result: CompareResponse | null;
  providers: AgentProvidersResponse;
  provider: string;
  model: string;
  graph_runtime: string;
  persisted: boolean;
};

export type AgentRunSummaryResponse = {
  run_id: string;
  thread_id: string;
  created_at: string;
  message: string;
  route: "shopping" | "faq" | "compare";
  final_answer_preview: string;
  warning_count: number;
  tool_call_count: number;
  selected_product_ids: string[];
  recommended_product_ids: string[];
  provider: string;
  model: string;
};

export type AgentRunListResponse = {
  backend: string;
  items: AgentRunSummaryResponse[];
};

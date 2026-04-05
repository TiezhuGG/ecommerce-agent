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

export type AgentChatResponse = {
  message: string;
  route: "shopping" | "faq" | "compare";
  route_reasoning: string;
  final_answer: string;
  warnings: string[];
  tool_calls: AgentToolCallResponse[];
  parsed_intent: IntentParseResponse | null;
  recommended_product_ids: string[];
  faq_result: FaqAskResponse | null;
  compare_result: CompareResponse | null;
  provider: string;
  model: string;
  graph_runtime: string;
};

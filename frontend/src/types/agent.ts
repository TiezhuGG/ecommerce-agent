import type { CompareResponse } from "../api/contracts/compare";
import type { FaqAskResponse } from "../api/contracts/faq";
import type { SearchFilters } from "./catalog";


export type AgentRoute = "shopping" | "faq" | "compare";

export type ParsedIntentResult = {
  query: string;
  searchFilters: SearchFilters;
  scenario: string;
  priorities: string[];
  appliedFilters: string[];
  reasoningSummary: string;
  provider: string;
  model: string;
};

export type AgentToolStatus = {
  name: string;
  enabled: boolean;
  description: string;
};

export type AgentToolCall = {
  toolName: string;
  status: string;
  summary: string;
  inputPayload: Record<string, unknown>;
  outputPayload: Record<string, unknown>;
};

export type AgentPrecheck = {
  status: string;
  summary: string;
  model: string;
  baseUrl: string | null;
  apiStyle: string;
  openaiSdkAvailable: boolean;
  langgraphAvailable: boolean;
  catalogTotal: number;
  warnings: string[];
  tools: AgentToolStatus[];
};

export type AgentResult = {
  message: string;
  route: AgentRoute;
  routeReasoning: string;
  finalAnswer: string;
  warnings: string[];
  toolCalls: AgentToolCall[];
  parsedIntent: ParsedIntentResult | null;
  recommendedProductIds: string[];
  faqResult: FaqAskResponse | null;
  compareResult: CompareResponse | null;
  provider: string;
  model: string;
  graphRuntime: string;
};

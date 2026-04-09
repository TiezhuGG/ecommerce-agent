import type { CompareResponse } from "../api/contracts/compare";
import type { SearchFilters } from "./catalog";
import type { FaqAskResult } from "./faq";


export type AgentRoute = "shopping" | "faq" | "compare";
export type AgentResultOrigin = "live" | "history";

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

export type AgentProviders = {
  routeProvider: string;
  intentProvider: string;
  answerProvider: string;
  retrievalProvider: string;
};

export type AgentConversationTurn = {
  userMessage: string;
  agentAnswer: string;
  route: AgentRoute | "";
  selectedProductIds: string[];
  recommendedProductIds: string[];
};

export type AgentPrecheck = {
  status: string;
  summary: string;
  model: string;
  baseUrl: string | null;
  apiStyle: string;
  openaiSdkAvailable: boolean;
  langgraphAvailable: boolean;
  dataBackend: string;
  agentLogBackend: string;
  catalogTotal: number;
  warnings: string[];
  tools: AgentToolStatus[];
};

export type AgentResult = {
  origin: AgentResultOrigin;
  createdAt: string | null;
  message: string;
  selectedProductIds: string[];
  conversationContext: AgentConversationTurn[];
  route: AgentRoute;
  routeReasoning: string;
  finalAnswer: string;
  warnings: string[];
  toolCalls: AgentToolCall[];
  parsedIntent: ParsedIntentResult | null;
  recommendedProductIds: string[];
  faqResult: FaqAskResult | null;
  compareResult: CompareResponse | null;
  providers: AgentProviders;
  provider: string;
  model: string;
  graphRuntime: string;
  runId: string | null;
  persisted: boolean;
};

export type AgentRunSummary = {
  runId: string;
  createdAt: string;
  message: string;
  route: AgentRoute;
  finalAnswerPreview: string;
  warningCount: number;
  toolCallCount: number;
  selectedProductIds: string[];
  recommendedProductIds: string[];
  providers: AgentProviders;
  provider: string;
  model: string;
};

export type AgentRunHistory = {
  backend: string;
  items: AgentRunSummary[];
};

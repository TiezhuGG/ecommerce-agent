export type AgentResult = {
  title: string;
  parsedIntent: string;
  appliedFilters: string[];
  answer: string;
  executionSteps: string[];
};

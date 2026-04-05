import type { SearchFilters } from "./catalog";


export type AgentResult = {
  query: string;
  searchFilters: SearchFilters;
  scenario: string;
  priorities: string[];
  appliedFilters: string[];
  reasoningSummary: string;
  provider: string;
  model: string;
};

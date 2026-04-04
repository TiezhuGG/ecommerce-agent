export type HealthResponse = {
  status: string;
  service: string;
  environment: string;
  phase: string;
};

export type Product = {
  id: string;
  name: string;
  category: string;
  brand: string;
  price: number;
  price_note: string;
  summary: string;
  scenario: string;
  tags: string[];
  specs: string[];
  official_url: string;
};

export type FaqEntry = {
  id: string;
  topic: string;
  question: string;
  answer: string;
  sourceLabel: string;
};

export type SearchFilters = {
  keyword: string;
  category: string;
  brand: string;
  maxPrice: number | null;
};

export type AgentResult = {
  title: string;
  parsedIntent: string;
  appliedFilters: string[];
  answer: string;
  executionSteps: string[];
};

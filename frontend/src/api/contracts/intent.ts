export type IntentSearchFiltersResponse = {
  keyword: string;
  category: string;
  brand: string;
  max_price: number | null;
};


export type IntentParseResponse = {
  query: string;
  search_filters: IntentSearchFiltersResponse;
  scenario: string;
  priorities: string[];
  applied_filters: string[];
  reasoning_summary: string;
  provider: string;
  model: string;
};

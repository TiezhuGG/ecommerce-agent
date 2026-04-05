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

export type SearchFilters = {
  keyword: string;
  category: string;
  brand: string;
  maxPrice: number | null;
};

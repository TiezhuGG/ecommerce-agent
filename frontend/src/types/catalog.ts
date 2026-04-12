export type Product = {
  id: string;
  name: string;
  category: string;
  brand: string;
  price: number;
  price_note: string;
  summary: string;
  scenario: string;
  aliases: string[];
  tags: string[];
  specs: string[];
  official_url: string;
};

export type ProductInput = {
  name: string;
  category: string;
  brand: string;
  price: number;
  price_note: string;
  summary: string;
  scenario: string;
  aliases: string[];
  tags: string[];
  specs: string[];
  official_url: string;
};

export type ProductCatalogAdminResult = {
  backend: string;
  items: Product[];
};

export type ProductImportMode = "upsert" | "replace";

export type ProductImportResult = {
  mode: ProductImportMode;
  importedCount: number;
  createdCount: number;
  updatedCount: number;
  backend: string;
};

export type SearchFilters = {
  keyword: string;
  category: string;
  brand: string;
  maxPrice: number | null;
};

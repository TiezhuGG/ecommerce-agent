import type { Product } from "../../types/catalog";

export type ProductResponse = Product;

export type ProductSearchResponse = {
  items: Product[];
  total: number;
  applied_filters: string[];
  available_categories: string[];
  available_brands: string[];
};

export type ProductListResponse = {
  backend: string;
  items: Product[];
};

export type ProductImportResponse = {
  mode: string;
  imported_count: number;
  created_count: number;
  updated_count: number;
  backend: string;
};

export type ProductDeleteResponse = {
  deleted: boolean;
  product_id: string;
};

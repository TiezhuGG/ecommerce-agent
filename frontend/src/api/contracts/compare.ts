import type { Product } from "../../types/catalog";

export type CompareResponse = {
  compared_products: Product[];
  summary: string;
  cheapest_product_name: string;
  most_expensive_product_name: string;
  price_gap: number;
  highlights: string[];
};

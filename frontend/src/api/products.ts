import type { Product, SearchFilters } from "../types";

type ProductSearchResponse = {
  items: Product[];
  total: number;
  applied_filters: string[];
  available_categories: string[];
  available_brands: string[];
};

const API_BASE_URL = "http://127.0.0.1:8000";

export async function fetchProducts(filters: SearchFilters): Promise<ProductSearchResponse> {
  const params = new URLSearchParams();

  // Keep the request builder explicit so you can clearly see how frontend state
  // maps into HTTP query parameters. This is important because later the agent
  // layer will produce the same filter structure programmatically.
  if (filters.keyword.trim()) {
    params.set("keyword", filters.keyword.trim());
  }
  if (filters.category) {
    params.set("category", filters.category);
  }
  if (filters.brand) {
    params.set("brand", filters.brand);
  }
  if (filters.maxPrice !== null) {
    params.set("max_price", String(filters.maxPrice));
  }

  const query = params.toString();
  const url = query ? `${API_BASE_URL}/products?${query}` : `${API_BASE_URL}/products`;
  const response = await fetch(url);

  if (!response.ok) {
    throw new Error(`商品搜索请求失败，状态码 ${response.status}`);
  }

  return (await response.json()) as ProductSearchResponse;
}

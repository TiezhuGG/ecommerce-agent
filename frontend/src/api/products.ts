import type { ProductSearchResponse } from "./contracts/products";
import type { SearchFilters } from "../types/catalog";

const API_BASE_URL = "http://127.0.0.1:8000";

export async function fetchProducts(filters: SearchFilters): Promise<ProductSearchResponse> {
  const params = new URLSearchParams();

  // 这里保留显式拼接参数的写法，是为了让你能清楚看到：
  // 页面里的结构化筛选状态，是如何一步步映射成后端查询参数的。
  // 后续 Agent 生成结构化条件时，本质上也会走同样的参数结构。
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

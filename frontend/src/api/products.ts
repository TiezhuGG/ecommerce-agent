import type { SearchFilters } from "../types/catalog";
import { requestJson } from "./client";
import type { ProductSearchResponse } from "./contracts/products";


export async function fetchProducts(filters: SearchFilters): Promise<ProductSearchResponse> {
  const params = new URLSearchParams();

  // 这里显式拼接查询参数，是为了让你能看清楚：
  // 页面里的结构化筛选状态，最终是如何映射成后端搜索接口参数的。
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
  const path = query ? `/products?${query}` : "/products";
  return requestJson<ProductSearchResponse>(path);
}

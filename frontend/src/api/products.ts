import type { ProductCatalogAdminResult, ProductInput, SearchFilters } from "../types/catalog";
import { requestJson } from "./client";
import type {
  ProductDeleteResponse,
  ProductListResponse,
  ProductResponse,
  ProductSearchResponse,
} from "./contracts/products";


function mapProductInput(input: ProductInput) {
  return {
    name: input.name,
    category: input.category,
    brand: input.brand,
    price: input.price,
    price_note: input.price_note,
    summary: input.summary,
    scenario: input.scenario,
    tags: input.tags,
    specs: input.specs,
    official_url: input.official_url,
  };
}


export async function fetchProducts(filters: SearchFilters): Promise<ProductSearchResponse> {
  const params = new URLSearchParams();

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


export async function fetchAdminProducts(): Promise<ProductCatalogAdminResult> {
  const response = await requestJson<ProductListResponse>("/products/admin");
  return {
    backend: response.backend,
    items: response.items,
  };
}


export async function createProduct(input: ProductInput): Promise<ProductResponse> {
  return requestJson<ProductResponse>("/products/admin", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(mapProductInput(input)),
  });
}


export async function updateProduct(productId: string, input: ProductInput): Promise<ProductResponse> {
  return requestJson<ProductResponse>(`/products/admin/${productId}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(mapProductInput(input)),
  });
}


export async function deleteProduct(productId: string): Promise<ProductDeleteResponse> {
  return requestJson<ProductDeleteResponse>(`/products/admin/${productId}`, {
    method: "DELETE",
  });
}

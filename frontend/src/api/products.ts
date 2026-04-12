import { buildAdminAccessHeaders } from "../auth/adminAccess";
import type {
  Product,
  ProductCatalogAdminResult,
  ProductImportMode,
  ProductImportResult,
  ProductInput,
  SearchFilters,
} from "../types/catalog";
import { requestJson } from "./client";
import type {
  ProductDeleteResponse,
  ProductImportResponse,
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
    aliases: input.aliases,
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
  const response = await requestJson<ProductListResponse>("/products/admin", {
    headers: buildAdminAccessHeaders(),
  });
  return {
    backend: response.backend,
    items: response.items,
  };
}


export async function exportAdminProducts(): Promise<ProductCatalogAdminResult> {
  const response = await requestJson<ProductListResponse>("/products/admin/export", {
    headers: buildAdminAccessHeaders(),
  });
  return {
    backend: response.backend,
    items: response.items,
  };
}


export async function importAdminProducts(
  items: Product[],
  mode: ProductImportMode,
): Promise<ProductImportResult> {
  const response = await requestJson<ProductImportResponse>("/products/admin/import", {
    method: "POST",
    headers: buildAdminAccessHeaders({
      "Content-Type": "application/json",
    }),
    body: JSON.stringify({
      mode,
      items: items.map((item) => ({
        id: item.id,
        name: item.name,
        category: item.category,
        brand: item.brand,
        price: item.price,
        price_note: item.price_note,
        summary: item.summary,
        scenario: item.scenario,
        aliases: item.aliases,
        tags: item.tags,
        specs: item.specs,
        official_url: item.official_url,
      })),
    }),
  });

  return {
    mode: response.mode as ProductImportMode,
    importedCount: response.imported_count,
    createdCount: response.created_count,
    updatedCount: response.updated_count,
    backend: response.backend,
  };
}


export async function createProduct(input: ProductInput): Promise<ProductResponse> {
  return requestJson<ProductResponse>("/products/admin", {
    method: "POST",
    headers: buildAdminAccessHeaders({
      "Content-Type": "application/json",
    }),
    body: JSON.stringify(mapProductInput(input)),
  });
}


export async function updateProduct(productId: string, input: ProductInput): Promise<ProductResponse> {
  return requestJson<ProductResponse>(`/products/admin/${productId}`, {
    method: "PUT",
    headers: buildAdminAccessHeaders({
      "Content-Type": "application/json",
    }),
    body: JSON.stringify(mapProductInput(input)),
  });
}


export async function deleteProduct(productId: string): Promise<ProductDeleteResponse> {
  return requestJson<ProductDeleteResponse>(`/products/admin/${productId}`, {
    method: "DELETE",
    headers: buildAdminAccessHeaders(),
  });
}

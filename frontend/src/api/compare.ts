import { requestJson } from "./client";
import type { CompareResponse } from "./contracts/compare";


export async function compareProducts(productIds: string[]): Promise<CompareResponse> {
  return requestJson<CompareResponse>("/compare", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ product_ids: productIds }),
  });
}

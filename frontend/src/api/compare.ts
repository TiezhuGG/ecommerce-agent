import type { CompareResponse } from "./contracts/compare";

const API_BASE_URL = "http://127.0.0.1:8000";

export async function compareProducts(productIds: string[]): Promise<CompareResponse> {
  const response = await fetch(`${API_BASE_URL}/compare`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ product_ids: productIds }),
  });

  if (!response.ok) {
    throw new Error(`商品对比请求失败，状态码 ${response.status}`);
  }

  return (await response.json()) as CompareResponse;
}

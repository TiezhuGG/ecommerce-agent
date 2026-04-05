import type { FaqAskResponse } from "./contracts/faq";

const API_BASE_URL = "http://127.0.0.1:8000";

export async function askFaq(question: string): Promise<FaqAskResponse> {
  const response = await fetch(`${API_BASE_URL}/faq/ask`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ question }),
  });

  if (!response.ok) {
    throw new Error(`FAQ 请求失败，状态码 ${response.status}`);
  }

  return (await response.json()) as FaqAskResponse;
}

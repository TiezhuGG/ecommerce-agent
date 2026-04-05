import { requestJson } from "./client";
import type { FaqAskResponse } from "./contracts/faq";


export async function askFaq(question: string): Promise<FaqAskResponse> {
  return requestJson<FaqAskResponse>("/faq/ask", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ question }),
  });
}

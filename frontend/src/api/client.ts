export const API_BASE_URL = "http://127.0.0.1:8000";


function buildErrorMessage(status: number, detail: string) {
  return detail ? `${detail}（状态码 ${status}）` : `请求失败，状态码 ${status}`;
}


export async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, init);

  if (!response.ok) {
    let detail = "";

    try {
      const data = (await response.json()) as { detail?: string };
      detail = data.detail ?? "";
    } catch {
      detail = "";
    }

    throw new Error(buildErrorMessage(response.status, detail));
  }

  return (await response.json()) as T;
}

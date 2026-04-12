const ADMIN_ACCESS_STORAGE_KEY = "ecommerce-agent.admin-access-code";
export const ADMIN_ACCESS_HEADER = "X-Admin-Access-Code";

export function getAdminAccessCode(): string {
  if (typeof window === "undefined") {
    return "";
  }

  return window.sessionStorage.getItem(ADMIN_ACCESS_STORAGE_KEY)?.trim() ?? "";
}

export function setAdminAccessCode(code: string) {
  if (typeof window === "undefined") {
    return;
  }

  const normalized = code.trim();
  if (normalized) {
    window.sessionStorage.setItem(ADMIN_ACCESS_STORAGE_KEY, normalized);
    return;
  }

  window.sessionStorage.removeItem(ADMIN_ACCESS_STORAGE_KEY);
}

export function clearAdminAccessCode() {
  if (typeof window === "undefined") {
    return;
  }

  window.sessionStorage.removeItem(ADMIN_ACCESS_STORAGE_KEY);
}

export function buildAdminAccessHeaders(headers?: HeadersInit): Headers {
  const merged = new Headers(headers);
  const code = getAdminAccessCode();

  if (code) {
    merged.set(ADMIN_ACCESS_HEADER, code);
  }

  return merged;
}

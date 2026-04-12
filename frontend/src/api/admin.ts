import { requestJson } from "./client";
import { buildAdminAccessHeaders } from "../auth/adminAccess";

type AdminAccessStatusResponse = {
  enabled: boolean;
};

type AdminAccessVerifyResponse = {
  enabled: boolean;
  verified: boolean;
};

type DatabaseSmokeResponse = {
  configured_backend: string;
  runtime_backend: string;
  runtime_status: string;
  persistence_enabled: boolean;
  runtime_message: string;
  product_total: number;
  faq_total: number;
  created_product_id: string;
  created_faq_entry_id: string;
  persisted_run_id: string;
};

export async function fetchAdminAccessStatus(): Promise<boolean> {
  const response = await requestJson<AdminAccessStatusResponse>("/admin/access/status");
  return response.enabled;
}

export async function verifyAdminAccess(): Promise<boolean> {
  const response = await requestJson<AdminAccessVerifyResponse>("/admin/access/verify", {
    method: "POST",
    headers: buildAdminAccessHeaders(),
  });
  return response.enabled ? response.verified : true;
}

export async function runDatabaseSmokeCheck(expectBackend?: string) {
  const suffix = expectBackend ? `?expect_backend=${encodeURIComponent(expectBackend)}` : "";
  const response = await requestJson<DatabaseSmokeResponse>(`/admin/database/smoke-check${suffix}`, {
    method: "POST",
    headers: buildAdminAccessHeaders(),
  });

  return {
    configuredBackend: response.configured_backend,
    runtimeBackend: response.runtime_backend,
    runtimeStatus: response.runtime_status,
    persistenceEnabled: response.persistence_enabled,
    runtimeMessage: response.runtime_message,
    productTotal: response.product_total,
    faqTotal: response.faq_total,
    createdProductId: response.created_product_id,
    createdFaqEntryId: response.created_faq_entry_id,
    persistedRunId: response.persisted_run_id,
  };
}

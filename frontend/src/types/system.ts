export type HealthResponse = {
  status: string;
  service: string;
  environment: string;
  phase: string;
  data_backend?: string;
  database_configured_backend?: string;
  database_runtime_status?: string;
  database_runtime_message?: string;
  database_persistence_enabled?: boolean;
};

export type DatabaseSmokeReport = {
  configuredBackend: string;
  runtimeBackend: string;
  runtimeStatus: string;
  persistenceEnabled: boolean;
  runtimeMessage: string;
  productTotal: number;
  faqTotal: number;
  createdProductId: string;
  createdFaqEntryId: string;
  persistedRunId: string;
};

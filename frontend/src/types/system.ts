export type HealthResponse = {
  status: string;
  service: string;
  environment: string;
  phase: string;
  data_backend?: string;
};

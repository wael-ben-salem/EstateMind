import { apiGet, apiPost } from '@/shared/api/http';

export type ScrapedStats = {
  totalProperties: number;
  uniqueLocations: number;
  propertyTypes: number;
  avgPrice: number;
};

export type LocationDistributionRow = { location: string; count: number };
export type PropertyTypeRow = { name: string; value: number };
export type TransactionTypeRow = { name: string; value: number };
export type PriceRangeRow = { range: string; count: number };
export type AvgPriceCityRow = { city: string; avgPrice: number };

export type DagTriggerResponse = {
  dag_run_id: string;
  dag_id: string;
  logical_date?: string;
  state?: string;
};

export type PipelineStep = {
  task_id: string;
  state: string | null;
  start_date: string | null;
  end_date: string | null;
  duration: number | null;
};

export type PipelineStatus = {
  state: string;
  run_id: string;
  steps: PipelineStep[];
};

export const estateMindApi = {
  health: () => apiGet<{ status: string }>('/health'),
  healthAirflow: () => apiGet<unknown>('/health/airflow'),

  stats: () => apiGet<ScrapedStats>('/scraped-data/stats'),
  locations: () => apiGet<LocationDistributionRow[]>('/scraped-data/locations'),
  propertyTypes: () => apiGet<PropertyTypeRow[]>('/scraped-data/property-types'),
  transactions: () => apiGet<TransactionTypeRow[]>('/scraped-data/transactions'),
  prices: () => apiGet<PriceRangeRow[]>('/scraped-data/prices'),
  avgPriceByCity: () => apiGet<AvgPriceCityRow[]>('/scraped-data/avg-price-city'),

  triggerPipeline: () => apiPost<DagTriggerResponse>('/etl/trigger', { conf: {} }),
  pipelineStatus: (runId: string) => apiGet<PipelineStatus>(`/etl/runs/${runId}/status`)
};


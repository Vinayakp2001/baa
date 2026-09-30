/**
 * Typed API client for the BAA pipeline backend.
 * All requests go through the Next.js rewrite proxy at /api.
 */

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost/api";

async function get<T>(path: string, params?: Record<string, string | number | boolean | undefined>): Promise<T> {
  const url = new URL(`${BASE}${path}`);
  if (params) {
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null) url.searchParams.set(k, String(v));
    });
  }
  const res = await fetch(url.toString(), { next: { revalidate: 60 } });
  if (!res.ok) throw new Error(`API ${res.status}: ${path}`);
  return res.json() as Promise<T>;
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`API ${res.status}: ${path}`);
  return res.json() as Promise<T>;
}

// ---- Types -----------------------------------------------------------------

export interface BusinessSummary {
  entity_id: string;
  canonical_name: string;
  legal_name: string | null;
  trade_name: string | null;
  entity_type: string | null;
  province: string | null;
  status: string | null;
  sales_ready: boolean;
  lead_quality_score: number | null;
  first_seen_at: string;
  last_verified_at: string | null;
}

export interface PaginatedBusinesses {
  total: number;
  page: number;
  page_size: number;
  next_cursor: number | null;
  results: BusinessSummary[];
}

export interface ContactOut {
  contact_id: string;
  contact_type: string;
  raw_value: string;
  normalised_value: string | null;
  is_valid: boolean | null;
  enrichment_source: string | null;
  confidence: string | null;
}

export interface LocationOut {
  location_id: string;
  address_line1: string | null;
  city: string | null;
  province: string | null;
  postal_code: string | null;
  country: string;
  latitude: number | null;
  longitude: number | null;
  is_primary: boolean;
}

export interface PersonOut {
  person_id: string;
  person_name: string;
  role_type: string | null;
  role_label_raw: string | null;
  confidence: string | null;
  source_url: string | null;
}

export interface EmployeeOut {
  employee_id: string;
  raw_employee_value: string;
  employee_min: number | null;
  employee_max: number | null;
  employee_bucket: string | null;
  employee_exact: boolean;
  data_quality_flag: string | null;
}

export interface IndustryOut {
  industry_id: string;
  source_naics: string | null;
  naics_sector: string | null;
  source_industry_str: string | null;
}

export interface QualityScoreOut {
  identity_confidence: number | null;
  address_confidence: number | null;
  phone_confidence: number | null;
  email_confidence: number | null;
  employee_confidence: number | null;
  industry_confidence: number | null;
  contact_confidence: number | null;
  recency_confidence: number | null;
  source_reliability: number | null;
  lead_quality_score: number | null;
  scored_at: string | null;
}

export interface BusinessDetail extends BusinessSummary {
  locations: LocationOut[];
  identifiers: { id_type: string; id_value: string }[];
  contacts: ContactOut[];
  persons: PersonOut[];
  employee_data: EmployeeOut[];
  industries: IndustryOut[];
  quality_score: QualityScoreOut | null;
}

export interface EventOut {
  event_id: string;
  event_type: string;
  event_date: string | null;
  raw_value: string | null;
  previous_value: string | null;
  created_at: string;
}

export interface PaginatedEvents {
  total: number;
  page: number;
  page_size: number;
  next_cursor: number | null;
  results: EventOut[];
}

export interface SourceStatusOut {
  source_id: string;
  source_key: string;
  source_name: string;
  province: string | null;
  source_type: string;
  source_class: string;
  is_enabled: boolean;
  schedule_cron: string | null;
  last_run_status: string | null;
  last_run_at: string | null;
  last_run_record_count: number | null;
}

export interface ProvinceStats {
  province: string;
  total_businesses: number;
  sales_ready: number;
  has_coverage_gap: boolean;
}

export interface PipelineStats {
  total_businesses: number;
  sales_ready_count: number;
  new_last_30_days: number;
  province_coverage_gaps: string[];
  by_province: ProvinceStats[];
  by_source: Record<string, number>;
  field_fill_rates: Record<string, number>;
}

export interface FieldObservationOut {
  observation_id: string;
  field_name: string;
  raw_value: string | null;
  normalised_value: string | null;
  source_id: string;
  observed_at: string;
  confidence: string | null;
  is_current: boolean;
}

export interface BusinessHistoryResponse {
  entity_id: string;
  fields: { field_name: string; observations: FieldObservationOut[] }[];
}

// ---- API calls -------------------------------------------------------------

export type BusinessFilters = {
  province?: string;
  city?: string;
  naics_sector?: string;
  employee_bucket?: string;
  status?: string;
  sales_ready?: boolean;
  has_phone?: boolean;
  has_email?: boolean;
  has_website?: boolean;
  has_director?: boolean;
  new_since?: string;
  event_type?: string;
  dnc?: boolean;
  page?: number;
  page_size?: number;
};

export const api = {
  businesses: {
    list: (filters: BusinessFilters = {}) =>
      get<PaginatedBusinesses>("/businesses", filters as Record<string, string | number | boolean | undefined>),
    get: (id: string) => get<BusinessDetail>(`/businesses/${id}`),
    history: (id: string) => get<BusinessHistoryResponse>(`/businesses/${id}/history`),
    sources: (id: string) => get<unknown[]>(`/businesses/${id}/sources`),
    setFlag: (id: string, flag_type: string, notes?: string) =>
      post<unknown>(`/businesses/${id}/flags`, { flag_type, notes }),
    removeFlag: async (id: string, flag_type: string) => {
      const res = await fetch(`${BASE}/businesses/${id}/flags/${flag_type}`, {
        method: "DELETE",
        cache: "no-store",
      });
      if (!res.ok) throw new Error(`API ${res.status}`);
    },
  },
  events: {
    list: (params: Record<string, string | number | undefined> = {}) =>
      get<PaginatedEvents>("/events", params),
  },
  sources: {
    list: () => get<SourceStatusOut[]>("/sources"),
  },
  stats: {
    get: () => get<PipelineStats>("/stats"),
  },
  export: {
    url: (params: Record<string, string | boolean | undefined>) => {
      const url = new URL(`${BASE}/export`);
      Object.entries(params).forEach(([k, v]) => {
        if (v !== undefined) url.searchParams.set(k, String(v));
      });
      return url.toString();
    },
  },
};

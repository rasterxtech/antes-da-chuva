/** Browser-facing contract emitted by scripts/export_frontend_data.py. */

export const PRESENTATION_SCHEMA_VERSION = 'v1' as const;

export type PresentationState =
  | 'record'
  | 'no_record'
  | 'no_coverage'
  | 'not_published'
  | 'not_in_legacy_universe';

export type MunicipalityIdentity = {
  codigo_ibge: string;
  municipio: string;
  municipio_normalized: string;
  uf: string;
  regiao: string;
  regiao_imediata: string;
  codigo_regiao_imediata: string;
  tipo_unidade_territorial: string;
};

export type MunicipalIndexEntry = MunicipalityIdentity & {
  shard: string;
};

export type MunicipalIndex = {
  schema_version: typeof PRESENTATION_SCHEMA_VERSION;
  territorial_universe: string;
  municipalities: MunicipalIndexEntry[];
};

export type PresentationMetadata = {
  schema_version: typeof PRESENTATION_SCHEMA_VERSION;
  territorial_universe: {
    id: string;
    municipality_count: number;
    reference: string;
  };
  sources: {
    ibge: {
      source: string;
      query_date: string;
      status: string;
    };
    atlas: {
      release: string;
      official_date: string | null;
      first_year: number;
      latest_year: number;
      materialized_at: string;
      source_sha256: string;
      manifest: string;
      catalog: Array<{ atlas_type_id: number; name: string; cobrade_codes: string[] }>;
    };
    mapbiomas: {
      collection_id: string;
      collection_version: string;
      first_year: number;
      latest_year: number;
      materialized_at: string;
      source_sha256: string;
      manifest: string;
    };
    census: {
      state: string;
      reference: string;
    };
    transferegov: {
      state: string;
      reference: string;
    };
  };
};

export type DisasterHistory = {
  state: Extract<PresentationState, 'record' | 'no_record'>;
  record_scope: string;
  all_event_count: number;
  rain_related_event_count: number;
  recognized_event_count: number;
  first_event_date: string | null;
  latest_event_date: string | null;
  human_impacts: {
    deaths: number;
    injured: number;
    homeless: number;
    displaced: number;
    missing: number;
    reported_affected_total: number;
  };
  annual: {
    first_year: number | null;
    latest_year: number | null;
    benchmark: { immediate_region: { codigo: string; nome: string; municipality_count: number; zeros_policy: 'included_as_zero' } };
    series: Array<{ atlas_type_id: number | null; points: Array<{ year: number; municipal_event_count: number; immediate_region_average_event_count: number }> }>;
  };
};

export type DisasterType = {
  codigo_ibge: string;
  cobrade_codes: string[];
  type_name: string;
  first_event_date: string | null;
  latest_event_date: string | null;
  event_count: number;
  deaths: number;
  injured: number;
  homeless: number;
  displaced: number;
  missing: number;
  recognized_event_count: number;
  reported_affected_total: number | null;
  atlas_type_id: number;
  event_pct: number;
};

export type LandCover = {
  state: Extract<PresentationState, 'record' | 'no_coverage'>;
  history: Array<{
    year: number;
    mapped_area_ha: number;
    urban_area_ha: number;
    urban_area_pct: number;
    native_vegetation_area_ha: number;
    native_vegetation_area_pct: number;
    agriculture_livestock_area_ha: number;
    agriculture_livestock_area_pct: number;
    water_area_ha: number;
    water_area_pct: number;
    wetland_area_ha: number;
    wetland_area_pct: number;
  }>;
  change: Record<string, number | null> | null;
};

export type TransitionalCensus = {
  state: Extract<
    PresentationState,
    'record' | 'not_published' | 'not_in_legacy_universe'
  >;
  provenance: 'transitional_legacy';
  year: number | null;
  connected_sewer_pct: number | null;
  outside_selected_sewer_pct: number | null;
};

export type TransitionalTransfers = {
  state: Extract<
    PresentationState,
    'record' | 'no_record' | 'not_in_legacy_universe'
  >;
  provenance: 'transitional_legacy';
  legacy: {
    agreements: number;
    firstYear: number;
    lastYear: number;
    actions: string[];
    attribution: string;
    latest: {
      number: string;
      year: number;
      status: string;
      object: string;
      globalValue: number | null;
    };
  } | null;
};

export type MunicipalityPresentation = {
  schema_version: typeof PRESENTATION_SCHEMA_VERSION;
  municipality: MunicipalityIdentity;
  summary: {
    territorial_universe: 'ibge_current_5571';
    thirty_second_text: string;
    source_states: Record<string, PresentationState>;
  };
  disasters: {
    state: Extract<PresentationState, 'record' | 'no_record'>;
    history: DisasterHistory;
    types: DisasterType[];
    months: Array<{
      month: number;
      event_count: number;
      rain_related_event_count: number;
      event_pct: number | null;
    }>;
    highlights: Array<Record<string, never>>;
  };
  land_cover: LandCover;
  census: TransitionalCensus;
  transfers: TransitionalTransfers;
  benchmarks: {
    immediate_region: {
      codigo: string;
      nome: string;
      municipality_count: number;
      includes_selected_municipality: true;
      metrics: Record<'rain_related_event_count_10y' | 'urban_change_20y_pct' | 'native_vegetation_change_20y_pct' | 'urban_area_pct' | 'native_vegetation_area_pct', {
        source: string; unit: string; reference: Record<string, number | string | null>;
        municipality_value: number | null; mean: number | null; median: number | null;
        percentile_strictly_lower_pct: number | null;
        denominator: { included: number; missing: number; undefined: number };
      }>;
    };
  };
  sources: string[];
};

export type MunicipalShard = {
  schema_version: typeof PRESENTATION_SCHEMA_VERSION;
  uf: string;
  municipalities: Record<string, MunicipalityPresentation>;
};

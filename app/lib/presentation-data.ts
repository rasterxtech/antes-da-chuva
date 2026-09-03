import {
  PRESENTATION_SCHEMA_VERSION,
  type MunicipalIndex,
  type MunicipalIndexEntry,
  type MunicipalShard,
  type MunicipalityIdentity,
  type MunicipalityPresentation,
  type PresentationMetadata,
  type PresentationState,
} from '@/lib/presentation-contract';

const IBGE_CODE = /^\d{7}$/;
const MUNICIPAL_SHARD_PATH = /^\/data\/v1\/uf\/([A-Z]{2})(?:-\d{3})?\.json$/;

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null;
}

function isMunicipalityIdentity(
  value: unknown,
): value is MunicipalityIdentity & Record<string, unknown> {
  if (!isObject(value)) return false;

  return (
    typeof value.codigo_ibge === 'string' &&
    IBGE_CODE.test(value.codigo_ibge) &&
    typeof value.municipio === 'string' &&
    typeof value.municipio_normalized === 'string' &&
    typeof value.uf === 'string' &&
    typeof value.regiao === 'string' &&
    typeof value.regiao_imediata === 'string' &&
    typeof value.codigo_regiao_imediata === 'string' &&
    typeof value.tipo_unidade_territorial === 'string'
  );
}

function isMunicipalIndexEntry(value: unknown): value is MunicipalIndexEntry {
  const shardMatch = isObject(value) && typeof value.shard === 'string'
    ? MUNICIPAL_SHARD_PATH.exec(value.shard)
    : null;
  return (
    isMunicipalityIdentity(value) &&
    isObject(value) &&
    shardMatch !== null &&
    value.uf === shardMatch[1]
  );
}

export function isCodigoIbge(value: string | null): value is string {
  return value !== null && IBGE_CODE.test(value);
}

export function requestedCodigoIbge(search: string): {
  code: string | null;
  hasInvalidCode: boolean;
} {
  const parameters = new URLSearchParams(search);
  const canonical = parameters.get('codigo_ibge');

  if (canonical !== null) {
    return {
      code: isCodigoIbge(canonical) ? canonical : null,
      hasInvalidCode: !isCodigoIbge(canonical),
    };
  }

  const legacy = parameters.get('municipio');
  return {
    code: isCodigoIbge(legacy) ? legacy : null,
    hasInvalidCode: legacy !== null && !isCodigoIbge(legacy),
  };
}

export function isMunicipalIndex(value: unknown): value is MunicipalIndex {
  if (
    !isObject(value) ||
    value.schema_version !== PRESENTATION_SCHEMA_VERSION ||
    typeof value.territorial_universe !== 'string' ||
    !Array.isArray(value.municipalities)
  ) {
    return false;
  }

  const codes = new Set<string>();
  return value.municipalities.every((municipality) => {
    if (
      !isMunicipalIndexEntry(municipality) ||
      codes.has(municipality.codigo_ibge)
    ) {
      return false;
    }
    codes.add(municipality.codigo_ibge);
    return true;
  });
}

export function isPresentationMetadata(
  value: unknown,
): value is PresentationMetadata {
  if (!isObject(value) || value.schema_version !== PRESENTATION_SCHEMA_VERSION) {
    return false;
  }

  const universe = value.territorial_universe;
  const sources = value.sources;
  if (!isObject(universe) || !isObject(sources)) return false;

  const atlas = sources.atlas;
  const mapbiomas = sources.mapbiomas;
  const ibge = sources.ibge;
  const census = sources.census;
  const transfers = sources.transferegov;
  return (
    typeof universe.id === 'string' &&
    typeof universe.municipality_count === 'number' &&
    typeof universe.reference === 'string' &&
    isObject(atlas) &&
    typeof atlas.release === 'string' &&
    (typeof atlas.official_date === 'string' || atlas.official_date === null) &&
    typeof atlas.first_year === 'number' &&
    typeof atlas.latest_year === 'number' &&
    typeof atlas.materialized_at === 'string' &&
    typeof atlas.source_sha256 === 'string' &&
    typeof atlas.manifest === 'string' &&
    Array.isArray(atlas.catalog) &&
    isObject(mapbiomas) &&
    typeof mapbiomas.collection_id === 'string' &&
    typeof mapbiomas.collection_version === 'string' &&
    typeof mapbiomas.first_year === 'number' &&
    typeof mapbiomas.latest_year === 'number' &&
    typeof mapbiomas.materialized_at === 'string' &&
    typeof mapbiomas.source_sha256 === 'string' &&
    typeof mapbiomas.manifest === 'string' &&
    isObject(ibge) &&
    typeof ibge.source === 'string' &&
    typeof ibge.query_date === 'string' &&
    typeof ibge.status === 'string' &&
    isObject(census) &&
    typeof census.state === 'string' &&
    typeof census.reference === 'string' &&
    isObject(transfers) &&
    typeof transfers.state === 'string' &&
    typeof transfers.reference === 'string'
  );
}

function isPresentationState(value: unknown): value is PresentationState {
  return (
    value === 'record' ||
    value === 'no_record' ||
    value === 'no_coverage' ||
    value === 'not_published' ||
    value === 'not_in_legacy_universe'
  );
}

function isNumberOrNull(value: unknown): value is number | null {
  return typeof value === 'number' || value === null;
}

function isDisasterHistory(value: unknown): boolean {
  if (!isObject(value)) return false;
  const impacts = value.human_impacts;
  return (
    (value.state === 'record' || value.state === 'no_record') &&
    typeof value.record_scope === 'string' &&
    typeof value.all_event_count === 'number' &&
    typeof value.rain_related_event_count === 'number' &&
    typeof value.recognized_event_count === 'number' &&
    (typeof value.first_event_date === 'string' || value.first_event_date === null) &&
    (typeof value.latest_event_date === 'string' || value.latest_event_date === null) &&
    isObject(impacts) &&
    typeof impacts.deaths === 'number' &&
    typeof impacts.injured === 'number' &&
    typeof impacts.homeless === 'number' &&
    typeof impacts.displaced === 'number' &&
    typeof impacts.missing === 'number'
    && typeof impacts.reported_affected_total === 'number'
    && isAnnualHistory(value.annual)
  );
}

const ATLAS_TYPE_IDS = [1, 2, 7, 8, 13] as const;

function isAnnualHistory(value: unknown): boolean {
  if (!isObject(value) || !isObject(value.benchmark) || !Array.isArray(value.series)) return false;
  const immediate = isObject(value.benchmark.immediate_region)
    ? value.benchmark.immediate_region
    : null;
  const firstYear = value.first_year;
  const latestYear = value.latest_year;
  const municipalityCount = immediate?.municipality_count;
  if (
    !immediate ||
    typeof immediate.codigo !== 'string' ||
    typeof immediate.nome !== 'string' ||
    !Number.isInteger(municipalityCount) ||
    typeof municipalityCount !== 'number' ||
    municipalityCount < 1 ||
    immediate.zeros_policy !== 'included_as_zero' ||
    !Number.isInteger(firstYear) ||
    !Number.isInteger(latestYear) ||
    typeof firstYear !== 'number' ||
    typeof latestYear !== 'number' ||
    firstYear > latestYear
  ) return false;
  const expectedYears = Array.from({ length: latestYear - firstYear + 1 }, (_, index) => firstYear + index);
  const ids = value.series.map((series) => isObject(series) ? series.atlas_type_id : undefined);
  if (new Set(ids).size !== 6 || ![null, ...ATLAS_TYPE_IDS].every((id) => ids.includes(id))) return false;
  return value.series.every((series) => isObject(series) && Array.isArray(series.points) && series.points.every((point, index) => isObject(point) && point.year === expectedYears[index] && typeof point.municipal_event_count === 'number' && typeof point.immediate_region_average_event_count === 'number'));
}

function isDisasterType(value: unknown): boolean {
  if (!isObject(value)) return false;
  return (
    isCodigoIbge(typeof value.codigo_ibge === 'string' ? value.codigo_ibge : null) &&
    Array.isArray(value.cobrade_codes) && value.cobrade_codes.every((code) => typeof code === 'string') &&
    typeof value.type_name === 'string' &&
    (typeof value.first_event_date === 'string' || value.first_event_date === null) &&
    (typeof value.latest_event_date === 'string' || value.latest_event_date === null) &&
    typeof value.event_count === 'number' &&
    typeof value.deaths === 'number' &&
    typeof value.injured === 'number' &&
    typeof value.homeless === 'number' &&
    typeof value.displaced === 'number' &&
    typeof value.missing === 'number' &&
    typeof value.recognized_event_count === 'number' &&
    isNumberOrNull(value.reported_affected_total)
    && typeof value.atlas_type_id === 'number'
    && typeof value.event_pct === 'number' && value.event_pct >= 0 && value.event_pct <= 100
  );
}

function isTransferRecord(value: unknown): boolean {
  if (value === null) return true;
  if (!isObject(value)) return false;
  const latest = value.latest;
  return (
    typeof value.agreements === 'number' &&
    typeof value.firstYear === 'number' &&
    typeof value.lastYear === 'number' &&
    Array.isArray(value.actions) &&
    value.actions.every((action) => typeof action === 'string') &&
    typeof value.attribution === 'string' &&
    isObject(latest) &&
    typeof latest.number === 'string' &&
    typeof latest.year === 'number' &&
    typeof latest.status === 'string' &&
    typeof latest.object === 'string' &&
    isNumberOrNull(latest.globalValue)
  );
}

function isMunicipalityPresentation(
  value: unknown,
): value is MunicipalityPresentation {
  if (!isObject(value) || value.schema_version !== PRESENTATION_SCHEMA_VERSION) {
    return false;
  }

  const municipality = value.municipality;
  const summary = value.summary;
  const disasters = value.disasters;
  const landCover = value.land_cover;
  const census = value.census;
  const transfers = value.transfers;
  return (
    isMunicipalityIdentity(municipality) &&
    isObject(summary) &&
    summary.territorial_universe === 'ibge_current_5571' &&
    typeof summary.thirty_second_text === 'string' &&
    isObject(summary.source_states) &&
    Object.values(summary.source_states).every(isPresentationState) &&
    isObject(disasters) &&
    (disasters.state === 'record' || disasters.state === 'no_record') &&
    isDisasterHistory(disasters.history) &&
    Array.isArray(disasters.types) &&
    (() => {
      const types = disasters.types;
      return types.length === 5 &&
        new Set(types.map((type) => isObject(type) ? type.atlas_type_id : null)).size === 5 &&
        ATLAS_TYPE_IDS.every((id) => types.some((type) => isObject(type) && type.atlas_type_id === id)) &&
        types.every(isDisasterType);
    })() &&
    Array.isArray(disasters.months) && disasters.months.length === 12 &&
    disasters.months.every((month, index) => isObject(month) && month.month === index + 1 && typeof month.event_count === 'number' && typeof month.rain_related_event_count === 'number' && isNumberOrNull(month.event_pct) && (month.event_pct === null || (month.event_pct >= 0 && month.event_pct <= 100))) &&
    isObject(landCover) &&
    (landCover.state === 'record' || landCover.state === 'no_coverage') &&
    Array.isArray(landCover.history) &&
    (landCover.change === null || isObject(landCover.change)) &&
    isObject(census) &&
    isPresentationState(census.state) &&
    census.provenance === 'transitional_legacy' &&
    isNumberOrNull(census.year) &&
    isNumberOrNull(census.connected_sewer_pct) &&
    isNumberOrNull(census.outside_selected_sewer_pct) &&
    isObject(transfers) &&
    isPresentationState(transfers.state) &&
    transfers.provenance === 'transitional_legacy' &&
    isTransferRecord(transfers.legacy) && isBenchmarks(value.benchmarks)
  );
}

function isBenchmarks(value: unknown): boolean {
  if (!isObject(value) || !isObject(value.immediate_region)) return false;
  const region = value.immediate_region;
  const municipalityCount = region.municipality_count;
  const metrics = region.metrics;
  const names = ['rain_related_event_count_10y', 'urban_change_20y_pct', 'native_vegetation_change_20y_pct', 'urban_area_pct', 'native_vegetation_area_pct'];
  if (typeof region.codigo !== 'string' || typeof region.nome !== 'string' || !Number.isInteger(municipalityCount) || typeof municipalityCount !== 'number' || municipalityCount < 1 || region.includes_selected_municipality !== true || !isObject(metrics) || Object.keys(metrics).length !== names.length || !names.every((name) => name in metrics)) return false;
  return names.every((name) => {
    const metric = metrics[name];
    if (!isObject(metric) || typeof metric.source !== 'string' || typeof metric.unit !== 'string' || !isObject(metric.reference) || !isNumberOrNull(metric.municipality_value) || !isNumberOrNull(metric.mean) || !isNumberOrNull(metric.median) || !isNumberOrNull(metric.percentile_strictly_lower_pct) || !isObject(metric.denominator)) return false;
    const denominator = metric.denominator;
    const included = denominator.included;
    const missing = denominator.missing;
    const undefinedCount = denominator.undefined;
    if (![included, missing, undefinedCount].every((count) => Number.isInteger(count) && typeof count === 'number' && count >= 0)) return false;
    return typeof included === 'number' && typeof missing === 'number' && typeof undefinedCount === 'number' && included + missing + undefinedCount === municipalityCount;
  });
}

export function isMunicipalShard(value: unknown): value is MunicipalShard {
  if (
    !isObject(value) ||
    value.schema_version !== PRESENTATION_SCHEMA_VERSION ||
    typeof value.uf !== 'string' ||
    !isObject(value.municipalities)
  ) {
    return false;
  }

  return Object.entries(value.municipalities).every(([code, payload]) => {
    return (
      isCodigoIbge(code) &&
      isMunicipalityPresentation(payload) &&
      payload.municipality.codigo_ibge === code &&
      payload.municipality.uf === value.uf
    );
  });
}

export async function fetchJson(url: string, signal?: AbortSignal): Promise<unknown> {
  const response = await fetch(url, { signal });
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }
  return response.json() as Promise<unknown>;
}

export function inactiveTransferStatus(status: string): boolean {
  const normalized = status
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLocaleLowerCase('pt-BR');
  return normalized.includes('cancel') || normalized.includes('anulad');
}

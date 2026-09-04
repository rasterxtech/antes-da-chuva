import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { afterEach, beforeAll, describe, expect, it, vi } from 'vitest';
import Home from '@/app/page';
import { inactiveTransferStatus, isMunicipalIndex } from '@/lib/presentation-data';
import type {
  MunicipalIndex,
  MunicipalityPresentation,
  PresentationMetadata,
} from '@/lib/presentation-contract';

const metadata: PresentationMetadata = {
  schema_version: 'v1',
  territorial_universe: {
    id: 'ibge_current_5571',
    municipality_count: 5571,
    reference: 'IBGE API de Localidades v1',
  },
  sources: {
    ibge: {
      source: 'IBGE API de Localidades v1',
      query_date: '2026-09-02',
      status: 'PASS',
    },
    atlas: {
      release: 'atlas_fixture',
      official_date: '2026-08-06',
      first_year: 1991,
      latest_year: 2025,
      materialized_at: '2026-09-02T21:06:38+00:00',
      source_sha256: 'fixture',
      manifest: 'fixture',
      catalog: [{ atlas_type_id: 1, name: 'Inundações', cobrade_codes: ['12100'] }],
    },
    mapbiomas: {
      collection_id: '11',
      collection_version: 'v1',
      first_year: 1985,
      latest_year: 2025,
      materialized_at: '2026-09-02T21:05:56+00:00',
      source_sha256: 'fixture',
      manifest: 'fixture',
    },
    munic: {
      reference_year: 2020,
      materialized_at: '2026-09-03T22:00:00+00:00',
      source_sha256: 'fixture',
      manifest: 'fixture',
      state: 'self_reported',
    },
    census: {
      state: 'transitional_legacy',
      reference: 'Censo fixture',
    },
    transferegov: {
      state: 'transitional_legacy',
      reference: 'Transferegov fixture',
    },
  },
};

const index: MunicipalIndex = {
  schema_version: 'v1',
  territorial_universe: 'ibge_current_5571',
  municipalities: [
    {
      codigo_ibge: '1200013',
      municipio: 'Acrelândia',
      municipio_normalized: 'acrelandia',
      uf: 'AC',
      regiao: 'Norte',
      regiao_imediata: 'Rio Branco',
      codigo_regiao_imediata: '120001',
      tipo_unidade_territorial: 'municipio',
      shard: '/data/v1/uf/AC.json',
    },
    {
      codigo_ibge: '4202404',
      municipio: 'Blumenau',
      municipio_normalized: 'blumenau',
      uf: 'SC',
      regiao: 'Sul',
      regiao_imediata: 'Blumenau',
      codigo_regiao_imediata: '420001',
      tipo_unidade_territorial: 'municipio',
      shard: '/data/v1/uf/SC-001.json',
    },
    {
      codigo_ibge: '2605459',
      municipio: 'Fernando de Noronha',
      municipio_normalized: 'fernando de noronha',
      uf: 'PE',
      regiao: 'Nordeste',
      regiao_imediata: 'Recife',
      codigo_regiao_imediata: '260001',
      tipo_unidade_territorial: 'distrito_estadual',
      shard: '/data/v1/uf/PE.json',
    },
  ],
};

function municipality(
  code: string,
  state: MunicipalityPresentation['disasters']['state'],
  landCoverState: MunicipalityPresentation['land_cover']['state'] = 'record',
): MunicipalityPresentation {
  const selected = index.municipalities.find(
    (item) => item.codigo_ibge === code,
  );
  if (!selected) throw new Error('Fixture municipal ausente.');
  const atlasTypes = [1, 2, 7, 8, 13];
  const years = Array.from({ length: 24 }, (_, index) => 2001 + index);
  const annualSeries = [null, ...atlasTypes].map((atlas_type_id) => ({
    atlas_type_id,
    points: years.map((year) => {
      const isRecordedYear = state === 'record' && (year === 2001 || year === 2024);
      const count = isRecordedYear && (atlas_type_id === null || atlas_type_id === 1) ? 1 : 0;
      return { year, municipal_event_count: count, immediate_region_average_event_count: count };
    }),
  }));
  const disasterTypes = atlasTypes.map((atlas_type_id) => ({
    codigo_ibge: code,
    cobrade_codes: atlas_type_id === 1 ? ['12100'] : [],
    type_name: `Tipo ${atlas_type_id}`,
    first_event_date: atlas_type_id === 1 && state === 'record' ? '2001-01-01' : null,
    latest_event_date: atlas_type_id === 1 && state === 'record' ? '2024-05-01' : null,
    event_count: atlas_type_id === 1 && state === 'record' ? 2 : 0,
    deaths: 0, injured: 0, homeless: 0, displaced: 0, missing: 0,
    recognized_event_count: 0, reported_affected_total: 0,
    atlas_type_id, event_pct: atlas_type_id === 1 && state === 'record' ? 100 : 0,
  }));

  return {
    schema_version: 'v1',
    municipality: selected,
    summary: {
      territorial_universe: 'ibge_current_5571',
      thirty_second_text:
        state === 'no_record'
          ? 'Nenhum registro foi encontrado nesta release do Atlas/S2ID.'
          : 'Desde 2001, foram encontrados 2 registros relacionados à chuva.',
      source_states: {
        ibge: 'record',
        atlas: state,
        mapbiomas: landCoverState,
        munic: code === '5101837' ? 'not_in_source' : 'record',
        census: state === 'no_record' ? 'not_published' : 'record',
        transferegov: 'record',
      },
    },
    disasters: {
      state,
      history: {
        state,
        record_scope: 'five_rain_related_cobrade_typologies',
        all_event_count: state === 'record' ? 2 : 0,
        rain_related_event_count: state === 'record' ? 2 : 0,
        recognized_event_count: 0,
        first_event_date: state === 'record' ? '2001-01-01' : null,
        latest_event_date: state === 'record' ? '2024-05-01' : null,
        human_impacts: {
          deaths: 0,
          injured: 0,
          homeless: 0,
          displaced: 0,
          missing: 0,
          reported_affected_total: 0,
        },
        annual: { first_year: 2001, latest_year: 2024, benchmark: { immediate_region: { codigo: selected.codigo_regiao_imediata, nome: selected.regiao_imediata, municipality_count: 1, zeros_policy: 'included_as_zero' } }, series: annualSeries },
      },
      types: disasterTypes,
      months: Array.from({ length: 12 }, (_, index) => ({ month: index + 1, event_count: 0, rain_related_event_count: index === 0 && state === 'record' ? 2 : 0, event_pct: state === 'record' ? (index === 0 ? 100 : 0) : null })),
      highlights: [],
    },
    land_cover: {
      state: landCoverState,
      history:
        landCoverState === 'record'
          ? [
              {
                year: 1985,
                mapped_area_ha: 1000,
                urban_area_ha: 1,
                urban_area_pct: 0.1,
                native_vegetation_area_ha: 900,
                native_vegetation_area_pct: 90,
                agriculture_livestock_area_ha: 50,
                agriculture_livestock_area_pct: 5,
                water_area_ha: 10,
                water_area_pct: 1,
                wetland_area_ha: 0,
                wetland_area_pct: 0,
              },
              {
                year: 2025,
                mapped_area_ha: 1000,
                urban_area_ha: 10,
                urban_area_pct: 1,
                native_vegetation_area_ha: 800,
                native_vegetation_area_pct: 80,
                agriculture_livestock_area_ha: 100,
                agriculture_livestock_area_pct: 10,
                water_area_ha: 10,
                water_area_pct: 1,
                wetland_area_ha: 0,
                wetland_area_pct: 0,
              },
            ]
          : [],
      change:
        landCoverState === 'record'
          ? {
              urban_area_change_ha: 9,
              urban_area_change_pct: 900,
              native_vegetation_change_ha: -100,
              native_vegetation_change_pct: -11.1,
            }
          : null,
    },
    municipal_capacity: {
      state: code === '5101837' ? 'not_in_source' : 'record',
      provenance: 'self_reported_munic_2020',
      reference_year: 2020,
      indicators: Object.fromEntries([
        'municipal_civil_defense_body',
        'civil_defense_budget_provision',
        'any_risk_prevention_planning_instrument',
        'flood_risk_mapping',
        'flood_contingency_plan',
        'flood_early_warning',
        'landslide_risk_mapping',
        'landslide_contingency_plan',
        'landslide_early_warning',
      ].map((name) => [name, code === '5101837' ? 'not_in_source' : 'declared_yes'])),
    } as MunicipalityPresentation['municipal_capacity'],
    census: {
      state: state === 'no_record' ? 'not_published' : 'record',
      provenance: 'transitional_legacy',
      year: 2022,
      connected_sewer_pct: state === 'no_record' ? null : 60,
      outside_selected_sewer_pct: state === 'no_record' ? null : 40,
    },
    transfers: {
      state: 'record',
      provenance: 'transitional_legacy',
      legacy: {
        agreements: 1,
        firstYear: 2020,
        lastYear: 2024,
        actions: [],
        attribution: 'fixture',
        latest: {
          number: '1',
          year: 2024,
          status: 'Convênio Anulado',
          object: 'Objeto fixture.',
          globalValue: 0,
        },
      },
    },
    benchmarks: {
      immediate_region: {
        codigo: selected.codigo_regiao_imediata, nome: selected.regiao_imediata,
        municipality_count: 1, includes_selected_municipality: true,
        metrics: Object.fromEntries([
          ['rain_related_event_count_10y', 2, 'registros'],
          ['urban_change_20y_pct', 900, 'percentual'],
          ['native_vegetation_change_20y_pct', -11.1, 'percentual'],
          ['urban_area_pct', 1, 'percentual'],
          ['native_vegetation_area_pct', 80, 'percentual'],
        ].map(([key, value, unit]) => [key, {
          source: key === 'rain_related_event_count_10y' ? 'Atlas Digital de Desastres/S2ID' : 'MapBiomas Brasil',
          unit, reference: key === 'rain_related_event_count_10y' ? { window_years: 10, reference_date: '2025-12-31' } : { latest_snapshot_year: 2025 },
          municipality_value: value, mean: value, median: value, percentile_strictly_lower_pct: 0,
          denominator: { included: 1, missing: 0, undefined: 0 },
        }])),
      },
    } as unknown as MunicipalityPresentation['benchmarks'],
    sources: [],
  };
}

function jsonResponse(value: unknown, status = 200) {
  return new Response(JSON.stringify(value), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });
}

function requestPath(input: RequestInfo | URL) {
  if (typeof input === 'string') return input;
  if (input instanceof URL) return input.pathname;
  return input.url;
}

function mockData(
  handlers: Record<string, () => Response | Promise<Response>>,
) {
  const mockedFetch = vi.fn((input: RequestInfo | URL) => {
    const handler = handlers[requestPath(input)];
    return Promise.resolve(handler ? handler() : jsonResponse({}, 404));
  });
  vi.stubGlobal('fetch', mockedFetch);
  return mockedFetch;
}

beforeAll(() => {
  HTMLElement.prototype.scrollIntoView = vi.fn();
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
  window.history.replaceState(null, '', '/');
});

describe('municipal v1 loading', () => {
  it('provides a skip link to the main content', () => {
    mockData({
      '/data/v1/municipal-index.json': () => jsonResponse(index),
      '/data/v1/metadata.json': () => jsonResponse(metadata),
    });

    render(<Home />);

    expect(
      screen.getByRole('link', { name: 'Pular para o conteúdo principal' }),
    ).toHaveProperty('hash', '#conteudo-principal');
  });

  it('treats cancelled and annulled Transferegov statuses as non-active', () => {
    expect(inactiveTransferStatus('Cancelado')).toBe(true);
    expect(inactiveTransferStatus('Convênio Anulado')).toBe(true);
    expect(inactiveTransferStatus('Em execução')).toBe(false);
  });

  it('accepts numbered shard paths only when their UF matches the index entry', () => {
    expect(isMunicipalIndex(index)).toBe(true);
    const invalid = structuredClone(index);
    invalid.municipalities[1].shard = '/data/v1/uf/MG-001.json';
    expect(isMunicipalIndex(invalid)).toBe(false);
  });

  it('resolves legacy links to canonical codigo_ibge and only fetches its UF shard', async () => {
    window.history.replaceState(null, '', '?municipio=4202404');
    const mockedFetch = mockData({
      '/data/v1/municipal-index.json': () => jsonResponse(index),
      '/data/v1/metadata.json': () => jsonResponse(metadata),
      '/data/v1/uf/SC-001.json': () =>
        jsonResponse({
          schema_version: 'v1',
          uf: 'SC',
          municipalities: { '4202404': municipality('4202404', 'record') },
        }),
    });

    render(<Home />);

    await screen.findByText('Blumenau · SC');
    expect(window.location.search).toBe('?codigo_ibge=4202404');
    expect(mockedFetch.mock.calls.map(([url]) => requestPath(url))).toEqual([
      '/data/v1/municipal-index.json',
      '/data/v1/metadata.json',
      '/data/v1/uf/SC-001.json',
    ]);
  });

  it('searches the index and loads the selected UF shard', async () => {
    const mockedFetch = mockData({
      '/data/v1/municipal-index.json': () => jsonResponse(index),
      '/data/v1/metadata.json': () => jsonResponse(metadata),
      '/data/v1/uf/SC-001.json': () =>
        jsonResponse({
          schema_version: 'v1',
          uf: 'SC',
          municipalities: { '4202404': municipality('4202404', 'record') },
        }),
    });

    render(<Home />);

    const search = await screen.findByLabelText('Busque por nome, UF ou código IBGE');
    fireEvent.focus(search);
    fireEvent.change(search, { target: { value: 'Blumenau' } });
    fireEvent.click(await screen.findByRole('option', { name: /Blumenau, SC/ }));

    await screen.findByText('Blumenau · SC');
    expect(window.location.search).toBe('?codigo_ibge=4202404');
    expect(mockedFetch.mock.calls.map(([url]) => requestPath(url))).toContain(
      '/data/v1/uf/SC-001.json',
    );
  });

  it('selects a municipality from the search with the keyboard', async () => {
    mockData({
      '/data/v1/municipal-index.json': () => jsonResponse(index),
      '/data/v1/metadata.json': () => jsonResponse(metadata),
      '/data/v1/uf/SC-001.json': () =>
        jsonResponse({
          schema_version: 'v1',
          uf: 'SC',
          municipalities: { '4202404': municipality('4202404', 'record') },
        }),
    });

    render(<Home />);

    const search = await screen.findByLabelText('Busque por nome, UF ou código IBGE');
    fireEvent.focus(search);
    fireEvent.change(search, { target: { value: 'Blumenau' } });
    fireEvent.keyDown(search, { key: 'Enter' });

    await screen.findByText('Blumenau · SC');
    expect(window.location.search).toBe('?codigo_ibge=4202404');
  });

  it('displays GOLD-derived MapBiomas changes using years from the payload', async () => {
    window.history.replaceState(null, '', '?codigo_ibge=4202404');
    mockData({
      '/data/v1/municipal-index.json': () => jsonResponse(index),
      '/data/v1/metadata.json': () => jsonResponse(metadata),
      '/data/v1/uf/SC-001.json': () =>
        jsonResponse({
          schema_version: 'v1',
          uf: 'SC',
          municipalities: { '4202404': municipality('4202404', 'record') },
        }),
    });

    render(<Home />);

    await screen.findByText('Cobertura e uso da terra');
    expect(screen.getByText('Série MapBiomas de 1985 a 2025.')).toBeTruthy();
    expect(screen.getAllByText('Área urbanizada').length).toBeGreaterThan(0);
    expect(screen.getByText('+9 ha · +900%')).toBeTruthy();
    expect(screen.getByText('-100 ha · -11,1%')).toBeTruthy();
    expect(
      screen.getByText(
        /Área urbanizada não equivale diretamente a superfície impermeabilizada/,
      ),
    ).toBeTruthy();
  });

  it('renders the deterministic 30-second summary with territorial identity and sources', async () => {
    window.history.replaceState(null, '', '?codigo_ibge=4202404');
    mockData({
      '/data/v1/municipal-index.json': () => jsonResponse(index),
      '/data/v1/metadata.json': () => jsonResponse(metadata),
      '/data/v1/uf/SC-001.json': () =>
        jsonResponse({
          schema_version: 'v1',
          uf: 'SC',
          municipalities: { '4202404': municipality('4202404', 'record') },
        }),
    });

    render(<Home />);

    await screen.findByRole('heading', { name: 'BLUMENAU / SC' });
    expect(screen.getByText('Região Geográfica Imediata de Blumenau')).toBeTruthy();
    const regionalComparison = screen.getByRole('region', {
      name: 'Como este município se compara à região?',
    });
    expect(
      within(regionalComparison).getByRole('heading', {
        name: 'Registros relacionados à chuva',
      }),
    ).toBeTruthy();
    expect(screen.getByText('Atlas/S2ID: 1991–2025')).toBeTruthy();
    expect(screen.getByText('MapBiomas: 1985–2025')).toBeTruthy();
    expect(
      screen.getByRole('heading', { name: 'Como o município declarou se preparar' }),
    ).toBeTruthy();
    expect(screen.getByText('Capacidade declarada · MUNIC 2020')).toBeTruthy();
    expect(screen.getAllByText('Sim')).toHaveLength(9);
  });

  it('keeps no record, missing values, and zero distinct', async () => {
    window.history.replaceState(null, '', '?codigo_ibge=1200013');
    mockData({
      '/data/v1/municipal-index.json': () => jsonResponse(index),
      '/data/v1/metadata.json': () => jsonResponse(metadata),
      '/data/v1/uf/AC.json': () =>
        jsonResponse({
          schema_version: 'v1',
          uf: 'AC',
          municipalities: { '1200013': municipality('1200013', 'no_record') },
        }),
    });

    render(<Home />);

    await screen.findByText('Nenhum registro encontrado no recorte');
    expect(
      screen.getByText('Nenhum registro foi encontrado nesta release do Atlas/S2ID.'),
    ).toBeTruthy();
    expect(screen.getByText('Valor não publicado')).toBeTruthy();
    expect(screen.getByText('R$ 0')).toBeTruthy();
    expect(
      screen.getByText(
        'Este instrumento está cancelado ou anulado e não é apresentado como capacidade ou prevenção em execução.',
      ),
    ).toBeTruthy();
  });

  it('shows Fernando de Noronha MapBiomas absence instead of zero', async () => {
    window.history.replaceState(null, '', '?codigo_ibge=2605459');
    mockData({
      '/data/v1/municipal-index.json': () => jsonResponse(index),
      '/data/v1/metadata.json': () => jsonResponse(metadata),
      '/data/v1/uf/PE.json': () =>
        jsonResponse({
          schema_version: 'v1',
          uf: 'PE',
          municipalities: {
            '2605459': municipality('2605459', 'record', 'no_coverage'),
          },
        }),
    });

    render(<Home />);

    await screen.findByText('Sem cobertura MapBiomas para este município');
    expect(screen.getByText('MapBiomas: sem cobertura')).toBeTruthy();
    expect(
      screen.getByText(
        'Não há classificação publicada para esta unidade territorial no recorte carregado. A ausência não é um valor zero.',
      ),
    ).toBeTruthy();
    expect(screen.queryByText('Área urbanizada')).toBeNull();
  });

  it('surfaces index and shard failures without a default municipality', async () => {
    mockData({
      '/data/v1/municipal-index.json': () => jsonResponse({}, 500),
      '/data/v1/metadata.json': () => jsonResponse(metadata),
    });

    const { unmount } = render(<Home />);
    await screen.findByText('Índice municipal indisponível');
    expect(screen.queryByText('Blumenau · SC')).toBeNull();
    unmount();

    window.history.replaceState(null, '', '?codigo_ibge=4202404');
    mockData({
      '/data/v1/municipal-index.json': () => jsonResponse(index),
      '/data/v1/metadata.json': () => jsonResponse(metadata),
      '/data/v1/uf/SC-001.json': () => jsonResponse({}, 500),
    });
    render(<Home />);

    await screen.findByText('Dados municipais indisponíveis');
    await waitFor(() => {
      expect(screen.getByText(/Não foi possível carregar o recorte de SC/)).toBeTruthy();
    });
  });

  it('refetches a shard after it did not contain the requested municipality', async () => {
    window.history.replaceState(null, '', '?codigo_ibge=4202404');
    let shardRequests = 0;
    mockData({
      '/data/v1/municipal-index.json': () => jsonResponse(index),
      '/data/v1/metadata.json': () => jsonResponse(metadata),
      '/data/v1/uf/SC-001.json': () => {
        shardRequests += 1;
        return jsonResponse(
          shardRequests === 1
            ? { schema_version: 'v1', uf: 'SC', municipalities: {} }
            : {
                schema_version: 'v1',
                uf: 'SC',
                municipalities: {
                  '4202404': municipality('4202404', 'record'),
                },
              },
        );
      },
    });

    render(<Home />);

    await screen.findByText('Dados municipais indisponíveis');
    fireEvent.click(screen.getByRole('button', { name: 'Tentar novamente' }));

    await screen.findByText('Blumenau · SC');
    expect(shardRequests).toBe(2);
  });
});

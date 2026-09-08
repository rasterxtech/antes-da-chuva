'use client';

import { useState } from 'react';
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import type { MunicipalityPresentation } from '@/lib/presentation-contract';
import { ChartKey, MAPBIOMAS_URL, SourceNote } from './editorial';

type Period = 'full' | 5 | 10 | 20;

function variation(
  change: Record<string, number | null>,
  period: Period,
  prefix: 'urban' | 'native_vegetation',
) {
  if (period === 'full') {
    return {
      area: change[`${prefix === 'urban' ? 'urban_area' : prefix}_change_ha`],
      pct: change[`${prefix === 'urban' ? 'urban_area' : prefix}_change_pct`],
    };
  }
  const key = prefix === 'urban' ? 'urban' : 'native_vegetation';
  return {
    area: change[`${key}_change_${period}y_ha`],
    pct: change[`${key}_change_${period}y_pct`],
  };
}

function formatVariation(area: number | null, pct: number | null) {
  if (area === null || pct === null) return 'Variação não publicada';
  const signed = (value: number) =>
    `${value > 0 ? '+' : ''}${value.toLocaleString('pt-BR')}`;
  return `${signed(area)} ha · ${signed(pct)}%`;
}

export function LandCoverHistory({
  landCover,
}: {
  landCover: MunicipalityPresentation['land_cover'];
}) {
  const [unit, setUnit] = useState<'pct' | 'km2'>('pct');
  const [period, setPeriod] = useState<Period>('full');
  if (landCover.state === 'no_coverage')
    return (
      <section className="mt-5 rounded-2xl border border-dashed border-border p-5">
        <h2 className="font-heading text-2xl font-semibold">
          Sem cobertura MapBiomas para este município
        </h2>
        <p className="mt-2 text-sm text-muted-foreground">
          Não há classificação publicada para esta unidade territorial no
          recorte carregado. A ausência não é um valor zero.
        </p>
        <SourceNote href={MAPBIOMAS_URL} label="MapBiomas Brasil">
          Cobertura não disponível no recorte publicado.
        </SourceNote>
      </section>
    );
  const first = landCover.history[0];
  const latest = landCover.history.at(-1);
  const change = landCover.change;
  if (!first || !latest || !change) return null;
  const availablePeriods: Period[] = [
    'full',
    ...([5, 10, 20] as const).filter(
      (years) => typeof change[`reference_year_${years}y`] === 'number',
    ),
  ];
  const referenceYear =
    period === 'full' ? first.year : change[`reference_year_${period}y`];
  const startYear =
    typeof referenceYear === 'number' ? referenceYear : first.year;
  const history = landCover.history.filter((row) => row.year >= startYear);
  const start = history[0] ?? first;
  const data = history.map((row) => ({
    year: row.year,
    urban: unit === 'pct' ? row.urban_area_pct : row.urban_area_ha / 100,
    native:
      unit === 'pct'
        ? row.native_vegetation_area_pct
        : row.native_vegetation_area_ha / 100,
  }));
  const format = (value: number) =>
    `${value.toLocaleString('pt-BR', { maximumFractionDigits: 2 })} ${unit === 'pct' ? '%' : 'km²'}`;
  const urban = variation(change, period, 'urban');
  const native = variation(change, period, 'native_vegetation');
  return (
    <section
      aria-labelledby="mapbiomas-historico"
      className="elevated-card mt-5 rounded-2xl bg-card p-5 shadow-[0_12px_45px_rgb(21_42_57/8%)] sm:p-7"
    >
      <div className="flex flex-wrap justify-between gap-3">
        <div>
          <h2
            id="mapbiomas-historico"
            className="font-heading text-2xl font-semibold"
          >
            Como o território mudou
          </h2>
          <span className="sr-only">Cobertura e uso da terra</span>
          <p className="mt-2 text-sm text-muted-foreground">
            Série MapBiomas de {start.year} a {latest.year}.
          </p>
        </div>
        <button
          type="button"
          className="min-h-11 rounded-lg border border-border px-3 py-2 text-sm font-bold hover:bg-muted"
          onClick={() => setUnit(unit === 'pct' ? 'km2' : 'pct')}
        >
          Mostrar {unit === 'pct' ? 'km²' : '%'}
        </button>
      </div>
      <label className="chart-controls">
        Período{' '}
        <select
          value={period}
          onChange={(event) =>
            setPeriod(
              event.target.value === 'full'
                ? 'full'
                : (Number(event.target.value) as 5 | 10 | 20),
            )
          }
        >
          {availablePeriods.map((value) => (
            <option key={value} value={value}>
              {value === 'full' ? 'Série completa' : `Últimos ${value} anos`}
            </option>
          ))}
        </select>
      </label>
      <div
        className="chart-frame"
        aria-label={`Série de área urbanizada e vegetação nativa em ${unit === 'pct' ? 'percentual' : 'quilômetros quadrados'}`}
      >
        <ResponsiveContainer
          width="100%"
          height="100%"
          initialDimension={{ width: 800, height: 288 }}
          minWidth={0}
        >
          <LineChart
            data={data}
            margin={{ top: 12, right: 8, bottom: 8, left: 0 }}
          >
            <CartesianGrid
              vertical={false}
              stroke="var(--border)"
              strokeDasharray="3 5"
            />
            <XAxis
              dataKey="year"
              interval="preserveStartEnd"
              minTickGap={28}
              tickLine={false}
              tick={{ fontSize: 12, fill: 'var(--muted-foreground)' }}
            />
            <YAxis
              width={40}
              tickLine={false}
              axisLine={false}
              tickFormatter={(value: number) =>
                value.toLocaleString('pt-BR', { notation: 'compact' })
              }
              tick={{ fontSize: 12, fill: 'var(--muted-foreground)' }}
            />
            <Tooltip
              contentStyle={{
                borderRadius: 12,
                borderColor: 'var(--border)',
                fontSize: 14,
                background: 'var(--card)',
              }}
              formatter={(value) => format(Number(value))}
            />
            <Line
              dataKey="urban"
              name="Área urbanizada"
              stroke="var(--chart-municipality)"
              strokeWidth={3}
              dot={false}
              isAnimationActive={false}
            />
            <Line
              dataKey="native"
              name="Vegetação nativa"
              stroke="var(--chart-vegetation)"
              strokeWidth={3}
              strokeDasharray="7 4"
              dot={false}
              isAnimationActive={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
      <ChartKey
        items={[
          { label: 'Área urbanizada', color: 'var(--chart-municipality)' },
          {
            label: 'Vegetação nativa',
            color: 'var(--chart-vegetation)',
            dashed: true,
          },
        ]}
      />
      <p className="mt-2 text-center text-sm text-muted-foreground">
        Unidade:{' '}
        {unit === 'pct'
          ? 'percentual da área mapeada (%)'
          : 'quilômetros quadrados (km²)'}
      </p>
      <div className="mt-5 grid gap-3 md:grid-cols-2">
        {[
          {
            name: 'Área urbanizada',
            start: start.urban_area_ha,
            end: latest.urban_area_ha,
            change: urban,
          },
          {
            name: 'Vegetação nativa',
            start: start.native_vegetation_area_ha,
            end: latest.native_vegetation_area_ha,
            change: native,
          },
        ].map((item) => (
          <div className="rounded-xl bg-muted/50 p-4" key={item.name}>
            <strong>{item.name}</strong>
            <p className="mt-2 text-sm">
              {(item.start / 100).toLocaleString('pt-BR')} km² em {start.year} →{' '}
              {(item.end / 100).toLocaleString('pt-BR')} km² em {latest.year}
            </p>
            <p className="text-sm font-bold">
              {formatVariation(item.change.area, item.change.pct)}
            </p>
          </div>
        ))}
      </div>
      <div className="mt-4 grid gap-3 text-sm sm:grid-cols-3">
        <Indicator
          label="Agropecuária"
          value={latest.agriculture_livestock_area_ha}
        />
        <Indicator label="Água" value={latest.water_area_ha} />
        <Indicator label="Áreas úmidas" value={latest.wetland_area_ha} />
      </div>
      <p className="mt-5 text-xs leading-5 text-muted-foreground">
        MapBiomas representa classificação de cobertura e uso da terra. Área
        urbanizada não equivale diretamente a superfície impermeabilizada. A
        série não permite afirmar causalidade com eventos, risco ou perda de
        vegetação.
      </p>
      <details className="data-details">
        <summary>Consultar valores por ano</summary>
        <table>
          <caption className="sr-only">
            Cobertura e uso da terra em {unit === 'pct' ? 'percentual' : 'km²'}
          </caption>
          <thead>
            <tr>
              <th scope="col">Ano</th>
              <th scope="col">Área urbanizada</th>
              <th scope="col">Vegetação nativa</th>
            </tr>
          </thead>
          <tbody>
            {data.map((row) => (
              <tr key={row.year}>
                <th scope="row">{row.year}</th>
                <td>{format(row.urban)}</td>
                <td>{format(row.native)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </details>
      <SourceNote href={MAPBIOMAS_URL} label="MapBiomas Brasil">
        Cobertura e uso da terra de {start.year} a {latest.year}.
      </SourceNote>
    </section>
  );
}
function Indicator({ label, value }: { label: string; value: number }) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-2 rounded-lg bg-muted p-3 sm:block">
      <span>{label}</span>
      <strong className="block">
        {(value / 100).toLocaleString('pt-BR')} km²
      </strong>
    </div>
  );
}

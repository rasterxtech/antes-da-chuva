'use client';

import { useState } from 'react';
import {
  Bar,
  ComposedChart,
  CartesianGrid,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import type { MunicipalityPresentation } from '@/lib/presentation-contract';
import { ATLAS_URL, ChartKey, SourceNote } from './editorial';

const number = new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 1 });
const integer = new Intl.NumberFormat('pt-BR');

export function DisasterHistory({
  disasters,
}: {
  disasters: MunicipalityPresentation['disasters'];
}) {
  const [typeId, setTypeId] = useState<number | null>(null);
  if (disasters.state === 'no_record')
    return (
      <section className="rounded-2xl border border-dashed border-border p-5">
        <h2 className="font-heading text-2xl font-semibold">
          Nenhum registro encontrado no recorte
        </h2>
        <p className="mt-2 text-sm text-muted-foreground">
          O Atlas não retornou ocorrência para as tipologias relacionadas à
          chuva. Isso não significa ausência de evento, risco ou necessidade de
          prevenção.
        </p>
        <SourceNote href={ATLAS_URL} label="Atlas Digital de Desastres / S2ID">
          Ausência de registros no recorte publicado, não ausência de risco.
        </SourceNote>
      </section>
    );
  const annual = disasters.history.annual;
  const selected =
    annual.series.find((series) => series.atlas_type_id === typeId) ??
    annual.series[0];
  const types = disasters.types;
  const peak = selected.points.reduce(
    (best, point) =>
      point.municipal_event_count > best.municipal_event_count ? point : best,
    selected.points[0],
  );
  return (
    <section
      aria-labelledby="historico-atlas"
      className="elevated-card rounded-2xl bg-card p-5 shadow-[0_12px_45px_rgb(21_42_57/8%)] sm:p-7"
    >
      <h2 id="historico-atlas" className="font-heading text-2xl font-semibold">
        O que já aconteceu
      </h2>
      <p className="mt-2 text-sm text-muted-foreground">
        Registros oficiais relacionados à chuva encontrados no Atlas/S2ID. A
        linha mostra a média dos municípios da mesma Região Geográfica Imediata,
        incluindo municípios sem registros como zero.
      </p>
      <label className="chart-controls">
        Tipo COBRADE/Atlas
        <select
          value={typeId ?? 'total'}
          onChange={(event) =>
            setTypeId(
              event.target.value === 'total'
                ? null
                : Number(event.target.value),
            )
          }
        >
          <option value="total">Todos relacionados à chuva</option>
          {types.map((type) => (
            <option key={type.atlas_type_id} value={type.atlas_type_id}>
              {type.type_name}
            </option>
          ))}
        </select>
      </label>
      <div
        className="chart-frame"
        aria-label={`Série anual de registros municipais e média da Região Imediata de ${annual.benchmark.immediate_region.nome}`}
      >
        <ResponsiveContainer
          width="100%"
          height="100%"
          initialDimension={{ width: 800, height: 288 }}
          minWidth={0}
        >
          <ComposedChart
            data={selected.points}
            margin={{ top: 12, right: 8, bottom: 8, left: 0 }}
          >
            <CartesianGrid
              vertical={false}
              stroke="var(--border)"
              strokeDasharray="3 5"
            />
            <XAxis
              dataKey="year"
              minTickGap={28}
              interval="preserveStartEnd"
              tickLine={false}
              tick={{ fontSize: 12, fill: 'var(--muted-foreground)' }}
            />
            <YAxis
              width={36}
              allowDecimals={false}
              tickLine={false}
              axisLine={false}
              tick={{ fontSize: 12, fill: 'var(--muted-foreground)' }}
            />
            <Tooltip
              contentStyle={{
                borderRadius: 12,
                borderColor: 'var(--border)',
                fontSize: 14,
                background: 'var(--card)',
              }}
              formatter={(value, _name, item) => [
                number.format(Number(value)),
                item.dataKey === 'municipal_event_count'
                  ? 'Município'
                  : 'Média regional',
              ]}
              labelFormatter={(year) => `${year}`}
            />
            <Bar
              dataKey="municipal_event_count"
              name="Município"
              fill="var(--chart-municipality)"
              radius={[3, 3, 0, 0]}
              isAnimationActive={false}
            />
            <Line
              type="monotone"
              dataKey="immediate_region_average_event_count"
              name="Média regional"
              stroke="var(--chart-regional)"
              strokeWidth={2.5}
              strokeDasharray="5 3"
              dot={false}
              isAnimationActive={false}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
      <ChartKey
        items={[
          { label: 'Município', color: 'var(--chart-municipality)' },
          {
            label: 'Média regional',
            color: 'var(--chart-regional)',
            dashed: true,
          },
        ]}
      />
      <p className="sr-only">
        {selected.points
          .map(
            (point) =>
              `${point.year}: município ${point.municipal_event_count}; média regional ${number.format(point.immediate_region_average_event_count)}.`,
          )
          .join(' ')}
      </p>
      <p className="mt-5 text-sm text-muted-foreground">
        Total, último registro e impactos se referem a todas as tipologias. O
        ano com mais registros acompanha o filtro selecionado.
      </p>
      <dl className="mt-5 grid gap-3 sm:grid-cols-2 sm:[&>div:last-child]:col-span-2 lg:grid-cols-5 lg:[&>div:last-child]:col-span-1">
        <Metric
          label="Total"
          value={integer.format(disasters.history.rain_related_event_count)}
        />
        <Metric
          label="Último registro"
          value={
            disasters.history.latest_event_date?.slice(0, 4) ?? 'Não informado'
          }
        />
        <Metric
          label="Ano com mais registros"
          value={
            peak && peak.municipal_event_count > 0
              ? `${peak.year} (${integer.format(peak.municipal_event_count)})`
              : 'Não informado'
          }
        />
        <Metric
          label="Mortes registradas"
          value={integer.format(disasters.history.human_impacts.deaths)}
        />
        <Metric
          label="Pessoas afetadas informadas"
          value={integer.format(
            disasters.history.human_impacts.reported_affected_total,
          )}
        />
      </dl>
      <details className="data-details">
        <summary>Consultar valores por ano</summary>
        <table>
          <caption className="sr-only">Série anual do tipo selecionado</caption>
          <thead>
            <tr>
              <th scope="col">Ano</th>
              <th scope="col">Município</th>
              <th scope="col">Média regional</th>
            </tr>
          </thead>
          <tbody>
            {selected.points.map((point) => (
              <tr key={point.year}>
                <th scope="row">{point.year}</th>
                <td>{integer.format(point.municipal_event_count)}</td>
                <td>
                  {number.format(point.immediate_region_average_event_count)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </details>
      <SourceNote href={ATLAS_URL} label="Atlas Digital de Desastres / S2ID">
        Série de {annual.first_year} a {annual.latest_year}. Registros
        informados, não uma previsão.
      </SourceNote>
    </section>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl bg-muted/50 p-3">
      <dt className="text-xs font-bold text-muted-foreground">{label}</dt>
      <dd className="mt-1 font-heading text-xl font-semibold">{value}</dd>
    </div>
  );
}

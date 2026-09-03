'use client';

import { useState } from 'react';
import { Bar, BarChart, CartesianGrid, Legend, Line, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import type { MunicipalityPresentation } from '@/lib/presentation-contract';

const number = new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 1 });

export function DisasterHistory({ disasters }: { disasters: MunicipalityPresentation['disasters'] }) {
  const [typeId, setTypeId] = useState<number | null>(null);
  if (disasters.state === 'no_record') return <section className="rounded-2xl border border-dashed border-border p-5"><h2 className="font-heading text-2xl font-semibold">Nenhum registro encontrado no recorte</h2><p className="mt-2 text-sm text-muted-foreground">O Atlas não retornou ocorrência para as tipologias relacionadas à chuva. Isso não significa ausência de evento, risco ou necessidade de prevenção.</p></section>;
  const annual = disasters.history.annual;
  const selected = annual.series.find((series) => series.atlas_type_id === typeId) ?? annual.series[0];
  const types = disasters.types;
  const peak = selected.points.reduce((best, point) => point.municipal_event_count > best.municipal_event_count ? point : best, selected.points[0]);
  return <section aria-labelledby="historico-atlas" className="elevated-card rounded-2xl bg-card p-5 shadow-[0_12px_45px_rgb(21_42_57/8%)] sm:p-7">
    <h2 id="historico-atlas" className="font-heading text-2xl font-semibold">O que já aconteceu</h2>
    <p className="mt-2 text-sm text-muted-foreground">Registros oficiais relacionados à chuva encontrados no Atlas/S2ID. A linha mostra a média dos municípios da mesma Região Geográfica Imediata, incluindo municípios sem registros como zero.</p>
    <label className="mt-5 block text-sm font-bold">Tipo COBRADE/Atlas
      <select className="ml-3 rounded border border-border bg-background p-2" value={typeId ?? 'total'} onChange={(event) => setTypeId(event.target.value === 'total' ? null : Number(event.target.value))}>
        <option value="total">Todos relacionados à chuva</option>
        {types.map((type) => <option key={type.atlas_type_id} value={type.atlas_type_id}>{type.type_name}</option>)}
      </select>
    </label>
    <div className="mt-5 h-72" aria-label={`Série anual de registros municipais e média da Região Imediata de ${annual.benchmark.immediate_region.nome}`}>
      <ResponsiveContainer width="100%" height="100%"><BarChart data={selected.points}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="year" /><YAxis /><Tooltip formatter={(value, name) => [number.format(Number(value)), name === 'municipal_event_count' ? 'Município' : 'Média regional']} labelFormatter={(year) => `${year}`} /><Legend /><Bar dataKey="municipal_event_count" name="Município" fill="#177e89" /><Line type="monotone" dataKey="immediate_region_average_event_count" name="Média regional" stroke="#d97706" strokeWidth={2} /></BarChart></ResponsiveContainer>
    </div>
    <p className="sr-only">{selected.points.map((point) => `${point.year}: município ${point.municipal_event_count}; média regional ${number.format(point.immediate_region_average_event_count)}.`).join(' ')}</p>
    <dl className="mt-5 grid gap-3 sm:grid-cols-5"><Metric label="Total" value={String(disasters.history.rain_related_event_count)} /><Metric label="Último registro" value={disasters.history.latest_event_date?.slice(0, 4) ?? 'Não informado'} /><Metric label="Ano com mais registros" value={peak ? `${peak.year} (${peak.municipal_event_count})` : 'Não informado'} /><Metric label="Mortes registradas" value={String(disasters.history.human_impacts.deaths)} /><Metric label="Pessoas afetadas informadas" value={String(disasters.history.human_impacts.reported_affected_total)} /></dl>
  </section>;
}

function Metric({ label, value }: { label: string; value: string }) { return <div className="rounded-xl bg-muted/50 p-3"><dt className="text-xs font-bold text-muted-foreground">{label}</dt><dd className="mt-1 font-heading text-xl font-semibold">{value}</dd></div>; }

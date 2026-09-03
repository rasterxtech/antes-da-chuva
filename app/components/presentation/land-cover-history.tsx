'use client';

import { useState } from 'react';
import { Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import type { MunicipalityPresentation } from '@/lib/presentation-contract';

type Period = 'full' | 5 | 10 | 20;

function variation(change: Record<string, number | null>, period: Period, prefix: 'urban' | 'native_vegetation') {
  if (period === 'full') {
    return {
      area: change[`${prefix === 'urban' ? 'urban_area' : prefix}_change_ha`],
      pct: change[`${prefix === 'urban' ? 'urban_area' : prefix}_change_pct`],
    };
  }
  const key = prefix === 'urban' ? 'urban' : 'native_vegetation';
  return { area: change[`${key}_change_${period}y_ha`], pct: change[`${key}_change_${period}y_pct`] };
}

function formatVariation(area: number | null, pct: number | null) {
  if (area === null || pct === null) return 'Variação não publicada';
  const signed = (value: number) => `${value > 0 ? '+' : ''}${value.toLocaleString('pt-BR')}`;
  return `${signed(area)} ha · ${signed(pct)}%`;
}

export function LandCoverHistory({ landCover }: { landCover: MunicipalityPresentation['land_cover'] }) {
  const [unit, setUnit] = useState<'pct' | 'km2'>('pct');
  const [period, setPeriod] = useState<Period>('full');
  if (landCover.state === 'no_coverage') return <section className="mt-5 rounded-2xl border border-dashed border-border p-5"><h2 className="font-heading text-2xl font-semibold">Sem cobertura MapBiomas para este município</h2><p className="mt-2 text-sm text-muted-foreground">Não há classificação publicada para esta unidade territorial no recorte carregado. A ausência não é um valor zero.</p></section>;
  const first = landCover.history[0]; const latest = landCover.history.at(-1); const change = landCover.change;
  if (!first || !latest || !change) return null;
  const availablePeriods: Period[] = ['full', ...([5, 10, 20] as const).filter((years) => change[`reference_year_${years}y`] !== null)];
  const referenceYear = period === 'full' ? first.year : change[`reference_year_${period}y`];
  const startYear = typeof referenceYear === 'number' ? referenceYear : first.year;
  const history = landCover.history.filter((row) => row.year >= startYear);
  const start = history[0] ?? first;
  const data = history.map(row => ({ year: row.year, urban: unit === 'pct' ? row.urban_area_pct : row.urban_area_ha / 100, native: unit === 'pct' ? row.native_vegetation_area_pct : row.native_vegetation_area_ha / 100 }));
  const format = (value: number) => `${value.toLocaleString('pt-BR', { maximumFractionDigits: 2 })} ${unit === 'pct' ? '%' : 'km²'}`;
  const urban = variation(change, period, 'urban');
  const native = variation(change, period, 'native_vegetation');
  return <section aria-labelledby="mapbiomas-historico" className="elevated-card mt-5 rounded-2xl bg-card p-5 shadow-[0_12px_45px_rgb(21_42_57/8%)] sm:p-7">
    <div className="flex flex-wrap justify-between gap-3"><div><h2 id="mapbiomas-historico" className="font-heading text-2xl font-semibold">Como o território mudou</h2><span className="sr-only">Cobertura e uso da terra</span><p className="mt-2 text-sm text-muted-foreground">Série MapBiomas de {start.year} a {latest.year}.</p></div><button type="button" className="rounded border border-border px-3 py-2 text-sm font-bold" onClick={() => setUnit(unit === 'pct' ? 'km2' : 'pct')}>Mostrar {unit === 'pct' ? 'km²' : '%'}</button></div>
    <label className="mt-5 block text-sm font-bold">Período <select className="ml-3 rounded border border-border bg-background p-2" value={period} onChange={(event) => setPeriod(event.target.value === 'full' ? 'full' : Number(event.target.value) as 5 | 10 | 20)}>{availablePeriods.map((value) => <option key={value} value={value}>{value === 'full' ? 'Série completa' : `Últimos ${value} anos`}</option>)}</select></label>
    <div className="mt-5 h-72" aria-label={`Série de área urbanizada e vegetação nativa em ${unit === 'pct' ? 'percentual' : 'quilômetros quadrados'}`}><ResponsiveContainer width="100%" height="100%"><LineChart data={data}><XAxis dataKey="year" /><YAxis /><Tooltip formatter={(value) => format(Number(value))} /><Legend /><Line dataKey="urban" name="Área urbanizada" stroke="#177e89" /><Line dataKey="native" name="Vegetação nativa" stroke="#15803d" /></LineChart></ResponsiveContainer></div>
    <div className="mt-5 grid gap-3 md:grid-cols-2">{[{ name: 'Área urbanizada', start: start.urban_area_ha, end: latest.urban_area_ha, change: urban }, { name: 'Vegetação nativa', start: start.native_vegetation_area_ha, end: latest.native_vegetation_area_ha, change: native }].map(item => <div className="rounded-xl bg-muted/50 p-4" key={item.name}><strong>{item.name}</strong><p className="mt-2 text-sm">{(item.start / 100).toLocaleString('pt-BR')} km² em {start.year} → {(item.end / 100).toLocaleString('pt-BR')} km² em {latest.year}</p><p className="text-sm font-bold">{formatVariation(item.change.area, item.change.pct)}</p></div>)}</div>
    <div className="mt-4 grid grid-cols-3 gap-3 text-sm"><Indicator label="Agropecuária" value={latest.agriculture_livestock_area_ha} /><Indicator label="Água" value={latest.water_area_ha} /><Indicator label="Áreas úmidas" value={latest.wetland_area_ha} /></div><p className="mt-5 text-xs leading-5 text-muted-foreground">MapBiomas representa classificação de cobertura e uso da terra. Área urbanizada não equivale diretamente a superfície impermeabilizada. A série não permite afirmar causalidade com eventos, risco ou perda de vegetação.</p>
  </section>;
}
function Indicator({ label, value }: { label: string; value: number }) { return <div className="rounded bg-muted p-3"><span>{label}</span><strong className="block">{(value / 100).toLocaleString('pt-BR')} km²</strong></div>; }

import type { MunicipalityPresentation } from '@/lib/presentation-contract';

const decimal = new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 2 });
const date = new Intl.DateTimeFormat('pt-BR', { timeZone: 'UTC' });

const definitions = [
  { key: 'rain_related_event_count_10y', title: 'Registros relacionados à chuva', suffix: ' registros', change: false },
  { key: 'urban_change_20y_pct', title: 'Variação da área urbanizada em 20 anos', suffix: '%', change: true },
  { key: 'native_vegetation_change_20y_pct', title: 'Variação da vegetação nativa em 20 anos', suffix: '%', change: true },
  { key: 'urban_area_pct', title: 'Área urbanizada atual', suffix: '%', change: false },
  { key: 'native_vegetation_area_pct', title: 'Vegetação nativa atual', suffix: '%', change: false },
] as const;

function format(value: number | null, suffix: string, signed: boolean) {
  if (value === null) return 'Não comparável';
  const sign = signed && value > 0 ? '+' : '';
  return `${sign}${decimal.format(value)}${suffix}`;
}

function formatReferenceDate(value: string) {
  return date.format(new Date(`${value}T00:00:00Z`));
}

export function RegionalComparison({ benchmarks }: Pick<MunicipalityPresentation, 'benchmarks'>) {
  const region = benchmarks.immediate_region;
  return (
    <section aria-labelledby="comparacao-regional" className="elevated-card mt-5 rounded-2xl border border-border bg-card p-5 shadow-[0_12px_45px_rgb(21_42_57/8%)] sm:p-7">
      <p className="text-sm font-bold text-rain-strong">Contexto territorial</p>
      <h2 className="mt-1 font-heading text-2xl font-semibold" id="comparacao-regional">Como este município se compara à região?</h2>
      <p className="mt-2 max-w-3xl text-sm leading-6 text-muted-foreground">Comparações independentes com os municípios da Região Geográfica Imediata de {region.nome}. As sínteses regionais usam os municípios comparáveis divulgados em cada métrica.</p>
      <div className="mt-6 grid gap-4 lg:grid-cols-2 xl:grid-cols-3">
        {definitions.map(({ key, title, suffix, change }) => {
          const metric = region.metrics[key];
          const denominator = metric.denominator;
          const hasPercentile = metric.percentile_strictly_lower_pct !== null && denominator.included > 1;
          const referenceDate = key === 'rain_related_event_count_10y' ? metric.reference.reference_date : null;
          return (
            <article className="rounded-xl border border-border bg-muted/25 p-4" key={key}>
              <h3 className="font-heading text-base font-semibold">{title}</h3>
              <dl className="mt-4 grid gap-3 text-sm">
                <div><dt className="text-xs font-bold uppercase tracking-wide text-muted-foreground">Município</dt><dd className="mt-1 text-xl font-semibold tabular-nums">{format(metric.municipality_value, suffix, change)}</dd></div>
                <div className="border-t border-border pt-3"><dt className="text-xs font-bold uppercase tracking-wide text-muted-foreground">Média regional</dt><dd className="mt-1 font-semibold tabular-nums">{format(metric.mean, suffix, change)}</dd></div>
                <div><dt className="text-xs font-bold uppercase tracking-wide text-muted-foreground">Mediana regional</dt><dd className="mt-1 text-xs text-muted-foreground tabular-nums">{format(metric.median, suffix, change)}</dd></div>
              </dl>
              {hasPercentile && <p className="mt-3 text-xs leading-5 text-muted-foreground">Valor estritamente maior que {decimal.format(metric.percentile_strictly_lower_pct!)}% dos {denominator.included} municípios comparáveis.</p>}
              <p className="mt-3 border-t border-border pt-3 text-xs leading-5 text-muted-foreground">Universo: {region.municipality_count} municípios; {denominator.included} comparáveis{denominator.missing ? `, ${denominator.missing} sem cobertura` : ''}{denominator.undefined ? `, ${denominator.undefined} sem base comparável` : ''}. {typeof referenceDate === 'string' ? `Janela de 10 anos encerrada em ${formatReferenceDate(referenceDate)}.` : ''}</p>
            </article>
          );
        })}
      </div>
    </section>
  );
}

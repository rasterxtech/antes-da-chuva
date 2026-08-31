'use client';

import { useEffect, useMemo, useRef, useState } from 'react';
import ArrowRight from 'lucide-react/dist/esm/icons/arrow-right.mjs';
import CalendarDays from 'lucide-react/dist/esm/icons/calendar-days.mjs';
import CheckCircle2 from 'lucide-react/dist/esm/icons/check-circle-2.mjs';
import CircleDashed from 'lucide-react/dist/esm/icons/circle-dashed.mjs';
import CloudRain from 'lucide-react/dist/esm/icons/cloud-rain.mjs';
import ExternalLink from 'lucide-react/dist/esm/icons/external-link.mjs';
import FileSearch from 'lucide-react/dist/esm/icons/file-search.mjs';
import HandCoins from 'lucide-react/dist/esm/icons/hand-coins.mjs';
import HomeIcon from 'lucide-react/dist/esm/icons/home.mjs';
import Info from 'lucide-react/dist/esm/icons/info.mjs';
import MapPin from 'lucide-react/dist/esm/icons/map-pin.mjs';
import Search from 'lucide-react/dist/esm/icons/search.mjs';
import ShieldCheck from 'lucide-react/dist/esm/icons/shield-check.mjs';
import TriangleAlert from 'lucide-react/dist/esm/icons/triangle-alert.mjs';

import {
  Card,
  CardAction,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';

type History = {
  records: number;
  recognized: number;
  firstYear: number;
  lastYear: number;
  types: Record<string, number>;
  years: Record<string, number>;
  deaths: number;
  injured: number;
  displaced: number;
  missing: number;
};

type Transfers = {
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
};

type Municipality = {
  code: string;
  name: string;
  uf: string;
  census: {
    connectedSewerPct: number | null;
    outsideSelectedSewerPct: number | null;
    year: number;
  };
  history: History | null;
  transfers: Transfers | null;
};

const DEFAULT_MUNICIPALITY: Municipality = {
  code: '4202404',
  name: 'Blumenau',
  uf: 'SC',
  census: {
    connectedSewerPct: 67.62,
    outsideSelectedSewerPct: 32.38,
    year: 2022,
  },
  history: {
    records: 30,
    recognized: 14,
    firstYear: 1991,
    lastYear: 2025,
    types: {
      Enxurradas: 13,
      'Chuvas intensas': 9,
      Inundações: 6,
      'Movimento de massa': 2,
    },
    years: {},
    deaths: 32,
    injured: 2524,
    displaced: 155729,
    missing: 6,
  },
  transfers: {
    agreements: 2,
    firstYear: 2010,
    lastYear: 2024,
    actions: ['00T5', 'prevenção/preparação'],
    attribution: 'objeto menciona o município',
    latest: {
      number: '959786',
      year: 2024,
      status: 'Em execução',
      object:
        'Execução de obras de contenção de encostas nas margens do Rio Itajaí-Açu e Ribeirão Garcia, no município de Blumenau/SC.',
      globalValue: 1499695.06,
    },
  },
};

const UF_NAMES: Record<string, string> = {
  AC: 'Acre',
  AL: 'Alagoas',
  AM: 'Amazonas',
  AP: 'Amapá',
  BA: 'Bahia',
  CE: 'Ceará',
  DF: 'Distrito Federal',
  ES: 'Espírito Santo',
  GO: 'Goiás',
  MA: 'Maranhão',
  MG: 'Minas Gerais',
  MS: 'Mato Grosso do Sul',
  MT: 'Mato Grosso',
  PA: 'Pará',
  PB: 'Paraíba',
  PE: 'Pernambuco',
  PI: 'Piauí',
  PR: 'Paraná',
  RJ: 'Rio de Janeiro',
  RN: 'Rio Grande do Norte',
  RO: 'Rondônia',
  RR: 'Roraima',
  RS: 'Rio Grande do Sul',
  SC: 'Santa Catarina',
  SE: 'Sergipe',
  SP: 'São Paulo',
  TO: 'Tocantins',
};

const numberFormatter = new Intl.NumberFormat('pt-BR');
const percentageFormatter = new Intl.NumberFormat('pt-BR', {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});
const currencyFormatter = new Intl.NumberFormat('pt-BR', {
  style: 'currency',
  currency: 'BRL',
  maximumFractionDigits: 0,
});

function normalizeSearch(value: string) {
  return value
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLocaleLowerCase('pt-BR');
}

function Tag({
  children,
  tone = 'outline',
}: {
  children: React.ReactNode;
  tone?: 'outline' | 'secondary' | 'danger' | 'inverse';
}) {
  const tones = {
    outline: 'border-border bg-transparent text-foreground',
    secondary: 'border-transparent bg-secondary text-secondary-foreground',
    danger: 'border-transparent bg-destructive/10 text-destructive',
    inverse: 'border-white/15 bg-white/10 text-white',
  };

  return (
    <span
      className={`inline-flex min-h-5 w-fit items-center rounded-full border px-2 py-0.5 text-xs font-semibold ${tones[tone]}`}
    >
      {children}
    </span>
  );
}

function sourceLink(href: string, children: React.ReactNode) {
  return (
    <a
      className="font-semibold underline decoration-current/30 underline-offset-4 transition-colors hover:text-foreground"
      href={href}
      rel="noreferrer"
      target="_blank"
    >
      {children}
    </a>
  );
}

function HistoryCard({ history }: { history: History | null }) {
  const types = history ? Object.entries(history.types) : [];
  const maximum = Math.max(...types.map(([, count]) => count), 1);

  return (
    <Card className="border-0 bg-card shadow-[0_12px_45px_rgb(21_42_57/8%)] ring-border">
      <CardHeader className="border-b border-border/80 pb-5">
        <div className="mb-3 grid size-11 place-items-center rounded-full bg-rain-soft text-rain-strong">
          <CloudRain aria-hidden="true" className="size-5" />
        </div>
        <CardTitle className="font-heading text-2xl font-semibold">
          O que já aconteceu
        </CardTitle>
        <CardDescription>
          Registros nas cinco tipologias ligadas à chuva selecionadas para o MVP.
        </CardDescription>
        <CardAction>
          <span className="font-heading text-4xl font-semibold text-primary">
            {history ? numberFormatter.format(history.records) : '—'}
          </span>
          <span className="block text-right text-xs text-muted-foreground">
            registros
          </span>
        </CardAction>
      </CardHeader>

      {history ? (
        <CardContent className="grid gap-6 pt-1 md:grid-cols-[0.9fr_1.1fr]">
          <div>
            <div className="mb-4 flex items-center gap-2 text-sm font-semibold">
              <CalendarDays aria-hidden="true" className="size-4 text-primary" />
              Entre {history.firstYear} e {history.lastYear}
            </div>
            <div className="space-y-3">
              {types.map(([type, count]) => (
                <div className="flex items-center gap-3" key={type}>
                  <span className="w-32 truncate text-xs text-muted-foreground sm:w-36">
                    {type}
                  </span>
                  <span className="h-1.5 flex-1 overflow-hidden rounded-full bg-muted">
                    <span
                      className="block h-full rounded-full bg-rain-strong"
                      style={{ width: `${(count / maximum) * 100}%` }}
                    />
                  </span>
                  <strong className="w-7 text-right text-xs tabular-nums">
                    {numberFormatter.format(count)}
                  </strong>
                </div>
              ))}
            </div>
          </div>
          <div className="rounded-xl bg-muted/55 p-5">
            <p className="text-[11px] font-bold uppercase tracking-[0.13em] text-muted-foreground">
              Impactos humanos informados
            </p>
            <div className="mt-4 grid grid-cols-2 gap-4">
              <div>
                <strong className="font-heading text-2xl font-semibold">
                  {numberFormatter.format(history.deaths)}
                </strong>
                <span className="block text-xs text-muted-foreground">
                  mortes registradas
                </span>
              </div>
              <div>
                <strong className="font-heading text-2xl font-semibold">
                  {numberFormatter.format(history.displaced)}
                </strong>
                <span className="block text-xs text-muted-foreground">
                  desabrigados ou desalojados
                </span>
              </div>
            </div>
            <p className="mt-5 flex gap-2 border-t border-border pt-4 text-xs leading-5 text-muted-foreground">
              <Info aria-hidden="true" className="mt-0.5 size-4 shrink-0" />
              São registros municipais do S2ID. Podem existir lacunas ou
              correções posteriores.
            </p>
          </div>
        </CardContent>
      ) : (
        <CardContent className="py-8">
          <div className="rounded-xl border border-dashed border-border bg-muted/40 p-6">
            <CircleDashed aria-hidden="true" className="mb-4 size-7 text-rain-strong" />
            <h3 className="font-heading text-xl font-semibold">
              Nenhum registro encontrado no recorte
            </h3>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">
              O Atlas não retornou ocorrência para as cinco tipologias entre 1991
              e 2025. Isso não significa ausência de evento, risco ou necessidade
              de prevenção.
            </p>
          </div>
        </CardContent>
      )}

      <CardFooter className="justify-between gap-4 text-xs text-muted-foreground">
        <span>
          Fonte:{' '}
          {sourceLink(
            'https://atlasdigital.mdr.gov.br/paginas/downloads.xhtml',
            'Atlas Digital de Desastres',
          )}
        </span>
        {history && <span>{history.recognized} registros reconhecidos</span>}
      </CardFooter>
    </Card>
  );
}

function CensusCard({ municipality }: { municipality: Municipality }) {
  const percentage = municipality.census.outsideSelectedSewerPct;

  return (
    <Card className="border-0 bg-primary text-primary-foreground shadow-[0_12px_45px_rgb(21_42_57/14%)] ring-0">
      <CardHeader>
        <div className="mb-3 grid size-11 place-items-center rounded-full bg-white/10 text-white">
          <HomeIcon aria-hidden="true" className="size-5" />
        </div>
        <CardTitle className="font-heading text-2xl font-semibold text-white">
          O que pode ampliar o dano
        </CardTitle>
        <CardDescription className="text-white/65">
          Condição estrutural observada nos domicílios em 2022.
        </CardDescription>
      </CardHeader>
      <CardContent className="pt-2">
        {percentage === null ? (
          <div className="rounded-xl border border-white/10 bg-white/5 p-5">
            <TriangleAlert aria-hidden="true" className="mb-4 size-7 text-white/80" />
            <strong className="font-heading text-xl font-semibold text-white">
              Valor não publicado
            </strong>
            <p className="mt-2 text-sm leading-6 text-white/65">
              O SIDRA não apresentou percentual para esta categoria no município.
              A ausência permanece explícita em vez de virar zero.
            </p>
          </div>
        ) : (
          <>
            <div className="font-heading text-5xl font-semibold tracking-tight text-white">
              {percentageFormatter.format(percentage)}%
            </div>
            <p className="mt-3 max-w-sm text-sm leading-6 text-white/72">
              dos domicílios estavam fora da categoria “rede geral, rede pluvial
              ou fossa ligada à rede”.
            </p>
            <div className="mt-6" role="group" aria-label="Parcela observada">
              <div className="mb-3 flex items-center justify-between text-sm text-white/70">
                <span>Parcela observada</span>
                <span>{percentageFormatter.format(percentage)}%</span>
              </div>
              <div
                aria-valuemax={100}
                aria-valuemin={0}
                aria-valuenow={percentage}
                className="h-1.5 overflow-hidden rounded-full bg-white/15"
                role="progressbar"
              >
                <span
                  className="block h-full rounded-full bg-white"
                  style={{ width: `${percentage}%` }}
                />
              </div>
            </div>
          </>
        )}
        <p className="mt-6 flex gap-2 border-t border-white/10 pt-5 text-xs leading-5 text-white/58">
          <Info aria-hidden="true" className="mt-0.5 size-4 shrink-0" />
          Isso não é uma nota de risco. É uma medida direta do Censo para orientar
          perguntas sobre infraestrutura.
        </p>
      </CardContent>
      <CardFooter className="border-white/10 bg-white/5 text-white/60">
        Fonte: IBGE · Censo 2022 · Tabela 6805
      </CardFooter>
    </Card>
  );
}

function TransferCard({ transfers }: { transfers: Transfers | null }) {
  const statusIsNegative =
    transfers?.latest.status.toLocaleLowerCase('pt-BR').includes('anulad') ??
    false;

  return (
    <Card className="border-0 bg-card shadow-[0_12px_45px_rgb(21_42_57/8%)] ring-border">
      <CardHeader>
        <div className="mb-3 grid size-11 place-items-center rounded-full bg-amber-100 text-amber-800">
          <HandCoins aria-hidden="true" className="size-5" />
        </div>
        <CardTitle className="font-heading text-2xl font-semibold">
          Prevenção pública encontrada
        </CardTitle>
        <CardDescription>
          Instrumentos federais em programas selecionados cujo objeto menciona o
          município.
        </CardDescription>
      </CardHeader>
      <CardContent>
        {transfers ? (
          <>
            <div className="flex items-end justify-between gap-4 border-b border-border pb-4">
              <div>
                <strong className="font-heading text-4xl font-semibold text-primary">
                  {transfers.agreements}
                </strong>
                <span className="ml-2 text-sm text-muted-foreground">
                  {transfers.agreements === 1 ? 'instrumento' : 'instrumentos'}
                </span>
              </div>
              <span className="text-xs text-muted-foreground">
                {transfers.firstYear}–{transfers.lastYear}
              </span>
            </div>
            <div className="pt-4">
              <div className="flex flex-wrap items-center gap-2">
                <Tag tone={statusIsNegative ? 'danger' : 'secondary'}>
                  {transfers.latest.status}
                </Tag>
                <span className="text-xs text-muted-foreground">
                  mais recente · {transfers.latest.year}
                </span>
              </div>
              <p className="mt-3 line-clamp-4 text-sm leading-6">
                {transfers.latest.object}
              </p>
              {transfers.latest.globalValue !== null && (
                <p className="mt-3 text-sm">
                  <span className="text-muted-foreground">Valor global: </span>
                  <strong>
                    {currencyFormatter.format(transfers.latest.globalValue)}
                  </strong>
                </p>
              )}
            </div>
          </>
        ) : (
          <div className="rounded-xl border border-dashed border-border bg-muted/40 p-5">
            <FileSearch aria-hidden="true" className="mb-4 size-7 text-amber-700" />
            <strong className="font-heading text-lg font-semibold">
              Nenhum instrumento encontrado neste recorte
            </strong>
            <p className="mt-2 text-sm leading-6 text-muted-foreground">
              Isso não significa ausência de investimento. O recorte cobre apenas
              programas federais selecionados e objetos que citam o município.
            </p>
          </div>
        )}
      </CardContent>
      <CardFooter className="text-xs leading-5 text-muted-foreground">
        Fonte:{' '}
        {sourceLink(
          'https://dados.gov.br/dados/conjuntos-dados/transferencias-e-parcerias-da-uniao',
          'Transferegov',
        )}
        . Proposta não é sinônimo de política municipal completa.
      </CardFooter>
    </Card>
  );
}

export default function Home() {
  const [municipalities, setMunicipalities] = useState<Municipality[]>([]);
  const [selected, setSelected] = useState<Municipality>(DEFAULT_MUNICIPALITY);
  const [searchFocused, setSearchFocused] = useState(false);
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [dataError, setDataError] = useState(false);
  const searchInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    let cancelled = false;

    fetch('/data/municipios.json')
      .then((response) => {
        if (!response.ok) throw new Error('Falha ao carregar dados municipais.');
        return response.json() as Promise<Municipality[]>;
      })
      .then((data) => {
        if (cancelled) return;
        setMunicipalities(data);
        const requestedCode = new URLSearchParams(window.location.search).get(
          'municipio',
        );
        const requested = data.find((item) => item.code === requestedCode);
        const defaultFromData = data.find(
          (item) => item.code === DEFAULT_MUNICIPALITY.code,
        );
        setSelected(requested ?? defaultFromData ?? DEFAULT_MUNICIPALITY);
        setLoading(false);
      })
      .catch(() => {
        if (cancelled) return;
        setDataError(true);
        setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, []);

  const searchEntries = useMemo(
    () =>
      municipalities.map((municipality) => ({
        municipality,
        search: normalizeSearch(
          `${municipality.name} ${municipality.uf} ${municipality.code}`,
        ),
      })),
    [municipalities],
  );

  const results = useMemo(() => {
    const normalizedQuery = normalizeSearch(query.trim());
    if (normalizedQuery.length < 2) {
      const featuredCodes = new Set([
        '4202404',
        '3303906',
        '2611606',
        '3550308',
        '1302603',
        '2927408',
      ]);
      return searchEntries
        .filter(({ municipality }) => featuredCodes.has(municipality.code))
        .map(({ municipality }) => municipality);
    }
    return searchEntries
      .filter(({ search }) => search.includes(normalizedQuery))
      .slice(0, 50)
      .map(({ municipality }) => municipality);
  }, [query, searchEntries]);

  function chooseMunicipality(municipality: Municipality) {
    setSelected(municipality);
    setSearchFocused(false);
    setQuery('');
    window.history.replaceState(null, '', `?municipio=${municipality.code}`);
    window.setTimeout(() => {
      document.getElementById('resultado')?.scrollIntoView({
        behavior: 'smooth',
        block: 'start',
      });
    }, 80);
  }

  return (
    <main className="min-h-screen overflow-hidden bg-background text-foreground">
      <div className="border-b border-white/10 bg-primary text-primary-foreground">
        <div className="mx-auto flex min-h-9 max-w-7xl items-center justify-center px-4 py-2 text-center text-[11px] font-semibold uppercase tracking-[0.15em] text-white/75 sm:px-8">
          Dados públicos para agir antes da próxima chuva
        </div>
      </div>

      <header className="border-b border-border/80 bg-background/95 backdrop-blur">
        <div className="mx-auto flex h-20 max-w-7xl items-center justify-between px-4 sm:px-8">
          <a className="group flex items-center gap-3" href="#topo">
            <span className="grid size-10 place-items-center rounded-full bg-primary text-primary-foreground shadow-sm transition-transform group-hover:-translate-y-0.5">
              <CloudRain aria-hidden="true" className="size-5" />
            </span>
            <span>
              <span className="block font-heading text-xl font-semibold leading-none tracking-tight">
                Antes da Chuva
              </span>
              <span className="mt-1 block text-[10px] font-bold uppercase tracking-[0.16em] text-muted-foreground">
                Leitura pública municipal
              </span>
            </span>
          </a>
          <a
            className="hidden items-center gap-2 text-sm font-semibold text-muted-foreground transition-colors hover:text-foreground sm:flex"
            href="#metodologia"
          >
            Como lemos os dados
            <ArrowRight aria-hidden="true" className="size-4" />
          </a>
        </div>
      </header>

      <section
        className="relative border-b border-border/80 bg-[linear-gradient(135deg,var(--surface-storm)_0%,var(--surface-rain)_100%)]"
        id="topo"
      >
        <div className="weather-lines absolute inset-0 opacity-35" />
        <div className="relative mx-auto grid max-w-7xl gap-8 px-4 py-10 sm:px-8 sm:py-14 lg:grid-cols-[1.05fr_0.95fr] lg:items-end lg:py-16">
          <div className="max-w-2xl text-white">
            <div className="mb-5">
              <Tag tone="inverse">5.570 localidades disponíveis</Tag>
            </div>
            <h1 className="font-heading text-4xl font-semibold leading-[1.03] tracking-[-0.035em] text-balance sm:text-5xl lg:text-[3.7rem]">
              O que precisa ser visto antes da próxima chuva?
            </h1>
            <p className="mt-5 max-w-xl text-base leading-7 text-white/76 sm:text-lg">
              Consulte o histórico ligado à chuva, uma condição dos domicílios e
              evidências federais de prevenção — sem nota opaca e sem falsa
              previsão.
            </p>
          </div>

          <div className="relative rounded-2xl border border-white/15 bg-white p-3 shadow-[0_24px_80px_rgb(4_20_32/28%)]">
            <p className="mb-2 px-2 text-[11px] font-bold uppercase tracking-[0.14em] text-muted-foreground">
              Busque seu município
            </p>
            <div className="flex items-center gap-2">
              <div className="relative flex h-12 min-w-0 flex-1 items-center rounded-xl border border-input bg-muted/40 px-4 focus-within:border-ring focus-within:ring-3 focus-within:ring-ring/30">
                <Search aria-hidden="true" className="mr-3 size-5 shrink-0 text-primary" />
                <input
                  aria-autocomplete="list"
                  aria-controls="municipios-resultados"
                  aria-expanded={searchFocused}
                  aria-label="Busque por nome, UF ou código IBGE"
                  className="min-w-0 flex-1 bg-transparent text-base font-semibold outline-none"
                  disabled={loading && municipalities.length === 0}
                  onBlur={() =>
                    window.setTimeout(() => setSearchFocused(false), 120)
                  }
                  onChange={(event) => setQuery(event.target.value)}
                  onFocus={() => {
                    setSearchFocused(true);
                    setQuery('');
                  }}
                  onKeyDown={(event) => {
                    if (event.key === 'Escape') {
                      setSearchFocused(false);
                      searchInputRef.current?.blur();
                    }
                  }}
                  ref={searchInputRef}
                  role="combobox"
                  value={
                    searchFocused
                      ? query
                      : loading
                        ? 'Carregando localidades…'
                        : `${selected.name}, ${selected.uf}`
                  }
                />
              </div>
              <button
                className="inline-flex h-12 items-center justify-center rounded-xl bg-primary px-5 text-sm font-semibold text-primary-foreground transition-colors hover:bg-primary/85 focus-visible:outline-none focus-visible:ring-3 focus-visible:ring-ring/50 disabled:opacity-50"
                disabled={loading && municipalities.length === 0}
                onClick={() => searchInputRef.current?.focus()}
                type="button"
              >
                Consultar
              </button>
            </div>
            {searchFocused && (
              <div
                className="absolute top-[calc(100%-0.4rem)] right-3 left-3 z-50 overflow-hidden rounded-xl border border-border bg-popover text-popover-foreground shadow-[0_18px_50px_rgb(9_30_43/18%)]"
                id="municipios-resultados"
                role="listbox"
              >
                <p className="border-b border-border px-4 py-2 text-[11px] font-bold uppercase tracking-[0.12em] text-muted-foreground">
                  {query.trim().length < 2 ? 'Sugestões' : 'Resultados'}
                </p>
                <div className="max-h-72 overflow-y-auto p-1">
                  {!loading && results.length === 0 && (
                    <p className="px-4 py-6 text-center text-sm text-muted-foreground">
                      Nenhum município encontrado.
                    </p>
                  )}
                  {results.map((municipality) => (
                    <button
                      className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left text-sm transition-colors hover:bg-muted focus-visible:bg-muted focus-visible:outline-none"
                      key={municipality.code}
                      onClick={() => chooseMunicipality(municipality)}
                      onMouseDown={(event) => event.preventDefault()}
                      role="option"
                      type="button"
                    >
                      <MapPin aria-hidden="true" className="size-4 shrink-0 text-rain-strong" />
                      <span className="min-w-0 flex-1 truncate font-medium">
                        {municipality.name}, {municipality.uf}
                      </span>
                      <span className="text-xs tabular-nums text-muted-foreground">
                        {municipality.code}
                      </span>
                    </button>
                  ))}
                </div>
              </div>
            )}
            <p className="px-2 pt-2 text-xs text-muted-foreground">
              {dataError
                ? 'A lista completa não carregou; o exemplo de Blumenau continua disponível.'
                : 'Digite o nome, a UF ou o código IBGE.'}
            </p>
          </div>
        </div>
      </section>

      <section
        aria-live="polite"
        className="mx-auto max-w-7xl scroll-mt-4 px-4 py-10 sm:px-8 sm:py-14"
        id="resultado"
      >
        <div className="mb-7 flex flex-col justify-between gap-4 border-b border-border pb-6 sm:flex-row sm:items-end">
          <div>
            <div className="mb-2 flex items-center gap-2 text-sm font-bold text-primary">
              <MapPin aria-hidden="true" className="size-4" />
              {selected.name} · {UF_NAMES[selected.uf] ?? selected.uf}
            </div>
            <h2 className="font-heading text-3xl font-semibold tracking-tight sm:text-4xl">
              A cidade em uma leitura
            </h2>
          </div>
          <div className="flex flex-wrap gap-2 text-xs text-muted-foreground">
            <Tag>Atlas 1991–2025</Tag>
            <Tag>Censo 2022</Tag>
            <Tag>Transferegov</Tag>
          </div>
        </div>

        <div className="grid items-start gap-5 lg:grid-cols-[1.2fr_0.8fr]">
          <HistoryCard history={selected.history} />
          <div className="grid gap-5">
            <CensusCard municipality={selected} />
            <TransferCard transfers={selected.transfers} />
          </div>
        </div>

        <div className="mt-5 flex flex-col justify-between gap-5 rounded-2xl border border-border bg-card p-5 shadow-sm sm:flex-row sm:items-center sm:p-6">
          <div className="max-w-2xl">
            <p className="text-[11px] font-bold uppercase tracking-[0.14em] text-rain-strong">
              Próxima ação
            </p>
            <h3 className="mt-1 font-heading text-xl font-semibold">
              Há um alerta ativo agora?
            </h3>
            <p className="mt-1 text-sm leading-6 text-muted-foreground">
              O Antes da Chuva não substitui a Defesa Civil. Consulte a fonte
              oficial para alertas em andamento.
            </p>
          </div>
          <a
            className="inline-flex h-11 shrink-0 items-center justify-center gap-2 rounded-xl border border-border bg-background px-4 text-sm font-semibold transition-colors hover:bg-muted focus-visible:outline-none focus-visible:ring-3 focus-visible:ring-ring/50"
            href="https://idap.mdr.gov.br/"
            rel="noreferrer"
            target="_blank"
          >
            Ver alertas oficiais
            <ExternalLink aria-hidden="true" data-icon="inline-end" />
          </a>
        </div>
      </section>

      <section
        className="border-y border-border bg-card/60"
        id="metodologia"
      >
        <div className="mx-auto max-w-7xl px-4 py-12 sm:px-8 sm:py-16">
          <div className="max-w-2xl">
            <div className="mb-4">
              <Tag tone="secondary">Transparência por desenho</Tag>
            </div>
            <h2 className="font-heading text-3xl font-semibold tracking-tight sm:text-4xl">
              Uma leitura, não um veredito
            </h2>
            <p className="mt-4 text-base leading-7 text-muted-foreground">
              Cada bloco responde uma pergunta específica. Nenhum deles, sozinho
              ou somado, diz se uma cidade está “protegida”.
            </p>
          </div>
          <div className="mt-8 grid gap-4 md:grid-cols-3">
            {[
              {
                icon: CheckCircle2,
                title: 'Recorte explícito',
                text: 'Cinco tipologias ligadas à chuva, um indicador do Censo e programas federais selecionados.',
              },
              {
                icon: ShieldCheck,
                title: 'Ausência não é zero',
                text: 'Sem registro significa apenas que a fonte e o recorte não retornaram um resultado.',
              },
              {
                icon: FileSearch,
                title: 'Fonte ao lado do fato',
                text: 'Período, origem e limitação aparecem na mesma tela, sem esconder a metodologia.',
              },
            ].map(({ icon: Icon, title, text }) => (
              <div
                className="rounded-2xl border border-border bg-background p-5"
                key={title}
              >
                <Icon aria-hidden="true" className="mb-4 size-6 text-rain-strong" />
                <h3 className="font-heading text-lg font-semibold">{title}</h3>
                <p className="mt-2 text-sm leading-6 text-muted-foreground">
                  {text}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <footer className="bg-primary text-primary-foreground">
        <div className="mx-auto flex max-w-7xl flex-col justify-between gap-5 px-4 py-8 text-sm sm:flex-row sm:items-center sm:px-8">
          <div>
            <strong className="font-heading text-lg">Antes da Chuva</strong>
            <p className="mt-1 text-white/60">
              Inteligência pública para prevenir desastres.
            </p>
          </div>
          <p className="max-w-lg text-xs leading-5 text-white/55 sm:text-right">
            Dados públicos podem orientar decisões, mas não substituem alertas,
            laudos técnicos ou a atuação da Defesa Civil.
          </p>
        </div>
      </footer>

    </main>
  );
}

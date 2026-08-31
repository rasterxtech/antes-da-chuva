'use client';

import { useEffect, useMemo, useRef, useState } from 'react';
import Image from 'next/image';
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
import MessageCircle from 'lucide-react/dist/esm/icons/message-circle.mjs';
import Radio from 'lucide-react/dist/esm/icons/radio.mjs';
import Search from 'lucide-react/dist/esm/icons/search.mjs';
import Send from 'lucide-react/dist/esm/icons/send.mjs';
import ShieldCheck from 'lucide-react/dist/esm/icons/shield-check.mjs';
import Smartphone from 'lucide-react/dist/esm/icons/smartphone.mjs';
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

function sourceLink(href: string, children: React.ReactNode, inverse = false) {
  return (
    <a
      className={`font-bold underline decoration-current/30 underline-offset-4 transition-colors ${
        inverse ? 'hover:text-white' : 'hover:text-foreground'
      }`}
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
    <Card className="elevated-card h-full border-0 bg-card shadow-[0_12px_45px_rgb(21_42_57/8%)] ring-border">
      <CardHeader className="border-b border-border/80 pb-5">
        <div className="mb-3 grid size-11 place-items-center rounded-full bg-rain-soft text-rain-strong">
          <CloudRain aria-hidden="true" className="size-5" />
        </div>
        <CardTitle className="font-heading text-2xl font-semibold">
          O que já aconteceu
        </CardTitle>
        <CardDescription>
          Registros nas cinco tipologias ligadas à chuva selecionadas para o
          MVP.
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
        <CardContent className="grid flex-1 gap-6 pt-1">
          <div>
            <div className="mb-4 flex items-center gap-2 text-sm font-semibold">
              <CalendarDays
                aria-hidden="true"
                className="size-4 text-primary"
              />
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
            <CircleDashed
              aria-hidden="true"
              className="mb-4 size-7 text-rain-strong"
            />
            <h3 className="font-heading text-xl font-semibold">
              Nenhum registro encontrado no recorte
            </h3>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">
              O Atlas não retornou ocorrência para as cinco tipologias entre
              1991 e 2025. Isso não significa ausência de evento, risco ou
              necessidade de prevenção.
            </p>
          </div>
        </CardContent>
      )}

      <CardFooter className="flex-col items-start gap-2 text-xs leading-5 text-muted-foreground">
        <p className="w-full min-w-0">
          Fonte:{' '}
          {sourceLink(
            'https://atlasdigital.mdr.gov.br/paginas/downloads.xhtml',
            'Atlas Digital de Desastres',
          )}
        </p>
        {history && (
          <p className="w-full">
            <strong>{history.recognized}</strong> registros com reconhecimento
            federal de situação de emergência ou calamidade pública.
          </p>
        )}
      </CardFooter>
    </Card>
  );
}

function CensusCard({ municipality }: { municipality: Municipality }) {
  const percentage = municipality.census.outsideSelectedSewerPct;

  return (
    <Card className="elevated-card h-full border-0 bg-primary text-primary-foreground shadow-[0_12px_45px_rgb(21_42_57/14%)] ring-0">
      <CardHeader>
        <div className="mb-3 grid size-11 place-items-center rounded-full bg-white/10 text-white">
          <HomeIcon aria-hidden="true" className="size-5" />
        </div>
        <CardTitle className="font-heading text-2xl font-semibold text-white">
          Uma condição de saneamento
        </CardTitle>
        <CardDescription className="text-white/65">
          Retrato estrutural dos domicílios observado pelo Censo 2022.
        </CardDescription>
      </CardHeader>
      <CardContent className="flex-1 pt-2">
        {percentage === null ? (
          <div className="rounded-xl border border-white/10 bg-white/5 p-5">
            <TriangleAlert
              aria-hidden="true"
              className="mb-4 size-7 text-white/80"
            />
            <strong className="font-heading text-xl font-semibold text-white">
              Valor não publicado
            </strong>
            <p className="mt-2 text-sm leading-6 text-white/65">
              O SIDRA não apresentou percentual para esta categoria no
              município. A ausência permanece explícita em vez de virar zero.
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
          Isso não mede sozinho o risco de desastre. É uma condição de
          saneamento que ajuda a orientar perguntas sobre infraestrutura.
        </p>
      </CardContent>
      <CardFooter className="border-white/10 bg-white/5 text-white/65">
        <p>
          Fonte:{' '}
          {sourceLink(
            'https://sidra.ibge.gov.br/tabela/6805',
            'IBGE · Censo 2022 · Tabela 6805',
            true,
          )}
        </p>
      </CardFooter>
    </Card>
  );
}

function TransferCard({ transfers }: { transfers: Transfers | null }) {
  const statusIsNegative =
    transfers?.latest.status.toLocaleLowerCase('pt-BR').includes('anulad') ??
    false;

  return (
    <Card className="elevated-card h-full border-0 bg-card shadow-[0_12px_45px_rgb(21_42_57/8%)] ring-border">
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
      <CardContent className="flex-1">
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
            <FileSearch
              aria-hidden="true"
              className="mb-4 size-7 text-amber-700"
            />
            <strong className="font-heading text-lg font-semibold">
              Nenhum instrumento encontrado neste recorte
            </strong>
            <p className="mt-2 text-sm leading-6 text-muted-foreground">
              Isso não significa ausência de investimento. O recorte cobre
              apenas programas federais selecionados e objetos que citam o
              município.
            </p>
          </div>
        )}
      </CardContent>
      <CardFooter className="flex-col items-start gap-2 text-xs leading-5 text-muted-foreground">
        <p className="w-full min-w-0">
          Fonte:{' '}
          {sourceLink(
            'https://dados.gov.br/dados/conjuntos-dados/transferencias-e-parcerias-da-uniao',
            'Transferegov',
          )}
        </p>
        <p className="w-full">
          Proposta não é sinônimo de política municipal completa.
        </p>
      </CardFooter>
    </Card>
  );
}

export default function Home() {
  const [municipalities, setMunicipalities] = useState<Municipality[]>([]);
  const [selected, setSelected] = useState<Municipality>(DEFAULT_MUNICIPALITY);
  const [searchFocused, setSearchFocused] = useState(false);
  const [query, setQuery] = useState('');
  const [activeResultIndex, setActiveResultIndex] = useState(-1);
  const [loading, setLoading] = useState(true);
  const [dataError, setDataError] = useState(false);
  const searchInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    let cancelled = false;

    fetch('/data/municipios.json')
      .then((response) => {
        if (!response.ok)
          throw new Error('Falha ao carregar dados municipais.');
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
    searchInputRef.current?.blur();
    setSelected(municipality);
    setSearchFocused(false);
    setQuery('');
    setActiveResultIndex(-1);
    window.history.replaceState(null, '', `?municipio=${municipality.code}`);
    window.setTimeout(() => {
      document.getElementById('resultado')?.scrollIntoView({
        behavior: 'smooth',
        block: 'start',
      });
    }, 80);
  }

  return (
    <main className="page-ambient min-h-screen overflow-x-hidden bg-background text-foreground">
      <div className="border-b border-white/10 bg-primary text-primary-foreground">
        <div className="mx-auto flex min-h-10 max-w-7xl items-center justify-between gap-4 px-4 py-2 text-[11px] font-bold uppercase tracking-[0.12em] text-white/75 sm:px-8">
          <span>Dados públicos para agir antes da próxima chuva</span>
          <span className="hidden items-center gap-5 text-white/55 sm:flex">
            <span>Atualizado em 30.08.2026</span>
          </span>
        </div>
      </div>

      <header className="sticky top-0 z-40 border-b border-border/80 bg-background/88 shadow-[0_8px_30px_rgb(17_47_62/5%)] backdrop-blur-xl">
        <div className="mx-auto flex min-h-20 max-w-7xl items-center justify-between gap-6 px-4 py-3 sm:px-8">
          <a className="group flex items-center gap-3" href="#topo">
            <span className="grid size-11 place-items-center rounded-full bg-primary text-primary-foreground shadow-sm transition-transform group-hover:-translate-y-0.5">
              <CloudRain aria-hidden="true" className="size-5" />
            </span>
            <span>
              <span className="block font-heading text-[1.35rem] font-semibold leading-none tracking-tight">
                Antes da Chuva
              </span>
              <span className="mt-1.5 block text-[10px] font-bold uppercase tracking-[0.14em] text-muted-foreground">
                Inteligência pública municipal
              </span>
            </span>
          </a>
          <nav
            aria-label="Navegação principal"
            className="hidden items-center gap-7 text-sm font-bold text-muted-foreground lg:flex"
          >
            <a
              className="transition-colors hover:text-foreground"
              href="#resultado"
            >
              Leitura municipal
            </a>
            <a
              className="transition-colors hover:text-foreground"
              href="#alertas"
            >
              Alertas oficiais
            </a>
            <a
              className="transition-colors hover:text-foreground"
              href="#metodologia"
            >
              Metodologia
            </a>
            <a
              className="transition-colors hover:text-foreground"
              href="#fontes"
            >
              Fontes
            </a>
          </nav>
        </div>
      </header>

      <section
        className="relative z-20 border-b border-border/80 bg-[linear-gradient(135deg,var(--surface-storm)_0%,var(--surface-rain)_100%)]"
        id="topo"
      >
        <div className="weather-lines absolute inset-0 opacity-35" />
        <div className="soft-grid absolute inset-0 opacity-30" />
        <div className="relative mx-auto grid max-w-7xl gap-8 px-4 py-10 sm:px-8 sm:py-14 lg:grid-cols-12 lg:items-center lg:gap-12 lg:py-16">
          <div className="min-w-0 text-white lg:col-span-7">
            <div className="mb-5 flex flex-wrap gap-2">
              <Tag tone="inverse">5.570 localidades disponíveis</Tag>
              <Tag tone="inverse">Leitura em menos de 1 minuto</Tag>
            </div>
            <h1 className="max-w-3xl font-heading text-4xl font-semibold leading-[1.03] tracking-[-0.035em] text-balance sm:text-5xl lg:text-[3.75rem]">
              O que precisa ser visto antes da próxima chuva?
            </h1>
            <p className="mt-5 max-w-2xl text-base leading-7 text-white/78 sm:text-lg">
              Em uma única leitura, veja o histórico de ocorrências ligadas à
              chuva, uma condição de saneamento e evidências federais de
              prevenção — com recorte e limitações à vista.
            </p>

            <div className="relative mt-8 min-w-0 rounded-2xl border border-white/15 bg-white p-3 text-foreground shadow-[0_24px_80px_rgb(4_20_32/28%)] sm:p-4">
              <p className="mb-2 px-2 text-[11px] font-bold uppercase tracking-[0.14em] text-muted-foreground">
                Busque seu município
              </p>
              <div className="grid min-w-0 gap-2 sm:grid-cols-[minmax(0,1fr)_auto]">
                <div className="relative flex h-12 min-w-0 items-center rounded-xl border border-input bg-muted/40 px-3 focus-within:border-ring focus-within:ring-3 focus-within:ring-ring/30 sm:px-4">
                  <Search
                    aria-hidden="true"
                    className="mr-3 size-5 shrink-0 text-primary"
                  />
                  <input
                    aria-activedescendant={
                      activeResultIndex >= 0 && results[activeResultIndex]
                        ? `municipio-option-${results[activeResultIndex].code}`
                        : undefined
                    }
                    aria-autocomplete="list"
                    aria-controls="municipios-resultados"
                    aria-expanded={searchFocused}
                    aria-label="Busque por nome, UF ou código IBGE"
                    className="min-w-0 flex-1 bg-transparent text-base font-bold outline-none"
                    disabled={loading && municipalities.length === 0}
                    onBlur={() =>
                      window.setTimeout(() => setSearchFocused(false), 120)
                    }
                    onChange={(event) => {
                      setQuery(event.target.value);
                      setActiveResultIndex(0);
                    }}
                    onFocus={() => {
                      setSearchFocused(true);
                      setQuery('');
                      setActiveResultIndex(0);
                    }}
                    onKeyDown={(event) => {
                      if (event.key === 'ArrowDown' && results.length > 0) {
                        event.preventDefault();
                        setActiveResultIndex((current) =>
                          current >= results.length - 1 ? 0 : current + 1,
                        );
                      }
                      if (event.key === 'ArrowUp' && results.length > 0) {
                        event.preventDefault();
                        setActiveResultIndex((current) =>
                          current <= 0 ? results.length - 1 : current - 1,
                        );
                      }
                      if (
                        event.key === 'Enter' &&
                        activeResultIndex >= 0 &&
                        results[activeResultIndex]
                      ) {
                        event.preventDefault();
                        chooseMunicipality(results[activeResultIndex]);
                      }
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
                  className="inline-flex h-12 w-full items-center justify-center rounded-xl bg-primary px-5 text-sm font-bold text-primary-foreground transition-colors hover:bg-primary/85 focus-visible:outline-none focus-visible:ring-3 focus-visible:ring-ring/50 disabled:opacity-50 sm:w-auto"
                  disabled={loading && municipalities.length === 0}
                  onClick={() => {
                    setSearchFocused(true);
                    setQuery('');
                    setActiveResultIndex(0);
                    searchInputRef.current?.focus();
                  }}
                  onMouseDown={(event) => event.preventDefault()}
                  type="button"
                >
                  Consultar
                </button>
              </div>
              {searchFocused && (
                <div
                  className="absolute top-[calc(100%-0.4rem)] right-3 left-3 z-50 overflow-hidden rounded-xl border border-border bg-popover text-popover-foreground shadow-[0_18px_50px_rgb(9_30_43/18%)] sm:right-4 sm:left-4"
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
                    {results.map((municipality, index) => (
                      <button
                        aria-selected={activeResultIndex === index}
                        className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left text-sm transition-colors hover:bg-muted focus-visible:bg-muted focus-visible:outline-none aria-selected:bg-muted"
                        id={`municipio-option-${municipality.code}`}
                        key={municipality.code}
                        onClick={() => chooseMunicipality(municipality)}
                        onMouseDown={(event) => event.preventDefault()}
                        onMouseEnter={() => setActiveResultIndex(index)}
                        role="option"
                        type="button"
                      >
                        <MapPin
                          aria-hidden="true"
                          className="size-4 shrink-0 text-rain-strong"
                        />
                        <span className="min-w-0 flex-1 truncate font-bold">
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
                  : 'Digite nome, UF ou código IBGE. Use as setas e Enter para selecionar.'}
              </p>
            </div>
          </div>

          <figure className="hero-map-frame relative min-h-[300px] overflow-hidden rounded-[1.75rem] border border-white/20 bg-white/10 shadow-2xl sm:min-h-[380px] lg:col-span-5 lg:min-h-[560px]">
            <Image
              alt="Ilustração de um território visto do alto, com rios, áreas urbanas e nuvens de chuva"
              className="hero-map-image object-cover"
              fill
              priority
              sizes="(max-width: 1024px) 100vw, 40vw"
              src="/hero-map.webp"
            />
            <figcaption className="absolute right-4 bottom-4 left-4 rounded-2xl border border-white/20 bg-primary/82 p-4 text-white shadow-lg backdrop-blur-md sm:p-5">
              <p className="text-[10px] font-bold uppercase tracking-[0.16em] text-white/60">
                Dados conectados ao território
              </p>
              <p className="mt-2 max-w-sm font-heading text-lg font-semibold leading-snug sm:text-xl">
                Evidências públicas para priorizar perguntas antes da crise.
              </p>
            </figcaption>
          </figure>
        </div>
      </section>

      <section
        aria-live="polite"
        className="relative z-0 mx-auto max-w-7xl scroll-mt-4 px-4 py-10 sm:px-8 sm:py-14"
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

        <div className="grid items-stretch gap-5 lg:grid-cols-3">
          <HistoryCard history={selected.history} />
          <CensusCard municipality={selected} />
          <TransferCard transfers={selected.transfers} />
        </div>

        <div className="elevated-card mt-5 flex flex-col justify-between gap-5 rounded-2xl border border-border bg-card p-5 shadow-sm sm:flex-row sm:items-center sm:p-6">
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
            href="#alertas"
          >
            Como receber alertas
            <ArrowRight aria-hidden="true" data-icon="inline-end" />
          </a>
        </div>
      </section>

      <section
        className="relative overflow-hidden border-y border-border bg-[linear-gradient(145deg,var(--surface-storm)_0%,#19495f_100%)] text-white"
        id="alertas"
      >
        <div className="weather-lines absolute inset-0 opacity-30" />
        <div className="soft-grid absolute inset-0 opacity-20" />
        <div className="relative mx-auto max-w-7xl px-4 py-12 sm:px-8 sm:py-16">
          <div className="grid gap-6 lg:grid-cols-[1fr_0.85fr] lg:items-end">
            <div>
              <div className="mb-4">
                <Tag tone="inverse">Serviço oficial e gratuito</Tag>
              </div>
              <h2 className="max-w-3xl font-heading text-3xl font-semibold tracking-tight text-balance sm:text-4xl">
                Receba os alertas da Defesa Civil no canal que funciona para
                você
              </h2>
            </div>
            <p className="max-w-2xl text-base leading-7 text-white/70 lg:justify-self-end">
              Os canais abaixo são mantidos ou indicados pela Defesa Civil
              Nacional. O Antes da Chuva ajuda você a encontrá-los, mas não
              emite nem substitui alertas oficiais.
            </p>
          </div>

          <div className="mt-8 grid items-stretch gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {[
              {
                icon: MessageCircle,
                eyebrow: 'Com cadastro',
                title: 'WhatsApp',
                text: 'Envie “Olá”, aceite os termos e cadastre um ou mais municípios, CEPs ou localidades de interesse.',
                detail: '(61) 2034-4611',
                href: 'https://wa.me/556120344611',
                action: 'Abrir WhatsApp',
                external: true,
              },
              {
                icon: Send,
                eyebrow: 'Com cadastro',
                title: 'Telegram',
                text: 'Inicie o robô Defesa Civil Alertas e escolha as áreas que deseja acompanhar.',
                detail: '@defesacivilbrbot',
                href: 'https://t.me/defesacivilbrbot',
                action: 'Abrir Telegram',
                external: true,
              },
              {
                icon: Smartphone,
                eyebrow: 'Com cadastro',
                title: 'SMS 40199',
                text: 'Envie somente o CEP da área que deseja acompanhar. É possível cadastrar mais de um CEP.',
                detail: 'Envie seu CEP para 40199',
                href: 'sms:40199',
                action: 'Preparar SMS',
                external: false,
              },
              {
                icon: Radio,
                eyebrow: 'Sem cadastro',
                title: 'Defesa Civil Alerta',
                text: 'Alertas críticos aparecem automaticamente em celulares compatíveis conectados às redes 4G ou 5G na área de risco.',
                detail: 'Transmissão pela rede móvel',
                href: 'https://www.gov.br/mdr/pt-br/assuntos/protecao-e-defesa-civil/defesa-civil-alerta',
                action: 'Entender como funciona',
                external: true,
              },
            ].map((channel) => {
              const Icon = channel.icon;

              return (
                <article
                  className="elevated-card flex h-full flex-col rounded-2xl border border-white/14 bg-white/9 p-5 shadow-[0_18px_45px_rgb(2_18_29/18%)] backdrop-blur-sm sm:p-6"
                  key={channel.title}
                >
                  <div className="flex items-start justify-between gap-4">
                    <span className="grid size-11 place-items-center rounded-full bg-white/12 text-white ring-1 ring-white/15">
                      <Icon aria-hidden="true" className="size-5" />
                    </span>
                    <span className="rounded-full border border-white/15 bg-white/8 px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.12em] text-white/65">
                      {channel.eyebrow}
                    </span>
                  </div>
                  <h3 className="mt-5 font-heading text-2xl font-semibold">
                    {channel.title}
                  </h3>
                  <p className="mt-3 flex-1 text-sm leading-6 text-white/68">
                    {channel.text}
                  </p>
                  <p className="mt-5 border-t border-white/12 pt-4 text-xs font-bold text-white/85">
                    {channel.detail}
                  </p>
                  <a
                    className="mt-4 inline-flex min-h-11 items-center justify-center gap-2 rounded-xl bg-white px-4 text-sm font-bold text-primary transition-colors hover:bg-white/88 focus-visible:outline-none focus-visible:ring-3 focus-visible:ring-white/40"
                    href={channel.href}
                    rel={channel.external ? 'noreferrer' : undefined}
                    target={channel.external ? '_blank' : undefined}
                  >
                    {channel.action}
                    {channel.external ? (
                      <ExternalLink aria-hidden="true" className="size-4" />
                    ) : (
                      <ArrowRight aria-hidden="true" className="size-4" />
                    )}
                  </a>
                </article>
              );
            })}
          </div>

          <div className="mt-6 flex flex-col justify-between gap-4 rounded-2xl border border-white/14 bg-black/10 p-5 sm:flex-row sm:items-center">
            <p className="max-w-3xl text-sm leading-6 text-white/68">
              Em uma emergência, siga as instruções recebidas pelos canais
              oficiais e as orientações da Defesa Civil do seu município.
            </p>
            <a
              className="inline-flex shrink-0 items-center gap-2 text-sm font-bold text-white underline decoration-white/30 underline-offset-4 transition-colors hover:text-white/80"
              href="https://www.gov.br/mdr/pt-br/assuntos/protecao-e-defesa-civil/alertas-de-desastres-1"
              rel="noreferrer"
              target="_blank"
            >
              Conferir orientações oficiais
              <ExternalLink aria-hidden="true" className="size-4" />
            </a>
          </div>
        </div>
      </section>

      <section className="border-y border-border bg-card/60" id="metodologia">
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
                className="elevated-card h-full rounded-2xl border border-border bg-background p-5"
                key={title}
              >
                <Icon
                  aria-hidden="true"
                  className="mb-4 size-6 text-rain-strong"
                />
                <h3 className="font-heading text-lg font-semibold">{title}</h3>
                <p className="mt-2 text-sm leading-6 text-muted-foreground">
                  {text}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section
        className="relative overflow-hidden border-b border-border bg-background"
        id="fontes"
      >
        <div className="rain-divider absolute inset-x-0 top-0 h-px" />
        <div className="mx-auto max-w-7xl px-4 py-12 sm:px-8 sm:py-16">
          <div className="grid gap-6 lg:grid-cols-[0.8fr_1.2fr] lg:items-end">
            <div>
              <div className="mb-4">
                <Tag>Fontes verificáveis</Tag>
              </div>
              <h2 className="font-heading text-3xl font-semibold tracking-tight sm:text-4xl">
                O dado termina em uma fonte, não em uma promessa
              </h2>
            </div>
            <p className="max-w-2xl text-base leading-7 text-muted-foreground lg:justify-self-end">
              A leitura reúne bases públicas com períodos e coberturas
              diferentes. Por isso, cada evidência mantém sua origem e seu
              limite visíveis.
            </p>
          </div>

          <div className="mt-8 grid items-stretch gap-4 md:grid-cols-3">
            {[
              {
                label: 'Histórico',
                title: 'Atlas Digital de Desastres no Brasil',
                text: 'Registros municipais das cinco tipologias relacionadas à chuva, entre 1991 e 2025.',
                href: 'https://atlasdigital.mdr.gov.br/paginas/downloads.xhtml',
                action: 'Consultar Atlas',
              },
              {
                label: 'Saneamento',
                title: 'Censo Demográfico 2022 · IBGE',
                text: 'Condição de esgotamento sanitário dos domicílios, a partir da tabela 6805 do SIDRA.',
                href: 'https://sidra.ibge.gov.br/tabela/6805',
                action: 'Consultar SIDRA',
              },
              {
                label: 'Prevenção federal',
                title: 'Transferências e Parcerias da União',
                text: 'Convênios selecionados por ação e objeto, com atribuição municipal explicitada na tela.',
                href: 'https://dados.gov.br/dados/conjuntos-dados/transferencias-e-parcerias-da-uniao',
                action: 'Consultar dados.gov.br',
              },
            ].map((source) => (
              <article
                className="elevated-card flex h-full flex-col rounded-2xl border border-border bg-card p-5 shadow-sm sm:p-6"
                key={source.title}
              >
                <p className="text-[11px] font-bold uppercase tracking-[0.14em] text-rain-strong">
                  {source.label}
                </p>
                <h3 className="mt-3 font-heading text-xl font-semibold leading-snug">
                  {source.title}
                </h3>
                <p className="mt-3 flex-1 text-sm leading-6 text-muted-foreground">
                  {source.text}
                </p>
                <a
                  className="mt-6 inline-flex items-center gap-2 text-sm font-bold text-primary transition-colors hover:text-rain-strong focus-visible:outline-none focus-visible:ring-3 focus-visible:ring-ring/40"
                  href={source.href}
                  rel="noreferrer"
                  target="_blank"
                >
                  {source.action}
                  <ArrowRight aria-hidden="true" className="size-4" />
                </a>
              </article>
            ))}
          </div>
        </div>
      </section>

      <footer className="relative overflow-hidden bg-primary text-primary-foreground">
        <div className="soft-grid absolute inset-0 opacity-20" />
        <div className="relative mx-auto grid max-w-7xl gap-10 px-4 py-12 text-sm sm:px-8 lg:grid-cols-[1.35fr_0.75fr_1fr_1.25fr] lg:py-14">
          <div>
            <a className="group inline-flex items-center gap-3" href="#topo">
              <span className="grid size-11 place-items-center rounded-full bg-white/10 text-white ring-1 ring-white/15 transition-transform group-hover:-translate-y-0.5">
                <CloudRain aria-hidden="true" className="size-5" />
              </span>
              <span className="font-heading text-xl font-semibold">
                Antes da Chuva
              </span>
            </a>
            <p className="mt-4 max-w-sm leading-6 text-white/62">
              Inteligência pública municipal para transformar bases abertas em
              perguntas melhores antes da próxima crise.
            </p>
            <p className="mt-4 text-xs font-bold uppercase tracking-[0.12em] text-white/40">
              Projeto independente · Concurso CGU 2026
            </p>
          </div>

          <div>
            <h2 className="text-xs font-bold uppercase tracking-[0.14em] text-white/45">
              Navegue
            </h2>
            <nav
              aria-label="Navegação do rodapé"
              className="mt-4 grid gap-3 font-bold text-white/72"
            >
              <a
                className="transition-colors hover:text-white"
                href="#resultado"
              >
                Leitura municipal
              </a>
              <a
                className="transition-colors hover:text-white"
                href="#metodologia"
              >
                Metodologia
              </a>
              <a className="transition-colors hover:text-white" href="#alertas">
                Alertas oficiais
              </a>
              <a className="transition-colors hover:text-white" href="#fontes">
                Fontes
              </a>
            </nav>
          </div>

          <div>
            <h2 className="text-xs font-bold uppercase tracking-[0.14em] text-white/45">
              Bases oficiais
            </h2>
            <div className="mt-4 grid gap-3 text-white/72">
              {sourceLink(
                'https://atlasdigital.mdr.gov.br/paginas/downloads.xhtml',
                'Atlas de Desastres',
                true,
              )}
              {sourceLink(
                'https://sidra.ibge.gov.br/tabela/6805',
                'Censo 2022 · IBGE',
                true,
              )}
              {sourceLink(
                'https://dados.gov.br/dados/conjuntos-dados/transferencias-e-parcerias-da-uniao',
                'Transferegov',
                true,
              )}
              {sourceLink(
                'https://www.gov.br/mdr/pt-br/assuntos/protecao-e-defesa-civil/alertas-de-desastres-1',
                'Alertas da Defesa Civil',
                true,
              )}
            </div>
          </div>

          <div>
            <h2 className="text-xs font-bold uppercase tracking-[0.14em] text-white/45">
              Transparência
            </h2>
            <ul className="mt-4 grid gap-3 leading-5 text-white/62">
              <li>Atualização da leitura: 30 de agosto de 2026.</li>
              <li>Código IBGE é a chave de integração municipal.</li>
              <li>
                Ausência de registro não significa ausência de ação ou risco.
              </li>
            </ul>
          </div>
        </div>

        <div className="relative border-t border-white/10">
          <div className="mx-auto flex max-w-7xl flex-col justify-between gap-3 px-4 py-5 text-xs leading-5 text-white/48 sm:px-8 md:flex-row md:items-center">
            <p>© 2026 Antes da Chuva. Dados públicos, leitura responsável.</p>
            <p className="max-w-2xl md:text-right">
              Não substitui alertas, laudos técnicos nem a atuação da Defesa
              Civil.
            </p>
          </div>
        </div>
      </footer>
    </main>
  );
}

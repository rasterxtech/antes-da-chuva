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
import MapIcon from 'lucide-react/dist/esm/icons/map.mjs';
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
import {
  fetchJson,
  inactiveTransferStatus,
  isMunicipalIndex,
  isMunicipalShard,
  isPresentationMetadata,
  requestedCodigoIbge,
} from '@/lib/presentation-data';
import type {
  MunicipalIndexEntry,
  MunicipalityPresentation,
  PresentationMetadata,
  PresentationState,
} from '@/lib/presentation-contract';
import { DisasterHistory } from '@/components/presentation/disaster-history';
import { TypesAndMonths } from '@/components/presentation/types-and-months';
import { LandCoverHistory } from '@/components/presentation/land-cover-history';
import { RegionalComparison } from '@/components/presentation/regional-comparison';

const numberFormatter = new Intl.NumberFormat('pt-BR');
const hectareFormatter = new Intl.NumberFormat('pt-BR', {
  maximumFractionDigits: 2,
});
const percentageFormatter = new Intl.NumberFormat('pt-BR', {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});
const currencyFormatter = new Intl.NumberFormat('pt-BR', {
  style: 'currency',
  currency: 'BRL',
  maximumFractionDigits: 0,
});
const dateFormatter = new Intl.DateTimeFormat('pt-BR', {
  day: '2-digit',
  month: 'long',
  year: 'numeric',
});

function normalizeSearch(value: string) {
  return value
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLocaleLowerCase('pt-BR');
}

function formatPublicationDate(value: string | null | undefined) {
  if (!value) return 'data não informada';
  const date = new Date(value.length === 10 ? `${value}T12:00:00Z` : value);
  return Number.isNaN(date.getTime()) ? value : dateFormatter.format(date);
}

function sourceStateLabel(source: string, state: PresentationState) {
  const labels: Record<PresentationState, string> = {
    record: 'registro disponível',
    no_record: 'sem registro no recorte',
    no_coverage: 'sem cobertura',
    not_published: 'não publicado',
    not_in_legacy_universe: 'fora do universo temporal',
  };
  return `${source}: ${labels[state]}`;
}

function sourceAbsenceCopy(source: 'census' | 'transfers', state: PresentationState) {
  if (state === 'not_in_legacy_universe') {
    return source === 'census'
      ? 'O município atual não existe no universo temporal do indicador censitário publicado.'
      : 'O município atual não existe no universo temporal do recorte publicado de transferências.';
  }
  if (state === 'not_published') {
    return 'O indicador existe na fonte, mas não foi publicado para este município.';
  }
  if (state === 'no_coverage') {
    return 'A fonte não cobre esta unidade territorial. Isso não é um valor zero.';
  }
  return source === 'census'
    ? 'Não há valor disponível nesta fonte para o município. A ausência não foi convertida em zero.'
    : 'Nenhum instrumento foi encontrado no recorte publicado. Isso não prova ausência de investimento.';
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
      className={`inline-flex min-h-8 w-fit items-center rounded-full border px-3 py-1.5 text-sm font-bold leading-none ${tones[tone]}`}
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
      <span className="sr-only"> (abre em uma nova aba)</span>
    </a>
  );
}

function ThirtySecondSummary({
  municipality,
  summary,
  disasters,
  landCover,
  metadata,
}: {
  municipality: MunicipalityPresentation['municipality'];
  summary: MunicipalityPresentation['summary'];
  disasters: MunicipalityPresentation['disasters'];
  landCover: MunicipalityPresentation['land_cover'];
  metadata: PresentationMetadata | null;
}) {
  const history = disasters.history;
  const change = landCover.change;
  const hasAtlas = disasters.state === 'record';
  const hasMapBiomas = landCover.state === 'record';
  const firstYear = landCover.history[0]?.year;
  const latestYear = landCover.history.at(-1)?.year;
  const atlasPeriod = metadata
    ? `${metadata.sources.atlas.first_year}–${metadata.sources.atlas.latest_year}`
    : 'período não informado';
  const mapBiomasPeriod = firstYear && latestYear ? `${firstYear}–${latestYear}` : null;

  return (
    <section
      aria-labelledby="resumo-30-segundos"
      className="elevated-card mb-7 overflow-hidden rounded-2xl border border-border bg-card shadow-[0_12px_45px_rgb(21_42_57/8%)]"
    >
      <div className="border-b border-border bg-[linear-gradient(135deg,var(--surface-storm)_0%,var(--surface-rain)_100%)] px-5 py-6 text-white sm:px-7">
        <p className="text-sm font-bold uppercase tracking-[0.14em] text-white/70">
          Resumo de 30 segundos
        </p>
        <h2
          className="mt-2 font-heading text-3xl font-semibold tracking-tight sm:text-4xl"
          id="resumo-30-segundos"
        >
          {municipality.municipio.toLocaleUpperCase('pt-BR')} / {municipality.uf}
        </h2>
        <p className="mt-2 text-sm font-semibold text-white/78 sm:text-base">
          Região Geográfica Imediata de {municipality.regiao_imediata}
        </p>
      </div>
      <div className="p-5 sm:p-7">
        <p className="max-w-4xl text-base leading-7 text-muted-foreground sm:text-lg">
          {summary.thirty_second_text}
        </p>
        <dl className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <div className="rounded-xl bg-rain-soft p-4">
            <dt className="text-xs font-bold uppercase tracking-wide text-muted-foreground">
              Registros relacionados à chuva
            </dt>
            <dd className="mt-2 font-heading text-2xl font-semibold text-primary">
              {hasAtlas ? numberFormatter.format(history.rain_related_event_count) : 'Sem registro'}
            </dd>
          </div>
          <div className="rounded-xl bg-muted/55 p-4">
            <dt className="text-xs font-bold uppercase tracking-wide text-muted-foreground">
              Último registro
            </dt>
            <dd className="mt-2 font-heading text-2xl font-semibold">
              {hasAtlas ? history.latest_event_date?.slice(0, 4) : 'Não disponível'}
            </dd>
          </div>
          {hasMapBiomas && (
            <>
              <div className="rounded-xl bg-emerald-50 p-4">
                <dt className="text-xs font-bold uppercase tracking-wide text-muted-foreground">
                  Área urbanizada
                </dt>
                <dd className="mt-2 font-heading text-2xl font-semibold text-emerald-900">
                  {formatSignedPercentage(change?.urban_area_change_pct) ?? 'Não publicada'}
                </dd>
                {mapBiomasPeriod && <span className="text-xs text-muted-foreground">desde {firstYear}</span>}
              </div>
              <div className="rounded-xl bg-emerald-50 p-4">
                <dt className="text-xs font-bold uppercase tracking-wide text-muted-foreground">
                  Vegetação nativa
                </dt>
                <dd className="mt-2 font-heading text-2xl font-semibold text-emerald-900">
                  {formatSignedPercentage(change?.native_vegetation_change_pct) ?? 'Não publicada'}
                </dd>
                {mapBiomasPeriod && <span className="text-xs text-muted-foreground">desde {firstYear}</span>}
              </div>
            </>
          )}
        </dl>
      </div>
      <div className="flex flex-col gap-2 border-t border-border px-5 py-4 text-xs leading-5 text-muted-foreground sm:flex-row sm:flex-wrap sm:gap-x-5 sm:px-7">
        <span>Atlas/S2ID: {atlasPeriod}</span>
        <span>
          MapBiomas: {mapBiomasPeriod ?? 'sem cobertura publicada para este município'}
        </span>
      </div>
    </section>
  );
}

export function HistoryCard({
  disasters,
  metadata,
}: {
  disasters: MunicipalityPresentation['disasters'];
  metadata: PresentationMetadata | null;
}) {
  const history = disasters.history;
  const types = disasters.types;
  const maximum = Math.max(...types.map((type) => Number(type.event_count)), 1);
  const hasRecord = disasters.state === 'record';

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
            {hasRecord
              ? numberFormatter.format(history.rain_related_event_count)
              : 'Sem registro'}
          </span>
          <span className="block text-right text-xs text-muted-foreground">
            {hasRecord ? 'registros' : 'no recorte'}
          </span>
        </CardAction>
      </CardHeader>

      {hasRecord ? (
        <CardContent className="grid flex-1 gap-6 pt-1">
          <div>
            <div className="mb-4 flex items-center gap-2 text-sm font-semibold">
              <CalendarDays
                aria-hidden="true"
                className="size-4 text-primary"
              />
              Entre {history.first_event_date?.slice(0, 4)} e{' '}
              {history.latest_event_date?.slice(0, 4)}
            </div>
            <div className="space-y-3">
              {types.map((type) => (
                <div
                  className="flex items-center gap-3"
                  key={`${type.atlas_type_id}-${type.type_name}`}
                >
                  <span className="w-32 truncate text-xs text-muted-foreground sm:w-36">
                    {type.type_name}
                  </span>
                  <span className="h-1.5 flex-1 overflow-hidden rounded-full bg-muted">
                    <span
                      className="block h-full rounded-full bg-rain-strong"
                      style={{
                        width: `${(Number(type.event_count) / maximum) * 100}%`,
                      }}
                    />
                  </span>
                  <strong className="w-7 text-right text-xs tabular-nums">
                    {numberFormatter.format(Number(type.event_count))}
                  </strong>
                </div>
              ))}
            </div>
          </div>
          <div className="rounded-xl bg-muted/55 p-5">
            <p className="text-sm font-bold text-muted-foreground">
              Impactos humanos informados
            </p>
            <div className="mt-4 grid grid-cols-2 gap-4">
              <div>
                <strong className="font-heading text-2xl font-semibold">
                  {numberFormatter.format(history.human_impacts.deaths)}
                </strong>
                <span className="block text-xs text-muted-foreground">
                  mortes registradas
                </span>
              </div>
              <div>
                <strong className="font-heading text-2xl font-semibold">
                  {numberFormatter.format(history.human_impacts.displaced)}
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
              O Atlas não retornou ocorrência para as cinco tipologias no
              recorte publicado. Isso não significa ausência de evento, risco
              ou necessidade de prevenção.
            </p>
          </div>
        </CardContent>
      )}

      <CardFooter className="flex-col items-start gap-2 text-xs leading-5 text-muted-foreground">
        <p className="w-full min-w-0">
          Fonte:{' '}
          {sourceLink(
            'https://atlasdigital.mdr.gov.br/paginas/downloads.xhtml',
            metadata
              ? `Atlas Digital de Desastres · ${metadata.sources.atlas.release}`
              : 'Atlas Digital de Desastres · metadados indisponíveis',
          )}
        </p>
        {hasRecord && (
          <p className="w-full">
            <strong>{numberFormatter.format(history.recognized_event_count)}</strong>{' '}
            registros com reconhecimento federal de situação de emergência ou
            calamidade pública.
          </p>
        )}
      </CardFooter>
    </Card>
  );
}

function CensusCard({
  census,
  metadata,
}: {
  census: MunicipalityPresentation['census'];
  metadata: PresentationMetadata | null;
}) {
  const percentage = census.outside_selected_sewer_pct;
  const hasRecord = census.state === 'record' && percentage !== null;

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
          Retrato estrutural dos domicílios observado na fonte publicada.
        </CardDescription>
      </CardHeader>
      <CardContent className="flex-1 pt-2">
        {!hasRecord ? (
          <div className="rounded-xl border border-white/10 bg-white/5 p-5">
            <TriangleAlert
              aria-hidden="true"
              className="mb-4 size-7 text-white/80"
            />
            <strong className="font-heading text-xl font-semibold text-white">
              {census.state === 'not_published'
                ? 'Valor não publicado'
                : 'Sem dado para este município'}
            </strong>
            <p className="mt-2 text-sm leading-6 text-white/65">
              {sourceAbsenceCopy('census', census.state)}
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
            metadata?.sources.census.reference ?? 'IBGE · metadados indisponíveis',
            true,
          )}
        </p>
      </CardFooter>
    </Card>
  );
}

function TransferCard({
  transfers,
  metadata,
}: {
  transfers: MunicipalityPresentation['transfers'];
  metadata: PresentationMetadata | null;
}) {
  const record = transfers.legacy;
  const statusIsNegative = record
    ? inactiveTransferStatus(record.latest.status)
    : false;

  return (
    <Card className="elevated-card h-full border-0 bg-card shadow-[0_12px_45px_rgb(21_42_57/8%)] ring-border">
      <CardHeader>
        <div className="mb-3 grid size-11 place-items-center rounded-full bg-amber-100 text-amber-800">
          <HandCoins aria-hidden="true" className="size-5" />
        </div>
        <CardTitle className="font-heading text-2xl font-semibold">
          Instrumentos federais encontrados
        </CardTitle>
        <CardDescription>
          Instrumentos federais em programas selecionados cujo objeto menciona o
          município.
        </CardDescription>
      </CardHeader>
      <CardContent className="flex-1">
        {transfers.state === 'record' && record ? (
          <>
            <div className="flex items-end justify-between gap-4 border-b border-border pb-4">
              <div>
                <strong className="font-heading text-4xl font-semibold text-primary">
                  {numberFormatter.format(record.agreements)}
                </strong>
                <span className="ml-2 text-sm text-muted-foreground">
                  {record.agreements === 1 ? 'instrumento' : 'instrumentos'}
                </span>
              </div>
              <span className="text-xs text-muted-foreground">
                {record.firstYear} a {record.lastYear}
              </span>
            </div>
            <div className="pt-4">
              <div className="flex flex-wrap items-center gap-2">
                <Tag tone={statusIsNegative ? 'danger' : 'secondary'}>
                  {record.latest.status}
                </Tag>
                <span className="text-xs text-muted-foreground">
                  mais recente · {record.latest.year}
                </span>
              </div>
              {statusIsNegative && (
                <p className="mt-3 rounded-lg bg-destructive/8 p-3 text-sm leading-6 text-destructive">
                  Este instrumento está cancelado ou anulado e não é apresentado
                  como capacidade ou prevenção em execução.
                </p>
              )}
              <p className="mt-3 line-clamp-4 text-sm leading-6">
                {record.latest.object}
              </p>
              {record.latest.globalValue !== null && (
                <p className="mt-3 text-sm">
                  <span className="text-muted-foreground">Valor global: </span>
                  <strong>
                    {currencyFormatter.format(record.latest.globalValue)}
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
              {transfers.state === 'no_record'
                ? 'Nenhum instrumento encontrado neste recorte'
                : 'Dados de transferência indisponíveis'}
            </strong>
            <p className="mt-2 text-sm leading-6 text-muted-foreground">
              {sourceAbsenceCopy('transfers', transfers.state)}
            </p>
          </div>
        )}
      </CardContent>
      <CardFooter className="flex-col items-start gap-2 text-xs leading-5 text-muted-foreground">
        <p className="w-full min-w-0">
          Fonte:{' '}
          {sourceLink(
            'https://dados.gov.br/dados/conjuntos-dados/transferencias-e-parcerias-da-uniao',
            metadata?.sources.transferegov.reference ??
              'Transferegov · metadados indisponíveis',
          )}
        </p>
        <p className="w-full">
          Proposta não é sinônimo de política municipal completa.
        </p>
      </CardFooter>
    </Card>
  );
}

function formatHectares(value: number) {
  return hectareFormatter.format(Math.abs(value));
}

function formatSignedHectares(value: number | null | undefined) {
  if (value === null || value === undefined) return null;
  const sign = value > 0 ? '+' : value < 0 ? '-' : '';
  return `${sign}${formatHectares(value)} ha`;
}

function formatSignedPercentage(value: number | null | undefined) {
  if (value === null || value === undefined) return null;
  const sign = value > 0 ? '+' : value < 0 ? '-' : '';
  return `${sign}${percentageFormatter.format(Math.abs(value))}%`;
}

function changeMetrics(
  areaChange: number | null | undefined,
  percentageChange: number | null | undefined,
) {
  const area = formatSignedHectares(areaChange);
  const percentage = formatSignedPercentage(percentageChange);
  if (area && percentage) return `${area} · ${percentage}`;
  if (area) return area;
  if (percentage) return percentage;
  return 'Variação não publicada';
}

function changeNarrative(
  label: string,
  areaChange: number | null | undefined,
  percentageChange: number | null | undefined,
) {
  if (areaChange === null || areaChange === undefined) {
    return `${label} não tem variação em hectares publicada`;
  }

  const percentage = formatSignedPercentage(percentageChange);
  if (areaChange === 0) {
    return `${label} não teve variação na área classificada (${formatHectares(areaChange)} ha${percentage ? `; ${percentage}` : ''})`;
  }

  const direction = areaChange > 0 ? 'aumentou' : 'diminuiu';
  return `${label} ${direction} ${formatHectares(areaChange)} ha${percentage ? ` (${percentage})` : ''}`;
}

export function LandCoverCard({
  landCover,
  metadata,
}: {
  landCover: MunicipalityPresentation['land_cover'];
  metadata: PresentationMetadata | null;
}) {
  const history = [...landCover.history].sort((left, right) => left.year - right.year);
  const first = history[0];
  const latest = history.at(-1);
  const change = landCover.change;
  const urbanAreaChange = change?.urban_area_change_ha;
  const urbanAreaPercentageChange = change?.urban_area_change_pct;
  const nativeVegetationChange = change?.native_vegetation_change_ha;
  const nativeVegetationPercentageChange =
    change?.native_vegetation_change_pct;
  const hasCoverage = landCover.state === 'record';
  const hasSnapshots = first !== undefined && latest !== undefined;
  const period = hasSnapshots
    ? first.year === latest.year
      ? `em ${first.year}`
      : `entre ${first.year} e ${latest.year}`
    : null;

  return (
    <Card className="elevated-card mt-5 border-0 bg-card shadow-[0_12px_45px_rgb(21_42_57/8%)] ring-border">
      <CardHeader className="border-b border-border/80 pb-5">
        <div className="mb-3 grid size-11 place-items-center rounded-full bg-emerald-100 text-emerald-800">
          <MapIcon aria-hidden="true" className="size-5" />
        </div>
        <CardTitle className="font-heading text-2xl font-semibold">
          Cobertura e uso da terra
        </CardTitle>
        <CardDescription>
          Classificação MapBiomas da área mapeada no município.
        </CardDescription>
        {period && (
          <CardAction>
            <span className="block text-right text-xs font-bold text-muted-foreground">
              Série disponível
            </span>
            <span className="block text-right text-sm font-bold text-primary">
              {period.replace('entre ', '').replace('em ', '')}
            </span>
          </CardAction>
        )}
      </CardHeader>

      {!hasCoverage ? (
        <CardContent className="py-8">
          <div className="rounded-xl border border-dashed border-border bg-muted/40 p-6">
            <CircleDashed
              aria-hidden="true"
              className="mb-4 size-7 text-rain-strong"
            />
            <h3 className="font-heading text-xl font-semibold">
              Sem cobertura MapBiomas para este município
            </h3>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">
              Não há classificação publicada para esta unidade territorial no
              recorte carregado. A ausência não é um valor zero.
            </p>
          </div>
        </CardContent>
      ) : !hasSnapshots ? (
        <CardContent className="py-8">
          <div className="rounded-xl border border-dashed border-border bg-muted/40 p-6">
            <TriangleAlert
              aria-hidden="true"
              className="mb-4 size-7 text-amber-700"
            />
            <h3 className="font-heading text-xl font-semibold">
              Série MapBiomas incompleta no recorte
            </h3>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">
              Há cobertura para o município, mas o payload não trouxe snapshots
              para apresentar o período e as variações.
            </p>
          </div>
        </CardContent>
      ) : (
        <CardContent className="pt-6">
          <p className="max-w-4xl text-base leading-7 text-muted-foreground">
            {`No período ${period}, ${changeNarrative(
              'a área classificada como urbanizada',
              urbanAreaChange,
              urbanAreaPercentageChange,
            )}; ${changeNarrative(
              'a vegetação nativa selecionada',
              nativeVegetationChange,
              nativeVegetationPercentageChange,
            )}.`}
          </p>

          <dl className="mt-6 grid gap-4 md:grid-cols-2">
            {[
              {
                title: 'Área urbanizada',
                description: 'Área classificada como urbanizada',
                firstArea: first.urban_area_ha,
                latestArea: latest.urban_area_ha,
                change: urbanAreaChange,
                percentage: urbanAreaPercentageChange,
              },
              {
                title: 'Vegetação nativa',
                description: 'Ramos naturais selecionados na classificação',
                firstArea: first.native_vegetation_area_ha,
                latestArea: latest.native_vegetation_area_ha,
                change: nativeVegetationChange,
                percentage: nativeVegetationPercentageChange,
              },
            ].map((metric) => (
              <div
                className="rounded-xl border border-border bg-muted/35 p-5"
                key={metric.title}
              >
                <dt className="font-heading text-lg font-semibold">
                  {metric.title}
                </dt>
                <dd className="mt-1 text-sm text-muted-foreground">
                  {metric.description}
                </dd>
                <dd className="mt-4 text-sm leading-6">
                  <span className="block text-xs font-bold uppercase tracking-wide text-muted-foreground">
                    Área classificada
                  </span>
                  <span className="font-semibold tabular-nums">
                    {`${hectareFormatter.format(metric.firstArea)} ha → ${hectareFormatter.format(metric.latestArea)} ha`}
                  </span>
                </dd>
                <dd className="mt-3 text-sm leading-6">
                  <span className="block text-xs font-bold uppercase tracking-wide text-muted-foreground">
                    Variação no período
                  </span>
                  <strong className="tabular-nums">
                    {changeMetrics(metric.change, metric.percentage)}
                  </strong>
                </dd>
              </div>
            ))}
          </dl>

          <p className="mt-6 flex gap-2 border-t border-border pt-5 text-xs leading-5 text-muted-foreground">
            <Info aria-hidden="true" className="mt-0.5 size-4 shrink-0" />
            Área urbanizada é uma classificação de cobertura da terra e não
            equivale a superfície impermeabilizada. Esses dados não medem, por
            si, risco ou vulnerabilidade.
          </p>
        </CardContent>
      )}

      <CardFooter className="text-xs leading-5 text-muted-foreground">
        <p>
          Fonte:{' '}
          {sourceLink(
            'https://brasil.mapbiomas.org/',
            metadata
              ? `MapBiomas Brasil · Coleção ${metadata.sources.mapbiomas.collection_id}, ${metadata.sources.mapbiomas.collection_version}`
              : 'MapBiomas Brasil · metadados indisponíveis',
          )}
        </p>
      </CardFooter>
    </Card>
  );
}

export default function Home() {
  const [municipalities, setMunicipalities] = useState<MunicipalIndexEntry[]>([]);
  const [metadata, setMetadata] = useState<PresentationMetadata | null>(null);
  const [selectedEntry, setSelectedEntry] =
    useState<MunicipalIndexEntry | null>(null);
  const [selected, setSelected] = useState<MunicipalityPresentation | null>(null);
  const [searchFocused, setSearchFocused] = useState(false);
  const [query, setQuery] = useState('');
  const [activeResultIndex, setActiveResultIndex] = useState(-1);
  const [indexLoading, setIndexLoading] = useState(true);
  const [indexError, setIndexError] = useState<string | null>(null);
  const [metadataError, setMetadataError] = useState<string | null>(null);
  const [payloadLoading, setPayloadLoading] = useState(false);
  const [payloadError, setPayloadError] = useState<string | null>(null);
  const [requestedCodeError, setRequestedCodeError] = useState<string | null>(
    null,
  );
  const searchInputRef = useRef<HTMLInputElement>(null);
  const shardCache = useRef(
    new Map<string, Record<string, MunicipalityPresentation>>(),
  );
  const payloadRequest = useRef(0);
  const payloadController = useRef<AbortController | null>(null);

  function publishCanonicalCode(code: string) {
    const url = new URL(window.location.href);
    url.searchParams.delete('municipio');
    url.searchParams.set('codigo_ibge', code);
    window.history.replaceState(null, '', `${url.pathname}${url.search}${url.hash}`);
  }

  function selectPayload(
    entry: MunicipalIndexEntry,
    municipalitiesByCode: Record<string, MunicipalityPresentation>,
    requestId: number,
  ) {
    const payload = municipalitiesByCode[entry.codigo_ibge];
    if (
      !payload ||
      payload.municipality.codigo_ibge !== entry.codigo_ibge ||
      payload.municipality.uf !== entry.uf
    ) {
      throw new Error('O recorte carregado não contém o município solicitado.');
    }
    if (payloadRequest.current !== requestId) return;
    setSelected(payload);
    setPayloadLoading(false);
  }

  function loadMunicipality(entry: MunicipalIndexEntry) {
    const requestId = payloadRequest.current + 1;
    payloadRequest.current = requestId;
    payloadController.current?.abort();
    payloadController.current = null;
    setSelectedEntry(entry);
    setSelected(null);
    setPayloadError(null);
    setRequestedCodeError(null);
    setPayloadLoading(true);
    publishCanonicalCode(entry.codigo_ibge);

    const cachedShard = shardCache.current.get(entry.shard);
    if (cachedShard) {
      try {
        selectPayload(entry, cachedShard, requestId);
      } catch (error) {
        shardCache.current.delete(entry.shard);
        if (payloadRequest.current !== requestId) return;
        setPayloadLoading(false);
        setPayloadError(
          error instanceof Error
            ? error.message
            : 'O recorte municipal publicado é inválido.',
        );
      }
      return;
    }

    const controller = new AbortController();
    payloadController.current = controller;
    void fetchJson(entry.shard, controller.signal)
      .then((data) => {
        if (!isMunicipalShard(data) || data.uf !== entry.uf) {
          throw new Error('O recorte municipal publicado é inválido.');
        }
        selectPayload(entry, data.municipalities, requestId);
        shardCache.current.set(entry.shard, data.municipalities);
      })
      .catch((error: unknown) => {
        if (
          payloadRequest.current !== requestId ||
          (error instanceof Error && error.name === 'AbortError')
        ) {
          return;
        }
        setPayloadLoading(false);
        setPayloadError(
          error instanceof Error
            ? `Não foi possível carregar o recorte de ${entry.uf}: ${error.message}`
            : `Não foi possível carregar o recorte de ${entry.uf}.`,
        );
      });
  }

  useEffect(() => {
    const controller = new AbortController();
    let cancelled = false;

    async function loadIndex() {
      try {
        const data = await fetchJson(
          '/data/v1/municipal-index.json',
          controller.signal,
        );
        if (!isMunicipalIndex(data)) {
          throw new Error('O índice municipal publicado é inválido.');
        }
        if (cancelled) return;

        setMunicipalities(data.municipalities);
        setIndexLoading(false);
        const requested = requestedCodigoIbge(window.location.search);
        if (requested.hasInvalidCode) {
          setRequestedCodeError(
            'O link informado não possui um código IBGE de sete dígitos.',
          );
          return;
        }
        if (!requested.code) return;

        const entry = data.municipalities.find(
          (municipality) => municipality.codigo_ibge === requested.code,
        );
        if (!entry) {
          setRequestedCodeError(
            'O código IBGE solicitado não foi encontrado no índice municipal publicado.',
          );
          return;
        }
        loadMunicipality(entry);
      } catch (error) {
        if (cancelled || (error instanceof Error && error.name === 'AbortError')) {
          return;
        }
        setIndexLoading(false);
        setIndexError(
          error instanceof Error
            ? `Não foi possível carregar o índice municipal: ${error.message}`
            : 'Não foi possível carregar o índice municipal.',
        );
      }
    }

    async function loadMetadata() {
      try {
        const data = await fetchJson('/data/v1/metadata.json', controller.signal);
        if (!isPresentationMetadata(data)) {
          throw new Error('Os metadados publicados são inválidos.');
        }
        if (!cancelled) setMetadata(data);
      } catch (error) {
        if (cancelled || (error instanceof Error && error.name === 'AbortError')) {
          return;
        }
        setMetadataError(
          error instanceof Error
            ? `Não foi possível carregar os metadados: ${error.message}`
            : 'Não foi possível carregar os metadados.',
        );
      }
    }

    void loadIndex();
    void loadMetadata();

    return () => {
      cancelled = true;
      controller.abort();
      payloadController.current?.abort();
    };
  }, []);

  const searchEntries = useMemo(
    () =>
      municipalities.map((municipality) => ({
        municipality,
        search: normalizeSearch(
          `${municipality.municipio} ${municipality.uf} ${municipality.codigo_ibge}`,
        ),
      })),
    [municipalities],
  );

  const results = useMemo(() => {
    const normalizedQuery = normalizeSearch(query.trim());
    if (normalizedQuery.length < 2) {
      return [];
    }
    return searchEntries
      .filter(({ search }) => search.includes(normalizedQuery))
      .slice(0, 50)
      .map(({ municipality }) => municipality);
  }, [query, searchEntries]);

  function chooseMunicipality(municipality: MunicipalIndexEntry) {
    searchInputRef.current?.blur();
    setSearchFocused(false);
    setQuery('');
    setActiveResultIndex(-1);
    loadMunicipality(municipality);
    window.setTimeout(() => {
      document.getElementById('resultado')?.scrollIntoView({
        behavior: 'smooth',
        block: 'start',
      });
    }, 80);
  }

  return (
    <>
      <a className="skip-link" href="#conteudo-principal">
        Pular para o conteúdo principal
      </a>
      <main
        className="page-ambient min-h-screen overflow-x-hidden bg-background text-foreground"
        id="topo"
      >
      <div className="border-b border-white/10 bg-primary text-primary-foreground">
        <div className="mx-auto flex min-h-11 max-w-7xl items-center justify-between gap-4 px-4 py-2 text-sm font-bold text-white/85 sm:px-8">
          <span>Dados públicos para agir antes da próxima chuva</span>
          <span className="hidden items-center gap-5 text-white/72 sm:flex">
            <span>
              {metadata
                ? `Atualizado em ${formatPublicationDate(metadata.sources.atlas.materialized_at)}`
                : metadataError
                  ? 'Metadados indisponíveis'
                  : 'Atualização em carregamento'}
            </span>
          </span>
        </div>
      </div>

      <header className="sticky top-0 z-40 border-b border-border/80 bg-background/88 shadow-[0_8px_30px_rgb(17_47_62/5%)] backdrop-blur-xl">
        <div className="mx-auto flex min-h-20 max-w-7xl items-center justify-between gap-6 px-4 py-3 sm:px-8">
          <a className="group flex items-center gap-3" href="#topo">
            <span className="relative size-12 shrink-0 transition-transform group-hover:-translate-y-0.5">
              <Image
                alt=""
                aria-hidden="true"
                className="object-contain"
                fill
                sizes="48px"
                src="/brand-mark.png"
              />
            </span>
            <span>
              <span className="font-brand block text-[1.45rem] font-bold leading-none tracking-[-0.025em]">
                Antes da Chuva
              </span>
              <span className="mt-1.5 block text-sm font-bold text-muted-foreground">
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
        id="conteudo-principal"
      >
        <div className="weather-lines absolute inset-0 opacity-35" />
        <div className="soft-grid absolute inset-0 opacity-30" />
        <div className="relative mx-auto grid max-w-7xl gap-8 px-4 py-10 sm:px-8 sm:py-14 lg:grid-cols-12 lg:items-center lg:gap-12 lg:py-16">
          <div className="min-w-0 text-white lg:col-span-7">
            <div className="mb-5 flex flex-wrap gap-3">
              <Tag tone="inverse">
                {metadata
                  ? `${numberFormatter.format(metadata.territorial_universe.municipality_count)} localidades disponíveis`
                  : metadataError
                    ? 'Metadados indisponíveis'
                    : 'Dados de publicação em carregamento'}
              </Tag>
              <Tag tone="inverse">Leitura em menos de 1 minuto</Tag>
            </div>
            <h1 className="max-w-3xl font-heading text-4xl font-semibold leading-[1.03] tracking-[-0.035em] text-balance sm:text-5xl lg:text-[3.75rem]">
              O que precisa ser visto antes da próxima chuva?
            </h1>
            <p className="mt-5 max-w-2xl text-base leading-7 text-white/78 sm:text-lg">
              Em uma única leitura, veja o histórico de ocorrências ligadas à
              chuva, uma condição de saneamento e evidências federais de
              prevenção, com recorte e limitações à vista.
            </p>

            <div className="relative mt-8 min-w-0 rounded-2xl border border-white/15 bg-white p-3 text-foreground shadow-[0_24px_80px_rgb(4_20_32/28%)] sm:p-4">
              <p className="mb-2 px-2 text-sm font-bold text-muted-foreground">
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
                        ? `municipio-option-${results[activeResultIndex].codigo_ibge}`
                        : undefined
                    }
                    aria-autocomplete="list"
                    aria-controls="municipios-resultados"
                    aria-expanded={searchFocused}
                    aria-label="Busque por nome, UF ou código IBGE"
                    className="min-w-0 flex-1 bg-transparent text-base font-bold outline-none"
                    disabled={indexLoading || indexError !== null}
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
                        : indexLoading
                          ? 'Carregando localidades…'
                          : selectedEntry
                            ? `${selectedEntry.municipio}, ${selectedEntry.uf}`
                            : ''
                    }
                  />
                </div>
                <button
                  className="inline-flex h-12 w-full items-center justify-center rounded-xl bg-primary px-5 text-sm font-bold text-primary-foreground transition-colors hover:bg-primary/85 focus-visible:outline-none focus-visible:ring-3 focus-visible:ring-ring/50 disabled:opacity-50 sm:w-auto"
                  disabled={indexLoading || indexError !== null}
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
                  <p className="border-b border-border px-4 py-2 text-sm font-bold text-muted-foreground">
                    {query.trim().length < 2
                      ? 'Digite ao menos dois caracteres'
                      : 'Resultados'}
                  </p>
                  <div className="max-h-72 overflow-y-auto p-1">
                    {indexLoading && (
                      <p className="px-4 py-6 text-center text-sm text-muted-foreground">
                        Carregando índice municipal…
                      </p>
                    )}
                    {!indexLoading && results.length === 0 && (
                      <p className="px-4 py-6 text-center text-sm text-muted-foreground">
                        {query.trim().length < 2
                          ? 'Digite nome, UF ou código IBGE para buscar.'
                          : 'Nenhum município encontrado.'}
                      </p>
                    )}
                    {results.map((municipality, index) => (
                      <button
                        aria-selected={activeResultIndex === index}
                        className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left text-sm transition-colors hover:bg-muted focus-visible:bg-muted focus-visible:outline-none aria-selected:bg-muted"
                        id={`municipio-option-${municipality.codigo_ibge}`}
                        key={municipality.codigo_ibge}
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
                          {municipality.municipio}, {municipality.uf}
                        </span>
                        <span className="text-xs tabular-nums text-muted-foreground">
                          {municipality.codigo_ibge}
                        </span>
                      </button>
                    ))}
                  </div>
                </div>
              )}
              {indexError ? (
                <p className="px-2 pt-2 text-xs font-bold text-destructive" role="alert">
                  {indexError}
                </p>
              ) : metadataError ? (
                <p className="px-2 pt-2 text-xs font-bold text-amber-900" role="alert">
                  {metadataError}
                </p>
              ) : (
                <p className="px-2 pt-2 text-xs text-muted-foreground">
                  Digite nome, UF ou código IBGE. Use as setas e Enter para
                  selecionar.
                </p>
              )}
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
              <p className="text-sm font-bold text-white/80">
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
        {indexLoading ? (
          <div className="rounded-2xl border border-dashed border-border bg-card/70 p-8 text-center">
            <CircleDashed
              aria-hidden="true"
              className="mx-auto mb-4 size-7 animate-spin text-rain-strong"
            />
            <h2 className="font-heading text-2xl font-semibold">
              Carregando índice municipal
            </h2>
            <p className="mt-2 text-sm text-muted-foreground">
              A busca será habilitada assim que a lista publicada estiver pronta.
            </p>
          </div>
        ) : indexError ? (
          <div
            className="rounded-2xl border border-destructive/30 bg-destructive/5 p-7"
            role="alert"
          >
            <TriangleAlert
              aria-hidden="true"
              className="mb-4 size-7 text-destructive"
            />
            <h2 className="font-heading text-2xl font-semibold">
              Índice municipal indisponível
            </h2>
            <p className="mt-2 text-sm leading-6 text-muted-foreground">
              {indexError}
            </p>
            <button
              className="mt-5 inline-flex h-10 items-center justify-center rounded-lg bg-primary px-4 text-sm font-bold text-primary-foreground"
              onClick={() => window.location.reload()}
              type="button"
            >
              Tentar novamente
            </button>
          </div>
        ) : requestedCodeError ? (
          <div
            className="rounded-2xl border border-amber-300 bg-amber-50 p-7"
            role="alert"
          >
            <TriangleAlert
              aria-hidden="true"
              className="mb-4 size-7 text-amber-800"
            />
            <h2 className="font-heading text-2xl font-semibold">
              Município não selecionado
            </h2>
            <p className="mt-2 text-sm leading-6 text-muted-foreground">
              {requestedCodeError} Use a busca para escolher um município válido.
            </p>
          </div>
        ) : payloadLoading && selectedEntry ? (
          <div className="rounded-2xl border border-dashed border-border bg-card/70 p-8 text-center">
            <CircleDashed
              aria-hidden="true"
              className="mx-auto mb-4 size-7 animate-spin text-rain-strong"
            />
            <h2 className="font-heading text-2xl font-semibold">
              Carregando dados de {selectedEntry.municipio}, {selectedEntry.uf}
            </h2>
            <p className="mt-2 text-sm text-muted-foreground">
              Somente o recorte de {selectedEntry.uf} está sendo carregado.
            </p>
          </div>
        ) : payloadError && selectedEntry ? (
          <div
            className="rounded-2xl border border-destructive/30 bg-destructive/5 p-7"
            role="alert"
          >
            <TriangleAlert
              aria-hidden="true"
              className="mb-4 size-7 text-destructive"
            />
            <h2 className="font-heading text-2xl font-semibold">
              Dados municipais indisponíveis
            </h2>
            <p className="mt-2 text-sm leading-6 text-muted-foreground">
              {payloadError}
            </p>
            <button
              className="mt-5 inline-flex h-10 items-center justify-center rounded-lg bg-primary px-4 text-sm font-bold text-primary-foreground"
              onClick={() => loadMunicipality(selectedEntry)}
              type="button"
            >
              Tentar novamente
            </button>
          </div>
          ) : selected ? (
          <>
            <div className="mb-7 flex flex-col justify-between gap-4 border-b border-border pb-6 sm:flex-row sm:items-end">
              <div>
                <div className="mb-2 flex items-center gap-2 text-sm font-bold text-primary">
                  <MapPin aria-hidden="true" className="size-4" />
                  {selected.municipality.municipio} · {selected.municipality.uf}
                </div>
                <h2 className="font-heading text-3xl font-semibold tracking-tight sm:text-4xl">
                  A cidade em uma leitura
                </h2>
              </div>
              <div className="flex flex-wrap gap-2 text-xs text-muted-foreground">
                <Tag>
                  {metadata
                    ? `Atlas ${metadata.sources.atlas.first_year} a ${metadata.sources.atlas.latest_year}`
                    : 'Atlas: metadados indisponíveis'}
                </Tag>
                <Tag>
                  {metadata?.sources.census.reference ??
                    'Censo: metadados indisponíveis'}
                </Tag>
                <Tag>
                  {metadata?.sources.transferegov.reference ??
                    'Transferegov: metadados indisponíveis'}
                </Tag>
                {selected.land_cover.state !== 'record' && (
                  <Tag>
                    {sourceStateLabel('MapBiomas', selected.land_cover.state)}
                  </Tag>
                )}
              </div>
            </div>

            <ThirtySecondSummary
              disasters={selected.disasters}
              landCover={selected.land_cover}
              metadata={metadata}
              municipality={selected.municipality}
              summary={selected.summary}
            />

            <div className="grid items-stretch gap-5 lg:grid-cols-3">
              <DisasterHistory disasters={selected.disasters} />
              <TypesAndMonths disasters={selected.disasters} />
              <CensusCard census={selected.census} metadata={metadata} />
              <TransferCard transfers={selected.transfers} metadata={metadata} />
            </div>

            <LandCoverHistory landCover={selected.land_cover} />
            <RegionalComparison benchmarks={selected.benchmarks} />

            <div className="elevated-card mt-5 flex flex-col justify-between gap-5 rounded-2xl border border-border bg-card p-5 shadow-sm sm:flex-row sm:items-center sm:p-6">
              <div className="max-w-2xl">
                <p className="text-sm font-bold text-rain-strong">
                  Próxima ação
                </p>
                <h3 className="mt-1 font-heading text-xl font-semibold">
                  Há um alerta ativo agora?
                </h3>
                <p className="mt-1 text-sm leading-6 text-muted-foreground">
                  Consulte o painel oficial de alertas ativos. Ele é separado do
                  histórico municipal apresentado acima.
                </p>
              </div>
              <div className="flex shrink-0 flex-col gap-2 sm:items-end">
                <a
                  className="inline-flex h-11 items-center justify-center gap-2 rounded-xl bg-primary px-4 text-sm font-semibold text-primary-foreground transition-colors hover:bg-primary/85 focus-visible:outline-none focus-visible:ring-3 focus-visible:ring-ring/50"
                  href="https://idap.mdr.gov.br/"
                  rel="noreferrer"
                  target="_blank"
                >
                  Ver alertas ativos no IDAP
                  <ExternalLink aria-hidden="true" className="size-4" />
                </a>
                <a
                  className="inline-flex min-h-10 items-center justify-center gap-2 text-sm font-semibold text-primary underline decoration-primary/30 underline-offset-4"
                  href="#alertas"
                >
                  Como receber alertas
                  <ArrowRight aria-hidden="true" data-icon="inline-end" />
                </a>
              </div>
            </div>
          </>
        ) : (
          <div className="rounded-2xl border border-dashed border-border bg-card/70 p-8 text-center">
            <MapPin
              aria-hidden="true"
              className="mx-auto mb-4 size-7 text-rain-strong"
            />
            <h2 className="font-heading text-2xl font-semibold">
              Escolha um município para começar
            </h2>
            <p className="mt-2 text-sm text-muted-foreground">
              A leitura municipal só é exibida depois que um código IBGE válido
              é selecionado no índice publicado.
            </p>
          </div>
        )}
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
                    <span className="rounded-full border border-white/15 bg-white/8 px-3 py-1.5 text-sm font-bold text-white/85">
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
                title: metadata
                  ? `Atlas Digital de Desastres · ${metadata.sources.atlas.release}`
                  : 'Atlas Digital de Desastres',
                text: metadata
                  ? `Registros municipais das cinco tipologias relacionadas à chuva, entre ${metadata.sources.atlas.first_year} e ${metadata.sources.atlas.latest_year}.`
                  : 'Registros municipais das cinco tipologias relacionadas à chuva.',
                href: 'https://atlasdigital.mdr.gov.br/paginas/downloads.xhtml',
                action: 'Consultar Atlas',
              },
              {
                label: 'Saneamento',
                title: metadata?.sources.census.reference ?? 'Censo Demográfico · IBGE',
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
                <p className="text-sm font-bold text-rain-strong">
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
              <span className="relative size-12 shrink-0 overflow-hidden rounded-xl bg-[#f3f0e7] shadow-sm ring-1 ring-white/20 transition-transform group-hover:-translate-y-0.5">
                <Image
                  alt=""
                  aria-hidden="true"
                  className="object-contain p-1"
                  fill
                  sizes="48px"
                  src="/brand-mark.png"
                />
              </span>
              <span className="font-brand text-2xl font-bold tracking-[-0.025em]">
                Antes da Chuva
              </span>
            </a>
            <p className="mt-4 max-w-sm leading-6 text-white/74">
              Inteligência pública municipal para transformar bases abertas em
              perguntas melhores antes da próxima crise.
            </p>
            <p className="mt-4 text-sm font-bold text-white/72">
              Projeto independente · Concurso CGU 2026
            </p>
          </div>

          <div>
            <h2 className="text-sm font-bold text-white/78">
              Navegue
            </h2>
            <nav
              aria-label="Navegação do rodapé"
              className="mt-4 grid gap-3 font-bold text-white/82"
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
            <h2 className="text-sm font-bold text-white/78">
              Bases oficiais
            </h2>
            <div className="mt-4 grid gap-3 text-white/82">
              {sourceLink(
                'https://atlasdigital.mdr.gov.br/paginas/downloads.xhtml',
                metadata
                  ? `Atlas de Desastres · ${metadata.sources.atlas.release}`
                  : 'Atlas de Desastres',
                true,
              )}
              {sourceLink(
                'https://sidra.ibge.gov.br/tabela/6805',
                metadata?.sources.census.reference ?? 'Censo · IBGE',
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
              {sourceLink(
                'https://idap.mdr.gov.br/',
                'Alertas ativos · IDAP',
                true,
              )}
            </div>
          </div>

          <div>
            <h2 className="text-sm font-bold text-white/78">
              Transparência
            </h2>
            <ul className="mt-4 grid gap-3 leading-5 text-white/74">
              <li>
                {metadata
                  ? `Atualização da leitura: ${formatPublicationDate(metadata.sources.atlas.materialized_at)}.`
                  : 'Atualização da leitura: metadados indisponíveis.'}
              </li>
              <li>Código IBGE é a chave de integração municipal.</li>
              <li>
                Ausência de registro não significa ausência de ação ou risco.
              </li>
            </ul>
          </div>
        </div>

        <div className="relative border-t border-white/10">
          <div className="mx-auto flex max-w-7xl flex-col justify-between gap-3 px-4 py-5 text-xs leading-5 text-white/70 sm:px-8 md:flex-row md:items-center">
            <p>© 2026 Antes da Chuva. Dados públicos, leitura responsável.</p>
            <p className="max-w-2xl md:text-right">
              Não substitui alertas, laudos técnicos nem a atuação da Defesa
              Civil.
            </p>
          </div>
        </div>
      </footer>
      </main>
    </>
  );
}

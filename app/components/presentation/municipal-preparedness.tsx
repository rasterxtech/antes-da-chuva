import Check from 'lucide-react/dist/esm/icons/check.mjs';
import CircleHelp from 'lucide-react/dist/esm/icons/circle-help.mjs';
import ExternalLink from 'lucide-react/dist/esm/icons/external-link.mjs';
import Landmark from 'lucide-react/dist/esm/icons/landmark.mjs';
import Minus from 'lucide-react/dist/esm/icons/minus.mjs';
import ShieldCheck from 'lucide-react/dist/esm/icons/shield-check.mjs';

import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
} from '@/components/ui/card';
import type {
  MunicipalCapacity,
  MunicIndicator,
  MunicStatus,
} from '@/lib/presentation-contract';

const SOURCE_URL =
  'https://www.ibge.gov.br/estatisticas/sociais/saude/10586-pesquisa-deinformacoes-basicas-municipais.html?edicao=32141';

const groups: Array<{
  title: string;
  id: string;
  icon: typeof Landmark;
  items: Array<[MunicIndicator, string]>;
}> = [
  {
    title: 'Estrutura municipal',
    id: 'estrutura',
    icon: Landmark,
    items: [
      ['municipal_civil_defense_body', 'Órgão de Proteção e Defesa Civil'],
      ['civil_defense_budget_provision', 'Previsão orçamentária na LOA'],
      ['any_risk_prevention_planning_instrument', 'Instrumento de planejamento preventivo'],
    ],
  },
  {
    title: 'Inundações',
    id: 'inundacoes',
    icon: ShieldCheck,
    items: [
      ['flood_risk_mapping', 'Mapeamento de áreas de risco'],
      ['flood_contingency_plan', 'Plano de contingência'],
      ['flood_early_warning', 'Sistema de alerta antecipado'],
    ],
  },
  {
    title: 'Deslizamentos',
    id: 'deslizamentos',
    icon: ShieldCheck,
    items: [
      ['landslide_risk_mapping', 'Mapeamento de áreas de risco'],
      ['landslide_contingency_plan', 'Plano de contingência'],
      ['landslide_early_warning', 'Sistema de alerta antecipado'],
    ],
  },
];

const statusContent: Record<MunicStatus, { label: string; icon: typeof Check; className: string }> = {
  declared_yes: { label: 'Sim', icon: Check, className: 'bg-emerald-100 text-emerald-800' },
  declared_no: { label: 'Não', icon: Minus, className: 'bg-muted text-muted-foreground' },
  refused: { label: 'Recusa', icon: CircleHelp, className: 'bg-amber-100 text-amber-900' },
  not_reported: { label: 'Não informou', icon: CircleHelp, className: 'bg-amber-100 text-amber-900' },
  not_applicable: { label: 'Não se aplica', icon: Minus, className: 'bg-muted text-muted-foreground' },
  unknown: { label: 'Não sabe', icon: CircleHelp, className: 'bg-amber-100 text-amber-900' },
  not_in_source: { label: 'Fora da fonte', icon: CircleHelp, className: 'bg-muted text-muted-foreground' },
};

function Status({ value }: { value: MunicStatus }) {
  const status = statusContent[value];
  const Icon = status.icon;
  return (
    <span className={`inline-flex shrink-0 items-center gap-1.5 rounded-full px-2.5 py-1.5 text-xs font-bold ${status.className}`}>
      <Icon aria-hidden="true" className="size-3.5" />
      {status.label}
    </span>
  );
}

export function MunicipalPreparedness({ capacity }: { capacity: MunicipalCapacity }) {
  return (
    <Card className="elevated-card mb-5 border-0 bg-card shadow-[0_12px_45px_rgb(21_42_57/8%)] ring-border">
      <CardHeader className="gap-2 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="mb-2 text-sm font-bold uppercase tracking-wide text-rain-strong">
            Capacidade declarada · MUNIC {capacity.reference_year}
          </p>
          <h2 className="font-heading text-2xl font-semibold sm:text-3xl">
            Como o município declarou se preparar
          </h2>
          <CardDescription className="mt-2 max-w-3xl leading-6">
            Estruturas e instrumentos informados pela prefeitura ao IBGE. As respostas não avaliam a qualidade nem a efetividade atual das ações.
          </CardDescription>
        </div>
        <span className="mt-1 inline-flex shrink-0 rounded-full bg-rain-pale px-3 py-1.5 text-xs font-bold text-rain-strong">
          Referência: {capacity.reference_year}
        </span>
      </CardHeader>

      <CardContent>
        {capacity.state === 'not_in_source' ? (
          <div className="rounded-xl border border-dashed border-border bg-muted/40 p-5">
            <CircleHelp aria-hidden="true" className="mb-3 size-7 text-rain-strong" />
            <h3 className="font-heading text-xl font-semibold">Município fora do universo da MUNIC 2020</h3>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-muted-foreground">
              Este município passou a integrar a divisão territorial depois da coleta. A ausência não deve ser interpretada como falta de estrutura.
            </p>
          </div>
        ) : (
          <div className="grid gap-6 lg:grid-cols-3">
            {groups.map(({ title, id, icon: GroupIcon, items }) => (
              <section aria-labelledby={`munic-${id}`} key={id}>
                <h3 className="mb-2 flex items-center gap-2 text-sm font-bold uppercase tracking-wide text-muted-foreground" id={`munic-${id}`}>
                  <GroupIcon aria-hidden="true" className="size-4 text-rain-strong" />
                  {title}
                </h3>
                <dl>
                  {items.map(([field, label]) => (
                    <div className="grid min-h-14 grid-cols-[minmax(0,1fr)_auto] items-center gap-3 border-t border-border py-2.5" key={field}>
                      <dt className="text-sm leading-5">{label}</dt>
                      <dd><Status value={capacity.indicators[field]} /></dd>
                    </div>
                  ))}
                </dl>
              </section>
            ))}
          </div>
        )}
      </CardContent>

      <CardFooter className="flex-col items-start justify-between gap-3 text-xs leading-5 text-muted-foreground sm:flex-row sm:items-center">
        <p>Resposta declaratória da prefeitura; não é nota, certificação ou retrato em tempo real.</p>
        <a className="inline-flex shrink-0 items-center gap-1.5 font-bold text-primary underline decoration-primary/30 underline-offset-4" href={SOURCE_URL} rel="noreferrer" target="_blank">
          Consultar MUNIC 2020
          <ExternalLink aria-hidden="true" className="size-3.5" />
        </a>
      </CardFooter>
    </Card>
  );
}

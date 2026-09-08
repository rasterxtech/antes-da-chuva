import type { ReactNode } from 'react';

export const ATLAS_URL =
  'https://atlasdigital.mdr.gov.br/paginas/downloads.xhtml';
export const MAPBIOMAS_URL =
  'https://brasil.mapbiomas.org/downloads/estatisticas/';

export function Chapter({
  number,
  title,
  children,
}: {
  number: string;
  title: string;
  children?: ReactNode;
}) {
  return (
    <div className="chapter-heading">
      <span className="chapter-number" aria-hidden="true">
        {number}
      </span>
      <div>
        <h2 className="font-heading text-2xl font-semibold sm:text-3xl">
          {title}
        </h2>
        {children && (
          <p className="mt-1 max-w-2xl text-base text-muted-foreground">
            {children}
          </p>
        )}
      </div>
    </div>
  );
}

export function SourceNote({
  href,
  label,
  children,
}: {
  href: string;
  label: string;
  children?: ReactNode;
}) {
  return (
    <div className="source-note">
      <p>
        Fonte:{' '}
        <a href={href} target="_blank" rel="noreferrer">
          {label}
          <span className="sr-only"> (abre em uma nova aba)</span>
        </a>
      </p>
      {children && <p>{children}</p>}
    </div>
  );
}

export function ChartKey({
  items,
}: {
  items: Array<{ label: string; color: string; dashed?: boolean }>;
}) {
  return (
    <ul className="chart-key" aria-label="Legenda do gráfico">
      {items.map(({ label, color, dashed }) => (
        <li key={label}>
          <span
            aria-hidden="true"
            style={{
              borderColor: color,
              borderTopStyle: dashed ? 'dashed' : 'solid',
            }}
          />
          {label}
        </li>
      ))}
    </ul>
  );
}

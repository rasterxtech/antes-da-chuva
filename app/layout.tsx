import type { Metadata } from 'next';
import '@fontsource/atkinson-hyperlegible/latin-400.css';
import '@fontsource/atkinson-hyperlegible/latin-700.css';
import './globals.css';

export const metadata: Metadata = {
  metadataBase: new URL('https://antesdachuva.info'),
  title: 'Antes da Chuva | Leitura pública municipal',
  description:
    'Histórico de ocorrências ligadas à chuva, evidências federais de prevenção e acesso aos canais oficiais de alerta em uma leitura municipal transparente.',
  openGraph: {
    title: 'Antes da Chuva',
    description:
      'Dados públicos para entender o que a chuva já causou e quais evidências de prevenção podem ser verificadas no seu município.',
    locale: 'pt_BR',
    type: 'website',
    images: [
      {
        url: '/og.png',
        width: 1200,
        height: 630,
        alt: 'Antes da Chuva, leitura pública municipal',
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Antes da Chuva',
    description:
      'Uma leitura municipal curta, transparente e baseada em dados públicos.',
    images: ['/og.png'],
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pt-BR">
      <body>{children}</body>
    </html>
  );
}

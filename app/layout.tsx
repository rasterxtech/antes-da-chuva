import type { Metadata } from 'next';
import { Geist, Geist_Mono } from 'next/font/google';
import './globals.css';

const geistSans = Geist({
  variable: '--font-geist-sans',
  subsets: ['latin'],
});

const geistMono = Geist_Mono({
  variable: '--font-geist-mono',
  subsets: ['latin'],
});

export const metadata: Metadata = {
  metadataBase: new URL('https://antes-da-chuva.felipeflumignan.chatgpt.site'),
  title: 'Antes da Chuva — Leitura pública municipal',
  description:
    'Histórico de desastres ligados à chuva e condições dos domicílios em uma leitura municipal curta, transparente e baseada em dados públicos.',
  openGraph: {
    title: 'Antes da Chuva',
    description:
      'Dados públicos para entender o que a chuva já causou e quais evidências de prevenção podem ser comprovadas no seu município.',
    locale: 'pt_BR',
    type: 'website',
    images: [
      {
        url: '/og.png',
        width: 1200,
        height: 630,
        alt: 'Antes da Chuva — leitura pública municipal',
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
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        {children}
      </body>
    </html>
  );
}

import type { Metadata, Viewport } from "next";
import { Montserrat } from "next/font/google";
import { Suspense } from "react";
import "./globals.css";
import { Nav } from "@/components/sidebar/Nav";
import { Filters } from "@/components/sidebar/Filters";
import { SidebarShell } from "@/components/sidebar/SidebarShell";
import { getLigues, getSaisons } from "@/lib/queries/referentiels";
import { getLocale } from "@/lib/i18n/getLocale";
import { I18nProvider } from "@/components/i18n/I18nProvider";
import { getTheme } from "@/lib/theme/getTheme";
import { ThemeProvider } from "@/components/theme/ThemeProvider";

const montserrat = Montserrat({
  variable: "--font-montserrat",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "RadarPépites",
  description: "Analyse U23 · 10 ligues européennes",
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
};

export default async function RootLayout({ children }: LayoutProps<"/">) {
  const [ligues, saisons, locale, theme] = await Promise.all([
    getLigues(),
    getSaisons(),
    getLocale(),
    getTheme(),
  ]);

  return (
    <html
      lang={locale}
      data-theme={theme}
      className={`${montserrat.variable} h-full antialiased`}
    >
      <head>
        <link
          rel="stylesheet"
          href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..300,0,0"
        />
      </head>
      <body className="min-h-full flex flex-col md:flex-row bg-bg text-text">
        <ThemeProvider theme={theme}>
          <I18nProvider locale={locale}>
            <SidebarShell
              sidebar={
                <>
                  <Nav />
                  <Suspense fallback={null}>
                    <Filters ligues={ligues} saisons={saisons} />
                  </Suspense>
                </>
              }
            >
              {children}
            </SidebarShell>
          </I18nProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}

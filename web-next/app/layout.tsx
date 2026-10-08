import type { Metadata, Viewport } from "next";
import { Geist } from "next/font/google";
import { Suspense } from "react";
import "./globals.css";
import { Nav } from "@/components/sidebar/Nav";
import { Filters } from "@/components/sidebar/Filters";
import { SidebarShell } from "@/components/sidebar/SidebarShell";
import { getLigues, getSaisons } from "@/lib/queries/referentiels";

const geistSans = Geist({
  variable: "--font-geist-sans",
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
  const [ligues, saisons] = await Promise.all([getLigues(), getSaisons()]);

  return (
    <html lang="fr" className={`${geistSans.variable} h-full antialiased`}>
      <head>
        <link
          rel="stylesheet"
          href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..300,0,0"
        />
      </head>
      <body className="min-h-full flex flex-col md:flex-row bg-bg text-text">
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
      </body>
    </html>
  );
}

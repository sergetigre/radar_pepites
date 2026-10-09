import { NextRequest } from "next/server";

const SOFASCORE_BASE = "https://www.sofascore.com/api/v1";
const ALLOWED_KINDS = new Set(["player", "team", "unique-tournament"]);

// Proxy + cache des images Sofascore (hotlinkées directement auparavant,
// cf. lib/media.ts). Sofascore (protégé par Cloudflare, cf. commit scraper
// 573ad47) renvoie des 403 intermittents dès qu'un visiteur charge
// plusieurs dizaines d'images en rafale depuis son navigateur — en passant
// par cette route, les requêtes sont regroupées côté serveur et mises en
// cache (Data Cache Next.js + Cache-Control CDN), donc chaque image n'est
// re-demandée à Sofascore qu'une fois par mois au pire, quel que soit le
// nombre de visiteurs.
const CACHE_SECONDS = 60 * 60 * 24 * 30; // 30 jours

async function fetchWithRetry(url: string, attempts = 3): Promise<Response | null> {
  for (let i = 0; i < attempts; i++) {
    const res = await fetch(url, {
      headers: {
        "User-Agent":
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        Referer: "https://www.sofascore.com/",
      },
      next: { revalidate: CACHE_SECONDS },
    });
    if (res.ok) return res;
    if (res.status !== 403) return res;
    await new Promise((r) => setTimeout(r, 300 * (i + 1)));
  }
  return null;
}

export async function GET(
  _req: NextRequest,
  { params }: { params: Promise<{ kind: string; id: string }> }
) {
  const { kind, id } = await params;
  if (!ALLOWED_KINDS.has(kind) || !/^\d+$/.test(id)) {
    return new Response(null, { status: 404 });
  }

  const upstream = await fetchWithRetry(`${SOFASCORE_BASE}/${kind}/${id}/image`);
  if (!upstream || !upstream.ok) {
    return new Response(null, { status: 404 });
  }

  const buf = await upstream.arrayBuffer();
  const contentType = upstream.headers.get("content-type") ?? "image/png";

  return new Response(buf, {
    headers: {
      "Content-Type": contentType,
      "Cache-Control": `public, max-age=${CACHE_SECONDS}, stale-while-revalidate=86400, immutable`,
    },
  });
}

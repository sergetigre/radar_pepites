import { NextRequest } from "next/server";
import { query } from "@/lib/db";

const ALLOWED_KINDS = new Set(["player", "team", "unique-tournament"]);

// Sert les images Sofascore (logos clubs/ligues, photos joueurs) depuis
// public.media_assets au lieu de les hotlinker — Sofascore (Cloudflare)
// bloque systématiquement les requêtes serveur-à-serveur, hotlink direct
// comme proxy avec fetch(), vérifié manuellement sur les deux. Les images
// sont téléchargées une fois via un vrai navigateur (etl/extract/
// download_media_assets.py) et stockées en base ; cette route ne fait que
// les relire, avec un Cache-Control long pour que le CDN Vercel ne
// rappelle quasiment jamais cette fonction pour une même image.
const CACHE_SECONDS = 60 * 60 * 24 * 30; // 30 jours

export async function GET(
  _req: NextRequest,
  { params }: { params: Promise<{ kind: string; id: string }> }
) {
  const { kind, id } = await params;
  if (!ALLOWED_KINDS.has(kind) || !/^\d+$/.test(id)) {
    return new Response(null, { status: 404 });
  }

  const rows = await query<{ content_type: string; data: Buffer }>`
    SELECT content_type, data FROM public.media_assets
    WHERE kind = ${kind} AND entity_id = ${Number(id)}
  `;
  const row = rows[0];
  if (!row) {
    return new Response(null, { status: 404 });
  }

  return new Response(new Uint8Array(row.data), {
    headers: {
      "Content-Type": row.content_type,
      "Cache-Control": `public, max-age=${CACHE_SECONDS}, immutable`,
    },
  });
}

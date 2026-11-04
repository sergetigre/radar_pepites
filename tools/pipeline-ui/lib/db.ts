import { neon } from "@neondatabase/serverless";

const databaseUrl = process.env.DATABASE_URL;

if (!databaseUrl) {
  throw new Error("DATABASE_URL introuvable (.env.local) — copier celle de web-next/.env.local.");
}

// Lecture seule ici : l'écriture dans public.pipeline_runs reste gérée par
// tools/pipeline_shared.py (via run_step_cli.py, lancé en subprocess par
// app/api/run/route.ts), pour ne pas dupliquer la logique de tracking.
export const sql = neon(databaseUrl);

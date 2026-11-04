import { NextResponse } from "next/server";
import { sql } from "@/lib/db";

export async function GET() {
  const runs = await sql`
    SELECT run_id, stage, step, status, started_at, finished_at, error
    FROM public.pipeline_runs
    ORDER BY started_at DESC
    LIMIT 50
  `;

  const lastSuccess = await sql`
    SELECT DISTINCT ON (step) step, started_at, finished_at
    FROM public.pipeline_runs
    WHERE status = 'success'
    ORDER BY step, started_at DESC
  `;

  const running = await sql`
    SELECT step FROM public.pipeline_runs WHERE status = 'running'
  `;

  return NextResponse.json({ runs, lastSuccess, runningSteps: running.map((r) => r.step) });
}

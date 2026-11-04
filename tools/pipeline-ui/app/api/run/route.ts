import { NextRequest } from "next/server";
import { spawn, type ChildProcess } from "child_process";
import path from "path";
import { STEPS_BY_KEY, type StepKey } from "@/lib/pipelineConfig";
import { sql } from "@/lib/db";

export const runtime = "nodejs";

// Process Python résolu explicitement plutôt que la commande "python" nue :
// sur cette machine (et probablement d'autres installs Windows avec le
// "App Execution Alias" du Store actif), spawn("python", ...) depuis Node
// atterrit sur le stub WindowsApps\python.exe, qui plante immédiatement
// (exit code 0xC0000005 / access violation, zéro sortie) quand il est lancé
// sans contexte console/shell attaché — reproductible, confirmé en isolant
// le problème (fonctionne via bash, casse via spawn() direct). PYTHON_BIN
// dans .env.local permet de pointer vers le vrai interpréteur ; à défaut on
// retombe sur "python" (fonctionne tel quel sur la plupart des setups
// macOS/Linux/Windows sans cette ambiguïté).
const PYTHON_BIN = process.env.PYTHON_BIN || "python";

// Process actifs par step, pour permettre Stop (tué sinon introuvable une
// fois la requête HTTP d'origine repartie). Le process Python lancé ici
// (run_step_cli.py) a lui-même un sous-process (le vrai script de scraping)
// — kill() seul ne tue que run_step_cli.py et laisserait le sous-process
// orphelin tourner sur Windows (pas de kill de l'arbre par défaut), d'où
// taskkill /T côté stop.
const activeProcesses = new Map<StepKey, { pid: number; child: ChildProcess }>();

export async function POST(req: NextRequest) {
  const { step, action } = (await req.json()) as { step?: string; action?: "run" | "stop" };

  if (!step || !(step in STEPS_BY_KEY)) {
    return new Response(`Étape inconnue : ${step}`, { status: 400 });
  }
  const stepKey = step as StepKey;

  if (action === "stop") {
    return stopStep(stepKey);
  }

  const cliPath = path.resolve(process.cwd(), "..", "run_step_cli.py");
  const projectRoot = path.resolve(process.cwd(), "..", "..");

  const child = spawn(PYTHON_BIN, [cliPath, stepKey], { cwd: projectRoot });
  if (child.pid) activeProcesses.set(stepKey, { pid: child.pid, child });

  const stream = new ReadableStream({
    start(controller) {
      const encoder = new TextEncoder();
      child.stdout.on("data", (chunk) => controller.enqueue(encoder.encode(chunk.toString())));
      child.stderr.on("data", (chunk) => controller.enqueue(encoder.encode(chunk.toString())));
      child.on("close", (code) => {
        activeProcesses.delete(stepKey);
        controller.enqueue(encoder.encode(`\n__DONE__${code}\n`));
        controller.close();
      });
      child.on("error", (err) => {
        activeProcesses.delete(stepKey);
        controller.enqueue(encoder.encode(`\nErreur de lancement : ${err.message}\n__DONE__1\n`));
        controller.close();
      });
    },
    cancel() {
      activeProcesses.delete(stepKey);
      child.kill();
    },
  });

  return new Response(stream, {
    headers: { "Content-Type": "text/plain; charset=utf-8", "Cache-Control": "no-cache" },
  });
}

async function stopStep(stepKey: StepKey): Promise<Response> {
  const entry = activeProcesses.get(stepKey);
  if (!entry) {
    return new Response(JSON.stringify({ stopped: false, reason: "not_running" }), {
      headers: { "Content-Type": "application/json" },
    });
  }

  // taskkill /T tue tout l'arbre (run_step_cli.py + le vrai script Python
  // qu'il a lancé) — child.kill() seul ne tue que run_step_cli.py et
  // laisserait le scraping continuer en orphelin sur Windows.
  if (process.platform === "win32") {
    spawn("taskkill", ["/pid", String(entry.pid), "/T", "/F"]);
  } else {
    entry.child.kill("SIGTERM");
  }
  activeProcesses.delete(stepKey);

  // run_step_cli.py n'a pas eu l'occasion d'appeler update_run_finish() —
  // la ligne pipeline_runs resterait bloquée à 'running' indéfiniment sinon
  // (même symptôme que le bug de timeout DB déjà rencontré, cause différente).
  await sql`
    UPDATE public.pipeline_runs
    SET status = 'stopped', finished_at = NOW(), error = 'Arrêté manuellement depuis la vue visuelle.'
    WHERE step = ${stepKey} AND status = 'running'
  `;

  return new Response(JSON.stringify({ stopped: true }), {
    headers: { "Content-Type": "application/json" },
  });
}

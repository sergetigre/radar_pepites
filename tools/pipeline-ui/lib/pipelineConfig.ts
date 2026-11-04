// Config du pipeline — structure fixe (pas d'édition du flux, cf. notice).
// Mêmes clés que tools/pipeline_shared.py::STEPS, pour que les statuts lus
// dans public.pipeline_runs correspondent exactement aux step déclenchés
// par tools/run_step_cli.py.

export type Stage = "collecte" | "consolidation" | "modelisation";

export const STAGE_LABELS: Record<Stage, string> = {
  collecte: "① Collecte",
  consolidation: "② Consolidation",
  modelisation: "③ Modélisation",
};

// Même palette que le schéma BI publié (artifact "Pipeline BI — outil par
// étape") : amber/teal/violet par étape, pour rester visuellement cohérent
// entre les deux représentations du même pipeline.
export const STAGE_COLORS: Record<Stage, { accent: string; bg: string }> = {
  collecte: { accent: "#e0a458", bg: "#e0a4581a" },
  consolidation: { accent: "#4ecdc4", bg: "#4ecdc41a" },
  modelisation: { accent: "#a78bfa", bg: "#a78bfa1a" },
};

export type StepKey = "fbref" | "sofascore" | "images" | "silver" | "public" | "score" | "gold_views";

export type StepConfig = {
  key: StepKey;
  stage: Stage;
  label: string;
  description: string;
  position: { x: number; y: number };
};

export const STEPS: StepConfig[] = [
  {
    key: "fbref",
    stage: "collecte",
    label: "FBref",
    description: "Scrape fbref.com (5 ligues) via soccerdata.",
    position: { x: 0, y: 0 },
  },
  {
    key: "sofascore",
    stage: "collecte",
    label: "Sofascore stats + profils",
    description: "Scrape Sofascore (10 ligues, stats + bios) via navigateur réel (Cloudflare).",
    position: { x: 300, y: 0 },
  },
  {
    key: "images",
    stage: "collecte",
    label: "Images",
    description: "Télécharge logos clubs/ligues + photos joueurs vers public.media_assets.",
    position: { x: 620, y: 0 },
  },
  {
    key: "silver",
    stage: "consolidation",
    label: "Bronze → Silver",
    description: "Nettoie et fusionne les CSV bruts FBref + Sofascore dans silver.*.",
    position: { x: 150, y: 200 },
  },
  {
    key: "public",
    stage: "modelisation",
    label: "Silver → Public",
    description: "Reconstruit dim_* et fact_stats depuis silver.*.",
    position: { x: 150, y: 400 },
  },
  {
    key: "score",
    stage: "modelisation",
    label: "Score Pépite",
    description: "Percentiles par poste/saison, pondération, Score Pépite.",
    position: { x: 450, y: 400 },
  },
  {
    key: "gold_views",
    stage: "modelisation",
    label: "Vues Gold",
    description: "Redéploie les vues gold.* (DDL, rapide, pas de scraping).",
    position: { x: 750, y: 400 },
  },
];

export const STEPS_BY_KEY: Record<StepKey, StepConfig> = Object.fromEntries(
  STEPS.map((s) => [s.key, s])
) as Record<StepKey, StepConfig>;

// Dépendances réelles, pour les arêtes du canvas — Images n'alimente rien
// d'autre (écrit directement media_assets), pas d'arête sortante.
export const EDGES: { source: StepKey; target: StepKey }[] = [
  { source: "fbref", target: "silver" },
  { source: "sofascore", target: "silver" },
  { source: "silver", target: "public" },
  { source: "public", target: "score" },
  { source: "score", target: "gold_views" },
];

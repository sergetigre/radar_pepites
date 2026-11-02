-- RadarPépites — Historique des exécutions du pipeline ETL
-- Alimenté par tools/pipeline_dashboard.py (tableau de bord local de
-- pilotage des alimentations) : chaque clic sur un bouton "lancer"
-- insère une ligne au démarrage et la met à jour à la fin.

CREATE TABLE IF NOT EXISTS public.pipeline_runs (
    run_id          SERIAL      PRIMARY KEY,
    stage           TEXT        NOT NULL,   -- 'collecte' | 'consolidation' | 'modelisation'
    step            TEXT        NOT NULL,   -- 'fbref' | 'sofascore' | 'images' | 'silver' | 'public' | 'score' | 'gold_views'
    status          TEXT        NOT NULL DEFAULT 'running',  -- 'running' | 'success' | 'failed'
    started_at      TIMESTAMP   NOT NULL DEFAULT NOW(),
    finished_at     TIMESTAMP,
    log_tail        TEXT,
    error           TEXT
);

COMMENT ON TABLE public.pipeline_runs IS
    'Historique des lancements manuels du pipeline ETL via tools/pipeline_dashboard.py (outil local, hors site public).';

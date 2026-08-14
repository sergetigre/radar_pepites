-- RadarPépites — Colonnes sources manquantes pour gold_builder.py (Score Pépite)
-- Contexte : gold_builder.py suppose que fact_stats porte déjà des colonnes
-- *_p90 défensives/creation et des stats gardien qui n'avaient jamais été
-- propagées depuis silver. Ce fichier ajoute les colonnes manquantes aux 3
-- niveaux (silver.players_combined, silver.keepers_combined, public.fact_stats).

-- silver.players_combined : dégagements/90, calculable (clearances_ss/minutes_ss*90)
-- mais jamais matérialisé.
ALTER TABLE silver.players_combined
    ADD COLUMN IF NOT EXISTS degagements_p90 FLOAT;

-- silver.keepers_combined : % longs ballons réussis, déjà scrapé côté
-- Sofascore (keepers_sofascore.accurate_long_balls_pct) mais jamais ramené
-- dans keepers_combined.
ALTER TABLE silver.keepers_combined
    ADD COLUMN IF NOT EXISTS long_balls_pct FLOAT;

-- public.fact_stats : 5 colonnes joueurs de champ (déjà calculées en silver,
-- jamais propagées) + 5 colonnes gardien (idem).
ALTER TABLE public.fact_stats
    ADD COLUMN IF NOT EXISTS key_passes_p90    FLOAT,
    ADD COLUMN IF NOT EXISTS dribbles_p90      FLOAT,
    ADD COLUMN IF NOT EXISTS tackles_p90       FLOAT,
    ADD COLUMN IF NOT EXISTS interceptions_p90 FLOAT,
    ADD COLUMN IF NOT EXISTS degagements_p90   FLOAT,
    ADD COLUMN IF NOT EXISTS saves_p90         FLOAT,
    ADD COLUMN IF NOT EXISTS goals_prevented   FLOAT,
    ADD COLUMN IF NOT EXISTS save_pct          FLOAT,
    ADD COLUMN IF NOT EXISTS clean_sheets_pct  FLOAT,
    ADD COLUMN IF NOT EXISTS long_balls_pct    FLOAT;

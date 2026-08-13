-- =============================================================
-- RadarPépites - Index de performance (schéma public)
-- Fichier  : 07_create_indexes.sql
-- Exécuter : en dernier
-- Optimisent les requêtes Power BI et les filtres Python
-- =============================================================

-- fact_stats : colonnes de filtre/jointure les plus fréquentes
CREATE INDEX IF NOT EXISTS idx_fact_joueur     ON fact_stats(joueur_id);
CREATE INDEX IF NOT EXISTS idx_fact_equipe     ON fact_stats(equipe_id);
CREATE INDEX IF NOT EXISTS idx_fact_ligue      ON fact_stats(ligue_id);
CREATE INDEX IF NOT EXISTS idx_fact_saison     ON fact_stats(saison_id);
CREATE INDEX IF NOT EXISTS idx_fact_poste      ON fact_stats(poste_id);
CREATE INDEX IF NOT EXISTS idx_fact_u23        ON fact_stats(est_u23);
CREATE INDEX IF NOT EXISTS idx_fact_minutes    ON fact_stats(minutes);

-- dim_joueurs : recherche par identifiants sources
CREATE INDEX IF NOT EXISTS idx_joueur_dob      ON dim_joueurs(date_naissance);
CREATE INDEX IF NOT EXISTS idx_joueur_fbref    ON dim_joueurs(fbref_id);
CREATE INDEX IF NOT EXISTS idx_joueur_ss       ON dim_joueurs(player_id_ss);

-- dim_equipes : recherche par identifiants sources
CREATE INDEX IF NOT EXISTS idx_equipe_fbref    ON dim_equipes(fbref_squad_id);
CREATE INDEX IF NOT EXISTS idx_equipe_ss       ON dim_equipes(team_id_ss);

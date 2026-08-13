-- =============================================================
-- RadarPépites - Table de faits
-- Fichier  : 03_create_facts.sql
-- Exécuter : après 01 et 02
-- =============================================================


-- -------------------------------------------------------------
-- fact_stats
-- Une ligne = un joueur dans une équipe pour une saison
-- Clé de déduplication : (joueur_id, equipe_id, saison_id)
-- Un joueur transféré en cours de saison = 2 lignes distinctes
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS fact_stats (

    -- Clé technique
    stat_id             SERIAL      PRIMARY KEY,

    -- Clés étrangères (schéma en étoile)
    joueur_id           TEXT        NOT NULL REFERENCES dim_joueurs(joueur_id),
    equipe_id           TEXT        NOT NULL REFERENCES dim_equipes(equipe_id),
    ligue_id            TEXT        NOT NULL REFERENCES dim_ligues(ligue_id),
    saison_id           TEXT        NOT NULL REFERENCES dim_saisons(saison_id),
    poste_id            TEXT        REFERENCES dim_postes(poste_id),

    -- Identité au moment du scraping
    age                 INT,                                -- Age au moment de la saison
    est_u23             BOOLEAN     GENERATED ALWAYS AS (
                            age <= 23
                        ) STORED,                          -- Flag calculé automatiquement

    -- Temps de jeu
    matchs_joues        INT,
    matchs_titulaire    INT,
    minutes             INT,
    minutes_p90         FLOAT       GENERATED ALWAYS AS (
                            minutes::FLOAT / 90.0
                        ) STORED,                          -- Nombre de 90 minutes joués

    -- Statistiques offensives brutes
    buts                FLOAT,
    passes_dec          FLOAT,
    buts_sans_pen       FLOAT,                             -- Buts hors penaltys (meilleur indicateur)
    penaltys_marques    FLOAT,
    penaltys_tentes     FLOAT,
    tirs                FLOAT,
    tirs_cadres         FLOAT,

    -- Expected Goals (xG)
    xg                  FLOAT,                             -- Expected Goals
    xag                 FLOAT,                             -- Expected Assisted Goals
    xg_sans_pen         FLOAT,                             -- xG hors penaltys

    -- Métriques /90 minutes (normalisées pour comparaisons équitables)
    buts_p90            FLOAT,
    passes_dec_p90      FLOAT,
    buts_sans_pen_p90   FLOAT,
    xg_p90              FLOAT,
    xag_p90             FLOAT,
    xg_sans_pen_p90     FLOAT,
    tirs_p90            FLOAT,
    tirs_cadres_p90     FLOAT,

    -- Passes et création
    passes_tentees      FLOAT,
    passes_reussies     FLOAT,
    passes_pct          FLOAT,                             -- % passes réussies
    passes_prog         FLOAT,                             -- Passes progressives
    passes_longues_pct  FLOAT,                             -- % passes longues réussies

    -- Progression balle
    courses_prog        FLOAT,                             -- Courses progressives
    receptions_prog     FLOAT,                             -- Réceptions en zone progressive

    -- Dribbles et duels
    dribbles_tentes     FLOAT,
    dribbles_reuss      FLOAT,
    dribbles_pct        FLOAT,                             -- % dribbles réussis
    duels_gagnes        FLOAT,
    duels_aeriens_pct   FLOAT,                             -- % duels aériens gagnés

    -- Défense
    tacles_tentes       FLOAT,
    tacles_reuss        FLOAT,
    interceptions       FLOAT,
    degagements         FLOAT,
    fautes_commises     FLOAT,
    fautes_subies       FLOAT,

    -- Pressing
    pressing            FLOAT,                             -- Actions de pressing tentées
    pressing_reuss      FLOAT,                             -- Pressing aboutissant à une récupération

    -- Discipline
    cartons_jaunes      INT,
    cartons_rouges      INT,

    -- Source et traçabilité
    source              TEXT        DEFAULT 'fbref',        -- Source de la donnée
    date_scraping       TIMESTAMP,                          -- Date exacte du scraping
    date_maj            TIMESTAMP   DEFAULT NOW(),          -- Dernière mise à jour

    -- Contrainte de déduplication
    CONSTRAINT uq_joueur_equipe_saison UNIQUE (joueur_id, equipe_id, saison_id)
);

COMMENT ON TABLE  fact_stats IS 'Table de faits centrale - stats par joueur par équipe par saison';
COMMENT ON COLUMN fact_stats.est_u23         IS 'Flag U23 calculé automatiquement depuis l''âge - ne pas alimenter manuellement';
COMMENT ON COLUMN fact_stats.minutes_p90     IS 'Nombre de matchs complets équivalents joués - dénominateur pour les stats /90';
COMMENT ON COLUMN fact_stats.buts_sans_pen   IS 'Buts hors penaltys - indicateur de performance plus fiable que les buts totaux';
COMMENT ON COLUMN fact_stats.xg_sans_pen     IS 'xG hors penaltys - même logique, comparaison entre attaquants plus équitable';
COMMENT ON COLUMN fact_stats.pressing        IS 'Nombre de fois où le joueur a pressé un adversaire en possession';


-- -------------------------------------------------------------
-- Index de performance
-- Optimisent les requêtes Power BI et les filtres Python
-- -------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_fact_joueur     ON fact_stats(joueur_id);
CREATE INDEX IF NOT EXISTS idx_fact_equipe     ON fact_stats(equipe_id);
CREATE INDEX IF NOT EXISTS idx_fact_ligue      ON fact_stats(ligue_id);
CREATE INDEX IF NOT EXISTS idx_fact_saison     ON fact_stats(saison_id);
CREATE INDEX IF NOT EXISTS idx_fact_poste      ON fact_stats(poste_id);
CREATE INDEX IF NOT EXISTS idx_fact_u23        ON fact_stats(est_u23);
CREATE INDEX IF NOT EXISTS idx_fact_minutes    ON fact_stats(minutes);
CREATE INDEX IF NOT EXISTS idx_joueur_dob      ON dim_joueurs(date_naissance);
CREATE INDEX IF NOT EXISTS idx_joueur_fbref    ON dim_joueurs(fbref_id);

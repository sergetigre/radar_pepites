-- =============================================================
-- RadarPépites - Tables physiques Gold (schéma gold)
-- Fichier  : 08_create_gold_tables.sql
-- Exécuter : après 06_create_gold_views.sql
-- N'affecte pas le schéma public (dim_*/fact_stats), conservé
-- tel quel. Pas de dim_equipes : équipe dénormalisée
-- (team_name/team_id) directement dans les tables de faits.
-- Alimentation : etl/load/load_gold_tables.py
-- =============================================================


-- -------------------------------------------------------------
-- gold.dim_ligues
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS gold.dim_ligues (
    ligue_id          TEXT PRIMARY KEY,
    nom_complet       TEXT NOT NULL,
    nom_court         TEXT,
    pays              TEXT,
    rang_projet       INT,
    couleur_hex       TEXT,
    coefficient_uefa  FLOAT
);


-- -------------------------------------------------------------
-- gold.dim_saisons
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS gold.dim_saisons (
    saison_id     TEXT PRIMARY KEY,
    annee_debut   INT,
    annee_fin     INT,
    saison_courte TEXT,
    est_courante  BOOLEAN DEFAULT FALSE
);


-- -------------------------------------------------------------
-- gold.dim_postes
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS gold.dim_postes (
    poste_id        TEXT PRIMARY KEY,
    poste_label_fr  TEXT NOT NULL,
    famille         TEXT NOT NULL,
    metriques_radar JSONB
);


-- -------------------------------------------------------------
-- gold.dim_nationalites
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS gold.dim_nationalites (
    nationalite_id     TEXT PRIMARY KEY,
    nom_fr             TEXT NOT NULL,
    continent          TEXT,
    confederation_fifa TEXT
);


-- -------------------------------------------------------------
-- gold.dim_joueurs
-- Une ligne par joueur (champ + gardiens confondus, identifiés
-- par player_id_ss). poste_principal = 'GK' pour les gardiens.
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS gold.dim_joueurs (
    player_id_ss     BIGINT PRIMARY KEY,
    player_name      TEXT,
    nom_court         TEXT,
    date_naissance    DATE,
    nationalite_id    TEXT REFERENCES gold.dim_nationalites(nationalite_id),
    poste_principal   TEXT REFERENCES gold.dim_postes(poste_id),
    pied_dominant     TEXT,
    taille_cm         INT,
    date_maj          TIMESTAMP DEFAULT NOW()
);


-- -------------------------------------------------------------
-- gold.fact_joueurs
-- Une ligne par joueur de champ x équipe x saison.
-- Contient TOUS les joueurs (pas seulement U23) ; is_u23 permet
-- de filtrer côté Power BI/Streamlit. Percentiles précalculés
-- par (poste_principal, saison_id) sur l'ensemble de la table.
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS gold.fact_joueurs (
    fact_id                 SERIAL  PRIMARY KEY,
    player_id_ss            BIGINT  NOT NULL REFERENCES gold.dim_joueurs(player_id_ss),
    ligue_id                TEXT    NOT NULL REFERENCES gold.dim_ligues(ligue_id),
    saison_id               TEXT    NOT NULL REFERENCES gold.dim_saisons(saison_id),
    team_name               TEXT,
    team_id                 BIGINT,
    is_u23                  BOOLEAN,

    -- Stats brutes Sofascore
    goals_ss                FLOAT,
    assists_ss              FLOAT,
    xg_ss                   FLOAT,
    xa_ss                   FLOAT,
    shots_on_target_ss      FLOAT,
    key_passes_ss           FLOAT,
    accurate_passes_pct_ss  FLOAT,
    successful_dribbles_ss  FLOAT,
    tackles_ss               FLOAT,
    interceptions_ss        FLOAT,
    clearances_ss            FLOAT,
    minutes_ss                INT,
    appearances_ss             INT,
    rating_ss                   FLOAT,

    -- Stats fbref (Big 5 uniquement)
    goals_fb                FLOAT,
    assists_fb               FLOAT,
    shots_on_target_fb       FLOAT,
    aerial_won_pct_fb        FLOAT,
    minutes_fb                INT,
    has_fbref_data          BOOLEAN DEFAULT FALSE,

    -- Métriques /90
    goals_p90               FLOAT,
    assists_p90              FLOAT,
    xg_p90                   FLOAT,
    xa_p90                    FLOAT,
    shots_p90                 FLOAT,
    key_passes_p90             FLOAT,
    tackles_p90                 FLOAT,
    interceptions_p90            FLOAT,
    dribbles_p90                  FLOAT,

    -- Percentiles précalculés (0-100, par poste_principal + saison_id)
    pct_goals_p90            FLOAT,
    pct_xg_p90                FLOAT,
    pct_assists_p90            FLOAT,
    pct_key_passes_p90          FLOAT,
    pct_dribbles_p90              FLOAT,
    pct_shots_p90                  FLOAT,
    pct_tackles_p90                 FLOAT,
    pct_interceptions_p90             FLOAT,
    pct_passes_pct                     FLOAT,

    date_maj                TIMESTAMP DEFAULT NOW(),

    CONSTRAINT uq_fact_joueurs UNIQUE (player_id_ss, saison_id, team_id)
);

CREATE INDEX IF NOT EXISTS idx_fj_ligue   ON gold.fact_joueurs(ligue_id);
CREATE INDEX IF NOT EXISTS idx_fj_saison  ON gold.fact_joueurs(saison_id);
CREATE INDEX IF NOT EXISTS idx_fj_u23     ON gold.fact_joueurs(is_u23);
CREATE INDEX IF NOT EXISTS idx_fj_player  ON gold.fact_joueurs(player_id_ss);


-- -------------------------------------------------------------
-- gold.fact_gardiens
-- Une ligne par gardien x équipe x saison. Percentiles
-- précalculés par saison_id sur l'ensemble de la table.
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS gold.fact_gardiens (
    fact_id                 SERIAL  PRIMARY KEY,
    player_id_ss            BIGINT  NOT NULL REFERENCES gold.dim_joueurs(player_id_ss),
    ligue_id                TEXT    NOT NULL REFERENCES gold.dim_ligues(ligue_id),
    saison_id               TEXT    NOT NULL REFERENCES gold.dim_saisons(saison_id),
    team_name                TEXT,
    is_u23                    BOOLEAN,

    -- Stats Sofascore
    saves_ss                 FLOAT,
    goals_prevented_ss        FLOAT,
    rating_ss                  FLOAT,
    minutes_ss                  INT,
    appearances_ss                INT,

    -- Stats fbref (Big 5 uniquement)
    saves_fb                 FLOAT,
    save_pct_fb                FLOAT,
    goals_against_p90_fb        FLOAT,
    clean_sheets_fb               INT,
    clean_sheets_pct_fb            FLOAT,
    pk_saved_fb                      INT,
    has_fbref_data           BOOLEAN DEFAULT FALSE,

    -- /90
    saves_p90                FLOAT,

    -- Percentiles précalculés (0-100, par saison_id)
    pct_saves_p90             FLOAT,
    pct_goals_prevented         FLOAT,

    date_maj                 TIMESTAMP DEFAULT NOW(),

    CONSTRAINT uq_fact_gardiens UNIQUE (player_id_ss, saison_id, team_name)
);

CREATE INDEX IF NOT EXISTS idx_fg_ligue   ON gold.fact_gardiens(ligue_id);
CREATE INDEX IF NOT EXISTS idx_fg_saison  ON gold.fact_gardiens(saison_id);
CREATE INDEX IF NOT EXISTS idx_fg_u23     ON gold.fact_gardiens(is_u23);
CREATE INDEX IF NOT EXISTS idx_fg_player  ON gold.fact_gardiens(player_id_ss);

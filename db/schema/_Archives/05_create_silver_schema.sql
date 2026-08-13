-- ═══════════════════════════════════════════════════════════════
-- RadarPépites — Couche Silver + Gold
-- 05_create_silver_schema.sql
-- ═══════════════════════════════════════════════════════════════

CREATE SCHEMA IF NOT EXISTS silver;
CREATE SCHEMA IF NOT EXISTS gold;

-- ─────────────────────────────────────────
-- RÉFÉRENTIELS SILVER
-- ─────────────────────────────────────────

CREATE TABLE IF NOT EXISTS silver.ref_ligues (
    ligue_id          TEXT PRIMARY KEY,
    nom_complet       TEXT NOT NULL,
    nom_court         TEXT,
    pays              TEXT,
    confederation     TEXT DEFAULT 'UEFA',
    coefficient_uefa  FLOAT,
    rang_projet       INT,
    couleur_hex       TEXT,
    soccerdata_key    TEXT,
    fbref_comp_id     INT,
    tournament_id_ss  INT
);

CREATE TABLE IF NOT EXISTS silver.ref_pays (
    pays_id            TEXT PRIMARY KEY,
    nom_fr             TEXT NOT NULL,
    nom_en             TEXT,
    continent          TEXT,
    confederation_fifa TEXT
);

CREATE TABLE IF NOT EXISTS silver.ref_nationalites (
    nationalite_id     TEXT PRIMARY KEY,
    nom_fr             TEXT NOT NULL,
    pays_id            TEXT REFERENCES silver.ref_pays(pays_id),
    confederation_fifa TEXT
);

CREATE TABLE IF NOT EXISTS silver.ref_postes (
    poste_id        TEXT PRIMARY KEY,
    poste_label_fr  TEXT NOT NULL,
    famille         TEXT NOT NULL,
    metriques_radar JSONB
);

CREATE TABLE IF NOT EXISTS silver.ref_saisons (
    saison_id    TEXT PRIMARY KEY,
    annee_debut  INT,
    annee_fin    INT,
    saison_courte TEXT,
    est_courante BOOLEAN DEFAULT FALSE
);

-- ─────────────────────────────────────────
-- DIMENSION JOUEURS
-- ─────────────────────────────────────────

CREATE TABLE IF NOT EXISTS silver.players_info (
    player_id_ss      BIGINT PRIMARY KEY,
    player_name       TEXT,
    nom_court         TEXT,
    date_naissance    DATE,
    annee_naissance   INT,
    is_u23            BOOLEAN,
    nationalite_id    TEXT,
    nationalite2_id   TEXT,
    poste_principal   TEXT,
    poste_detail      TEXT,
    pied_dominant     TEXT,
    taille_cm         INT,
    poids_kg          INT,
    player_name_fbref TEXT,
    born_fbref        INT,
    date_maj          TIMESTAMP DEFAULT NOW()
);

-- ─────────────────────────────────────────
-- FAITS JOUEURS DE CHAMP
-- ─────────────────────────────────────────

CREATE TABLE IF NOT EXISTS silver.players_fbref (
    id                      SERIAL PRIMARY KEY,
    player_name             TEXT,
    born                    INT,
    team                    TEXT,
    nation                  TEXT,
    pos                     TEXT,
    ligue_id                TEXT REFERENCES silver.ref_ligues(ligue_id),
    saison_id               TEXT REFERENCES silver.ref_saisons(saison_id),
    matches_played          INT,
    starts                  INT,
    minutes                 INT,
    minutes_90s             FLOAT,
    goals                   FLOAT,
    assists                 FLOAT,
    goals_no_pk             FLOAT,
    yellow_cards            INT,
    red_cards               INT,
    shots                   FLOAT,
    shots_on_target         FLOAT,
    shots_on_target_pct     FLOAT,
    shots_p90               FLOAT,
    shots_on_target_p90     FLOAT,
    xg                      FLOAT,
    xag                     FLOAT,
    fouls_committed         FLOAT,
    fouls_drawn             FLOAT,
    interceptions           FLOAT,
    tackles_won             FLOAT,
    aerial_won              FLOAT,
    aerial_lost             FLOAT,
    aerial_won_pct          FLOAT,
    is_u23                  BOOLEAN,
    source                  TEXT DEFAULT 'fbref',
    date_maj                TIMESTAMP DEFAULT NOW(),
    UNIQUE (player_name, born, team, saison_id)
);

CREATE TABLE IF NOT EXISTS silver.players_sofascore (
    id                      SERIAL PRIMARY KEY,
    player_id_ss            BIGINT,
    player_name             TEXT,
    team_name               TEXT,
    team_id                 BIGINT,
    ligue_id                TEXT REFERENCES silver.ref_ligues(ligue_id),
    saison_id               TEXT REFERENCES silver.ref_saisons(saison_id),
    rating                  FLOAT,
    goals                   FLOAT,
    assists                 FLOAT,
    expected_goals          FLOAT,
    expected_assists        FLOAT,
    shots_on_target         FLOAT,
    total_shots             FLOAT,
    big_chances_created     FLOAT,
    big_chances_missed      FLOAT,
    accurate_passes         FLOAT,
    accurate_passes_pct     FLOAT,
    key_passes              FLOAT,
    accurate_long_balls     FLOAT,
    accurate_long_balls_pct FLOAT,
    successful_dribbles     FLOAT,
    successful_dribbles_pct FLOAT,
    tackles                 FLOAT,
    interceptions           FLOAT,
    clearances              FLOAT,
    possession_lost         FLOAT,
    minutes_played          INT,
    appearances             INT,
    yellow_cards            INT,
    red_cards               INT,
    goals_p90               FLOAT,
    assists_p90             FLOAT,
    xg_p90                  FLOAT,
    xa_p90                  FLOAT,
    shots_on_target_p90     FLOAT,
    key_passes_p90          FLOAT,
    tackles_p90             FLOAT,
    interceptions_p90       FLOAT,
    is_u23                  BOOLEAN,
    source                  TEXT DEFAULT 'sofascore',
    date_maj                TIMESTAMP DEFAULT NOW(),
    UNIQUE (player_id_ss, team_id, saison_id)
);

-- ─────────────────────────────────────────
-- TABLE COMBINÉE PRINCIPALE
-- ─────────────────────────────────────────

CREATE TABLE IF NOT EXISTS silver.players_combined (
    id                       SERIAL PRIMARY KEY,
    player_id_ss             BIGINT,
    player_name              TEXT,
    born                     INT,
    date_naissance           DATE,
    is_u23                   BOOLEAN,
    nationalite_id           TEXT,
    poste_principal          TEXT,
    pied_dominant            TEXT,
    taille_cm                INT,
    team_name                TEXT,
    team_id                  BIGINT,
    ligue_id                 TEXT REFERENCES silver.ref_ligues(ligue_id),
    saison_id                TEXT REFERENCES silver.ref_saisons(saison_id),
    -- Sofascore
    rating                   FLOAT,
    goals_ss                 FLOAT,
    assists_ss               FLOAT,
    xg_ss                    FLOAT,
    xa_ss                    FLOAT,
    shots_on_target_ss       FLOAT,
    key_passes_ss            FLOAT,
    accurate_passes_ss       FLOAT,
    accurate_passes_pct_ss   FLOAT,
    successful_dribbles_ss   FLOAT,
    tackles_ss               FLOAT,
    interceptions_ss         FLOAT,
    clearances_ss            FLOAT,
    minutes_ss               INT,
    appearances_ss           INT,
    -- FBref (Big 5 uniquement)
    goals_fb                 FLOAT,
    assists_fb               FLOAT,
    shots_fb                 FLOAT,
    shots_on_target_fb       FLOAT,
    tackles_won_fb           FLOAT,
    interceptions_fb         FLOAT,
    aerial_won_pct_fb        FLOAT,
    minutes_fb               INT,
    -- Métriques /90
    goals_p90                FLOAT,
    assists_p90              FLOAT,
    xg_p90                   FLOAT,
    xa_p90                   FLOAT,
    shots_p90                FLOAT,
    key_passes_p90           FLOAT,
    tackles_p90              FLOAT,
    interceptions_p90        FLOAT,
    dribbles_p90             FLOAT,
    -- Flags
    has_fbref_data           BOOLEAN DEFAULT FALSE,
    has_sofascore_data       BOOLEAN DEFAULT FALSE,
    date_maj                 TIMESTAMP DEFAULT NOW(),
    UNIQUE (player_id_ss, saison_id, team_id)
);

-- ─────────────────────────────────────────
-- FAITS GARDIENS
-- ─────────────────────────────────────────

CREATE TABLE IF NOT EXISTS silver.keepers_sofascore (
    id                      SERIAL PRIMARY KEY,
    player_id_ss            BIGINT,
    player_name             TEXT,
    team_name               TEXT,
    team_id                 BIGINT,
    ligue_id                TEXT REFERENCES silver.ref_ligues(ligue_id),
    saison_id               TEXT REFERENCES silver.ref_saisons(saison_id),
    saves                   FLOAT,
    goals_prevented         FLOAT,
    rating                  FLOAT,
    minutes_played          INT,
    appearances             INT,
    accurate_passes         FLOAT,
    accurate_long_balls     FLOAT,
    accurate_long_balls_pct FLOAT,
    yellow_cards            INT,
    red_cards               INT,
    saves_p90               FLOAT,
    is_u23                  BOOLEAN,
    source                  TEXT DEFAULT 'sofascore',
    date_maj                TIMESTAMP DEFAULT NOW(),
    UNIQUE (player_id_ss, team_id, saison_id)
);

CREATE TABLE IF NOT EXISTS silver.keepers_fbref (
    id                       SERIAL PRIMARY KEY,
    player_name              TEXT,
    born                     INT,
    team                     TEXT,
    nation                   TEXT,
    ligue_id                 TEXT REFERENCES silver.ref_ligues(ligue_id),
    saison_id                TEXT REFERENCES silver.ref_saisons(saison_id),
    matches_played           INT,
    minutes                  INT,
    goals_against            FLOAT,
    goals_against_p90        FLOAT,
    shots_on_target_against  FLOAT,
    saves                    FLOAT,
    save_pct                 FLOAT,
    wins                     INT,
    draws                    INT,
    losses                   INT,
    clean_sheets             INT,
    clean_sheets_pct         FLOAT,
    pk_attempted             INT,
    pk_allowed               INT,
    pk_saved                 INT,
    pk_missed                INT,
    pk_save_pct              FLOAT,
    is_u23                   BOOLEAN,
    source                   TEXT DEFAULT 'fbref',
    date_maj                 TIMESTAMP DEFAULT NOW(),
    UNIQUE (player_name, born, team, saison_id)
);

CREATE TABLE IF NOT EXISTS silver.keepers_combined (
    id                   SERIAL PRIMARY KEY,
    player_id_ss         BIGINT,
    player_name          TEXT,
    born                 INT,
    date_naissance       DATE,
    is_u23               BOOLEAN,
    nationalite_id       TEXT,
    team_name            TEXT,
    team_id              BIGINT,
    ligue_id             TEXT REFERENCES silver.ref_ligues(ligue_id),
    saison_id            TEXT REFERENCES silver.ref_saisons(saison_id),
    saves_ss             FLOAT,
    goals_prevented_ss   FLOAT,
    rating_ss            FLOAT,
    minutes_ss           INT,
    appearances_ss       INT,
    saves_fb             FLOAT,
    save_pct_fb          FLOAT,
    goals_against_fb     FLOAT,
    goals_against_p90_fb FLOAT,
    clean_sheets_fb      INT,
    clean_sheets_pct_fb  FLOAT,
    pk_saved_fb          INT,
    saves_p90            FLOAT,
    has_fbref_data       BOOLEAN DEFAULT FALSE,
    has_sofascore_data   BOOLEAN DEFAULT FALSE,
    date_maj             TIMESTAMP DEFAULT NOW(),
    UNIQUE (player_id_ss, saison_id, team_id)
);

-- ─────────────────────────────────────────
-- INDEX PERFORMANCE
-- ─────────────────────────────────────────

CREATE INDEX IF NOT EXISTS idx_sp_ligue   ON silver.players_combined(ligue_id);
CREATE INDEX IF NOT EXISTS idx_sp_saison  ON silver.players_combined(saison_id);
CREATE INDEX IF NOT EXISTS idx_sp_u23     ON silver.players_combined(is_u23);
CREATE INDEX IF NOT EXISTS idx_sp_poste   ON silver.players_combined(poste_principal);
CREATE INDEX IF NOT EXISTS idx_sk_ligue   ON silver.keepers_combined(ligue_id);
CREATE INDEX IF NOT EXISTS idx_sk_u23     ON silver.keepers_combined(is_u23);

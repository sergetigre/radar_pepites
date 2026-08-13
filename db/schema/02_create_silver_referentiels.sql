-- =============================================================
-- RadarPépites - Référentiels silver
-- Fichier  : 02_create_silver_referentiels.sql
-- Exécuter : après 01_create_schemas.sql
-- =============================================================


-- -------------------------------------------------------------
-- silver.ref_ligues
-- -------------------------------------------------------------
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


-- -------------------------------------------------------------
-- silver.ref_saisons
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS silver.ref_saisons (
    saison_id     TEXT PRIMARY KEY,
    annee_debut   INT,
    annee_fin     INT,
    saison_courte TEXT,
    est_courante  BOOLEAN DEFAULT FALSE
);


-- -------------------------------------------------------------
-- silver.ref_pays
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS silver.ref_pays (
    pays_id            TEXT PRIMARY KEY,
    nom_fr             TEXT NOT NULL,
    nom_en             TEXT,
    continent          TEXT,
    confederation_fifa TEXT
);


-- -------------------------------------------------------------
-- silver.ref_nationalites
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS silver.ref_nationalites (
    nationalite_id     TEXT PRIMARY KEY,
    nom_fr             TEXT NOT NULL,
    pays_id            TEXT REFERENCES silver.ref_pays(pays_id),
    confederation_fifa TEXT
);


-- -------------------------------------------------------------
-- silver.ref_postes
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS silver.ref_postes (
    poste_id        TEXT PRIMARY KEY,
    poste_label_fr  TEXT NOT NULL,
    famille         TEXT NOT NULL,
    metriques_radar JSONB
);

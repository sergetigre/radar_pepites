-- =============================================================
-- RadarPépites - Schéma dimensions
-- Fichier  : 01_create_dimensions.sql
-- Exécuter : en premier, avant les faits et les vues
-- =============================================================


-- -------------------------------------------------------------
-- dim_ligues
-- Référentiel des 10 championnats européens
-- Très stable : rarement modifié après création initiale
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dim_ligues (
    ligue_id            TEXT        PRIMARY KEY,            -- Ex : 'ENG', 'ESP'
    nom_complet         TEXT        NOT NULL,               -- 'Premier League'
    nom_court           TEXT        NOT NULL,               -- 'PL'
    pays                TEXT        NOT NULL,               -- 'Angleterre'
    confederation       TEXT        NOT NULL DEFAULT 'UEFA',
    coefficient_uefa    FLOAT,                              -- Coefficient UEFA officiel
    rang_projet         INT,                                -- Ordre priorité RadarPépites (1-10)
    soccerdata_key      TEXT,                               -- Clé API soccerdata : 'ENG-Premier League'
    fbref_comp_id       INT,                                -- ID compétition fbref (pour URL scraping)
    couleur_hex         TEXT,                               -- Couleur dédiée pour les visuels web
    date_maj            TIMESTAMP   DEFAULT NOW()
);

COMMENT ON TABLE  dim_ligues IS 'Référentiel des 10 championnats couverts par RadarPépites';
COMMENT ON COLUMN dim_ligues.soccerdata_key IS 'Clé exacte attendue par la librairie soccerdata';
COMMENT ON COLUMN dim_ligues.fbref_comp_id  IS 'Identifiant numérique fbref utilisé dans les URLs de scraping';
COMMENT ON COLUMN dim_ligues.couleur_hex    IS 'Code couleur HEX pour les visuels Plotly et le site web';


-- -------------------------------------------------------------
-- dim_saisons
-- Référentiel temporel - indispensable pour l'analyse N vs N-1
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dim_saisons (
    saison_id           TEXT        PRIMARY KEY,            -- '2024-2025'
    annee_debut         INT         NOT NULL,               -- 2024
    annee_fin           INT         NOT NULL,               -- 2025
    saison_courte       TEXT        NOT NULL,               -- '24/25' (pour les labels visuels)
    est_saison_courante BOOLEAN     NOT NULL DEFAULT FALSE,  -- Filtre rapide Power BI
    date_maj            TIMESTAMP   DEFAULT NOW()
);

COMMENT ON TABLE  dim_saisons IS 'Référentiel temporel des saisons footballistiques';
COMMENT ON COLUMN dim_saisons.est_saison_courante IS 'TRUE pour la saison active uniquement - permet des filtres rapides en DAX';


-- -------------------------------------------------------------
-- dim_nationalites
-- Référentiel géographique des nationalités
-- Permet des analyses par pays, continent, confédération FIFA
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dim_nationalites (
    nationalite_id          TEXT    PRIMARY KEY,            -- Code ISO 3 lettres : 'FRA', 'BRA'
    nom_fr                  TEXT    NOT NULL,               -- 'France', 'Brésil'
    continent               TEXT,                           -- 'Europe', 'Afrique', 'Amérique du Sud'...
    confederation_fifa      TEXT,                           -- 'UEFA', 'CAF', 'CONMEBOL', 'AFC', 'CONCACAF', 'OFC'
    date_maj                TIMESTAMP DEFAULT NOW()
);

COMMENT ON TABLE  dim_nationalites IS 'Référentiel des nationalités pour analyses géographiques';
COMMENT ON COLUMN dim_nationalites.confederation_fifa IS 'Confédération FIFA : UEFA, CAF, CONMEBOL, AFC, CONCACAF, OFC';


-- -------------------------------------------------------------
-- dim_postes
-- Référentiel des postes avec regroupement par famille
-- Critique : les métriques radar varient selon le poste
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dim_postes (
    poste_id            TEXT    PRIMARY KEY,                -- 'FW', 'MF', 'DF', 'GK'
    poste_label_fr      TEXT    NOT NULL,                   -- 'Attaquant', 'Milieu', 'Défenseur', 'Gardien'
    poste_detail        TEXT,                               -- 'Ailier gauche', 'Défenseur central'...
    famille             TEXT    NOT NULL,                   -- Regroupement haut niveau pour filtres
    metriques_cles      JSONB,                              -- Métriques prioritaires pour les radars de ce poste
    date_maj            TIMESTAMP DEFAULT NOW()
);

COMMENT ON TABLE  dim_postes IS 'Référentiel des postes avec métriques radar associées par poste';
COMMENT ON COLUMN dim_postes.metriques_cles IS 'JSON listant les axes prioritaires du radar selon le poste : ex {"axes": ["xg_p90", "buts_p90", "dribbles_reuss"]}';


-- -------------------------------------------------------------
-- dim_joueurs
-- Référentiel des joueurs - données identitaires stables
-- Source principale : fbref + transfermarkt (phase 2)
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dim_joueurs (
    joueur_id               TEXT    PRIMARY KEY,            -- ID unique fbref
    nom_complet             TEXT    NOT NULL,               -- Nom affiché complet
    nom_court               TEXT,                           -- Prénom + initiale ou surnom (pour visuels)
    date_naissance          DATE,                           -- Calcul âge dynamique + filtre U23
    nationalite_principale  TEXT    REFERENCES dim_nationalites(nationalite_id),
    deuxieme_nationalite    TEXT    REFERENCES dim_nationalites(nationalite_id),
    poste_principal         TEXT    REFERENCES dim_postes(poste_id),
    poste_detail            TEXT,                           -- Précision fbref brute
    pied_dominant           TEXT,                           -- 'Droit', 'Gauche', 'Les deux'
    taille_cm               INT,                            -- Source : transfermarkt (phase 2)
    poids_kg                INT,                            -- Source : transfermarkt (phase 2)
    fbref_id                TEXT    NOT NULL UNIQUE,        -- ID scraping fbref (construction URLs)
    transfermarkt_id        TEXT,                           -- Clé jointure transfermarkt (phase 2)
    date_maj                TIMESTAMP DEFAULT NOW()
);

COMMENT ON TABLE  dim_joueurs IS 'Référentiel identitaire des joueurs - données stables scraping fbref + transfermarkt';
COMMENT ON COLUMN dim_joueurs.nom_court             IS 'Version courte pour les labels radar et classements';
COMMENT ON COLUMN dim_joueurs.deuxieme_nationalite  IS 'Important pour analyse recrutement (bi-nationaux)';
COMMENT ON COLUMN dim_joueurs.fbref_id              IS 'Identifiant fbref utilisé pour construire les URLs de scraping par joueur';
COMMENT ON COLUMN dim_joueurs.transfermarkt_id      IS 'Renseigné en phase 2 pour jointure valeur marchande';


-- -------------------------------------------------------------
-- dim_equipes
-- Référentiel des clubs
-- Un joueur peut changer de club en cours de saison :
-- → les deux clubs apparaissent comme lignes distinctes en fact_stats
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dim_equipes (
    equipe_id           TEXT    PRIMARY KEY,                -- ID unique fbref
    nom_complet         TEXT    NOT NULL,                   -- Nom officiel
    nom_court           TEXT,                               -- Sigle ou surnom (pour visuels)
    ligue_id            TEXT    REFERENCES dim_ligues(ligue_id),
    pays                TEXT,
    fbref_squad_id      TEXT    NOT NULL UNIQUE,            -- ID squad fbref (construction URLs)
    transfermarkt_id    TEXT,                               -- Clé jointure phase 2
    date_maj            TIMESTAMP DEFAULT NOW()
);

COMMENT ON TABLE  dim_equipes IS 'Référentiel des clubs des 10 championnats couverts';
COMMENT ON COLUMN dim_equipes.fbref_squad_id    IS 'ID squad fbref pour les URLs de scraping par équipe';
COMMENT ON COLUMN dim_equipes.transfermarkt_id  IS 'Renseigné en phase 2 pour jointure valeur marchande de l''équipe';

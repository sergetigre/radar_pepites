-- =============================================================
-- RadarPépites - Tables finales Gold (schéma public)
-- Fichier  : 05_create_public_tables.sql
-- Exécuter : après 04_create_silver_tables.sql
-- Remplace : l'ancien 01_create_dimensions.sql + 03_create_facts.sql
-- Ces tables sont consommées directement par Power BI et sont
-- alimentées depuis silver.* par l'étape de load.
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
-- Source : silver.players_info (fbref + Sofascore via datafc)
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dim_joueurs (
    joueur_id               TEXT    PRIMARY KEY,            -- ID interne projet
    nom_complet             TEXT    NOT NULL,               -- Nom affiché complet
    nom_court               TEXT,                           -- Prénom + initiale ou surnom (pour visuels)
    date_naissance          DATE,                           -- Calcul âge dynamique + filtre U23
    nationalite_principale  TEXT    REFERENCES dim_nationalites(nationalite_id),
    deuxieme_nationalite    TEXT    REFERENCES dim_nationalites(nationalite_id),
    poste_principal         TEXT    REFERENCES dim_postes(poste_id),
    poste_detail            TEXT,                           -- Précision fbref brute
    pied_dominant           TEXT,                           -- 'Droit', 'Gauche', 'Les deux'
    taille_cm               INT,                            -- Source : Sofascore via datafc
    poids_kg                INT,                            -- Source : Sofascore via datafc
    fbref_id                TEXT    UNIQUE,                 -- ID scraping fbref (Big 5 uniquement)
    player_id_ss            BIGINT  UNIQUE,                 -- ID Sofascore (10 ligues)
    transfermarkt_id        TEXT,                           -- Clé jointure transfermarkt (phase 2)
    date_maj                TIMESTAMP DEFAULT NOW()
);

COMMENT ON TABLE  dim_joueurs IS 'Référentiel identitaire des joueurs - fusion fbref (Big 5) + Sofascore (10 ligues)';
COMMENT ON COLUMN dim_joueurs.nom_court             IS 'Version courte pour les labels radar et classements';
COMMENT ON COLUMN dim_joueurs.deuxieme_nationalite  IS 'Important pour analyse recrutement (bi-nationaux)';
COMMENT ON COLUMN dim_joueurs.fbref_id              IS 'Identifiant fbref - NULL pour les joueurs des ligues 6-10 (hors Big 5)';
COMMENT ON COLUMN dim_joueurs.player_id_ss          IS 'Identifiant Sofascore (datafc) - couvre les 10 ligues';
COMMENT ON COLUMN dim_joueurs.transfermarkt_id      IS 'Renseigné en phase 2 pour jointure valeur marchande';


-- -------------------------------------------------------------
-- dim_equipes
-- Référentiel des clubs
-- Un joueur peut changer de club en cours de saison :
-- → les deux clubs apparaissent comme lignes distinctes en fact_stats
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dim_equipes (
    equipe_id           TEXT    PRIMARY KEY,                -- ID interne projet
    nom_complet         TEXT    NOT NULL,                   -- Nom officiel
    nom_court           TEXT,                               -- Sigle ou surnom (pour visuels)
    ligue_id            TEXT    REFERENCES dim_ligues(ligue_id),
    pays                TEXT,
    fbref_squad_id      TEXT    UNIQUE,                     -- ID squad fbref (Big 5 uniquement)
    team_id_ss          BIGINT  UNIQUE,                     -- ID équipe Sofascore (10 ligues)
    transfermarkt_id    TEXT,                               -- Clé jointure phase 2
    date_maj            TIMESTAMP DEFAULT NOW()
);

COMMENT ON TABLE  dim_equipes IS 'Référentiel des clubs des 10 championnats couverts';
COMMENT ON COLUMN dim_equipes.fbref_squad_id    IS 'ID squad fbref - NULL pour les ligues hors Big 5';
COMMENT ON COLUMN dim_equipes.team_id_ss        IS 'Identifiant équipe Sofascore (datafc) - couvre les 10 ligues';
COMMENT ON COLUMN dim_equipes.transfermarkt_id  IS 'Renseigné en phase 2 pour jointure valeur marchande de l''équipe';


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

    -- Sofascore : colonnes sans équivalent fbref direct
    rating               FLOAT,                             -- Note Sofascore du match/saison
    big_chances_creees    FLOAT,                             -- Occasions franches créées
    big_chances_manquees   FLOAT,                             -- Occasions franches manquées
    possession_perdue     FLOAT,                             -- Pertes de balle

    -- Source et traçabilité
    source              TEXT        DEFAULT 'fbref',        -- Source principale de la donnée
    has_fbref_data      BOOLEAN     DEFAULT FALSE,          -- Ligne alimentée depuis fbref
    has_sofascore_data  BOOLEAN     DEFAULT FALSE,          -- Ligne alimentée depuis Sofascore
    date_scraping       TIMESTAMP,                          -- Date exacte du scraping
    date_maj            TIMESTAMP   DEFAULT NOW(),          -- Dernière mise à jour

    -- Contrainte de déduplication
    CONSTRAINT uq_joueur_equipe_saison UNIQUE (joueur_id, equipe_id, saison_id)
);

COMMENT ON TABLE  fact_stats IS 'Table de faits centrale - stats par joueur par équipe par saison, fusion fbref + Sofascore';
COMMENT ON COLUMN fact_stats.est_u23         IS 'Flag U23 calculé automatiquement depuis l''âge - ne pas alimenter manuellement';
COMMENT ON COLUMN fact_stats.minutes_p90     IS 'Nombre de matchs complets équivalents joués - dénominateur pour les stats /90';
COMMENT ON COLUMN fact_stats.buts_sans_pen   IS 'Buts hors penaltys - indicateur de performance plus fiable que les buts totaux';
COMMENT ON COLUMN fact_stats.xg_sans_pen     IS 'xG hors penaltys - même logique, comparaison entre attaquants plus équitable';
COMMENT ON COLUMN fact_stats.pressing        IS 'Nombre de fois où le joueur a pressé un adversaire en possession';
COMMENT ON COLUMN fact_stats.rating          IS 'Note de match/saison Sofascore - pas d''équivalent fbref';

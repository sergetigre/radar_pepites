-- =============================================================
-- RadarPépites - Données initiales des référentiels
-- Fichier  : 02_insert_referentiels.sql
-- Exécuter : après 01_create_dimensions.sql
-- =============================================================


-- -------------------------------------------------------------
-- dim_ligues : les 10 championnats du projet
-- -------------------------------------------------------------
INSERT INTO dim_ligues (ligue_id, nom_complet, nom_court, pays, confederation, coefficient_uefa, rang_projet, soccerdata_key, fbref_comp_id, couleur_hex)
VALUES
    ('ENG', 'Premier League',        'PL',      'Angleterre', 'UEFA', 104.33, 1,  'ENG-Premier League',     9,   '#3D195B'),
    ('ESP', 'La Liga',               'Liga',    'Espagne',    'UEFA',  96.33, 2,  'ESP-La Liga',            12,  '#EE2523'),
    ('GER', 'Bundesliga',            'BL',      'Allemagne',  'UEFA',  86.16, 3,  'GER-Bundesliga',         20,  '#D3010C'),
    ('ITA', 'Serie A',               'SerieA',  'Italie',     'UEFA',  78.83, 4,  'ITA-Serie A',            11,  '#024494'),
    ('FRA', 'Ligue 1',               'L1',      'France',     'UEFA',  66.83, 5,  'FRA-Ligue 1',            13,  '#FFFFFF'),
    ('POR', 'Primeira Liga',         'PL PT',   'Portugal',   'UEFA',  55.00, 6,  'POR-Primeira Liga',      32,  '#006600'),
    ('NED', 'Eredivisie',            'Ere',     'Pays-Bas',   'UEFA',  52.50, 7,  'NED-Eredivisie',         23,  '#FF6600'),
    ('BEL', 'First Division A',      'JPL',     'Belgique',   'UEFA',  47.50, 8,  'BEL-First Division A',   37,  '#000000'),
    ('TUR', 'Süper Lig',             'SL',      'Turquie',    'UEFA',  40.50, 9,  'TUR-Super Lig',          26,  '#E30A17'),
    ('AUT', 'Bundesliga Autriche',   'BL AT',   'Autriche',   'UEFA',  37.00, 10, 'AUT-Bundesliga',         44,  '#ED2939')
ON CONFLICT (ligue_id) DO NOTHING;


-- -------------------------------------------------------------
-- dim_saisons : saisons disponibles
-- -------------------------------------------------------------
INSERT INTO dim_saisons (saison_id, annee_debut, annee_fin, saison_courte, est_saison_courante)
VALUES
    ('2022-2023', 2022, 2023, '22/23', FALSE),
    ('2023-2024', 2023, 2024, '23/24', FALSE),
    ('2024-2025', 2024, 2025, '24/25', TRUE)
ON CONFLICT (saison_id) DO NOTHING;


-- -------------------------------------------------------------
-- dim_postes : référentiel des postes
-- metriques_cles définit les axes radar par poste
-- -------------------------------------------------------------
INSERT INTO dim_postes (poste_id, poste_label_fr, poste_detail, famille, metriques_cles)
VALUES
    ('GK', 'Gardien',           'Gardien de but',           'Gardien',   '{"axes": ["arrets_pct", "xg_concedes", "sorties", "passes_longues_pct", "clean_sheets"]}'),
    ('CB', 'Défenseur central', 'Défenseur central',         'Défenseur', '{"axes": ["tacles_reuss", "interceptions", "duels_aeriens_pct", "passes_prog", "fautes"]}'),
    ('LB', 'Latéral gauche',   'Défenseur latéral gauche',  'Défenseur', '{"axes": ["tacles_reuss", "interceptions", "passes_prog", "courses_prog", "dribbles_reuss"]}'),
    ('RB', 'Latéral droit',    'Défenseur latéral droit',   'Défenseur', '{"axes": ["tacles_reuss", "interceptions", "passes_prog", "courses_prog", "dribbles_reuss"]}'),
    ('DM', 'Milieu défensif',  'Milieu défensif central',   'Milieu',    '{"axes": ["tacles_reuss", "interceptions", "passes_prog", "pressing", "duels_gagnes"]}'),
    ('CM', 'Milieu central',   'Milieu central',             'Milieu',    '{"axes": ["passes_prog", "passes_dec_p90", "xag_p90", "pressing", "courses_prog"]}'),
    ('AM', 'Milieu offensif',  'Milieu offensif / no 10',   'Milieu',    '{"axes": ["xg_p90", "xag_p90", "passes_dec_p90", "dribbles_reuss", "passes_prog"]}'),
    ('LW', 'Ailier gauche',    'Ailier gauche',              'Attaquant', '{"axes": ["xg_p90", "buts_p90", "dribbles_reuss", "courses_prog", "passes_dec_p90"]}'),
    ('RW', 'Ailier droit',     'Ailier droit',               'Attaquant', '{"axes": ["xg_p90", "buts_p90", "dribbles_reuss", "courses_prog", "passes_dec_p90"]}'),
    ('FW', 'Attaquant',        'Avant-centre / attaquant',   'Attaquant', '{"axes": ["xg_p90", "buts_p90", "tirs_cadres_p90", "passes_dec_p90", "duels_aeriens_pct"]}')
ON CONFLICT (poste_id) DO NOTHING;


-- -------------------------------------------------------------
-- dim_nationalites : principales nationalités (non exhaustif)
-- À compléter au fil du scraping
-- -------------------------------------------------------------
INSERT INTO dim_nationalites (nationalite_id, nom_fr, continent, confederation_fifa)
VALUES
    -- Europe
    ('FRA', 'France',           'Europe',           'UEFA'),
    ('ENG', 'Angleterre',       'Europe',           'UEFA'),
    ('ESP', 'Espagne',          'Europe',           'UEFA'),
    ('GER', 'Allemagne',        'Europe',           'UEFA'),
    ('ITA', 'Italie',           'Europe',           'UEFA'),
    ('POR', 'Portugal',         'Europe',           'UEFA'),
    ('NED', 'Pays-Bas',         'Europe',           'UEFA'),
    ('BEL', 'Belgique',         'Europe',           'UEFA'),
    ('TUR', 'Turquie',          'Europe',           'UEFA'),
    ('AUT', 'Autriche',         'Europe',           'UEFA'),
    ('NOR', 'Norvège',          'Europe',           'UEFA'),
    ('DEN', 'Danemark',         'Europe',           'UEFA'),
    ('SWE', 'Suède',            'Europe',           'UEFA'),
    ('CRO', 'Croatie',          'Europe',           'UEFA'),
    ('SRB', 'Serbie',           'Europe',           'UEFA'),
    -- Afrique
    ('CIV', 'Côte d''Ivoire',   'Afrique',          'CAF'),
    ('SEN', 'Sénégal',          'Afrique',          'CAF'),
    ('NGA', 'Nigeria',          'Afrique',          'CAF'),
    ('MAR', 'Maroc',            'Afrique',          'CAF'),
    ('GHA', 'Ghana',            'Afrique',          'CAF'),
    ('MLI', 'Mali',             'Afrique',          'CAF'),
    ('CMR', 'Cameroun',         'Afrique',          'CAF'),
    ('EGY', 'Égypte',           'Afrique',          'CAF'),
    -- Amérique du Sud
    ('BRA', 'Brésil',           'Amérique du Sud',  'CONMEBOL'),
    ('ARG', 'Argentine',        'Amérique du Sud',  'CONMEBOL'),
    ('COL', 'Colombie',         'Amérique du Sud',  'CONMEBOL'),
    ('URU', 'Uruguay',          'Amérique du Sud',  'CONMEBOL'),
    -- Amérique du Nord / Centrale
    ('USA', 'États-Unis',       'Amérique du Nord', 'CONCACAF'),
    ('MEX', 'Mexique',          'Amérique du Nord', 'CONCACAF'),
    -- Asie
    ('JPN', 'Japon',            'Asie',             'AFC'),
    ('KOR', 'Corée du Sud',     'Asie',             'AFC')
ON CONFLICT (nationalite_id) DO NOTHING;

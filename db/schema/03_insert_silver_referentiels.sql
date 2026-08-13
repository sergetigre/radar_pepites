-- =============================================================
-- RadarPépites - Données initiales des référentiels silver
-- Fichier  : 03_insert_silver_referentiels.sql
-- Exécuter : après 02_create_silver_referentiels.sql
-- =============================================================


-- -------------------------------------------------------------
-- silver.ref_ligues : les 10 championnats du projet
-- -------------------------------------------------------------
INSERT INTO silver.ref_ligues (ligue_id, nom_complet, nom_court, pays, confederation, coefficient_uefa, rang_projet, couleur_hex, soccerdata_key, fbref_comp_id, tournament_id_ss)
VALUES
    ('ENG','Premier League','PL','Angleterre','UEFA',104.33,1,'#3D195B','ENG-Premier League',9,17),
    ('ESP','La Liga','Liga','Espagne','UEFA',96.33,2,'#EE2523','ESP-La Liga',12,8),
    ('GER','Bundesliga','BL','Allemagne','UEFA',86.16,3,'#D3010C','GER-Bundesliga',20,35),
    ('ITA','Serie A','SerieA','Italie','UEFA',78.83,4,'#024494','ITA-Serie A',11,23),
    ('FRA','Ligue 1','L1','France','UEFA',66.83,5,'#FFFFFF','FRA-Ligue 1',13,34),
    ('POR','Primeira Liga','PL PT','Portugal','UEFA',55.00,6,'#006600','POR-Primeira Liga',32,238),
    ('NED','Eredivisie','Ere','Pays-Bas','UEFA',52.50,7,'#FF6600','NED-Eredivisie',23,37),
    ('BEL','Pro League','JPL','Belgique','UEFA',47.50,8,'#000000','BEL-First Division A',37,38),
    ('TUR','Süper Lig','SL','Turquie','UEFA',40.50,9,'#E30A17','TUR-Super Lig',26,52),
    ('AUT','Bundesliga AUT','BL AT','Autriche','UEFA',37.00,10,'#ED2939','AUT-Bundesliga',44,45)
ON CONFLICT (ligue_id) DO NOTHING;


-- -------------------------------------------------------------
-- silver.ref_saisons : 4 saisons couvertes, 2025-2026 = courante
-- -------------------------------------------------------------
INSERT INTO silver.ref_saisons (saison_id, annee_debut, annee_fin, saison_courte, est_courante)
VALUES
    ('2022-2023', 2022, 2023, '22/23', FALSE),
    ('2023-2024', 2023, 2024, '23/24', FALSE),
    ('2024-2025', 2024, 2025, '24/25', FALSE),
    ('2025-2026', 2025, 2026, '25/26', TRUE)
ON CONFLICT (saison_id) DO NOTHING;


-- -------------------------------------------------------------
-- silver.ref_postes : 11 postes, axes radar en JSON
-- MF et DF sont des postes génériques (fallback quand la source
-- ne donne pas de détail plus précis) : ils reprennent les axes
-- de CM et CB respectivement.
-- -------------------------------------------------------------
INSERT INTO silver.ref_postes (poste_id, poste_label_fr, famille, metriques_radar)
VALUES
    ('GK', 'Gardien',           'Gardien',   '{"axes": ["saves_p90", "save_pct", "goals_prevented", "clean_sheets_pct", "accurate_long_balls_pct"]}'),
    ('CB', 'Défenseur central', 'Défenseur', '{"axes": ["tackles_p90", "interceptions_p90", "aerial_won_pct", "clearances", "accurate_passes_pct"]}'),
    ('LB', 'Latéral gauche',    'Défenseur', '{"axes": ["tackles_p90", "interceptions_p90", "key_passes_p90", "dribbles_p90", "accurate_passes_pct"]}'),
    ('RB', 'Latéral droit',     'Défenseur', '{"axes": ["tackles_p90", "interceptions_p90", "key_passes_p90", "dribbles_p90", "accurate_passes_pct"]}'),
    ('DF', 'Défenseur',         'Défenseur', '{"axes": ["tackles_p90", "interceptions_p90", "aerial_won_pct", "clearances", "accurate_passes_pct"]}'),
    ('CM', 'Milieu central',    'Milieu',    '{"axes": ["accurate_passes_pct", "key_passes_p90", "tackles_p90", "interceptions_p90", "xg_p90"]}'),
    ('AM', 'Milieu offensif',   'Milieu',    '{"axes": ["xg_p90", "xa_p90", "key_passes_p90", "dribbles_p90", "accurate_passes_pct"]}'),
    ('MF', 'Milieu',            'Milieu',    '{"axes": ["accurate_passes_pct", "key_passes_p90", "tackles_p90", "interceptions_p90", "xg_p90"]}'),
    ('LW', 'Ailier gauche',     'Attaquant', '{"axes": ["xg_p90", "assists_p90", "dribbles_p90", "shots_p90", "key_passes_p90"]}'),
    ('RW', 'Ailier droit',      'Attaquant', '{"axes": ["xg_p90", "assists_p90", "dribbles_p90", "shots_p90", "key_passes_p90"]}'),
    ('FW', 'Attaquant',         'Attaquant', '{"axes": ["xg_p90", "goals_p90", "shots_p90", "assists_p90", "aerial_won_pct"]}')
ON CONFLICT (poste_id) DO NOTHING;


-- -------------------------------------------------------------
-- silver.ref_pays : pays les plus représentés dans le football
-- européen (non exhaustif, à compléter au fil du scraping)
-- -------------------------------------------------------------
INSERT INTO silver.ref_pays (pays_id, nom_fr, nom_en, continent, confederation_fifa)
VALUES
    -- Europe
    ('FRA', 'France',           'France',        'Europe', 'UEFA'),
    ('ENG', 'Angleterre',       'England',       'Europe', 'UEFA'),
    ('ESP', 'Espagne',          'Spain',         'Europe', 'UEFA'),
    ('GER', 'Allemagne',        'Germany',       'Europe', 'UEFA'),
    ('ITA', 'Italie',           'Italy',         'Europe', 'UEFA'),
    ('POR', 'Portugal',         'Portugal',      'Europe', 'UEFA'),
    ('NED', 'Pays-Bas',         'Netherlands',   'Europe', 'UEFA'),
    ('BEL', 'Belgique',         'Belgium',       'Europe', 'UEFA'),
    ('TUR', 'Turquie',          'Turkey',        'Europe', 'UEFA'),
    ('AUT', 'Autriche',         'Austria',       'Europe', 'UEFA'),
    ('NOR', 'Norvège',          'Norway',        'Europe', 'UEFA'),
    ('DEN', 'Danemark',         'Denmark',       'Europe', 'UEFA'),
    ('SWE', 'Suède',            'Sweden',        'Europe', 'UEFA'),
    ('CRO', 'Croatie',          'Croatia',       'Europe', 'UEFA'),
    ('SRB', 'Serbie',           'Serbia',        'Europe', 'UEFA'),
    ('POL', 'Pologne',          'Poland',        'Europe', 'UEFA'),
    ('UKR', 'Ukraine',          'Ukraine',       'Europe', 'UEFA'),
    ('SCO', 'Écosse',           'Scotland',      'Europe', 'UEFA'),
    ('WAL', 'Pays de Galles',   'Wales',         'Europe', 'UEFA'),
    ('IRL', 'Irlande',          'Ireland',       'Europe', 'UEFA'),
    -- Afrique
    ('CIV', 'Côte d''Ivoire',   'Ivory Coast',   'Afrique', 'CAF'),
    ('SEN', 'Sénégal',          'Senegal',       'Afrique', 'CAF'),
    ('NGA', 'Nigeria',          'Nigeria',       'Afrique', 'CAF'),
    ('MAR', 'Maroc',            'Morocco',       'Afrique', 'CAF'),
    ('GHA', 'Ghana',            'Ghana',         'Afrique', 'CAF'),
    ('MLI', 'Mali',             'Mali',          'Afrique', 'CAF'),
    ('CMR', 'Cameroun',         'Cameroon',      'Afrique', 'CAF'),
    ('EGY', 'Égypte',           'Egypt',         'Afrique', 'CAF'),
    ('COD', 'RD Congo',         'DR Congo',      'Afrique', 'CAF'),
    ('GUI', 'Guinée',           'Guinea',        'Afrique', 'CAF'),
    -- Amérique du Sud
    ('BRA', 'Brésil',           'Brazil',        'Amérique du Sud', 'CONMEBOL'),
    ('ARG', 'Argentine',        'Argentina',     'Amérique du Sud', 'CONMEBOL'),
    ('COL', 'Colombie',         'Colombia',      'Amérique du Sud', 'CONMEBOL'),
    ('URU', 'Uruguay',          'Uruguay',       'Amérique du Sud', 'CONMEBOL'),
    ('CHI', 'Chili',            'Chile',         'Amérique du Sud', 'CONMEBOL'),
    ('ECU', 'Équateur',         'Ecuador',       'Amérique du Sud', 'CONMEBOL'),
    ('PAR', 'Paraguay',         'Paraguay',      'Amérique du Sud', 'CONMEBOL'),
    ('PER', 'Pérou',            'Peru',          'Amérique du Sud', 'CONMEBOL'),
    -- Amérique du Nord
    ('USA', 'États-Unis',       'United States', 'Amérique du Nord', 'CONCACAF'),
    ('MEX', 'Mexique',          'Mexico',        'Amérique du Nord', 'CONCACAF'),
    ('CAN', 'Canada',           'Canada',        'Amérique du Nord', 'CONCACAF'),
    ('JAM', 'Jamaïque',         'Jamaica',       'Amérique du Nord', 'CONCACAF'),
    ('CRC', 'Costa Rica',       'Costa Rica',    'Amérique du Nord', 'CONCACAF'),
    -- Asie
    ('JPN', 'Japon',            'Japan',         'Asie', 'AFC'),
    ('KOR', 'Corée du Sud',     'South Korea',   'Asie', 'AFC'),
    ('IRN', 'Iran',             'Iran',          'Asie', 'AFC'),
    ('AUS', 'Australie',        'Australia',     'Asie', 'AFC')
ON CONFLICT (pays_id) DO NOTHING;


-- -------------------------------------------------------------
-- silver.ref_nationalites : reprend ref_pays (nationalite_id = pays_id)
-- -------------------------------------------------------------
INSERT INTO silver.ref_nationalites (nationalite_id, nom_fr, pays_id, confederation_fifa)
SELECT pays_id, nom_fr, pays_id, confederation_fifa
FROM silver.ref_pays
ON CONFLICT (nationalite_id) DO NOTHING;

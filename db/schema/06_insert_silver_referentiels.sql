-- ═══════════════════════════════════════════════════════════════
-- RadarPépites — Référentiels Silver
-- 06_insert_silver_referentiels.sql
-- ═══════════════════════════════════════════════════════════════

-- ─────────────────────────────────────────
-- REF_LIGUES
-- ─────────────────────────────────────────

INSERT INTO silver.ref_ligues
    (ligue_id, nom_complet, nom_court, pays, confederation, coefficient_uefa,
     rang_projet, couleur_hex, soccerdata_key, fbref_comp_id, tournament_id_ss)
VALUES
    ('ENG','Premier League','PL','Angleterre','UEFA',104.33,1,'#3D195B','ENG-Premier League',9,17),
    ('ESP','La Liga','Liga','Espagne','UEFA',96.33,2,'#EE2523','ESP-La Liga',12,8),
    ('GER','Bundesliga','Buli','Allemagne','UEFA',87.83,3,'#D20515','GER-Bundesliga',20,35),
    ('ITA','Serie A','SerieA','Italie','UEFA',73.50,4,'#024494','ITA-Serie A',11,23),
    ('FRA','Ligue 1','L1','France','UEFA',52.83,5,'#FFFFFF','FRA-Ligue 1',13,34),
    ('POR','Primeira Liga','Liga','Portugal','UEFA',48.00,6,'#006600','POR-Primeira Liga',NULL,238),
    ('NED','Eredivisie','Ere','Pays-Bas','UEFA',46.25,7,'#FF6600','NED-Eredivisie',23,37),
    ('BEL','Pro League','JPL','Belgique','UEFA',29.50,8,'#FF0000','BEL-Pro League',37,38),
    ('TUR','Super Lig','SüperLig','Turquie','UEFA',27.50,9,'#E30A17','TUR-Super Lig',26,52),
    ('AUT','Bundesliga Autriche','BL-AUT','Autriche','UEFA',22.50,10,'#ED2939','AUT-Bundesliga',NULL,45)
ON CONFLICT (ligue_id) DO UPDATE SET
    nom_complet      = EXCLUDED.nom_complet,
    nom_court        = EXCLUDED.nom_court,
    pays             = EXCLUDED.pays,
    confederation    = EXCLUDED.confederation,
    coefficient_uefa = EXCLUDED.coefficient_uefa,
    rang_projet      = EXCLUDED.rang_projet,
    couleur_hex      = EXCLUDED.couleur_hex,
    soccerdata_key   = EXCLUDED.soccerdata_key,
    fbref_comp_id    = EXCLUDED.fbref_comp_id,
    tournament_id_ss = EXCLUDED.tournament_id_ss;


-- ─────────────────────────────────────────
-- REF_SAISONS
-- ─────────────────────────────────────────

INSERT INTO silver.ref_saisons
    (saison_id, annee_debut, annee_fin, saison_courte, est_courante)
VALUES
    ('2022-2023', 2022, 2023, '22/23', FALSE),
    ('2023-2024', 2023, 2024, '23/24', FALSE),
    ('2024-2025', 2024, 2025, '24/25', FALSE),
    ('2025-2026', 2025, 2026, '25/26', TRUE)
ON CONFLICT (saison_id) DO UPDATE SET
    annee_debut   = EXCLUDED.annee_debut,
    annee_fin     = EXCLUDED.annee_fin,
    saison_courte = EXCLUDED.saison_courte,
    est_courante  = EXCLUDED.est_courante;


-- ─────────────────────────────────────────
-- REF_POSTES
-- ─────────────────────────────────────────

INSERT INTO silver.ref_postes
    (poste_id, poste_label_fr, famille, metriques_radar)
VALUES
    ('GK',  'Gardien',                  'Gardien',  '["saves_p90","save_pct","goals_prevented","goals_against_p90","clean_sheets_pct"]'),
    ('CB',  'Défenseur Central',        'Défenseur', '["interceptions_p90","tackles_p90","aerial_won_pct","clearances_p90","dribbles_p90"]'),
    ('LB',  'Latéral Gauche',           'Défenseur', '["interceptions_p90","tackles_p90","assists_p90","key_passes_p90","dribbles_p90"]'),
    ('RB',  'Latéral Droit',            'Défenseur', '["interceptions_p90","tackles_p90","assists_p90","key_passes_p90","dribbles_p90"]'),
    ('DM',  'Milieu Défensif',          'Milieu',    '["tackles_p90","interceptions_p90","accurate_passes_pct","key_passes_p90","dribbles_p90"]'),
    ('CM',  'Milieu Central',           'Milieu',    '["key_passes_p90","assists_p90","tackles_p90","xg_p90","dribbles_p90"]'),
    ('AM',  'Milieu Offensif',          'Milieu',    '["key_passes_p90","assists_p90","xg_p90","dribbles_p90","goals_p90"]'),
    ('LW',  'Ailier Gauche',            'Attaquant', '["goals_p90","assists_p90","dribbles_p90","xg_p90","key_passes_p90"]'),
    ('RW',  'Ailier Droit',             'Attaquant', '["goals_p90","assists_p90","dribbles_p90","xg_p90","key_passes_p90"]'),
    ('SS',  'Avant-Centre Second',      'Attaquant', '["goals_p90","xg_p90","assists_p90","key_passes_p90","aerial_won_pct"]'),
    ('ST',  'Avant-Centre',             'Attaquant', '["goals_p90","xg_p90","shots_p90","aerial_won_pct","dribbles_p90"]')
ON CONFLICT (poste_id) DO UPDATE SET
    poste_label_fr  = EXCLUDED.poste_label_fr,
    famille         = EXCLUDED.famille,
    metriques_radar = EXCLUDED.metriques_radar;


-- ─────────────────────────────────────────
-- REF_PAYS
-- ─────────────────────────────────────────

INSERT INTO silver.ref_pays
    (pays_id, nom_fr, nom_en, continent, confederation_fifa)
VALUES
    -- Pays des ligues
    ('ENG', 'Angleterre',    'England',     'Europe',   'UEFA'),
    ('ESP', 'Espagne',       'Spain',       'Europe',   'UEFA'),
    ('GER', 'Allemagne',     'Germany',     'Europe',   'UEFA'),
    ('ITA', 'Italie',        'Italy',       'Europe',   'UEFA'),
    ('FRA', 'France',        'France',      'Europe',   'UEFA'),
    ('POR', 'Portugal',      'Portugal',    'Europe',   'UEFA'),
    ('NED', 'Pays-Bas',      'Netherlands', 'Europe',   'UEFA'),
    ('BEL', 'Belgique',      'Belgium',     'Europe',   'UEFA'),
    ('TUR', 'Turquie',       'Turkey',      'Europe',   'UEFA'),
    ('AUT', 'Autriche',      'Austria',     'Europe',   'UEFA'),
    -- Autres pays européens fréquents
    ('BRA', 'Brésil',        'Brazil',      'Amérique', 'CONMEBOL'),
    ('ARG', 'Argentine',     'Argentina',   'Amérique', 'CONMEBOL'),
    ('URU', 'Uruguay',       'Uruguay',     'Amérique', 'CONMEBOL'),
    ('COL', 'Colombie',      'Colombia',    'Amérique', 'CONMEBOL'),
    ('CHI', 'Chili',         'Chile',       'Amérique', 'CONMEBOL'),
    ('PAR', 'Paraguay',      'Paraguay',    'Amérique', 'CONMEBOL'),
    ('ECU', 'Equateur',      'Ecuador',     'Amérique', 'CONMEBOL'),
    ('PER', 'Pérou',         'Peru',        'Amérique', 'CONMEBOL'),
    ('VEN', 'Venezuela',     'Venezuela',   'Amérique', 'CONMEBOL'),
    ('BOL', 'Bolivie',       'Bolivia',     'Amérique', 'CONMEBOL'),
    ('USA', 'États-Unis',    'USA',         'Amérique', 'CONCACAF'),
    ('MEX', 'Mexique',       'Mexico',      'Amérique', 'CONCACAF'),
    -- Afrique
    ('SEN', 'Sénégal',       'Senegal',     'Afrique',  'CAF'),
    ('NGA', 'Nigeria',       'Nigeria',     'Afrique',  'CAF'),
    ('MAR', 'Maroc',         'Morocco',     'Afrique',  'CAF'),
    ('CIV', 'Côte d''Ivoire','Ivory Coast', 'Afrique',  'CAF'),
    ('CMR', 'Cameroun',      'Cameroon',    'Afrique',  'CAF'),
    ('GHA', 'Ghana',         'Ghana',       'Afrique',  'CAF'),
    ('MLI', 'Mali',          'Mali',        'Afrique',  'CAF'),
    ('GUI', 'Guinée',        'Guinea',      'Afrique',  'CAF'),
    ('ALG', 'Algérie',       'Algeria',     'Afrique',  'CAF'),
    ('EGY', 'Egypte',        'Egypt',       'Afrique',  'CAF'),
    ('TUN', 'Tunisie',       'Tunisia',     'Afrique',  'CAF'),
    -- Europe autres
    ('CRO', 'Croatie',       'Croatia',     'Europe',   'UEFA'),
    ('SRB', 'Serbie',        'Serbia',      'Europe',   'UEFA'),
    ('POL', 'Pologne',       'Poland',      'Europe',   'UEFA'),
    ('DEN', 'Danemark',      'Denmark',     'Europe',   'UEFA'),
    ('NOR', 'Norvège',       'Norway',      'Europe',   'UEFA'),
    ('SWE', 'Suède',         'Sweden',      'Europe',   'UEFA'),
    ('SCO', 'Ecosse',        'Scotland',    'Europe',   'UEFA'),
    ('WAL', 'Pays de Galles','Wales',       'Europe',   'UEFA'),
    ('IRL', 'Irlande',       'Ireland',     'Europe',   'UEFA'),
    ('GRE', 'Grèce',         'Greece',      'Europe',   'UEFA'),
    ('ROU', 'Roumanie',      'Romania',     'Europe',   'UEFA'),
    ('HUN', 'Hongrie',       'Hungary',     'Europe',   'UEFA'),
    ('CZE', 'Tchéquie',      'Czech Rep.',  'Europe',   'UEFA'),
    ('SVK', 'Slovaquie',     'Slovakia',    'Europe',   'UEFA'),
    ('SVN', 'Slovénie',      'Slovenia',    'Europe',   'UEFA'),
    ('UKR', 'Ukraine',       'Ukraine',     'Europe',   'UEFA'),
    ('RUS', 'Russie',        'Russia',      'Europe',   'UEFA'),
    ('SUI', 'Suisse',        'Switzerland', 'Europe',   'UEFA'),
    ('AUT2','Autriche',      'Austria',     'Europe',   'UEFA'),
    -- Asie
    ('JPN', 'Japon',         'Japan',       'Asie',     'AFC'),
    ('KOR', 'Corée du Sud',  'South Korea', 'Asie',     'AFC'),
    ('IRN', 'Iran',          'Iran',        'Asie',     'AFC'),
    ('SAU', 'Arabie Saoudite','Saudi Arabia','Asie',    'AFC'),
    ('QAT', 'Qatar',         'Qatar',       'Asie',     'AFC'),
    ('AUS', 'Australie',     'Australia',   'Asie',     'AFC')
ON CONFLICT (pays_id) DO UPDATE SET
    nom_fr             = EXCLUDED.nom_fr,
    nom_en             = EXCLUDED.nom_en,
    continent          = EXCLUDED.continent,
    confederation_fifa = EXCLUDED.confederation_fifa;


-- ─────────────────────────────────────────
-- REF_NATIONALITES
-- ─────────────────────────────────────────

INSERT INTO silver.ref_nationalites
    (nationalite_id, nom_fr, pays_id, confederation_fifa)
VALUES
    ('ENG', 'Anglais',       'ENG', 'UEFA'),
    ('ESP', 'Espagnol',      'ESP', 'UEFA'),
    ('GER', 'Allemand',      'GER', 'UEFA'),
    ('ITA', 'Italien',       'ITA', 'UEFA'),
    ('FRA', 'Français',      'FRA', 'UEFA'),
    ('POR', 'Portugais',     'POR', 'UEFA'),
    ('NED', 'Néerlandais',   'NED', 'UEFA'),
    ('BEL', 'Belge',         'BEL', 'UEFA'),
    ('TUR', 'Turc',          'TUR', 'UEFA'),
    ('AUT', 'Autrichien',    'AUT', 'UEFA'),
    ('BRA', 'Brésilien',     'BRA', 'CONMEBOL'),
    ('ARG', 'Argentin',      'ARG', 'CONMEBOL'),
    ('URU', 'Uruguayen',     'URU', 'CONMEBOL'),
    ('COL', 'Colombien',     'COL', 'CONMEBOL'),
    ('SEN', 'Sénégalais',    'SEN', 'CAF'),
    ('NGA', 'Nigérian',      'NGA', 'CAF'),
    ('MAR', 'Marocain',      'MAR', 'CAF'),
    ('CIV', 'Ivoirien',      'CIV', 'CAF'),
    ('CMR', 'Camerounais',   'CMR', 'CAF'),
    ('GHA', 'Ghanéen',       'GHA', 'CAF'),
    ('MLI', 'Malien',        'MLI', 'CAF'),
    ('ALG', 'Algérien',      'ALG', 'CAF'),
    ('CRO', 'Croate',        'CRO', 'UEFA'),
    ('SRB', 'Serbe',         'SRB', 'UEFA'),
    ('POL', 'Polonais',      'POL', 'UEFA'),
    ('DEN', 'Danois',        'DEN', 'UEFA'),
    ('NOR', 'Norvégien',     'NOR', 'UEFA'),
    ('SWE', 'Suédois',       'SWE', 'UEFA'),
    ('SUI', 'Suisse',        'SUI', 'UEFA'),
    ('GRE', 'Grec',          'GRE', 'UEFA'),
    ('JPN', 'Japonais',      'JPN', 'AFC'),
    ('KOR', 'Sud-Coréen',    'KOR', 'AFC'),
    ('USA', 'Américain',     'USA', 'CONCACAF'),
    ('MEX', 'Mexicain',      'MEX', 'CONCACAF')
ON CONFLICT (nationalite_id) DO UPDATE SET
    nom_fr             = EXCLUDED.nom_fr,
    pays_id            = EXCLUDED.pays_id,
    confederation_fifa = EXCLUDED.confederation_fifa;

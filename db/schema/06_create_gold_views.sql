-- =============================================================
-- RadarPépites - Vues Gold
-- Fichier  : 06_create_gold_views.sql
-- Exécuter : après 05_create_public_tables.sql (schéma gold créé
--            par 01_create_schemas.sql)
-- Ces vues lisent silver.* et sont consommées par Power BI et
-- Streamlit. Colonnes vérifiées contre le schéma réel de
-- silver.players_combined / keepers_combined / ref_* (cf. note en
-- fin de fichier pour les écarts corrigés par rapport au brief).
-- =============================================================


-- PostgreSQL interdit de renommer les colonnes d'une vue via
-- CREATE OR REPLACE VIEW (uniquement la requête sous-jacente peut
-- changer, pas la liste de colonnes) -> DROP préalable pour
-- permettre de repartir sur des noms de colonnes propres.
DROP VIEW IF EXISTS gold.vue_top_u23_par_ligue CASCADE;
DROP VIEW IF EXISTS gold.vue_radar_joueur CASCADE;
DROP VIEW IF EXISTS gold.vue_progression_saison CASCADE;
DROP VIEW IF EXISTS gold.vue_top_u23_gk CASCADE;
DROP VIEW IF EXISTS gold.vue_comparaison_joueurs CASCADE;


-- -------------------------------------------------------------
-- gold.vue_top_u23_par_ligue
-- Top joueurs U23 par ligue, toutes métriques.
-- Filtre : is_u23 = TRUE ET minutes_ss >= 450
-- -------------------------------------------------------------
CREATE OR REPLACE VIEW gold.vue_top_u23_par_ligue AS
SELECT
    pc.player_id_ss,
    pc.player_name,
    pc.date_naissance,
    DATE_PART('year', AGE(pc.date_naissance)) AS age_actuel,
    pc.poste_principal,
    pc.nationalite_id,
    n.nom_fr AS nationalite_fr,
    n.confederation_fifa,
    pc.team_name,
    pc.ligue_id,
    l.nom_complet AS ligue,
    l.pays,
    l.rang_projet,
    l.couleur_hex,
    pc.saison_id,
    s.saison_courte,
    -- Temps de jeu
    pc.minutes_ss,
    pc.appearances_ss,
    -- Stats offensives
    pc.rating_ss,
    pc.goals_ss,
    pc.assists_ss,
    pc.xg_ss,
    pc.xa_ss,
    pc.shots_on_target_ss,
    ps.big_chances_created AS big_chances_created_ss,
    -- Stats passes
    pc.key_passes_ss,
    pc.accurate_passes_ss,
    pc.accurate_passes_pct_ss,
    -- Stats technique
    pc.successful_dribbles_ss,
    -- Stats défensives
    pc.tackles_ss,
    pc.interceptions_ss,
    pc.clearances_ss,
    -- Métriques /90
    pc.goals_p90,
    pc.assists_p90,
    pc.xg_p90,
    pc.xa_p90,
    pc.shots_p90,
    pc.key_passes_p90,
    pc.tackles_p90,
    pc.interceptions_p90,
    pc.dribbles_p90,
    -- Stats fbref (Big 5 uniquement)
    pc.has_fbref_data,
    pc.shots_on_target_fb,
    pc.aerial_won_pct_fb,
    -- Discipline (silver.players_combined ne les porte pas -> jointure directe)
    ps.yellow_cards AS yellow_cards_ss,
    ps.red_cards AS red_cards_ss
FROM silver.players_combined pc
JOIN silver.ref_ligues l ON pc.ligue_id = l.ligue_id
JOIN silver.ref_saisons s ON pc.saison_id = s.saison_id
LEFT JOIN silver.ref_nationalites n ON pc.nationalite_id = n.nationalite_id
LEFT JOIN silver.players_sofascore ps
    ON ps.player_id_ss = pc.player_id_ss AND ps.team_id = pc.team_id AND ps.saison_id = pc.saison_id
WHERE pc.is_u23 = TRUE
  AND pc.minutes_ss >= 450;

COMMENT ON VIEW gold.vue_top_u23_par_ligue IS 'Top U23 par ligue/saison, filtre 450 min, consommée par Power BI';


-- -------------------------------------------------------------
-- gold.vue_radar_joueur
-- Données normalisées en percentile par poste pour les radars.
-- Filtre : is_u23 = TRUE ET minutes_ss >= 450
-- -------------------------------------------------------------
CREATE OR REPLACE VIEW gold.vue_radar_joueur AS
SELECT
    pc.player_id_ss,
    pc.player_name,
    pc.poste_principal,
    pc.team_name,
    pc.ligue_id,
    l.nom_complet AS ligue,
    l.couleur_hex,
    pc.saison_id,
    -- Métriques brutes /90
    pc.goals_p90,
    pc.assists_p90,
    pc.xg_p90,
    pc.xa_p90,
    pc.shots_p90,
    pc.key_passes_p90,
    pc.tackles_p90,
    pc.interceptions_p90,
    pc.dribbles_p90,
    pc.accurate_passes_pct_ss,
    pc.aerial_won_pct_fb,
    -- Percentiles par poste et saison (0-100)
    ROUND(PERCENT_RANK() OVER (
        PARTITION BY pc.poste_principal, pc.saison_id
        ORDER BY pc.goals_p90
    ) * 100) AS pct_goals_p90,
    ROUND(PERCENT_RANK() OVER (
        PARTITION BY pc.poste_principal, pc.saison_id
        ORDER BY pc.xg_p90
    ) * 100) AS pct_xg_p90,
    ROUND(PERCENT_RANK() OVER (
        PARTITION BY pc.poste_principal, pc.saison_id
        ORDER BY pc.assists_p90
    ) * 100) AS pct_assists_p90,
    ROUND(PERCENT_RANK() OVER (
        PARTITION BY pc.poste_principal, pc.saison_id
        ORDER BY pc.key_passes_p90
    ) * 100) AS pct_key_passes_p90,
    ROUND(PERCENT_RANK() OVER (
        PARTITION BY pc.poste_principal, pc.saison_id
        ORDER BY pc.dribbles_p90
    ) * 100) AS pct_dribbles_p90,
    ROUND(PERCENT_RANK() OVER (
        PARTITION BY pc.poste_principal, pc.saison_id
        ORDER BY pc.shots_p90
    ) * 100) AS pct_shots_p90,
    ROUND(PERCENT_RANK() OVER (
        PARTITION BY pc.poste_principal, pc.saison_id
        ORDER BY pc.tackles_p90
    ) * 100) AS pct_tackles_p90,
    ROUND(PERCENT_RANK() OVER (
        PARTITION BY pc.poste_principal, pc.saison_id
        ORDER BY pc.interceptions_p90
    ) * 100) AS pct_interceptions_p90,
    ROUND(PERCENT_RANK() OVER (
        PARTITION BY pc.poste_principal, pc.saison_id
        ORDER BY pc.accurate_passes_pct_ss
    ) * 100) AS pct_passes_pct
FROM silver.players_combined pc
JOIN silver.ref_ligues l ON pc.ligue_id = l.ligue_id
WHERE pc.is_u23 = TRUE
  AND pc.minutes_ss >= 450;

COMMENT ON VIEW gold.vue_radar_joueur IS 'Percentiles par poste/saison pour les graphiques radar Plotly/Streamlit';


-- -------------------------------------------------------------
-- gold.vue_progression_saison
-- Comparaison N vs N-1 pour les joueurs U23 (même club).
-- -------------------------------------------------------------
CREATE OR REPLACE VIEW gold.vue_progression_saison AS
SELECT
    curr.player_id_ss,
    curr.player_name,
    curr.poste_principal,
    curr.team_name,
    curr.ligue_id,
    curr.saison_id AS saison_curr,
    prev.saison_id AS saison_prev,
    -- Progression goals
    curr.goals_p90 AS goals_p90_curr,
    prev.goals_p90 AS goals_p90_prev,
    ROUND((curr.goals_p90 - prev.goals_p90)::numeric, 3) AS delta_goals_p90,
    -- Progression xG
    curr.xg_p90 AS xg_p90_curr,
    prev.xg_p90 AS xg_p90_prev,
    ROUND((curr.xg_p90 - prev.xg_p90)::numeric, 3) AS delta_xg_p90,
    -- Progression assists
    curr.assists_p90 AS assists_p90_curr,
    prev.assists_p90 AS assists_p90_prev,
    ROUND((curr.assists_p90 - prev.assists_p90)::numeric, 3) AS delta_assists_p90,
    -- Progression minutes
    curr.minutes_ss AS minutes_curr,
    prev.minutes_ss AS minutes_prev,
    curr.minutes_ss - prev.minutes_ss AS delta_minutes,
    -- Progression rating
    curr.rating_ss AS rating_curr,
    prev.rating_ss AS rating_prev,
    ROUND((curr.rating_ss - prev.rating_ss)::numeric, 2) AS delta_rating
FROM silver.players_combined curr
JOIN silver.players_combined prev
    ON curr.player_id_ss = prev.player_id_ss
    AND curr.team_name   = prev.team_name
JOIN silver.ref_saisons s_curr ON curr.saison_id = s_curr.saison_id
JOIN silver.ref_saisons s_prev ON prev.saison_id = s_prev.saison_id
    AND s_prev.annee_debut = s_curr.annee_debut - 1
WHERE curr.is_u23 = TRUE
  AND curr.minutes_ss >= 450
  AND prev.minutes_ss >= 450;

COMMENT ON VIEW gold.vue_progression_saison IS 'Comparaison N vs N-1 (même club) pour identifier les U23 en progression';


-- -------------------------------------------------------------
-- gold.vue_top_u23_gk
-- Top gardiens U23, toutes métriques.
-- Filtre : is_u23 = TRUE ET minutes_ss >= 270
-- -------------------------------------------------------------
CREATE OR REPLACE VIEW gold.vue_top_u23_gk AS
SELECT
    kc.player_id_ss,
    kc.player_name,
    kc.date_naissance,
    DATE_PART('year', AGE(kc.date_naissance)) AS age_actuel,
    kc.nationalite_id,
    kc.team_name,
    kc.ligue_id,
    l.nom_complet AS ligue,
    l.pays,
    l.couleur_hex,
    kc.saison_id,
    s.saison_courte,
    -- Stats Sofascore
    kc.saves_ss,
    kc.goals_prevented_ss,
    kc.rating_ss,
    kc.minutes_ss,
    kc.appearances_ss,
    kc.saves_p90,
    -- Stats fbref Big 5
    kc.has_fbref_data,
    kc.saves_fb,
    kc.save_pct_fb,
    kc.goals_against_fb,
    kc.goals_against_p90_fb,
    kc.clean_sheets_fb,
    kc.clean_sheets_pct_fb,
    kc.pk_saved_fb,
    -- Percentiles GK (par saison)
    ROUND(PERCENT_RANK() OVER (
        PARTITION BY kc.saison_id
        ORDER BY kc.saves_p90
    ) * 100) AS pct_saves_p90,
    ROUND(PERCENT_RANK() OVER (
        PARTITION BY kc.saison_id
        ORDER BY kc.goals_prevented_ss
    ) * 100) AS pct_goals_prevented
FROM silver.keepers_combined kc
JOIN silver.ref_ligues l ON kc.ligue_id = l.ligue_id
JOIN silver.ref_saisons s ON kc.saison_id = s.saison_id
WHERE kc.is_u23 = TRUE
  AND kc.minutes_ss >= 270;

COMMENT ON VIEW gold.vue_top_u23_gk IS 'Top gardiens U23, filtre 270 min (3 matchs équiv.)';


-- -------------------------------------------------------------
-- gold.vue_comparaison_joueurs
-- Comparaison directe de joueurs (Streamlit), tous âges.
-- -------------------------------------------------------------
CREATE OR REPLACE VIEW gold.vue_comparaison_joueurs AS
SELECT
    pc.player_id_ss,
    pc.player_name,
    pc.poste_principal,
    pc.team_name,
    pc.ligue_id,
    l.nom_complet AS ligue,
    l.couleur_hex,
    pc.saison_id,
    pc.minutes_ss,
    pc.rating_ss,
    -- Toutes métriques /90 pour comparaison
    pc.goals_p90,
    pc.assists_p90,
    pc.xg_p90,
    pc.xa_p90,
    pc.shots_p90,
    pc.key_passes_p90,
    pc.dribbles_p90,
    pc.tackles_p90,
    pc.interceptions_p90,
    pc.accurate_passes_pct_ss,
    -- Percentiles pour radar comparatif
    ROUND(PERCENT_RANK() OVER (
        PARTITION BY pc.poste_principal, pc.saison_id
        ORDER BY pc.goals_p90
    ) * 100) AS pct_goals,
    ROUND(PERCENT_RANK() OVER (
        PARTITION BY pc.poste_principal, pc.saison_id
        ORDER BY pc.xg_p90
    ) * 100) AS pct_xg,
    ROUND(PERCENT_RANK() OVER (
        PARTITION BY pc.poste_principal, pc.saison_id
        ORDER BY pc.assists_p90
    ) * 100) AS pct_assists,
    ROUND(PERCENT_RANK() OVER (
        PARTITION BY pc.poste_principal, pc.saison_id
        ORDER BY pc.key_passes_p90
    ) * 100) AS pct_key_passes,
    ROUND(PERCENT_RANK() OVER (
        PARTITION BY pc.poste_principal, pc.saison_id
        ORDER BY pc.dribbles_p90
    ) * 100) AS pct_dribbles,
    ROUND(PERCENT_RANK() OVER (
        PARTITION BY pc.poste_principal, pc.saison_id
        ORDER BY pc.shots_p90
    ) * 100) AS pct_shots,
    ROUND(PERCENT_RANK() OVER (
        PARTITION BY pc.poste_principal, pc.saison_id
        ORDER BY pc.tackles_p90
    ) * 100) AS pct_tackles,
    ROUND(PERCENT_RANK() OVER (
        PARTITION BY pc.poste_principal, pc.saison_id
        ORDER BY pc.interceptions_p90
    ) * 100) AS pct_interceptions,
    ROUND(PERCENT_RANK() OVER (
        PARTITION BY pc.poste_principal, pc.saison_id
        ORDER BY pc.accurate_passes_pct_ss
    ) * 100) AS pct_passes
FROM silver.players_combined pc
JOIN silver.ref_ligues l ON pc.ligue_id = l.ligue_id
WHERE pc.minutes_ss >= 450;

COMMENT ON VIEW gold.vue_comparaison_joueurs IS 'Comparaison directe de joueurs (tous âges) pour Streamlit';


-- =============================================================
-- Note — écarts corrigés par rapport au brief initial :
-- silver.players_combined ne porte pas big_chances_created,
-- yellow_cards, red_cards (colonnes présentes uniquement dans la
-- table brute silver.players_sofascore). vue_top_u23_par_ligue
-- fait donc une jointure directe sur silver.players_sofascore
-- (player_id_ss + team_id + saison_id) pour les récupérer.
-- Toutes les autres colonnes du brief existaient déjà telles
-- quelles dans silver.players_combined / keepers_combined /
-- ref_ligues / ref_saisons / ref_nationalites (vérifié contre
-- information_schema.columns avant écriture).
-- =============================================================

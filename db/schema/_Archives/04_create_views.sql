-- =============================================================
-- RadarPépites - Vues Gold
-- Fichier  : 04_create_views.sql
-- Exécuter : après 03_create_facts.sql
-- Ces vues constituent la couche Gold consommée par
-- Power BI et les scripts Python de visualisation
-- =============================================================


-- -------------------------------------------------------------
-- vue_top_u23_par_ligue
-- Classement des meilleurs U23 par ligue
-- Filtre minimum 450 minutes (5 matchs complets equiv.)
-- -------------------------------------------------------------
CREATE OR REPLACE VIEW vue_top_u23_par_ligue AS
SELECT
    j.joueur_id,
    j.nom_complet                               AS joueur,
    j.nom_court,
    j.date_naissance,
    DATE_PART('year', AGE(j.date_naissance))    AS age_actuel,
    j.poste_principal,
    j.nationalite_principale,
    n.continent,
    e.nom_complet                               AS equipe,
    l.nom_complet                               AS ligue,
    l.pays,
    l.rang_projet,
    s.saison_id                                 AS saison,
    s.saison_courte,
    -- Temps de jeu
    f.matchs_joues,
    f.matchs_titulaire,
    f.minutes,
    f.minutes_p90,
    -- Stats offensives
    f.buts,
    f.passes_dec,
    f.buts_sans_pen,
    f.xg,
    f.xag,
    -- Stats /90
    f.buts_p90,
    f.passes_dec_p90,
    f.buts_sans_pen_p90,
    f.xg_p90,
    f.xag_p90,
    -- Stats de progression
    f.passes_prog,
    f.courses_prog,
    f.dribbles_reuss,
    f.dribbles_pct,
    -- Stats défensives
    f.interceptions,
    f.tacles_reuss,
    f.pressing
FROM fact_stats f
JOIN dim_joueurs     j ON f.joueur_id = j.joueur_id
JOIN dim_equipes     e ON f.equipe_id = e.equipe_id
JOIN dim_ligues      l ON f.ligue_id  = l.ligue_id
JOIN dim_saisons     s ON f.saison_id = s.saison_id
LEFT JOIN dim_nationalites n ON j.nationalite_principale = n.nationalite_id
WHERE f.est_u23   = TRUE
  AND f.minutes  >= 450;                                    -- Seuil minimum de temps de jeu

COMMENT ON VIEW vue_top_u23_par_ligue IS 'Vue principale U23 : toutes ligues, filtre 450 min, consommée par Power BI et classements Python';


-- -------------------------------------------------------------
-- vue_radar_joueur
-- Données normalisées pour les graphiques radar
-- Percentile par poste et saison (comparaison équitable)
-- -------------------------------------------------------------
CREATE OR REPLACE VIEW vue_radar_joueur AS
SELECT
    j.joueur_id,
    j.nom_complet                               AS joueur,
    j.nom_court,
    j.poste_principal,
    e.nom_complet                               AS equipe,
    l.nom_complet                               AS ligue,
    l.couleur_hex                               AS couleur_ligue,
    f.saison_id,
    -- Axes radar attaquants
    f.xg_p90,
    f.buts_p90,
    f.buts_sans_pen_p90,
    f.tirs_cadres_p90,
    f.passes_dec_p90,
    f.xag_p90,
    -- Axes radar milieux
    f.passes_prog,
    f.courses_prog,
    f.receptions_prog,
    -- Axes radar défenseurs
    f.tacles_reuss,
    f.interceptions,
    f.duels_aeriens_pct,
    f.pressing,
    -- Axes transversaux
    f.dribbles_reuss,
    f.dribbles_pct,
    f.fautes_subies,
    -- Percentiles par poste (pour normalisation radar 0-100)
    PERCENT_RANK() OVER (
        PARTITION BY j.poste_principal, f.saison_id
        ORDER BY f.xg_p90
    ) * 100                                     AS pct_xg_p90,
    PERCENT_RANK() OVER (
        PARTITION BY j.poste_principal, f.saison_id
        ORDER BY f.buts_p90
    ) * 100                                     AS pct_buts_p90,
    PERCENT_RANK() OVER (
        PARTITION BY j.poste_principal, f.saison_id
        ORDER BY f.passes_dec_p90
    ) * 100                                     AS pct_passes_dec_p90,
    PERCENT_RANK() OVER (
        PARTITION BY j.poste_principal, f.saison_id
        ORDER BY f.passes_prog
    ) * 100                                     AS pct_passes_prog,
    PERCENT_RANK() OVER (
        PARTITION BY j.poste_principal, f.saison_id
        ORDER BY f.courses_prog
    ) * 100                                     AS pct_courses_prog,
    PERCENT_RANK() OVER (
        PARTITION BY j.poste_principal, f.saison_id
        ORDER BY f.dribbles_reuss
    ) * 100                                     AS pct_dribbles_reuss,
    PERCENT_RANK() OVER (
        PARTITION BY j.poste_principal, f.saison_id
        ORDER BY f.pressing
    ) * 100                                     AS pct_pressing,
    PERCENT_RANK() OVER (
        PARTITION BY j.poste_principal, f.saison_id
        ORDER BY f.tacles_reuss
    ) * 100                                     AS pct_tacles_reuss,
    PERCENT_RANK() OVER (
        PARTITION BY j.poste_principal, f.saison_id
        ORDER BY f.interceptions
    ) * 100                                     AS pct_interceptions
FROM fact_stats f
JOIN dim_joueurs j ON f.joueur_id = j.joueur_id
JOIN dim_equipes e ON f.equipe_id = e.equipe_id
JOIN dim_ligues  l ON f.ligue_id  = l.ligue_id
WHERE f.est_u23  = TRUE
  AND f.minutes >= 450;

COMMENT ON VIEW vue_radar_joueur IS 'Données normalisées en percentile par poste pour les graphiques radar Plotly';


-- -------------------------------------------------------------
-- vue_progression_saison
-- Comparaison N vs N-1 pour les joueurs U23
-- Permet de visualiser la progression annuelle
-- -------------------------------------------------------------
CREATE OR REPLACE VIEW vue_progression_saison AS
SELECT
    j.joueur_id,
    j.nom_complet                               AS joueur,
    j.poste_principal,
    e.nom_complet                               AS equipe,
    l.nom_complet                               AS ligue,
    f_curr.saison_id                            AS saison_courante,
    f_prev.saison_id                            AS saison_precedente,
    -- Progression buts /90
    f_curr.buts_p90                             AS buts_p90_curr,
    f_prev.buts_p90                             AS buts_p90_prev,
    f_curr.buts_p90 - f_prev.buts_p90          AS delta_buts_p90,
    -- Progression xG /90
    f_curr.xg_p90                               AS xg_p90_curr,
    f_prev.xg_p90                               AS xg_p90_prev,
    f_curr.xg_p90 - f_prev.xg_p90              AS delta_xg_p90,
    -- Progression passes /90
    f_curr.passes_dec_p90                       AS pd_p90_curr,
    f_prev.passes_dec_p90                       AS pd_p90_prev,
    f_curr.passes_dec_p90 - f_prev.passes_dec_p90 AS delta_pd_p90,
    -- Progression minutes
    f_curr.minutes                              AS minutes_curr,
    f_prev.minutes                              AS minutes_prev,
    f_curr.minutes - f_prev.minutes             AS delta_minutes
FROM fact_stats f_curr
JOIN fact_stats f_prev  ON  f_curr.joueur_id  = f_prev.joueur_id
                        AND f_curr.equipe_id   = f_prev.equipe_id
                        AND f_curr.saison_id  != f_prev.saison_id
JOIN dim_saisons s_curr ON f_curr.saison_id   = s_curr.saison_id
JOIN dim_saisons s_prev ON f_prev.saison_id   = s_prev.saison_id
                        AND s_prev.annee_debut = s_curr.annee_debut - 1
JOIN dim_joueurs j      ON f_curr.joueur_id   = j.joueur_id
JOIN dim_equipes e      ON f_curr.equipe_id   = e.equipe_id
JOIN dim_ligues  l      ON f_curr.ligue_id    = l.ligue_id
WHERE f_curr.est_u23 = TRUE
  AND f_curr.minutes >= 450
  AND f_prev.minutes >= 450;

COMMENT ON VIEW vue_progression_saison IS 'Comparaison N vs N-1 pour identifier les joueurs en progression - dashboard évolution';

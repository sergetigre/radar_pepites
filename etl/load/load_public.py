"""
etl/load/load_public.py
RadarPépites — Silver -> Public (Gold : dim_* + fact_stats)

Étapes :
  1. load_dim_ligues()        — depuis silver.ref_ligues
  2. load_dim_saisons()       — depuis silver.ref_saisons
  3. load_dim_nationalites()  — depuis silver.ref_nationalites + ref_pays (continent)
  4. load_dim_postes()        — depuis silver.ref_postes
  5. load_dim_joueurs()       — depuis silver.players_combined + keepers_combined (union),
                                  enrichi par silver.players_info
  6. load_dim_equipes()       — équipes distinctes (joueurs + gardiens)
  7. load_fact_stats()        — joueurs de champ + gardiens, colonnes Sofascore
                                  exclusives (rating, big_chances, possession) via
                                  jointure directe sur players_sofascore/keepers_sofascore
  8. verify()                 — row counts

Limites connues (colonnes absentes de silver, donc NULL dans fact_stats) :
  passes_prog, courses_prog, receptions_prog, duels_gagnes, dribbles_tentes,
  fautes_commises, fautes_subies, tacles_tentes, pressing, pressing_reuss
  -> ces stats avancées ne sont pas dans le périmètre de scraping actuel
     (fbref stat_types "passing"/"possession"/"defense" non scrapés).

Usage :
  python etl/load/load_public.py
"""

import ast
import logging
import sys
from datetime import datetime
from pathlib import Path

from sqlalchemy import text

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "etl" / "transform"))
from silver_transformer import get_engine, execute_with_retry, to_records  # noqa: E402
import pandas as pd  # noqa: E402

LOGS_DIR = ROOT / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# dim_joueurs.poste_detail stocke les codes natifs Sofascore, ex. "['MC', 'DM']"
# (position primaire en premier). dim_postes n'a pas de code DM -> repli sur CM
# (milieu central) ; MR/ML (milieux latéraux) -> repli sur RW/LW, catégorie
# large la plus proche disponible dans le référentiel.
SOFASCORE_TO_DIM_POSTE = {
    "GK": "GK", "DC": "CB", "DR": "RB", "DL": "LB", "DM": "CM",
    "MC": "CM", "MR": "RW", "ML": "LW", "AM": "AM", "ST": "FW",
    "LW": "LW", "RW": "RW",
}


def resolve_poste_fin(poste_detail_raw):
    if not poste_detail_raw:
        return None
    try:
        codes = ast.literal_eval(poste_detail_raw)
    except (ValueError, SyntaxError):
        return None
    if not codes:
        return None
    return SOFASCORE_TO_DIM_POSTE.get(codes[0])


def setup_logger() -> logging.Logger:
    run_ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = LOGS_DIR / f"load_public_{run_ts}.log"
    fmt = "%(asctime)s [%(levelname)s] %(message)s"
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.stream.reconfigure(encoding="utf-8", errors="replace")
    logging.basicConfig(
        level=logging.INFO,
        format=fmt,
        handlers=[stream_handler, logging.FileHandler(log_file, encoding="utf-8")],
    )
    logger = logging.getLogger("load_public")
    logger.info(f"Log : {log_file}")
    return logger


# ── 1. dim_ligues ────────────────────────────────────────────────────────────
def load_dim_ligues(engine, logger):
    logger.info("[1/7] silver.ref_ligues -> public.dim_ligues")
    with engine.connect() as conn:
        df = pd.read_sql(text("""
            SELECT ligue_id, nom_complet, nom_court, pays, confederation,
                   coefficient_uefa, rang_projet, soccerdata_key, fbref_comp_id, couleur_hex
            FROM silver.ref_ligues
        """), conn)
    rows = to_records(df)
    sql = text("""
        INSERT INTO dim_ligues
            (ligue_id, nom_complet, nom_court, pays, confederation,
             coefficient_uefa, rang_projet, soccerdata_key, fbref_comp_id, couleur_hex)
        VALUES
            (:ligue_id, :nom_complet, :nom_court, :pays, :confederation,
             :coefficient_uefa, :rang_projet, :soccerdata_key, :fbref_comp_id, :couleur_hex)
        ON CONFLICT (ligue_id) DO UPDATE SET
            nom_complet = EXCLUDED.nom_complet, nom_court = EXCLUDED.nom_court,
            pays = EXCLUDED.pays, confederation = EXCLUDED.confederation,
            coefficient_uefa = EXCLUDED.coefficient_uefa, rang_projet = EXCLUDED.rang_projet,
            soccerdata_key = EXCLUDED.soccerdata_key, fbref_comp_id = EXCLUDED.fbref_comp_id,
            couleur_hex = EXCLUDED.couleur_hex, date_maj = NOW()
    """)
    execute_with_retry(engine, sql, rows, logger)
    logger.info(f"  [OK] {len(rows)} lignes")


# ── 2. dim_saisons ───────────────────────────────────────────────────────────
def load_dim_saisons(engine, logger):
    logger.info("[2/7] silver.ref_saisons -> public.dim_saisons")
    with engine.connect() as conn:
        df = pd.read_sql(text("""
            SELECT saison_id, annee_debut, annee_fin, saison_courte,
                   est_courante AS est_saison_courante
            FROM silver.ref_saisons
        """), conn)
    rows = to_records(df)
    sql = text("""
        INSERT INTO dim_saisons (saison_id, annee_debut, annee_fin, saison_courte, est_saison_courante)
        VALUES (:saison_id, :annee_debut, :annee_fin, :saison_courte, :est_saison_courante)
        ON CONFLICT (saison_id) DO UPDATE SET
            annee_debut = EXCLUDED.annee_debut, annee_fin = EXCLUDED.annee_fin,
            saison_courte = EXCLUDED.saison_courte,
            est_saison_courante = EXCLUDED.est_saison_courante, date_maj = NOW()
    """)
    execute_with_retry(engine, sql, rows, logger)
    logger.info(f"  [OK] {len(rows)} lignes")


# ── 3. dim_nationalites ──────────────────────────────────────────────────────
def load_dim_nationalites(engine, logger):
    logger.info("[3/7] silver.ref_nationalites + ref_pays -> public.dim_nationalites")
    with engine.connect() as conn:
        df = pd.read_sql(text("""
            SELECT n.nationalite_id, n.nom_fr, p.continent, n.confederation_fifa
            FROM silver.ref_nationalites n
            LEFT JOIN silver.ref_pays p ON n.pays_id = p.pays_id
        """), conn)
    rows = to_records(df)
    sql = text("""
        INSERT INTO dim_nationalites (nationalite_id, nom_fr, continent, confederation_fifa)
        VALUES (:nationalite_id, :nom_fr, :continent, :confederation_fifa)
        ON CONFLICT (nationalite_id) DO UPDATE SET
            nom_fr = EXCLUDED.nom_fr, continent = EXCLUDED.continent,
            confederation_fifa = EXCLUDED.confederation_fifa, date_maj = NOW()
    """)
    execute_with_retry(engine, sql, rows, logger)
    logger.info(f"  [OK] {len(rows)} lignes")


# ── 4. dim_postes ────────────────────────────────────────────────────────────
def load_dim_postes(engine, logger):
    logger.info("[4/7] silver.ref_postes -> public.dim_postes")
    with engine.connect() as conn:
        df = pd.read_sql(text("""
            SELECT poste_id, poste_label_fr, famille, metriques_radar::text AS metriques_cles
            FROM silver.ref_postes
        """), conn)
    rows = to_records(df)
    sql = text("""
        INSERT INTO dim_postes (poste_id, poste_label_fr, famille, metriques_cles)
        VALUES (:poste_id, :poste_label_fr, :famille, CAST(:metriques_cles AS JSONB))
        ON CONFLICT (poste_id) DO UPDATE SET
            poste_label_fr = EXCLUDED.poste_label_fr, famille = EXCLUDED.famille,
            metriques_cles = EXCLUDED.metriques_cles, date_maj = NOW()
    """)
    execute_with_retry(engine, sql, rows, logger)
    logger.info(f"  [OK] {len(rows)} lignes")


# ── 5. dim_joueurs ───────────────────────────────────────────────────────────
def load_dim_joueurs(engine, logger):
    logger.info("[5/7] silver.players_combined + keepers_combined -> public.dim_joueurs")
    with engine.connect() as conn:
        df = pd.read_sql(text("""
            SELECT DISTINCT ON (u.player_id_ss)
                u.player_id_ss::text     AS joueur_id,
                u.player_id_ss,
                u.player_name            AS nom_complet,
                pi.nom_court,
                u.date_naissance,
                u.nationalite_id         AS nationalite_principale,
                pi.nationalite2_id       AS deuxieme_nationalite,
                u.poste_principal,
                pi.poste_detail,
                u.pied_dominant,
                u.taille_cm,
                pi.poids_kg
            FROM (
                SELECT player_id_ss, player_name, date_naissance, nationalite_id,
                       poste_principal, pied_dominant, taille_cm
                FROM silver.players_combined
                UNION ALL
                SELECT player_id_ss, player_name, date_naissance, nationalite_id,
                       'GK' AS poste_principal, NULL AS pied_dominant, NULL AS taille_cm
                FROM silver.keepers_combined
            ) u
            LEFT JOIN silver.players_info pi ON pi.player_id_ss = u.player_id_ss
            WHERE u.player_id_ss IS NOT NULL
            ORDER BY u.player_id_ss, u.date_naissance NULLS LAST
        """), conn)

    # nationalite_principale / deuxieme_nationalite / poste_principal doivent
    # référencer dim_nationalites / dim_postes (FK) -> normaliser les valeurs
    # inconnues en NULL plutôt que planter l'insert.
    with engine.connect() as conn:
        valid_nat = set(pd.read_sql(text("SELECT nationalite_id FROM dim_nationalites"), conn)["nationalite_id"])
        valid_poste = set(pd.read_sql(text("SELECT poste_id FROM dim_postes"), conn)["poste_id"])

    df["nationalite_principale"] = df["nationalite_principale"].where(df["nationalite_principale"].isin(valid_nat), None)
    df["deuxieme_nationalite"] = df["deuxieme_nationalite"].where(df["deuxieme_nationalite"].isin(valid_nat), None)
    df["poste_principal"] = df["poste_principal"].where(df["poste_principal"].isin(valid_poste), None)

    rows = to_records(df)
    sql = text("""
        INSERT INTO dim_joueurs
            (joueur_id, player_id_ss, nom_complet, nom_court, date_naissance, nationalite_principale,
             deuxieme_nationalite, poste_principal, poste_detail, pied_dominant, taille_cm, poids_kg)
        VALUES
            (:joueur_id, :player_id_ss, :nom_complet, :nom_court, :date_naissance, :nationalite_principale,
             :deuxieme_nationalite, :poste_principal, :poste_detail, :pied_dominant, :taille_cm, :poids_kg)
        ON CONFLICT (joueur_id) DO UPDATE SET
            player_id_ss = EXCLUDED.player_id_ss,
            nom_complet = EXCLUDED.nom_complet, nom_court = EXCLUDED.nom_court,
            date_naissance = EXCLUDED.date_naissance,
            nationalite_principale = EXCLUDED.nationalite_principale,
            deuxieme_nationalite = EXCLUDED.deuxieme_nationalite,
            poste_principal = EXCLUDED.poste_principal, poste_detail = EXCLUDED.poste_detail,
            pied_dominant = EXCLUDED.pied_dominant, taille_cm = EXCLUDED.taille_cm,
            poids_kg = EXCLUDED.poids_kg, date_maj = NOW()
    """)
    execute_with_retry(engine, sql, rows, logger)

    # L'upsert seul n'enlève jamais un joueur disparu de la source (ex:
    # lignes 2022-2023 supprimées) -> orphelin indéfiniment sinon.
    execute_with_retry(engine, text("""
        DELETE FROM dim_joueurs
        WHERE joueur_id NOT IN (
            SELECT player_id_ss::text FROM silver.players_combined
            UNION
            SELECT player_id_ss::text FROM silver.keepers_combined
        )
    """), [{}], logger)

    logger.info(f"  [OK] {len(rows)} lignes")


# ── 6. dim_equipes ───────────────────────────────────────────────────────────
def load_dim_equipes(engine, logger):
    logger.info("[6/7] players_combined + keepers_combined -> public.dim_equipes")
    with engine.connect() as conn:
        df = pd.read_sql(text("""
            SELECT DISTINCT ON (team_id)
                team_id::text AS equipe_id,
                team_id       AS team_id_ss,
                team_name     AS nom_complet,
                ligue_id
            FROM (
                SELECT team_id, team_name, ligue_id FROM silver.players_combined
                UNION ALL
                SELECT team_id, team_name, ligue_id FROM silver.keepers_combined
            ) u
            WHERE team_id IS NOT NULL
            ORDER BY team_id
        """), conn)

    with engine.connect() as conn:
        pays_par_ligue = pd.read_sql(text("SELECT ligue_id, pays FROM silver.ref_ligues"), conn)
    df = df.merge(pays_par_ligue, on="ligue_id", how="left")

    rows = to_records(df)
    sql = text("""
        INSERT INTO dim_equipes (equipe_id, nom_complet, ligue_id, pays, team_id_ss)
        VALUES (:equipe_id, :nom_complet, :ligue_id, :pays, :team_id_ss)
        ON CONFLICT (equipe_id) DO UPDATE SET
            nom_complet = EXCLUDED.nom_complet, ligue_id = EXCLUDED.ligue_id,
            pays = EXCLUDED.pays, team_id_ss = EXCLUDED.team_id_ss, date_maj = NOW()
    """)
    execute_with_retry(engine, sql, rows, logger)
    logger.info(f"  [OK] {len(rows)} lignes")


# ── 7. fact_stats ────────────────────────────────────────────────────────────
def load_fact_stats(engine, logger):
    logger.info("[7/7] players_combined + keepers_combined -> public.fact_stats")

    with engine.connect() as conn:
        # Joueurs de champ
        df_players = pd.read_sql(text("""
            SELECT
                pc.player_id_ss::text AS joueur_id,
                pc.team_id::text      AS equipe_id,
                pc.ligue_id,
                pc.saison_id,
                pc.poste_principal    AS poste_id,
                s.annee_debut - EXTRACT(YEAR FROM pc.date_naissance)::int AS age,
                pc.appearances_ss     AS matchs_joues,
                NULL::int              AS matchs_titulaire,
                pc.minutes_ss          AS minutes,
                COALESCE(pc.goals_fb, pc.goals_ss)                       AS buts,
                COALESCE(pc.assists_fb, pc.assists_ss)                   AS passes_dec,
                COALESCE(pc.shots_fb, NULL)                              AS tirs,
                COALESCE(pc.shots_on_target_fb, pc.shots_on_target_ss)   AS tirs_cadres,
                pc.xg_ss                AS xg,
                pc.xa_ss                AS xag,
                pc.goals_p90, pc.assists_p90 AS passes_dec_p90,
                pc.xg_p90, pc.xa_p90 AS xag_p90, pc.shots_p90,
                NULL::float AS tirs_cadres_p90,  -- pas de "shots on target /90" distinct en silver
                pc.accurate_passes_ss   AS passes_reussies,
                pc.accurate_passes_pct_ss AS passes_pct,
                pc.successful_dribbles_ss AS dribbles_reuss,
                pc.aerial_won_pct_fb    AS duels_aeriens_pct,
                COALESCE(pc.tackles_won_fb, pc.tackles_ss) AS tacles_reuss,
                COALESCE(pc.interceptions_fb, pc.interceptions_ss) AS interceptions,
                pc.clearances_ss        AS degagements,
                pc.key_passes_p90, pc.tackles_p90, pc.interceptions_p90,
                pc.dribbles_p90, pc.degagements_p90,
                NULL::float AS saves_p90, NULL::float AS goals_prevented,
                NULL::float AS save_pct, NULL::float AS clean_sheets_pct,
                NULL::float AS long_balls_pct,
                pc.has_fbref_data, pc.has_sofascore_data, pc.date_maj AS date_scraping,
                ps.rating, ps.big_chances_created AS big_chances_creees,
                ps.big_chances_missed AS big_chances_manquees, ps.possession_lost AS possession_perdue,
                ps.yellow_cards AS cartons_jaunes, ps.red_cards AS cartons_rouges
            FROM silver.players_combined pc
            JOIN silver.ref_saisons s ON s.saison_id = pc.saison_id
            LEFT JOIN silver.players_sofascore ps
                ON ps.player_id_ss = pc.player_id_ss AND ps.team_id = pc.team_id AND ps.saison_id = pc.saison_id
        """), conn)

        # Gardiens : mêmes colonnes de sortie, mais fact_stats n'a pas de
        # champs dédiés gardien (saves, buts encaissés...) -> uniquement le
        # temps de jeu, la discipline, et les métriques Sofascore génériques.
        df_keepers = pd.read_sql(text("""
            SELECT
                kc.player_id_ss::text AS joueur_id,
                kc.team_id::text      AS equipe_id,
                kc.ligue_id,
                kc.saison_id,
                'GK'                   AS poste_id,
                s.annee_debut - EXTRACT(YEAR FROM kc.date_naissance)::int AS age,
                kc.appearances_ss     AS matchs_joues,
                NULL::int              AS matchs_titulaire,
                kc.minutes_ss          AS minutes,
                NULL::float AS buts, NULL::float AS passes_dec, NULL::float AS tirs,
                NULL::float AS tirs_cadres, NULL::float AS xg, NULL::float AS xag,
                NULL::float AS goals_p90, NULL::float AS passes_dec_p90,
                NULL::float AS xg_p90, NULL::float AS xag_p90, NULL::float AS shots_p90,
                NULL::float AS tirs_cadres_p90,
                NULL::float AS passes_reussies, NULL::float AS passes_pct,
                NULL::float AS dribbles_reuss, NULL::float AS duels_aeriens_pct,
                NULL::float AS tacles_reuss, NULL::float AS interceptions,
                NULL::float AS degagements,
                NULL::float AS key_passes_p90, NULL::float AS tackles_p90,
                NULL::float AS interceptions_p90, NULL::float AS dribbles_p90,
                NULL::float AS degagements_p90,
                kc.saves_p90, kc.goals_prevented_ss AS goals_prevented,
                kc.save_pct_fb AS save_pct, kc.clean_sheets_pct_fb AS clean_sheets_pct,
                kc.long_balls_pct,
                kc.has_fbref_data, kc.has_sofascore_data, kc.date_maj AS date_scraping,
                kc.rating_ss AS rating, NULL::float AS big_chances_creees,
                NULL::float AS big_chances_manquees, NULL::float AS possession_perdue,
                ks.yellow_cards AS cartons_jaunes, ks.red_cards AS cartons_rouges
            FROM silver.keepers_combined kc
            JOIN silver.ref_saisons s ON s.saison_id = kc.saison_id
            LEFT JOIN silver.keepers_sofascore ks
                ON ks.player_id_ss = kc.player_id_ss AND ks.team_id = kc.team_id AND ks.saison_id = kc.saison_id
        """), conn)

    df = pd.concat([df_players, df_keepers], ignore_index=True)
    df = df[df["joueur_id"].notna() & df["equipe_id"].notna()].copy()

    # Enrichissement poste_id : dim_joueurs.poste_detail porte les codes
    # Sofascore natifs (plus précis que le poste_principal générique fbref
    # MF/DF/FW/GK) -> on résout le poste primaire et on le mappe vers les 11
    # codes dim_postes quand la donnée existe, sinon on garde le générique.
    with engine.connect() as conn:
        df_pd = pd.read_sql(text(
            "SELECT joueur_id, poste_detail FROM dim_joueurs WHERE poste_detail IS NOT NULL"
        ), conn)
    poste_fin_map = {
        row.joueur_id: resolve_poste_fin(row.poste_detail) for row in df_pd.itertuples()
    }
    df["poste_id"] = [
        poste_fin_map.get(jid) or generique
        for jid, generique in zip(df["joueur_id"], df["poste_id"])
    ]

    # poste_id doit référencer dim_postes -> valeurs hors référentiel -> NULL
    with engine.connect() as conn:
        valid_poste = set(pd.read_sql(text("SELECT poste_id FROM dim_postes"), conn)["poste_id"])
    df["poste_id"] = df["poste_id"].where(df["poste_id"].isin(valid_poste), None)

    rows = to_records(df)
    logger.info(f"  {len(rows)} lignes à upserter (joueurs + gardiens)")

    sql = text("""
        INSERT INTO fact_stats
            (joueur_id, equipe_id, ligue_id, saison_id, poste_id, age,
             matchs_joues, matchs_titulaire, minutes,
             buts, passes_dec, tirs, tirs_cadres, xg, xag,
             buts_p90, passes_dec_p90, xg_p90, xag_p90, tirs_p90, tirs_cadres_p90,
             passes_reussies, passes_pct, dribbles_reuss, duels_aeriens_pct,
             tacles_reuss, interceptions, degagements,
             key_passes_p90, tackles_p90, interceptions_p90, dribbles_p90, degagements_p90,
             saves_p90, goals_prevented, save_pct, clean_sheets_pct, long_balls_pct,
             cartons_jaunes, cartons_rouges,
             rating, big_chances_creees, big_chances_manquees, possession_perdue,
             source, has_fbref_data, has_sofascore_data, date_scraping)
        VALUES
            (:joueur_id, :equipe_id, :ligue_id, :saison_id, :poste_id, :age,
             :matchs_joues, :matchs_titulaire, :minutes,
             :buts, :passes_dec, :tirs, :tirs_cadres, :xg, :xag,
             :goals_p90, :passes_dec_p90, :xg_p90, :xag_p90, :shots_p90, :tirs_cadres_p90,
             :passes_reussies, :passes_pct, :dribbles_reuss, :duels_aeriens_pct,
             :tacles_reuss, :interceptions, :degagements,
             :key_passes_p90, :tackles_p90, :interceptions_p90, :dribbles_p90, :degagements_p90,
             :saves_p90, :goals_prevented, :save_pct, :clean_sheets_pct, :long_balls_pct,
             :cartons_jaunes, :cartons_rouges,
             :rating, :big_chances_creees, :big_chances_manquees, :possession_perdue,
             'silver_combined', :has_fbref_data, :has_sofascore_data, :date_scraping)
        ON CONFLICT (joueur_id, equipe_id, saison_id) DO UPDATE SET
            ligue_id = EXCLUDED.ligue_id, poste_id = EXCLUDED.poste_id, age = EXCLUDED.age,
            matchs_joues = EXCLUDED.matchs_joues, minutes = EXCLUDED.minutes,
            buts = EXCLUDED.buts, passes_dec = EXCLUDED.passes_dec, tirs = EXCLUDED.tirs,
            tirs_cadres = EXCLUDED.tirs_cadres, xg = EXCLUDED.xg, xag = EXCLUDED.xag,
            buts_p90 = EXCLUDED.buts_p90, passes_dec_p90 = EXCLUDED.passes_dec_p90,
            xg_p90 = EXCLUDED.xg_p90, xag_p90 = EXCLUDED.xag_p90,
            tirs_p90 = EXCLUDED.tirs_p90, tirs_cadres_p90 = EXCLUDED.tirs_cadres_p90,
            passes_reussies = EXCLUDED.passes_reussies, passes_pct = EXCLUDED.passes_pct,
            dribbles_reuss = EXCLUDED.dribbles_reuss, duels_aeriens_pct = EXCLUDED.duels_aeriens_pct,
            tacles_reuss = EXCLUDED.tacles_reuss, interceptions = EXCLUDED.interceptions,
            degagements = EXCLUDED.degagements,
            key_passes_p90 = EXCLUDED.key_passes_p90, tackles_p90 = EXCLUDED.tackles_p90,
            interceptions_p90 = EXCLUDED.interceptions_p90, dribbles_p90 = EXCLUDED.dribbles_p90,
            degagements_p90 = EXCLUDED.degagements_p90,
            saves_p90 = EXCLUDED.saves_p90, goals_prevented = EXCLUDED.goals_prevented,
            save_pct = EXCLUDED.save_pct, clean_sheets_pct = EXCLUDED.clean_sheets_pct,
            long_balls_pct = EXCLUDED.long_balls_pct,
            cartons_jaunes = EXCLUDED.cartons_jaunes, cartons_rouges = EXCLUDED.cartons_rouges,
            rating = EXCLUDED.rating, big_chances_creees = EXCLUDED.big_chances_creees,
            big_chances_manquees = EXCLUDED.big_chances_manquees, possession_perdue = EXCLUDED.possession_perdue,
            has_fbref_data = EXCLUDED.has_fbref_data, has_sofascore_data = EXCLUDED.has_sofascore_data,
            date_scraping = EXCLUDED.date_scraping, date_maj = NOW()
    """)
    execute_with_retry(engine, sql, rows, logger)
    logger.info(f"  [OK] {len(rows)} lignes")


# ── Vérification ─────────────────────────────────────────────────────────────
def verify(engine, logger):
    tables = ["dim_ligues", "dim_saisons", "dim_nationalites", "dim_postes",
              "dim_joueurs", "dim_equipes", "fact_stats"]
    logger.info("")
    logger.info("=" * 55)
    logger.info("  VERIFICATION — Row counts public (Gold)")
    logger.info("=" * 55)
    with engine.connect() as conn:
        for tbl in tables:
            try:
                c = conn.execute(text(f"SELECT COUNT(*) FROM {tbl}")).scalar()
                logger.info(f"  {tbl:<20} {c:>7} lignes")
            except Exception as e:
                logger.warning(f"  {tbl:<20} ERREUR: {e}")
    logger.info("=" * 55)


def run():
    logger = setup_logger()
    engine = get_engine()

    logger.info("=" * 65)
    logger.info("  RadarPepites — Load Public (Gold)")
    logger.info(f"  {datetime.now():%Y-%m-%d %H:%M:%S}")
    logger.info("=" * 65)

    load_dim_ligues(engine, logger)
    load_dim_saisons(engine, logger)
    load_dim_nationalites(engine, logger)
    load_dim_postes(engine, logger)
    load_dim_joueurs(engine, logger)
    load_dim_equipes(engine, logger)
    load_fact_stats(engine, logger)
    verify(engine, logger)

    logger.info("")
    logger.info("  Load Public termine avec succes.")


if __name__ == "__main__":
    run()

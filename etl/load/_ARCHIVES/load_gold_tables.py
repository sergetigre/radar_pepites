"""
etl/load/load_gold_tables.py
RadarPépites — Silver -> Gold (tables physiques)

Alimente les tables physiques du schéma gold (dim_* + fact_joueurs +
fact_gardiens), distinctes des vues gold.vue_* (qui restent branchées
sur silver.*) et du schéma public (dim_*/fact_stats, conservé tel quel).

Différences avec etl/load/load_public.py :
  - Cible le schéma gold, pas public
  - Pas de dim_equipes : team_name/team_id dénormalisés dans les faits
  - fact_joueurs et fact_gardiens séparés (au lieu d'un fact_stats
    unique) : les gardiens ont enfin leurs propres colonnes (saves,
    clean_sheets...) au lieu d'être des lignes à moitié vides
  - Percentiles précalculés comme colonnes physiques (via PERCENT_RANK()
    en SQL au moment du chargement, pas recalculés à chaque requête)
  - fact_joueurs/fact_gardiens contiennent TOUS les joueurs (pas
    seulement U23) ; is_u23 est une colonne filtrable, pas un filtre
    d'inclusion. Les percentiles sont donc calculés sur la population
    complète par poste/saison, pas seulement parmi les U23.

Étapes :
  1. load_dim_ligues()
  2. load_dim_saisons()
  3. load_dim_postes()
  4. load_dim_nationalites()
  5. load_dim_joueurs()      — union players_combined + keepers_combined
  6. load_fact_joueurs()     — INSERT...SELECT avec PERCENT_RANK()
  7. load_fact_gardiens()    — idem
  8. verify()

Usage : python etl/load/load_gold_tables.py
"""

import logging
import sys
import time
from datetime import datetime
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.exc import OperationalError

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "etl" / "transform"))
from silver_transformer import get_engine  # noqa: E402

LOGS_DIR = ROOT / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)


def setup_logger() -> logging.Logger:
    run_ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = LOGS_DIR / f"load_gold_tables_{run_ts}.log"
    fmt = "%(asctime)s [%(levelname)s] %(message)s"
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.stream.reconfigure(encoding="utf-8", errors="replace")
    logging.basicConfig(
        level=logging.INFO,
        format=fmt,
        handlers=[stream_handler, logging.FileHandler(log_file, encoding="utf-8")],
    )
    logger = logging.getLogger("load_gold_tables")
    logger.info(f"Log : {log_file}")
    return logger


def exec_with_retry(engine, sql: str, logger: logging.Logger, max_retries: int = 4, delay: float = 5.0) -> None:
    """Comme execute_with_retry() dans silver_transformer.py, mais pour un
    unique statement SQL sans paramètres liés (INSERT...SELECT direct)."""
    last_exc = None
    for attempt in range(1, max_retries + 1):
        try:
            with engine.begin() as conn:
                conn.exec_driver_sql(sql)
            return
        except OperationalError as e:
            last_exc = e
            logger.warning(f"    Connexion DB perdue (tentative {attempt}/{max_retries}), nouvel essai dans {delay:.0f}s...")
            time.sleep(delay)
    raise last_exc


# ── 1-4. Référentiels ────────────────────────────────────────────────────────
def load_dim_ligues(engine, logger):
    logger.info("[1/7] silver.ref_ligues -> gold.dim_ligues")
    exec_with_retry(engine, """
        INSERT INTO gold.dim_ligues (ligue_id, nom_complet, nom_court, pays, rang_projet, couleur_hex, coefficient_uefa)
        SELECT ligue_id, nom_complet, nom_court, pays, rang_projet, couleur_hex, coefficient_uefa
        FROM silver.ref_ligues
        ON CONFLICT (ligue_id) DO UPDATE SET
            nom_complet = EXCLUDED.nom_complet, nom_court = EXCLUDED.nom_court,
            pays = EXCLUDED.pays, rang_projet = EXCLUDED.rang_projet,
            couleur_hex = EXCLUDED.couleur_hex, coefficient_uefa = EXCLUDED.coefficient_uefa
    """, logger)
    logger.info("  [OK]")


def load_dim_saisons(engine, logger):
    logger.info("[2/7] silver.ref_saisons -> gold.dim_saisons")
    exec_with_retry(engine, """
        INSERT INTO gold.dim_saisons (saison_id, annee_debut, annee_fin, saison_courte, est_courante)
        SELECT saison_id, annee_debut, annee_fin, saison_courte, est_courante
        FROM silver.ref_saisons
        ON CONFLICT (saison_id) DO UPDATE SET
            annee_debut = EXCLUDED.annee_debut, annee_fin = EXCLUDED.annee_fin,
            saison_courte = EXCLUDED.saison_courte, est_courante = EXCLUDED.est_courante
    """, logger)
    logger.info("  [OK]")


def load_dim_postes(engine, logger):
    logger.info("[3/7] silver.ref_postes -> gold.dim_postes")
    exec_with_retry(engine, """
        INSERT INTO gold.dim_postes (poste_id, poste_label_fr, famille, metriques_radar)
        SELECT poste_id, poste_label_fr, famille, metriques_radar
        FROM silver.ref_postes
        ON CONFLICT (poste_id) DO UPDATE SET
            poste_label_fr = EXCLUDED.poste_label_fr, famille = EXCLUDED.famille,
            metriques_radar = EXCLUDED.metriques_radar
    """, logger)
    logger.info("  [OK]")


def load_dim_nationalites(engine, logger):
    logger.info("[4/7] silver.ref_nationalites + ref_pays -> gold.dim_nationalites")
    exec_with_retry(engine, """
        INSERT INTO gold.dim_nationalites (nationalite_id, nom_fr, continent, confederation_fifa)
        SELECT n.nationalite_id, n.nom_fr, p.continent, n.confederation_fifa
        FROM silver.ref_nationalites n
        LEFT JOIN silver.ref_pays p ON n.pays_id = p.pays_id
        ON CONFLICT (nationalite_id) DO UPDATE SET
            nom_fr = EXCLUDED.nom_fr, continent = EXCLUDED.continent,
            confederation_fifa = EXCLUDED.confederation_fifa
    """, logger)
    logger.info("  [OK]")


# ── 5. dim_joueurs ───────────────────────────────────────────────────────────
def load_dim_joueurs(engine, logger):
    logger.info("[5/7] players_combined + keepers_combined -> gold.dim_joueurs")
    exec_with_retry(engine, """
        INSERT INTO gold.dim_joueurs (player_id_ss, player_name, nom_court, date_naissance, nationalite_id, poste_principal, pied_dominant, taille_cm)
        SELECT DISTINCT ON (u.player_id_ss)
            u.player_id_ss, u.player_name, pi.nom_court, u.date_naissance,
            dn.nationalite_id, dp.poste_id, u.pied_dominant, u.taille_cm
        FROM (
            SELECT player_id_ss, player_name, date_naissance, nationalite_id,
                   poste_principal, pied_dominant, taille_cm
            FROM silver.players_combined
            UNION ALL
            SELECT player_id_ss, player_name, date_naissance, nationalite_id,
                   'GK' AS poste_principal, NULL::text AS pied_dominant, NULL::int AS taille_cm
            FROM silver.keepers_combined
        ) u
        LEFT JOIN silver.players_info pi ON pi.player_id_ss = u.player_id_ss
        LEFT JOIN gold.dim_nationalites dn ON dn.nationalite_id = u.nationalite_id
        LEFT JOIN gold.dim_postes dp ON dp.poste_id = u.poste_principal
        WHERE u.player_id_ss IS NOT NULL
        ORDER BY u.player_id_ss, u.date_naissance NULLS LAST
        ON CONFLICT (player_id_ss) DO UPDATE SET
            player_name = EXCLUDED.player_name, nom_court = EXCLUDED.nom_court,
            date_naissance = EXCLUDED.date_naissance, nationalite_id = EXCLUDED.nationalite_id,
            poste_principal = EXCLUDED.poste_principal, pied_dominant = EXCLUDED.pied_dominant,
            taille_cm = EXCLUDED.taille_cm, date_maj = NOW()
    """, logger)
    # L'upsert seul n'enlève jamais un joueur qui a disparu de la source
    # (ex: uniquement des lignes 2022-2023 supprimées) -> il reste orphelin
    # dans dim_joueurs indéfiniment. Purge après chaque chargement.
    exec_with_retry(engine, """
        DELETE FROM gold.dim_joueurs
        WHERE player_id_ss NOT IN (
            SELECT player_id_ss FROM silver.players_combined
            UNION
            SELECT player_id_ss FROM silver.keepers_combined
        )
    """, logger)
    logger.info("  [OK]")


# ── 6. fact_joueurs ──────────────────────────────────────────────────────────
FACT_JOUEURS_MIN_MINUTES = 450  # seuil pour la POPULATION de calcul des percentiles


def load_fact_joueurs(engine, logger):
    logger.info("[6/7] silver.players_combined -> gold.fact_joueurs (avec percentiles)")

    # Toutes les lignes sont conservées dans fact_joueurs, mais les
    # PERCENT_RANK() sont calculés à l'intérieur du CTE "ranked", donc
    # uniquement sur la population filtrée (>= 450 minutes cette
    # saison-là) : sinon un joueur à 8 minutes avec un xg_p90 extrapolé
    # délirant fausse tout le classement (vérifié : un joueur à 10.5
    # xg_p90/8min dépassait des titulaires à 400+ minutes). Le LEFT JOIN
    # final donne NULL aux lignes sous le seuil plutôt qu'une valeur
    # trompeuse.
    # NULLS LAST par défaut sous PERCENT_RANK() donnerait un percentile
    # élevé à un joueur dont la métrique est NULL (il "gagne" en se
    # retrouvant trié en dernier) -> CASE WHEN pour forcer NULL->NULL.
    def pct(col: str) -> str:
        return (
            f"CASE WHEN {col} IS NULL THEN NULL ELSE "
            f"ROUND((PERCENT_RANK() OVER (PARTITION BY poste_principal, saison_id ORDER BY {col}) * 100)::numeric, 1) END"
        )

    sql = f"""
        WITH ranked AS (
            SELECT player_id_ss, saison_id, team_id,
                {pct('goals_p90')}            AS pct_goals_p90,
                {pct('xg_p90')}                AS pct_xg_p90,
                {pct('assists_p90')}           AS pct_assists_p90,
                {pct('key_passes_p90')}        AS pct_key_passes_p90,
                {pct('dribbles_p90')}          AS pct_dribbles_p90,
                {pct('shots_p90')}             AS pct_shots_p90,
                {pct('tackles_p90')}           AS pct_tackles_p90,
                {pct('interceptions_p90')}     AS pct_interceptions_p90,
                {pct('accurate_passes_pct_ss')} AS pct_passes_pct
            FROM silver.players_combined
            WHERE minutes_ss >= {FACT_JOUEURS_MIN_MINUTES}
        )
        INSERT INTO gold.fact_joueurs (
            player_id_ss, ligue_id, saison_id, team_name, team_id, is_u23,
            goals_ss, assists_ss, xg_ss, xa_ss, shots_on_target_ss, key_passes_ss,
            accurate_passes_pct_ss, successful_dribbles_ss, tackles_ss, interceptions_ss,
            clearances_ss, minutes_ss, appearances_ss, rating_ss,
            goals_fb, assists_fb, shots_on_target_fb, aerial_won_pct_fb, minutes_fb, has_fbref_data,
            goals_p90, assists_p90, xg_p90, xa_p90, shots_p90, key_passes_p90, tackles_p90, interceptions_p90, dribbles_p90,
            pct_goals_p90, pct_xg_p90, pct_assists_p90, pct_key_passes_p90, pct_dribbles_p90,
            pct_shots_p90, pct_tackles_p90, pct_interceptions_p90, pct_passes_pct
        )
        SELECT
            pc.player_id_ss, pc.ligue_id, pc.saison_id, pc.team_name, pc.team_id, pc.is_u23,
            pc.goals_ss, pc.assists_ss, pc.xg_ss, pc.xa_ss, pc.shots_on_target_ss, pc.key_passes_ss,
            pc.accurate_passes_pct_ss, pc.successful_dribbles_ss, pc.tackles_ss, pc.interceptions_ss,
            pc.clearances_ss, pc.minutes_ss, pc.appearances_ss, pc.rating_ss,
            pc.goals_fb, pc.assists_fb, pc.shots_on_target_fb, pc.aerial_won_pct_fb, pc.minutes_fb, pc.has_fbref_data,
            pc.goals_p90, pc.assists_p90, pc.xg_p90, pc.xa_p90, pc.shots_p90, pc.key_passes_p90, pc.tackles_p90, pc.interceptions_p90, pc.dribbles_p90,
            r.pct_goals_p90, r.pct_xg_p90, r.pct_assists_p90, r.pct_key_passes_p90, r.pct_dribbles_p90,
            r.pct_shots_p90, r.pct_tackles_p90, r.pct_interceptions_p90, r.pct_passes_pct
        FROM silver.players_combined pc
        LEFT JOIN ranked r ON r.player_id_ss = pc.player_id_ss
                           AND r.saison_id = pc.saison_id AND r.team_id = pc.team_id
        WHERE pc.player_id_ss IS NOT NULL AND pc.team_id IS NOT NULL
        ON CONFLICT (player_id_ss, saison_id, team_id) DO UPDATE SET
            ligue_id = EXCLUDED.ligue_id, team_name = EXCLUDED.team_name, is_u23 = EXCLUDED.is_u23,
            goals_ss = EXCLUDED.goals_ss, assists_ss = EXCLUDED.assists_ss, xg_ss = EXCLUDED.xg_ss, xa_ss = EXCLUDED.xa_ss,
            shots_on_target_ss = EXCLUDED.shots_on_target_ss, key_passes_ss = EXCLUDED.key_passes_ss,
            accurate_passes_pct_ss = EXCLUDED.accurate_passes_pct_ss, successful_dribbles_ss = EXCLUDED.successful_dribbles_ss,
            tackles_ss = EXCLUDED.tackles_ss, interceptions_ss = EXCLUDED.interceptions_ss,
            clearances_ss = EXCLUDED.clearances_ss, minutes_ss = EXCLUDED.minutes_ss,
            appearances_ss = EXCLUDED.appearances_ss, rating_ss = EXCLUDED.rating_ss,
            goals_fb = EXCLUDED.goals_fb, assists_fb = EXCLUDED.assists_fb, shots_on_target_fb = EXCLUDED.shots_on_target_fb,
            aerial_won_pct_fb = EXCLUDED.aerial_won_pct_fb, minutes_fb = EXCLUDED.minutes_fb, has_fbref_data = EXCLUDED.has_fbref_data,
            goals_p90 = EXCLUDED.goals_p90, assists_p90 = EXCLUDED.assists_p90, xg_p90 = EXCLUDED.xg_p90, xa_p90 = EXCLUDED.xa_p90,
            shots_p90 = EXCLUDED.shots_p90, key_passes_p90 = EXCLUDED.key_passes_p90, tackles_p90 = EXCLUDED.tackles_p90,
            interceptions_p90 = EXCLUDED.interceptions_p90, dribbles_p90 = EXCLUDED.dribbles_p90,
            pct_goals_p90 = EXCLUDED.pct_goals_p90, pct_xg_p90 = EXCLUDED.pct_xg_p90, pct_assists_p90 = EXCLUDED.pct_assists_p90,
            pct_key_passes_p90 = EXCLUDED.pct_key_passes_p90, pct_dribbles_p90 = EXCLUDED.pct_dribbles_p90,
            pct_shots_p90 = EXCLUDED.pct_shots_p90, pct_tackles_p90 = EXCLUDED.pct_tackles_p90,
            pct_interceptions_p90 = EXCLUDED.pct_interceptions_p90, pct_passes_pct = EXCLUDED.pct_passes_pct,
            date_maj = NOW()
    """
    exec_with_retry(engine, sql, logger)
    logger.info("  [OK]")


# ── 7. fact_gardiens ─────────────────────────────────────────────────────────
FACT_GARDIENS_MIN_MINUTES = 270  # 3 matchs équiv. — seuil pour la POPULATION de calcul


def load_fact_gardiens(engine, logger):
    logger.info("[7/7] silver.keepers_combined -> gold.fact_gardiens (avec percentiles)")

    # Même logique que fact_joueurs : PERCENT_RANK() calculé dans le CTE
    # filtré (>= 270 minutes), puis LEFT JOIN pour laisser NULL les
    # gardiens sous le seuil plutôt qu'un percentile faussé.
    def pct(col: str) -> str:
        return (
            f"CASE WHEN {col} IS NULL THEN NULL ELSE "
            f"ROUND((PERCENT_RANK() OVER (PARTITION BY saison_id ORDER BY {col}) * 100)::numeric, 1) END"
        )

    sql = f"""
        WITH ranked AS (
            SELECT player_id_ss, saison_id, team_name,
                {pct('saves_p90')}          AS pct_saves_p90,
                {pct('goals_prevented_ss')} AS pct_goals_prevented
            FROM silver.keepers_combined
            WHERE minutes_ss >= {FACT_GARDIENS_MIN_MINUTES}
        )
        INSERT INTO gold.fact_gardiens (
            player_id_ss, ligue_id, saison_id, team_name, is_u23,
            saves_ss, goals_prevented_ss, rating_ss, minutes_ss, appearances_ss,
            saves_fb, save_pct_fb, goals_against_p90_fb, clean_sheets_fb, clean_sheets_pct_fb,
            pk_saved_fb, has_fbref_data, saves_p90,
            pct_saves_p90, pct_goals_prevented
        )
        SELECT
            kc.player_id_ss, kc.ligue_id, kc.saison_id, kc.team_name, kc.is_u23,
            kc.saves_ss, kc.goals_prevented_ss, kc.rating_ss, kc.minutes_ss, kc.appearances_ss,
            kc.saves_fb, kc.save_pct_fb, kc.goals_against_p90_fb, kc.clean_sheets_fb, kc.clean_sheets_pct_fb,
            kc.pk_saved_fb, kc.has_fbref_data, kc.saves_p90,
            r.pct_saves_p90, r.pct_goals_prevented
        FROM silver.keepers_combined kc
        LEFT JOIN ranked r ON r.player_id_ss = kc.player_id_ss
                           AND r.saison_id = kc.saison_id AND r.team_name = kc.team_name
        WHERE kc.player_id_ss IS NOT NULL
        ON CONFLICT (player_id_ss, saison_id, team_name) DO UPDATE SET
            ligue_id = EXCLUDED.ligue_id, is_u23 = EXCLUDED.is_u23,
            saves_ss = EXCLUDED.saves_ss, goals_prevented_ss = EXCLUDED.goals_prevented_ss,
            rating_ss = EXCLUDED.rating_ss, minutes_ss = EXCLUDED.minutes_ss, appearances_ss = EXCLUDED.appearances_ss,
            saves_fb = EXCLUDED.saves_fb, save_pct_fb = EXCLUDED.save_pct_fb,
            goals_against_p90_fb = EXCLUDED.goals_against_p90_fb, clean_sheets_fb = EXCLUDED.clean_sheets_fb,
            clean_sheets_pct_fb = EXCLUDED.clean_sheets_pct_fb, pk_saved_fb = EXCLUDED.pk_saved_fb,
            has_fbref_data = EXCLUDED.has_fbref_data, saves_p90 = EXCLUDED.saves_p90,
            pct_saves_p90 = EXCLUDED.pct_saves_p90, pct_goals_prevented = EXCLUDED.pct_goals_prevented,
            date_maj = NOW()
    """
    exec_with_retry(engine, sql, logger)
    logger.info("  [OK]")


# ── Vérification ─────────────────────────────────────────────────────────────
def verify(engine, logger):
    tables = ["dim_ligues", "dim_saisons", "dim_postes", "dim_nationalites",
              "dim_joueurs", "fact_joueurs", "fact_gardiens"]
    logger.info("")
    logger.info("=" * 55)
    logger.info("  VERIFICATION — Row counts gold.* (tables physiques)")
    logger.info("=" * 55)
    with engine.connect() as conn:
        for tbl in tables:
            try:
                c = conn.execute(text(f"SELECT COUNT(*) FROM gold.{tbl}")).scalar()
                logger.info(f"  gold.{tbl:<18} {c:>7} lignes")
            except Exception as e:
                logger.warning(f"  gold.{tbl:<18} ERREUR: {e}")
    logger.info("=" * 55)


def run():
    logger = setup_logger()
    engine = get_engine()

    logger.info("=" * 65)
    logger.info("  RadarPepites — Load Gold Tables")
    logger.info(f"  {datetime.now():%Y-%m-%d %H:%M:%S}")
    logger.info("=" * 65)

    load_dim_ligues(engine, logger)
    load_dim_saisons(engine, logger)
    load_dim_postes(engine, logger)
    load_dim_nationalites(engine, logger)
    load_dim_joueurs(engine, logger)
    load_fact_joueurs(engine, logger)
    load_fact_gardiens(engine, logger)
    verify(engine, logger)

    logger.info("")
    logger.info("  Load Gold Tables termine avec succes.")


if __name__ == "__main__":
    run()

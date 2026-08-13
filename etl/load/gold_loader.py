"""
etl/load/gold_loader.py
RadarPépites — Déploiement des vues Gold

1. Connexion Neon via DATABASE_URL (config/.env) / DB_HOST-DB_PASSWORD
2. CREATE SCHEMA IF NOT EXISTS gold (idempotent, déjà créé par
   01_create_schemas.sql normalement)
3. Exécute db/schema/06_create_gold_views.sql
4. Vérifie que chaque vue est accessible + affiche un compte de lignes

Les vues gold.* sont des requêtes calculées à la volée sur silver.* —
il n'y a pas de données à "charger" à proprement parler, seulement le
DDL des vues à (re)déployer. Ce script est donc rapide (pas de
scraping, pas d'upsert de lignes).

Usage : python etl/load/gold_loader.py
"""

import logging
import sys
from datetime import datetime
from pathlib import Path

from sqlalchemy import text

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "etl" / "transform"))
from silver_transformer import get_engine  # noqa: E402

SQL_FILE = ROOT / "db" / "schema" / "06_create_gold_views.sql"
LOGS_DIR = ROOT / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

VUES = [
    "gold.vue_top_u23_par_ligue",
    "gold.vue_radar_joueur",
    "gold.vue_progression_saison",
    "gold.vue_top_u23_gk",
    "gold.vue_comparaison_joueurs",
]


def setup_logger() -> logging.Logger:
    run_ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = LOGS_DIR / f"gold_loader_{run_ts}.log"
    fmt = "%(asctime)s [%(levelname)s] %(message)s"
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.stream.reconfigure(encoding="utf-8", errors="replace")
    logging.basicConfig(
        level=logging.INFO,
        format=fmt,
        handlers=[stream_handler, logging.FileHandler(log_file, encoding="utf-8")],
    )
    logger = logging.getLogger("gold_loader")
    logger.info(f"Log : {log_file}")
    return logger


def deploy_views(engine, logger: logging.Logger) -> None:
    logger.info(f"Exécution de {SQL_FILE.relative_to(ROOT)}")
    sql_script = SQL_FILE.read_text(encoding="utf-8")
    with engine.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS gold"))
        conn.exec_driver_sql(sql_script)
    logger.info("  [OK] Vues déployées")


def verify_gold(engine, logger: logging.Logger) -> None:
    logger.info("")
    logger.info("=" * 55)
    logger.info("  VERIFICATION — gold.*")
    logger.info("=" * 55)
    with engine.connect() as conn:
        for vue in VUES:
            try:
                count = conn.execute(text(f"SELECT COUNT(*) FROM {vue}")).scalar()
                logger.info(f"  {vue:<32} {count:>7} lignes")
            except Exception as e:
                logger.warning(f"  {vue:<32} ERREUR: {type(e).__name__}: {e}")
    logger.info("=" * 55)


def run() -> None:
    logger = setup_logger()
    engine = get_engine()

    logger.info("=" * 65)
    logger.info("  RadarPepites — Gold Loader")
    logger.info(f"  {datetime.now():%Y-%m-%d %H:%M:%S}")
    logger.info("=" * 65)

    deploy_views(engine, logger)
    verify_gold(engine, logger)

    logger.info("")
    logger.info("  Gold Loader termine avec succes.")


if __name__ == "__main__":
    run()

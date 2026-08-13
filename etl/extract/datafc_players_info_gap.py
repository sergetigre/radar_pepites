"""
etl/extract/datafc_players_info_gap.py
RadarPépites — Comble le trou de players_info

datafc_players_info_all.py utilise standings -> squad -> player, mais
squad_data() renvoie l'effectif ACTUEL d'une équipe, pas l'effectif
historique d'une saison passée. Résultat : les joueurs partis depuis
sont invisibles, même s'ils ont bien des stats pour cette saison-là
dans silver.players_sofascore.

Ce script cible directement les player_id_ss connus de
silver.players_sofascore mais absents de silver.players_info, et
appelle datafc.player_data() sur cette liste précise (bypass complet
de standings/squad).

Sortie : data/bronze/YYYYMMDD_HHMMSS_GAP_players_info.csv
Logs   : logs/players_info_gap_YYYYMMDD_HHMMSS.log
"""

import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import datafc
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

ROOT       = Path(__file__).resolve().parents[2]
BRONZE_DIR = ROOT / "data" / "bronze"
LOGS_DIR   = ROOT / "logs"

load_dotenv(ROOT / "config" / ".env")

RATE_LIMIT = 2.0


def setup_logger() -> logging.Logger:
    run_ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = LOGS_DIR / f"players_info_gap_{run_ts}.log"

    fmt = "%(asctime)s [%(levelname)s] %(message)s"
    stream_handler = logging.StreamHandler()
    stream_handler.setStream(sys.stdout)
    stream_handler.stream.reconfigure(encoding="utf-8", errors="replace")
    logging.basicConfig(
        level=logging.INFO,
        format=fmt,
        handlers=[stream_handler, logging.FileHandler(log_file, encoding="utf-8")],
    )
    logger = logging.getLogger("players_info_gap")
    logger.info(f"Log : {log_file}")
    return logger


def get_engine():
    database_url = os.environ.get("DATABASE_URL")
    if database_url:
        return create_engine(database_url, pool_pre_ping=True, pool_recycle=280)
    url = URL.create(
        drivername="postgresql+psycopg2",
        username=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        host=os.environ["DB_HOST"],
        port=int(os.environ["DB_PORT"]),
        database=os.environ["DB_NAME"],
    )
    return create_engine(url, pool_pre_ping=True, pool_recycle=280)


def main():
    logger = setup_logger()
    engine = get_engine()

    logger.info("=" * 65)
    logger.info("  datafc — Comble le trou players_info (bio manquantes)")
    logger.info("=" * 65)

    with engine.connect() as conn:
        # players_sofascore ET keepers_sofascore : ce sont deux tables
        # distinctes (2 appels séparés côté scraping), un gardien peut donc
        # être absent de players_info sans jamais passer par players_sofascore.
        df_gap = pd.read_sql(text("""
            SELECT DISTINCT ON (src.player_id_ss)
                src.player_id_ss AS player_id,
                src.player_name,
                src.ligue_id,
                src.saison_id
            FROM (
                SELECT player_id_ss, player_name, ligue_id, saison_id FROM silver.players_sofascore
                UNION ALL
                SELECT player_id_ss, player_name, ligue_id, saison_id FROM silver.keepers_sofascore
            ) src
            LEFT JOIN silver.players_info pi ON pi.player_id_ss = src.player_id_ss
            WHERE pi.player_id_ss IS NULL
            ORDER BY src.player_id_ss, src.saison_id DESC
        """), conn)

    total = len(df_gap)
    logger.info(f"  Joueurs manquants à combler : {total}")

    if total == 0:
        logger.info("  Rien à faire — players_info est déjà complet.")
        return

    logger.info("  Appel datafc.player_data() (1 requête/joueur, bypass squad)...")
    try:
        df_players = datafc.player_data(
            squad_df=df_gap[["player_id", "player_name"]],
            rate_limit=RATE_LIMIT,
        )
    except Exception as e:
        logger.error(f"  Échec : {type(e).__name__}: {e}")
        raise

    if df_players is None or df_players.empty:
        logger.warning("  Aucune donnée récupérée.")
        return

    logger.info(f"  {len(df_players)}/{total} bios récupérées")

    df_players = df_players.copy()
    df_players["_league_id"]  = "GAP"
    df_players["_season"]     = "GAP"
    df_players["_source"]     = "datafc_sofascore"
    df_players["_scraped_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    ts  = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = BRONZE_DIR / f"{ts}_GAP_players_info.csv"
    df_players.to_csv(out, index=False, encoding="utf-8-sig")
    logger.info(f"  [OK] {out.name}")
    logger.info("=" * 65)
    logger.info("  Terminé.")
    logger.info("=" * 65)


if __name__ == "__main__":
    main()

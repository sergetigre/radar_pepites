"""
etl/extract/datafc_players_info_all.py
RadarPépites — Infos bio joueurs via datafc (10 ligues)

Chaîne par ligue × saison : standings → squad → player (bio)
Reconstruit le step "players_info" retiré lors du passage à la
convention "_all" (run_all.py n'orchestrait plus que fbref + datafc
stats, laissant silver.players_info à sa dernière valeur du 09/08).

Sortie : data/bronze/YYYYMMDD_HHMMSS_{league_id}_{saison}_players_info.csv
Logs   : logs/players_info_all_YYYYMMDD_HHMMSS.log
"""

import logging
import time
from datetime import datetime, timezone

import datafc

from datafc_scraper_all import (
    BRONZE_DIR,
    LEAGUES,
    LOGS_DIR,
    SEASON_IDS,
    call_with_retry,
    load_config,
    saison_to_sofascore_key,
)

REQUEST_DELAY_SEC = 2.0
RATE_LIMIT        = 2.0


# ── Logging ────────────────────────────────────────────────────────────────────
def setup_logger() -> logging.Logger:
    run_ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = LOGS_DIR / f"players_info_all_{run_ts}.log"

    fmt = "%(asctime)s [%(levelname)s] %(message)s"
    stream_handler = logging.StreamHandler()
    stream_handler.setStream(__import__("sys").stdout)
    stream_handler.stream.reconfigure(encoding="utf-8", errors="replace")
    logging.basicConfig(
        level=logging.INFO,
        format=fmt,
        handlers=[
            stream_handler,
            logging.FileHandler(log_file, encoding="utf-8"),
        ],
    )
    logger = logging.getLogger("players_info_all")
    logger.info(f"Log : {log_file}")
    return logger


# ── Utilitaires ────────────────────────────────────────────────────────────────
def add_metadata(df, league_id: str, saison: str):
    df = df.copy()
    df["_league_id"]  = league_id
    df["_season"]     = saison
    df["_source"]     = "datafc_sofascore"
    df["_scraped_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    return df


def build_output_path(league_id: str, saison: str):
    ts          = datetime.now().strftime("%Y%m%d_%H%M%S")
    saison_slug = saison.replace("-", "")
    return BRONZE_DIR / f"{ts}_{league_id}_{saison_slug}_players_info.csv"


# ── Scraping d'un bloc ligue × saison ─────────────────────────────────────────
def scrape_one(league_id: str, saison: str, logger: logging.Logger) -> bool:
    meta       = LEAGUES[league_id]
    tid        = meta["tournament_id"]
    season_key = saison_to_sofascore_key(saison)
    season_id  = SEASON_IDS.get(tid, {}).get(season_key)

    if season_id is None:
        logger.warning(f"  Season ID introuvable — {league_id} | {saison} ({season_key})")
        return False

    logger.info(f"  [1/3] Standings (tournament={tid}, season={season_id})")

    def fetch_standings():
        return datafc.standings_data(tournament_id=tid, season_id=season_id, rate_limit=RATE_LIMIT)

    df_standings = call_with_retry(fetch_standings, logger, f"{league_id}|{saison}|standings")
    if df_standings is None or df_standings.empty:
        logger.warning(f"    Standings vide — {league_id} | {saison}")
        return False
    logger.info(f"    {len(df_standings)} lignes standings")
    time.sleep(REQUEST_DELAY_SEC)

    logger.info("  [2/3] Squad (roster par équipe)")

    def fetch_squad():
        return datafc.squad_data(standings_df=df_standings, rate_limit=RATE_LIMIT)

    df_squad = call_with_retry(fetch_squad, logger, f"{league_id}|{saison}|squad")
    if df_squad is None or df_squad.empty:
        logger.warning(f"    Squad vide — {league_id} | {saison}")
        return False
    logger.info(f"    {len(df_squad)} joueurs en squad")
    time.sleep(REQUEST_DELAY_SEC)

    logger.info("  [3/3] Player bio (naissance, nationalité, poste, pied, taille)")

    def fetch_players():
        return datafc.player_data(squad_df=df_squad, rate_limit=RATE_LIMIT)

    df_players = call_with_retry(fetch_players, logger, f"{league_id}|{saison}|players")
    if df_players is None or df_players.empty:
        logger.warning(f"    Player data vide — {league_id} | {saison}")
        return False

    df_players = add_metadata(df_players, league_id, saison)
    out = build_output_path(league_id, saison)
    df_players.to_csv(out, index=False, encoding="utf-8-sig")
    logger.info(f"    [OK] {out.name} — {len(df_players)} joueurs")
    return True


# ── Point d'entrée ─────────────────────────────────────────────────────────────
def main():
    logger              = setup_logger()
    saisons, league_ids = load_config()

    tasks   = [(lid, sai) for lid in league_ids for sai in saisons]
    total   = len(tasks)
    success = 0
    failures: list[str] = []

    logger.info("=" * 65)
    logger.info("  datafc — Infos bio joueurs (standings → squad → player)")
    logger.info(f"  Ligues  : {league_ids}")
    logger.info(f"  Saisons : {saisons}")
    logger.info(f"  Total   : {total} combinaisons ligue x saison")
    logger.info("=" * 65)

    for i, (league_id, saison) in enumerate(tasks, 1):
        logger.info(
            f"[{i:>{len(str(total))}}/{total}] "
            f"{LEAGUES[league_id]['nom']} ({league_id}) | {saison}"
        )
        ok = scrape_one(league_id, saison, logger)
        if ok:
            success += 1
        else:
            failures.append(f"{league_id} | {saison}")

        if i < total:
            time.sleep(REQUEST_DELAY_SEC)

    logger.info("=" * 65)
    logger.info(f"  BILAN : {success}/{total} combinaisons réussies")
    if failures:
        logger.warning(f"  Échecs ({len(failures)}) :")
        for f in failures:
            logger.warning(f"    - {f}")
    logger.info("=" * 65)


if __name__ == "__main__":
    main()

# =============================================================
# RadarPépites — Scraping fbref Gardiens → Bronze
# Fichier  : etl/extract/fbref_keeper_scraper.py
# Rôle     : Récupère les stats spécifiques gardiens fbref
#            via soccerdata pour les Big 5
#            stat_type : keeper, keeper_adv
# Pilotage : config/scraping_config.json
# Usage    : python etl/extract/fbref_keeper_scraper.py
# =============================================================

import os
import sys
import json
import time
import logging
from datetime import datetime

import pandas as pd
import soccerdata as sd

# ---------------------------------------------------------------------------
# Chemins
# ---------------------------------------------------------------------------

DIR_ROOT   = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DIR_BRONZE = os.path.join(DIR_ROOT, "data", "bronze")
DIR_LOGS   = os.path.join(DIR_ROOT, "logs")
CONFIG     = os.path.join(DIR_ROOT, "config", "scraping_config.json")

DELAY = 4

# ---------------------------------------------------------------------------
# Big 5 uniquement — soccerdata ne couvre pas les ligues 6-10
# ---------------------------------------------------------------------------

BIG5 = {
    "ENG": "ENG-Premier League",
    "ESP": "ESP-La Liga",
    "GER": "GER-Bundesliga",
    "ITA": "ITA-Serie A",
    "FRA": "FRA-Ligue 1",
}

# Stats gardiens disponibles sur fbref via soccerdata
KEEPER_STATS = [
    "keeper",      # Stats de base : buts encaissés, arrêts, clean sheets
    "keeper_adv",  # Stats avancées : % arrêts par zone, passes, sorties
]

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

os.makedirs(DIR_BRONZE, exist_ok=True)
os.makedirs(DIR_LOGS,   exist_ok=True)

log_file = os.path.join(DIR_LOGS, f"fbref_keeper_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(log_file, encoding="utf-8"),
    ],
)
log = logging.getLogger("RadarPepites.Keeper.FBref")

# ---------------------------------------------------------------------------
# Scraping
# ---------------------------------------------------------------------------

def scrape_keeper(league_key: str, league_name: str,
                  season: str, stat_type: str) -> pd.DataFrame | None:
    try:
        log.info(f"    Scraping {stat_type}...")
        fbref = sd.FBref(leagues=league_name, seasons=season)
        df    = fbref.read_player_season_stats(stat_type=stat_type)

        # Aplatir MultiIndex
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = ["_".join(filter(None, map(str, col))).strip()
                          for col in df.columns]

        # Filtrer uniquement les gardiens
        pos_col = next((c for c in df.columns if c.lower() in ["pos", "position"]), None)
        if pos_col:
            df = df[df[pos_col].astype(str).str.contains("GK", na=False)].copy()

        log.info(f"    → {len(df)} gardiens")
        return df

    except Exception as e:
        log.error(f"    ERREUR {stat_type} : {e}")
        return None


def save_bronze(df: pd.DataFrame, league_key: str,
                season: str, stat_type: str) -> str:
    timestamp  = datetime.now().strftime("%Y%m%d_%H%M%S")
    saison_fmt = season.replace("-", "_")
    filename   = os.path.join(
        DIR_BRONZE,
        f"{timestamp}_{league_key}_{saison_fmt}_{stat_type}.csv"
    )
    df["_league_id"]  = league_key
    df["_season"]     = season
    df["_stat_type"]  = stat_type
    df["_source"]     = "fbref_soccerdata"
    df["_scraped_at"] = datetime.now().isoformat()
    df.to_csv(filename, index=True, encoding="utf-8-sig")
    return filename

# ---------------------------------------------------------------------------
# Exécution principale
# ---------------------------------------------------------------------------

def load_config() -> dict:
    with open(CONFIG, "r", encoding="utf-8") as f:
        return json.load(f)

def run():
    config         = load_config()
    ligues_actives = [l for l in config["ligues"] if l.get("actif") is True]
    saisons        = config["saisons"]

    # Filtrer Big 5 uniquement
    ligues_cibles = [l for l in ligues_actives if l["id"] in BIG5]

    total    = len(ligues_cibles) * len(saisons) * len(KEEPER_STATS)
    success  = 0
    failures = []
    counter  = 0

    log.info("=" * 65)
    log.info("  RadarPepites - Scraping fbref Gardiens -> Bronze")
    log.info("=" * 65)
    log.info(f"  Ligues  : {[l['id'] for l in ligues_cibles]} (Big 5 uniquement)")
    log.info(f"  Saisons : {saisons}")
    log.info(f"  Stats   : {KEEPER_STATS}")
    log.info(f"  Total   : {total} fichiers")
    log.info(f"  Duree   : ~{round(total * DELAY / 60)} minutes")
    log.info("=" * 65)

    for ligue in ligues_cibles:
        league_key  = ligue["id"]
        league_name = BIG5[league_key]

        for season in saisons:
            for stat_type in KEEPER_STATS:
                counter += 1
                log.info(f"[{counter}/{total}] {league_key} | {season} | {stat_type}")

                df = scrape_keeper(league_key, league_name, season, stat_type)

                if df is not None and not df.empty:
                    path = save_bronze(df, league_key, season, stat_type)
                    log.info(f"  -> {os.path.basename(path)}")
                    success += 1
                else:
                    failures.append(f"{league_key}_{season}_{stat_type}")
                    log.warning(f"  -> Echec")

                log.info(f"  -> Pause {DELAY}s...")
                time.sleep(DELAY)

    log.info("=" * 65)
    log.info(f"  Termine  : {success}/{total}")
    if failures:
        log.warning(f"  Echecs   : {failures}")
    log.info("=" * 65)

if __name__ == "__main__":
    run()

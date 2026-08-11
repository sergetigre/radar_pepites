# =============================================================
# RadarPépites — Scraping fbref → Bronze
# Fichier  : etl/extract/fbref_scraper.py
# Pilotage : config/scraping_config.json
#            → mets "actif": true/false pour choisir les ligues
#            → modifie "saisons" pour choisir les années
# Usage    : python etl/extract/fbref_scraper.py
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

DELAY = 4  # secondes entre chaque requête — NE PAS RÉDUIRE (rate-limit fbref)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

os.makedirs(DIR_BRONZE, exist_ok=True)
os.makedirs(DIR_LOGS,   exist_ok=True)

log_file = os.path.join(DIR_LOGS, f"scraping_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(log_file, encoding="utf-8"),
    ],
)
log = logging.getLogger("RadarPepites")

# ---------------------------------------------------------------------------
# Lecture de la configuration
# ---------------------------------------------------------------------------

def load_config() -> dict:
    """Charge et valide le fichier scraping_config.json."""
    if not os.path.exists(CONFIG):
        log.error(f"Fichier de config introuvable : {CONFIG}")
        sys.exit(1)

    with open(CONFIG, "r", encoding="utf-8") as f:
        config = json.load(f)

    # Ligues actives uniquement
    config["ligues_actives"] = [
        l for l in config["ligues"] if l.get("actif") is True
    ]

    if not config["ligues_actives"]:
        log.error("Aucune ligue active dans scraping_config.json. Mets 'actif': true sur au moins une ligue.")
        sys.exit(1)

    if not config["saisons"]:
        log.error("Aucune saison definie dans scraping_config.json.")
        sys.exit(1)

    return config

# ---------------------------------------------------------------------------
# Scraping
# ---------------------------------------------------------------------------

def scrape_stat(league_name: str, season: str, stat_type: str):
    """Scrape un type de stats pour une ligue et une saison."""
    try:
        fbref = sd.FBref(leagues=league_name, seasons=season)
        df    = fbref.read_player_season_stats(stat_type=stat_type)

        # Aplatir le MultiIndex de colonnes si present
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = ["_".join(filter(None, map(str, col))).strip() for col in df.columns]

        return df

    except Exception as e:
        log.error(f"    ERREUR scraping : {e}")
        return None


def save_bronze(df, league_id: str, season: str, stat_type: str) -> str:
    """Sauvegarde le CSV brut horodate dans data/bronze/."""
    timestamp  = datetime.now().strftime("%Y%m%d_%H%M%S")
    saison_fmt = season.replace("-", "_")
    filename   = os.path.join(DIR_BRONZE, f"{timestamp}_{league_id}_{saison_fmt}_{stat_type}.csv")

    df["_league_id"]  = league_id
    df["_season"]     = season
    df["_stat_type"]  = stat_type
    df["_scraped_at"] = datetime.now().isoformat()

    df.to_csv(filename, index=True, encoding="utf-8-sig")
    return filename

# ---------------------------------------------------------------------------
# Execution principale
# ---------------------------------------------------------------------------

def run():
    config         = load_config()
    ligues_actives = config["ligues_actives"]
    saisons        = config["saisons"]
    stat_types     = config["stat_types_soccerdata"]

    total   = len(ligues_actives) * len(saisons) * len(stat_types)
    success = 0
    failures = []
    counter  = 0

    log.info("=" * 65)
    log.info("  RadarPepites - Scraping Bronze")
    log.info("=" * 65)
    log.info(f"  Ligues actives : {[l['id'] for l in ligues_actives]}")
    log.info(f"  Saisons        : {saisons}")
    log.info(f"  Types de stats : {stat_types}")
    log.info(f"  Total requetes : {total}")
    log.info(f"  Duree estimee  : ~{round(total * DELAY / 60)} minutes")
    log.info("=" * 65)

    for ligue in ligues_actives:
        league_id   = ligue["id"]
        league_name = ligue["soccerdata_key"]
        league_nom  = ligue["nom"]

        for season in saisons:
            for stat_type in stat_types:
                counter += 1
                log.info(f"[{counter}/{total}] {league_nom} | {season} | {stat_type}")

                df = scrape_stat(league_name, season, stat_type)

                if df is not None and not df.empty:
                    path = save_bronze(df, league_id, season, stat_type)
                    log.info(f"  -> {len(df)} lignes -> {os.path.basename(path)}")
                    success += 1
                else:
                    ref = f"{league_id}_{season}_{stat_type}"
                    failures.append(ref)
                    log.warning(f"  -> Ignore : {ref}")

                # Pause rate-limit - NE PAS SUPPRIMER
                log.info(f"  -> Pause {DELAY}s...")
                time.sleep(DELAY)

    # Bilan final
    log.info("=" * 65)
    log.info(f"  Scraping termine")
    log.info(f"  Succes  : {success}/{total}")
    log.info(f"  Echecs  : {len(failures)}")
    if failures:
        log.warning(f"  Detail echecs : {failures}")
    log.info(f"  Fichiers dans  : {DIR_BRONZE}")
    log.info("=" * 65)


if __name__ == "__main__":
    run()

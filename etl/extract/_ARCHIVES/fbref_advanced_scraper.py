# =============================================================
# RadarPépites — Scraping fbref avancé → Bronze
# Fichier  : etl/extract/fbref_advanced_scraper.py
# Rôle     : Récupère les stats avancées via cloudscraper
#            (contourne Cloudflare sans Chrome)
#            Stats : passing, passing_types, defense,
#                    possession, goal_shot_creation
# Pilotage : config/scraping_config.json
# Usage    : python etl/extract/fbref_advanced_scraper.py
# =============================================================

import os
import sys
import json
import time
import logging
from datetime import datetime
from io import StringIO

import pandas as pd
import cloudscraper
from bs4 import BeautifulSoup, Comment

# ---------------------------------------------------------------------------
# Chemins
# ---------------------------------------------------------------------------

DIR_ROOT   = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DIR_BRONZE = os.path.join(DIR_ROOT, "data", "bronze")
DIR_LOGS   = os.path.join(DIR_ROOT, "logs")
CONFIG     = os.path.join(DIR_ROOT, "config", "scraping_config.json")

DELAY = 6  # secondes — augmenté car cloudscraper est plus visible que Selenium

# Mapping stat_type → id de la table dans le HTML fbref
TABLE_IDS = {
    "passing":            "stats_passing",
    "passing_types":      "stats_passing_types",
    "goal_shot_creation": "stats_gca",
    "defense":            "stats_defense",
    "possession":         "stats_possession",
}

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

os.makedirs(DIR_BRONZE, exist_ok=True)
os.makedirs(DIR_LOGS,   exist_ok=True)

log_file = os.path.join(DIR_LOGS, f"advanced_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(log_file, encoding="utf-8"),
    ],
)
log = logging.getLogger("RadarPepites.Advanced")

# ---------------------------------------------------------------------------
# Session cloudscraper (créée une seule fois, réutilisée)
# ---------------------------------------------------------------------------

scraper = cloudscraper.create_scraper(
    browser={"browser": "chrome", "platform": "windows", "mobile": False}
)

# ---------------------------------------------------------------------------
# Construction URL fbref
# ---------------------------------------------------------------------------

def build_url(comp_id: int, slug: str, season: str, stat_type: str) -> str:
    current_season = "2024-2025"
    if season == current_season:
        return f"https://fbref.com/en/comps/{comp_id}/{stat_type}/{slug}-Stats"
    else:
        return f"https://fbref.com/en/comps/{comp_id}/{season}/{stat_type}/{season}-{slug}-Stats"

# ---------------------------------------------------------------------------
# Extraction table depuis HTML (gestion commentaires fbref)
# ---------------------------------------------------------------------------

def extract_table(html: str, table_id: str):
    soup = BeautifulSoup(html, "lxml")

    # Tentative 1 : table directement visible
    table = soup.find("table", {"id": table_id})

    # Tentative 2 : table cachée dans un commentaire HTML
    if table is None:
        comments = soup.find_all(string=lambda text: isinstance(text, Comment))
        for comment in comments:
            if table_id in comment:
                comment_soup = BeautifulSoup(comment, "lxml")
                table = comment_soup.find("table", {"id": table_id})
                if table:
                    break

    if table is None:
        return None

    try:
        df = pd.read_html(StringIO(str(table)))[0]

        # Aplatir MultiIndex
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [
                "_".join(filter(lambda x: x and "Unnamed" not in x, map(str, col))).strip()
                for col in df.columns
            ]

        # Supprimer lignes de sous-totaux fbref
        if "Rk" in df.columns:
            df = df[df["Rk"] != "Rk"].copy()

        df.dropna(how="all", inplace=True)
        return df

    except Exception as e:
        log.error(f"    Erreur parsing table {table_id} : {e}")
        return None

# ---------------------------------------------------------------------------
# Scraping d'une combinaison ligue / saison / stat
# ---------------------------------------------------------------------------

def scrape_advanced(comp_id: int, slug: str, league_id: str,
                    season: str, stat_type: str):
    url      = build_url(comp_id, slug, season, stat_type)
    table_id = TABLE_IDS.get(stat_type)

    log.info(f"    URL : {url}")

    try:
        response = scraper.get(url, timeout=30)

        if response.status_code == 429:
            log.warning("    Rate limit (429) — pause 120s...")
            time.sleep(120)
            response = scraper.get(url, timeout=30)

        if response.status_code == 403:
            log.error(f"    HTTP 403 — Cloudflare non contourné sur cette URL")
            return None

        if response.status_code != 200:
            log.error(f"    HTTP {response.status_code}")
            return None

        log.info(f"    HTTP 200 OK")
        df = extract_table(response.text, table_id)

        if df is None or df.empty:
            log.warning(f"    Table '{table_id}' introuvable dans la page")
            return None

        return df

    except Exception as e:
        log.error(f"    Erreur : {e}")
        return None

# ---------------------------------------------------------------------------
# Sauvegarde Bronze
# ---------------------------------------------------------------------------

def save_bronze(df, league_id: str, season: str, stat_type: str) -> str:
    timestamp  = datetime.now().strftime("%Y%m%d_%H%M%S")
    saison_fmt = season.replace("-", "_")
    filename   = os.path.join(DIR_BRONZE, f"{timestamp}_{league_id}_{saison_fmt}_{stat_type}.csv")

    df["_league_id"]  = league_id
    df["_season"]     = season
    df["_stat_type"]  = stat_type
    df["_scraped_at"] = datetime.now().isoformat()
    df["_source"]     = "fbref_cloudscraper"

    df.to_csv(filename, index=False, encoding="utf-8-sig")
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
    stat_types     = config["stat_types_advanced"]

    total    = len(ligues_actives) * len(saisons) * len(stat_types)
    success  = 0
    failures = []
    counter  = 0

    log.info("=" * 65)
    log.info("  RadarPepites - Scraping Avance Bronze (cloudscraper)")
    log.info("=" * 65)
    log.info(f"  Ligues  : {[l['id'] for l in ligues_actives]}")
    log.info(f"  Saisons : {saisons}")
    log.info(f"  Stats   : {stat_types}")
    log.info(f"  Total   : {total} fichiers")
    log.info(f"  Duree   : ~{round(total * DELAY / 60)} minutes")
    log.info("=" * 65)

    for ligue in ligues_actives:
        league_id = ligue["id"]
        comp_id   = ligue["fbref_comp_id"]
        slug      = ligue["fbref_slug"]
        nom       = ligue["nom"]

        for season in saisons:
            for stat_type in stat_types:
                counter += 1
                log.info(f"[{counter}/{total}] {nom} | {season} | {stat_type}")

                df = scrape_advanced(comp_id, slug, league_id, season, stat_type)

                if df is not None and not df.empty:
                    path = save_bronze(df, league_id, season, stat_type)
                    log.info(f"  -> {len(df)} lignes -> {os.path.basename(path)}")
                    success += 1
                else:
                    ref = f"{league_id}_{season}_{stat_type}"
                    failures.append(ref)
                    log.warning(f"  -> Echec : {ref}")

                log.info(f"  -> Pause {DELAY}s...")
                time.sleep(DELAY)

    log.info("=" * 65)
    log.info(f"  Termine : {success}/{total} fichiers generes")
    if failures:
        log.warning(f"  Echecs  : {failures}")
    log.info(f"  Bronze  : {DIR_BRONZE}")
    log.info("=" * 65)

if __name__ == "__main__":
    run()

# =============================================================
# RadarPépites — Scraping fbref via Playwright → Bronze
# Fichier  : etl/extract/fbref_playwright_scraper.py
# Rôle     : Récupère les stats avancées fbref pour les ligues
#            6-10 (POR, NED, BEL, TUR, AUT) qui ne sont pas
#            couvertes par soccerdata
#            Stats : passing, defense, possession,
#                    goal_shot_creation, passing_types
# Usage    : python etl/extract/fbref_playwright_scraper.py
# =============================================================

import os
import sys
import json
import time
import logging
from datetime import datetime
from io import StringIO

import pandas as pd
from bs4 import BeautifulSoup, Comment
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from playwright_stealth import stealth_sync

# ---------------------------------------------------------------------------
# Chemins
# ---------------------------------------------------------------------------

DIR_ROOT   = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DIR_BRONZE = os.path.join(DIR_ROOT, "data", "bronze")
DIR_LOGS   = os.path.join(DIR_ROOT, "logs")
CONFIG     = os.path.join(DIR_ROOT, "config", "scraping_config.json")

DELAY = 5  # secondes entre pages

# ---------------------------------------------------------------------------
# Configuration des ligues 6-10
# fbref_comp_id : ID de la compétition dans les URLs fbref
# fbref_slug    : slug dans les URLs fbref
# ---------------------------------------------------------------------------

LEAGUES = {
    "POR": {
        "nom":          "Primeira Liga",
        "fbref_comp_id": 32,
        "fbref_slug":   "Primeira-Liga",
    },
    "NED": {
        "nom":          "Eredivisie",
        "fbref_comp_id": 23,
        "fbref_slug":   "Eredivisie",
    },
    "BEL": {
        "nom":          "Pro League",
        "fbref_comp_id": 37,
        "fbref_slug":   "Belgian-First-Division-A",
    },
    "TUR": {
        "nom":          "Super Lig",
        "fbref_comp_id": 26,
        "fbref_slug":   "Super-Lig",
    },
    "AUT": {
        "nom":          "Bundesliga Autriche",
        "fbref_comp_id": 44,
        "fbref_slug":   "Austrian-Football-Bundesliga",
    },
}

# Types de stats avancées à récupérer
STAT_TYPES = {
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

log_file = os.path.join(DIR_LOGS, f"fbref_playwright_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(log_file, encoding="utf-8"),
    ],
)
log = logging.getLogger("RadarPepites.Playwright")

# ---------------------------------------------------------------------------
# Construction de l'URL fbref
# ---------------------------------------------------------------------------

def build_url(comp_id: int, slug: str, season: str, stat_type: str) -> str:
    """
    Exemples :
    Saison courante : https://fbref.com/en/comps/32/passing/Primeira-Liga-Stats
    Saison passée   : https://fbref.com/en/comps/32/2024-2025/passing/2024-2025-Primeira-Liga-Stats
    """
    current_season = "2025-2026"
    if season == current_season:
        return f"https://fbref.com/en/comps/{comp_id}/{stat_type}/{slug}-Stats"
    else:
        return f"https://fbref.com/en/comps/{comp_id}/{season}/{stat_type}/{season}-{slug}-Stats"

# ---------------------------------------------------------------------------
# Extraction de la table depuis le HTML
# fbref cache beaucoup de tables dans des commentaires HTML
# ---------------------------------------------------------------------------

def extract_table(html: str, table_id: str) -> pd.DataFrame | None:
    soup = BeautifulSoup(html, "lxml")

    # Tentative 1 : table directement visible
    table = soup.find("table", {"id": table_id})

    # Tentative 2 : table dans un commentaire HTML
    if table is None:
        comments = soup.find_all(string=lambda t: isinstance(t, Comment))
        for comment in comments:
            if table_id in comment:
                comment_soup = BeautifulSoup(comment, "lxml")
                table = comment_soup.find("table", {"id": table_id})
                if table:
                    break

    if table is None:
        log.warning(f"    Table '{table_id}' introuvable dans la page")
        return None

    try:
        df = pd.read_html(StringIO(str(table)))[0]

        # Aplatir MultiIndex de colonnes
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [
                "_".join(filter(lambda x: x and "Unnamed" not in x, map(str, col))).strip()
                for col in df.columns
            ]

        # Supprimer lignes répétées (sous-totaux fbref)
        if "Rk" in df.columns:
            df = df[df["Rk"] != "Rk"].copy()

        df.dropna(how="all", inplace=True)
        df.reset_index(drop=True, inplace=True)

        return df

    except Exception as e:
        log.error(f"    Erreur parsing table : {e}")
        return None

# ---------------------------------------------------------------------------
# Scraping d'une page via Playwright
# ---------------------------------------------------------------------------

def scrape_page(page, url: str, table_id: str) -> pd.DataFrame | None:
    """
    Ouvre l'URL avec Playwright (Chrome headless) et extrait la table.
    """
    log.info(f"    URL : {url}")
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=30000)

        # Attendre que la page soit chargée
        page.wait_for_timeout(5000)

        # Vérifier si Cloudflare bloque
        content = page.content()
        if "Just a moment" in content or "cf-browser-verification" in content or "challenge" in content.lower():
            log.warning("    Cloudflare détecté — attente 20s...")
            page.wait_for_timeout(20000)
            content = page.content()
            # Deuxième vérification
            if "Just a moment" in content:
                log.warning("    Cloudflare persistant — attente 30s supplémentaires...")
                page.wait_for_timeout(30000)
                content = page.content()

        df = extract_table(content, table_id)
        return df

    except PlaywrightTimeout:
        log.error(f"    Timeout sur {url}")
        return None
    except Exception as e:
        log.error(f"    Erreur page : {e}")
        return None

# ---------------------------------------------------------------------------
# Sauvegarde Bronze
# ---------------------------------------------------------------------------

def save_bronze(df: pd.DataFrame, league_key: str,
                season: str, stat_type: str) -> str:
    timestamp  = datetime.now().strftime("%Y%m%d_%H%M%S")
    saison_fmt = season.replace("-", "_")
    filename   = os.path.join(
        DIR_BRONZE,
        f"{timestamp}_{league_key}_{saison_fmt}_{stat_type}_fbref.csv"
    )
    df["_league_id"]  = league_key
    df["_season"]     = season
    df["_stat_type"]  = stat_type
    df["_source"]     = "fbref_playwright"
    df["_scraped_at"] = datetime.now().isoformat()
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

    # Filtrer uniquement les ligues 6-10
    ligues_cibles = [l for l in ligues_actives if l["id"] in LEAGUES]

    total    = len(ligues_cibles) * len(saisons) * len(STAT_TYPES)
    success  = 0
    failures = []
    counter  = 0

    log.info("=" * 65)
    log.info("  RadarPepites - Scraping fbref Playwright -> Bronze")
    log.info("=" * 65)
    log.info(f"  Ligues  : {[l['id'] for l in ligues_cibles]}")
    log.info(f"  Saisons : {saisons}")
    log.info(f"  Stats   : {list(STAT_TYPES.keys())}")
    log.info(f"  Total   : {total} pages à scraper")
    log.info(f"  Durée   : ~{round(total * (DELAY + 5) / 60)} minutes")
    log.info("=" * 65)

    with sync_playwright() as p:
        # Lancer Chrome en mode headless
        # Utilise le vrai Chrome installé avec le profil utilisateur existant
        # Les cookies fbref déjà présents permettent de contourner Cloudflare
        user_data_dir = r"C:\Users\serge\AppData\Local\Google\Chrome\User Data"

        context = p.chromium.launch_persistent_context(
            user_data_dir  = user_data_dir,
            channel        = "chrome",        # Vrai Chrome, pas Chromium
            headless       = False,
            args           = [
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--profile-directory=Default",
            ],
            user_agent = (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            viewport = {"width": 1920, "height": 1080},
        )
        page = context.new_page()
        stealth_sync(page)

        # Première visite fbref pour charger les cookies existants
        log.info("Initialisation avec profil Chrome existant...")
        try:
            page.goto("https://fbref.com", wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(5000)
            log.info("Session fbref établie avec profil Chrome")
        except Exception as e:
            log.warning(f"Init fbref : {e}")

        for ligue in ligues_cibles:
            league_key = ligue["id"]
            info       = LEAGUES[league_key]
            comp_id    = info["fbref_comp_id"]
            slug       = info["fbref_slug"]
            nom        = info["nom"]

            for season in saisons:
                for stat_type, table_id in STAT_TYPES.items():
                    counter += 1
                    log.info(f"[{counter}/{total}] {nom} | {season} | {stat_type}")

                    url = build_url(comp_id, slug, season, stat_type)
                    df  = scrape_page(page, url, table_id)

                    if df is not None and not df.empty:
                        path = save_bronze(df, league_key, season, stat_type)
                        log.info(f"  -> {len(df)} joueurs -> {os.path.basename(path)}")
                        success += 1
                    else:
                        ref = f"{league_key}_{season}_{stat_type}"
                        failures.append(ref)
                        log.warning(f"  -> Echec : {ref}")

                    # Pause entre pages
                    log.info(f"  -> Pause {DELAY}s...")
                    time.sleep(DELAY)

        context.close()

    log.info("=" * 65)
    log.info(f"  Termine  : {success}/{total} fichiers générés")
    if failures:
        log.warning(f"  Echecs   : {failures}")
    log.info(f"  Bronze   : {DIR_BRONZE}")
    log.info("=" * 65)

if __name__ == "__main__":
    run()

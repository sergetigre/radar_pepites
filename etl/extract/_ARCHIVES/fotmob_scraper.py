# =============================================================
# RadarPépites — Scraping FotMob → Bronze
# Fichier  : etl/extract/fotmob_scraper.py
# Rôle     : Stats joueurs via API FotMob (Next.js)
#            - Récupère le buildId dynamiquement
#            - Récupère le seasonId via api/data/leagues
#            - Scrape les stats via _next/data
# Usage    : python etl/extract/fotmob_scraper.py
# =============================================================

import os
import sys
import re
import json
import time
import logging
from datetime import datetime

import pandas as pd
import requests

# ---------------------------------------------------------------------------
# Chemins
# ---------------------------------------------------------------------------

DIR_ROOT   = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DIR_BRONZE = os.path.join(DIR_ROOT, "data", "bronze")
DIR_LOGS   = os.path.join(DIR_ROOT, "logs")
CONFIG     = os.path.join(DIR_ROOT, "config", "scraping_config.json")

DELAY = 4

# ---------------------------------------------------------------------------
# IDs FotMob des 10 ligues + slugs pour construction des URLs
# ---------------------------------------------------------------------------

FOTMOB_LEAGUES = {
    "ENG": {"id": 47,  "nom": "Premier League",     "slug": "premier-league"},
    "ESP": {"id": 87,  "nom": "La Liga",            "slug": "laliga"},
    "GER": {"id": 54,  "nom": "Bundesliga",         "slug": "bundesliga"},
    "ITA": {"id": 55,  "nom": "Serie A",            "slug": "serie-a"},
    "FRA": {"id": 53,  "nom": "Ligue 1",            "slug": "ligue-1"},
    "POR": {"id": 61,  "nom": "Primeira Liga",      "slug": "liga-portugal"},
    "NED": {"id": 57,  "nom": "Eredivisie",         "slug": "eredivisie"},
    "BEL": {"id": 40,  "nom": "First Division A",  "slug": "first-division-a"},
    "TUR": {"id": 71,  "nom": "Super Lig",          "slug": "super-lig"},
    "AUT": {"id": 38,  "nom": "Bundesliga Autriche","slug": "bundesliga-austria"},
}

# Mapping saison RadarPépites → format FotMob
SEASON_MAP = {
    "2022-2023": "2022/2023",
    "2023-2024": "2023/2024",
    "2024-2025": "2024/2025",
}

# Stats à récupérer
STAT_NAMES = [
    "goals", "assists", "rating", "accurate_passes",
    "key_passes", "tackles_won", "interceptions",
    "shots_on_target", "dribble_success", "minutes_played",
    "yellow_cards", "red_cards", "expected_goals", "expected_assists",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, */*",
    "Referer": "https://www.fotmob.com/",
}

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

os.makedirs(DIR_BRONZE, exist_ok=True)
os.makedirs(DIR_LOGS,   exist_ok=True)

log_file = os.path.join(DIR_LOGS, f"fotmob_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(log_file, encoding="utf-8"),
    ],
)
log = logging.getLogger("RadarPepites.FotMob")

session = requests.Session()
session.headers.update(HEADERS)

# ---------------------------------------------------------------------------
# Étape 1 : Récupérer le buildId Next.js dynamiquement
# ---------------------------------------------------------------------------

def get_build_id() -> str | None:
    """
    Récupère le buildId Next.js depuis la page principale FotMob.
    Il est injecté dans le HTML dans __NEXT_DATA__ à chaque déploiement.
    """
    log.info("Récupération du buildId FotMob...")
    try:
        r = session.get("https://www.fotmob.com", timeout=15)
        if r.status_code != 200:
            log.error(f"Homepage → HTTP {r.status_code}")
            return None

        # Extraction du buildId depuis __NEXT_DATA__
        match = re.search(r'"buildId"\s*:\s*"([^"]+)"', r.text)
        if match:
            build_id = match.group(1)
            log.info(f"buildId trouvé : {build_id}")
            return build_id

        log.error("buildId non trouvé dans la page")
        return None

    except Exception as e:
        log.error(f"Erreur get_build_id : {e}")
        return None

# ---------------------------------------------------------------------------
# Étape 2 : Récupérer le seasonId via api/data/leagues
# ---------------------------------------------------------------------------

def get_season_id(league_id: int, fotmob_season: str) -> int | None:
    """
    Récupère le seasonId numérique FotMob pour une saison donnée.
    Endpoint stable : /api/data/leagues?id=X&ccode3=FRA&season=YYYY%2FYYYY
    """
    encoded_season = fotmob_season.replace("/", "%2F")
    url = f"https://www.fotmob.com/api/data/leagues?id={league_id}&ccode3=FRA&season={encoded_season}"

    try:
        r = session.get(url, timeout=15)
        if r.status_code != 200:
            log.error(f"    api/data/leagues → HTTP {r.status_code}")
            return None

        data = r.json()

        # Cherche le seasonId dans la réponse
        # Structure possible : data['details']['selectedSeason'] ou data['season']['id']
        season_id = (
            data.get("details", {}).get("selectedSeason") or
            data.get("season", {}).get("id") or
            data.get("selectedSeason") or
            data.get("seasonId")
        )

        if season_id:
            log.info(f"    seasonId : {season_id}")
            return int(season_id)

        # Fallback : cherche dans la liste des saisons
        seasons = (
            data.get("seasons") or
            data.get("details", {}).get("seasons") or
            []
        )
        for s in seasons:
            s_name = str(s.get("name", "") or s.get("season", ""))
            if fotmob_season in s_name or s_name in fotmob_season:
                sid = s.get("id") or s.get("seasonId")
                log.info(f"    seasonId (fallback) : {sid}")
                return int(sid)

        # Log la structure reçue pour debug
        log.warning(f"    seasonId non trouvé. Clés reçues : {list(data.keys())}")
        return None

    except Exception as e:
        log.error(f"    Erreur get_season_id : {e}")
        return None

# ---------------------------------------------------------------------------
# Étape 3 : Récupérer les stats joueurs via _next/data
# ---------------------------------------------------------------------------

def get_player_stats(build_id: str, league_id: int, season_id: int,
                     slug: str, league_key: str) -> list:
    """
    Récupère les stats joueurs via l'endpoint _next/data de FotMob.
    URL pattern découverte depuis DevTools :
    /api/data/leagues/{id}/stats/season/{seasonId}/players/{stat}
    """
    all_rows = []

    for stat_name in STAT_NAMES:
        # Endpoint _next/data (Next.js SSR)
        url = (
            f"https://www.fotmob.com/_next/data/{build_id}/fr"
            f"/leagues/{league_id}/stats/season/{season_id}"
            f"/players/{stat_name}/{slug}-players.json"
            f"?lng=fr&id={league_id}&season={season_id}"
            f"&type=players&stat={stat_name}&slug={slug}-players"
        )

        try:
            r = session.get(url, timeout=15)

            if r.status_code == 404:
                # Essai sans le préfixe de langue
                url2 = (
                    f"https://www.fotmob.com/_next/data/{build_id}"
                    f"/leagues/{league_id}/stats/season/{season_id}"
                    f"/players/{stat_name}/{slug}-players.json"
                    f"?id={league_id}&season={season_id}"
                    f"&type=players&stat={stat_name}&slug={slug}-players"
                )
                r = session.get(url2, timeout=15)

            if r.status_code != 200:
                log.warning(f"      {stat_name} → HTTP {r.status_code}")
                time.sleep(DELAY)
                continue

            data = r.json()

            # Navigation dans la structure Next.js : pageProps → data → stats
            page_props = data.get("pageProps", {})
            stats_data = (
                page_props.get("data", {}) or
                page_props.get("stats", {}) or
                page_props
            )

            # Extraction des joueurs
            players = []
            if "TopLists" in stats_data:
                for top in stats_data["TopLists"]:
                    players.extend(top.get("StatList", []))
            elif "stats" in stats_data:
                raw = stats_data["stats"]
                if isinstance(raw, list):
                    players = raw
                elif isinstance(raw, dict):
                    players = raw.get("players", raw.get("items", []))
            elif isinstance(stats_data, list):
                players = stats_data

            for p in players:
                row = {
                    "player_id":   p.get("ParticipantId") or p.get("id"),
                    "player_name": p.get("ParticipantName") or p.get("name"),
                    "team_name":   p.get("TeamName") or p.get("teamName"),
                    "team_id":     p.get("TeamId") or p.get("teamId"),
                    "position":    p.get("Position") or p.get("position"),
                    "stat_name":   stat_name,
                    "stat_value":  p.get("StatValue") or p.get("statValue") or p.get("value"),
                    "minutes":     p.get("MinutesPlayed") or p.get("minutesPlayed"),
                    "matches":     p.get("MatchesPlayed") or p.get("matchesPlayed"),
                    "nationality": p.get("CountryCode") or p.get("ccode"),
                    "season_id":   season_id,
                }
                all_rows.append(row)

            log.info(f"      {stat_name} → {len(players)} joueurs")

        except Exception as e:
            log.error(f"      {stat_name} → Erreur : {e}")

        time.sleep(DELAY)

    return all_rows

# ---------------------------------------------------------------------------
# Sauvegarde Bronze
# ---------------------------------------------------------------------------

def save_bronze(rows: list, league_key: str, season: str) -> str:
    df = pd.DataFrame(rows)
    timestamp  = datetime.now().strftime("%Y%m%d_%H%M%S")
    saison_fmt = season.replace("-", "_")
    filename   = os.path.join(DIR_BRONZE, f"{timestamp}_{league_key}_{saison_fmt}_fotmob.csv")
    df["_league_id"]  = league_key
    df["_season"]     = season
    df["_source"]     = "fotmob"
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
    ligues_fotmob  = [l for l in ligues_actives if l["id"] in FOTMOB_LEAGUES]

    # Récupération du buildId (une seule fois pour toute la session)
    build_id = get_build_id()
    if not build_id:
        log.error("Impossible de récupérer le buildId. Abandon.")
        sys.exit(1)

    time.sleep(DELAY)

    total    = len(ligues_fotmob) * len(saisons)
    success  = 0
    failures = []
    counter  = 0

    log.info("=" * 65)
    log.info("  RadarPepites - Scraping FotMob -> Bronze")
    log.info("=" * 65)
    log.info(f"  BuildId : {build_id}")
    log.info(f"  Ligues  : {[l['id'] for l in ligues_fotmob]}")
    log.info(f"  Saisons : {saisons}")
    log.info(f"  Total   : {total} combinaisons ligue x saison")
    log.info("=" * 65)

    for ligue in ligues_fotmob:
        league_key  = ligue["id"]
        fotmob_info = FOTMOB_LEAGUES[league_key]
        league_id   = fotmob_info["id"]
        slug        = fotmob_info["slug"]
        nom         = fotmob_info["nom"]

        for season in saisons:
            counter += 1
            fotmob_season = SEASON_MAP.get(season, season)
            log.info(f"[{counter}/{total}] {nom} | {season}")

            # Récupération du seasonId
            season_id = get_season_id(league_id, fotmob_season)
            if not season_id:
                log.warning(f"  -> seasonId introuvable, on passe")
                failures.append(f"{league_key}_{season}")
                time.sleep(DELAY)
                continue

            time.sleep(DELAY)

            # Scraping des stats
            rows = get_player_stats(build_id, league_id, season_id, slug, league_key)

            if rows:
                path = save_bronze(rows, league_key, season)
                log.info(f"  -> {len(rows)} lignes -> {os.path.basename(path)}")
                success += 1
            else:
                failures.append(f"{league_key}_{season}")
                log.warning(f"  -> Aucune donnée : {league_key}_{season}")

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

"""
etl/extract/download_media_assets.py — Télécharge les images Sofascore
(logos clubs/ligues, photos joueurs) et les stocke dans public.media_assets.

Contexte : Sofascore (Cloudflare, cf. commit scraper 573ad47) bloque toute
requête serveur-à-serveur, hotlink direct comme proxy Next.js — vérifié
manuellement sur les deux avant d'écrire ce script. Seul un vrai navigateur
(undetected-chromedriver, déjà utilisé par datafc_scraper_all.py) passe le
challenge. On télécharge donc une fois via le navigateur et on stocke le
binaire en base : le site Next.js sert ensuite ces images sans jamais
recontacter Sofascore à l'exécution.

Technique : une seule navigation vers www.sofascore.com pour résoudre le
challenge Cloudflare initial, puis tous les téléchargements suivants se
font via `fetch()` exécuté dans la page (même origine, pas de CORS, pas de
re-navigation) — beaucoup plus rapide que relancer driver.get() par image.

Idempotent/reprenable : les paires (kind, entity_id) déjà présentes dans
media_assets sont sautées, donc un rerun après interruption ne retélécharge
que ce qui manque. À relancer périodiquement pour capter les nouveaux
joueurs/équipes ajoutés par le pipeline ETL.

Usage : python etl/extract/download_media_assets.py
"""

import argparse
import base64
import logging
import os
import sys
import time
from pathlib import Path

import psycopg2
import psycopg2.extras
import seleniumbase as sb
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / "config" / ".env")

SOFASCORE_BASE = "https://www.sofascore.com/api/v1"
CF_CHALLENGE_MARKERS = [
    "Verify you are human", "Checking your browser", "Just a moment...",
    "Ray ID:", "cf-challenge", "Please stand by",
]

# ligue_id (dim_ligues) -> tournament_id Sofascore — copié de
# web-next/lib/media.ts::LIGUE_TOURNAMENT_IDS (seule source, pas de table
# dédiée pour ces 10 valeurs fixes).
LIGUE_TOURNAMENT_IDS = [17, 8, 35, 23, 34, 238, 37, 38, 52, 45]

BATCH_COMMIT_SIZE = 50
FETCH_TIMEOUT_S = 20


def get_connection():
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL introuvable dans config/.env")
    return psycopg2.connect(database_url)


def fetch_targets(conn) -> list[tuple[str, int]]:
    """Liste (kind, entity_id) à couvrir, moins ce qui est déjà en base."""
    with conn.cursor() as cur:
        cur.execute("SELECT DISTINCT player_id_ss FROM public.dim_joueurs WHERE player_id_ss IS NOT NULL")
        players = [("player", r[0]) for r in cur.fetchall()]

        cur.execute("SELECT DISTINCT team_id_ss FROM public.dim_equipes WHERE team_id_ss IS NOT NULL")
        teams = [("team", r[0]) for r in cur.fetchall()]

        tournaments = [("unique-tournament", tid) for tid in LIGUE_TOURNAMENT_IDS]

        cur.execute("SELECT kind, entity_id FROM public.media_assets")
        existing = {(k, eid) for k, eid in cur.fetchall()}

    targets = players + teams + tournaments
    remaining = [t for t in targets if t not in existing]
    logger.info(
        "Cibles : %d joueurs, %d équipes, %d ligues — %d déjà en base, %d restants",
        len(players), len(teams), len(tournaments), len(existing), len(remaining),
    )
    return remaining


def solve_challenge(driver) -> None:
    driver.get("https://www.sofascore.com/")
    time.sleep(1.5)
    body = driver.get_text("body")
    if any(marker in body for marker in CF_CHALLENGE_MARKERS):
        logger.info("Challenge Cloudflare détecté, attente 15s...")
        time.sleep(15)
        driver.get("https://www.sofascore.com/")
        time.sleep(1.5)
        body = driver.get_text("body")
        if any(marker in body for marker in CF_CHALLENGE_MARKERS):
            raise RuntimeError("Challenge Cloudflare non résolu après retry")
    logger.info("Challenge Cloudflare résolu, session prête.")


FETCH_SCRIPT = """
const callback = arguments[arguments.length - 1];
fetch(arguments[0])
  .then(r => {
    if (!r.ok) { callback({status: r.status}); return; }
    const ct = r.headers.get('content-type') || 'image/png';
    return r.arrayBuffer().then(buf => {
      const bytes = new Uint8Array(buf);
      let binary = '';
      for (let i = 0; i < bytes.byteLength; i++) binary += String.fromCharCode(bytes[i]);
      callback({status: 200, data: btoa(binary), contentType: ct});
    });
  })
  .catch(e => callback({status: 0, error: String(e)}));
"""


def fetch_image(driver, kind: str, entity_id: int) -> tuple[bytes, str] | None:
    """Retourne (bytes, content_type) si l'image existe, None si 404 légitime."""
    url = f"{SOFASCORE_BASE}/{kind}/{entity_id}/image"
    driver.set_script_timeout(FETCH_TIMEOUT_S)
    result = driver.execute_async_script(FETCH_SCRIPT, url)
    if result.get("status") == 404:
        return None
    if result.get("status") != 200:
        raise RuntimeError(f"status={result.get('status')} error={result.get('error')}")
    return base64.b64decode(result["data"]), result["contentType"]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None, help="Limite le nombre de cibles (test rapide)")
    args = parser.parse_args()

    conn = get_connection()
    conn.autocommit = False
    targets = fetch_targets(conn)
    if args.limit:
        targets = targets[: args.limit]
    if not targets:
        logger.info("Rien à télécharger, tout est déjà en base.")
        return

    logger.info("Démarrage du navigateur undetected-chromedriver...")
    driver_holder = [sb.Driver(uc=True, headless=True)]
    conn_holder = [conn]
    try:
        solve_challenge(driver_holder[0])

        ok_count = 0
        notfound_count = 0
        fail_count = 0
        consecutive_fails = 0
        pending: list[tuple[str, int, str, bytes]] = []

        def insert_rows(rows):
            with conn_holder[0].cursor() as cur:
                psycopg2.extras.execute_values(
                    cur,
                    """
                    INSERT INTO public.media_assets (kind, entity_id, content_type, data)
                    VALUES %s
                    ON CONFLICT (kind, entity_id)
                    DO UPDATE SET content_type = EXCLUDED.content_type,
                                  data = EXCLUDED.data,
                                  date_maj = NOW()
                    """,
                    rows,
                )
            conn_holder[0].commit()

        def flush():
            nonlocal pending
            if not pending:
                return
            rows = [(k, eid, ct, psycopg2.Binary(data)) for k, eid, ct, data in pending]
            try:
                insert_rows(rows)
            except psycopg2.OperationalError as exc:
                # Neon ferme parfois les connexions inactives (cf. silver_transformer.get_engine) —
                # reconnecte et retente une fois avant d'abandonner le batch.
                logger.warning("Connexion DB perdue (%s), reconnexion...", exc)
                try:
                    conn_holder[0].close()
                except Exception:
                    pass
                conn_holder[0] = get_connection()
                conn_holder[0].autocommit = False
                insert_rows(rows)
            pending = []

        def restart_driver():
            logger.warning("Redémarrage complet du navigateur...")
            try:
                driver_holder[0].quit()
            except Exception:
                pass
            driver_holder[0] = sb.Driver(uc=True, headless=True)
            solve_challenge(driver_holder[0])

        for i, (kind, entity_id) in enumerate(targets, start=1):
            try:
                result = fetch_image(driver_holder[0], kind, entity_id)
                consecutive_fails = 0
                if result is None:
                    notfound_count += 1
                else:
                    data, content_type = result
                    pending.append((kind, entity_id, content_type, data))
                    ok_count += 1
            except Exception as exc:
                fail_count += 1
                consecutive_fails += 1
                logger.warning("Échec %s/%d (%s/%d): %s", i, len(targets), kind, entity_id, exc)
                if consecutive_fails >= 5:
                    logger.warning("5 échecs consécutifs, nouvelle résolution du challenge...")
                    try:
                        solve_challenge(driver_holder[0])
                    except Exception:
                        restart_driver()
                    consecutive_fails = 0

            if len(pending) >= BATCH_COMMIT_SIZE:
                flush()

            if i % 100 == 0:
                logger.info(
                    "Progression %d/%d — ok=%d not_found=%d fail=%d",
                    i, len(targets), ok_count, notfound_count, fail_count,
                )

        flush()
        logger.info(
            "Terminé — ok=%d not_found=%d fail=%d sur %d cibles",
            ok_count, notfound_count, fail_count, len(targets),
        )
    finally:
        try:
            driver_holder[0].quit()
        except Exception:
            pass
        conn_holder[0].close()


if __name__ == "__main__":
    sys.exit(main() or 0)

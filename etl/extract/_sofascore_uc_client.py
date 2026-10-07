"""
etl/extract/_sofascore_uc_client.py — Monkeypatch Sofascore : navigateur réel
au lieu de curl_cffi.

Depuis [date de ce correctif], l'API Sofascore renvoie un challenge Cloudflare
("403 challenge") à toute requête curl_cffi (impersonation TLS chrome124),
aussi bien sur api.sofascore.com que www.sofascore.com, y compris pour de
simples lectures de stats publiques — vérifié manuellement avant d'écrire ce
correctif. Un navigateur réel (seleniumbase + undetected-chromedriver, déjà
utilisé avec succès par soccerdata pour FBref dans ce projet) passe sans
accroc : le bot-detection de Cloudflare se base sur des signaux (canvas,
WebGL, etc.) qu'une impersonation TLS seule ne reproduit pas.

Ce module patche SofascoreClient.get() (datafc.utils._client) pour router
toutes les requêtes via un navigateur headless partagé au lieu de curl_cffi,
en conservant le cache disque et la logique de retry existants. Toutes les
fonctions de datafc.sofascore.* (standings_data, squad_data, player_data,
league_player_stats_data_fixed...) en bénéficient automatiquement, sans
modification de datafc_scraper_all.py / datafc_players_info_all.py /
datafc_players_info_gap.py.

Usage : importer ce module avant tout appel à datafc.* ou au client Sofascore
    import _sofascore_uc_client  # noqa: F401 (active le patch par import)
"""

import json
import logging
import threading
import time

import seleniumbase as sb
from datafc.exceptions import APIError
from datafc.utils._client import SofascoreClient
from datafc.utils._config import API_URLS, WWW_URLS

logger = logging.getLogger(__name__)

_driver = None
_driver_lock = threading.Lock()

CF_CHALLENGE_MARKERS = [
    "Verify you are human", "Checking your browser", "Just a moment...",
    "Ray ID:", "cf-challenge", "Please stand by",
]


def _get_driver() -> "sb.Driver":
    global _driver
    with _driver_lock:
        if _driver is None:
            logger.info("Démarrage du navigateur undetected-chromedriver (Sofascore)...")
            _driver = sb.Driver(uc=True, headless=True)
        return _driver


def close_driver() -> None:
    """À appeler en fin de script pour libérer proprement le navigateur."""
    global _driver
    with _driver_lock:
        if _driver is not None:
            try:
                _driver.quit()
            except Exception:
                pass
            _driver = None


def _browser_get_json(url: str) -> dict:
    driver = _get_driver()
    driver.get(url)
    time.sleep(0.6)  # laisse le temps au JSON de s'afficher (page vide sinon)

    def _read_body() -> str:
        try:
            return driver.get_text("pre")
        except Exception:
            return driver.get_text("body")

    body = _read_body()
    if any(marker in body for marker in CF_CHALLENGE_MARKERS):
        logger.warning("Challenge Cloudflare détecté, nouvelle tentative dans 15s — %s", url)
        time.sleep(15)
        driver.get(url)
        time.sleep(0.6)
        body = _read_body()
        if any(marker in body for marker in CF_CHALLENGE_MARKERS):
            raise APIError(403, url, "Challenge Cloudflare non résolu après retry")

    try:
        return json.loads(body)
    except json.JSONDecodeError as e:
        raise APIError(0, url, f"Réponse non-JSON ({e})") from e


def _patched_get(self, url: str) -> dict:
    if self._cache is not None:
        cached = self._cache.get(url)
        if cached is not None:
            logger.debug("Cache hit: %s", url)
            return cached

    last_exc: Exception | None = None
    for attempt in range(1, self._retries + 1):
        self._rate_limit_wait()
        try:
            data = _browser_get_json(url)
            if not isinstance(data, dict):
                raise APIError(200, url, f"Non-dict JSON response ({type(data).__name__})")
            if self._cache is not None:
                self._cache.set(url, data)
            return data
        except APIError:
            raise
        except Exception as exc:
            logger.warning("Requête navigateur échouée (tentative %d/%d): %s", attempt, self._retries, exc)
            last_exc = exc
            time.sleep(2 ** attempt)

    raise APIError(0, url, f"Échec des {self._retries} tentatives") from last_exc


SofascoreClient.get = _patched_get

# api.sofascore.com renvoie un 403 "Forbidden" sec (même via navigateur réel),
# alors que www.sofascore.com (même espace de chemins /api/v1/...) répond
# normalement — vérifié manuellement sur /seasons, /statistics, /player/{id}.
# On redirige donc aussi le dict lu dynamiquement par les fonctions internes
# de datafc (standings_data, squad_data, player_data...), qui construisent
# encore leurs URLs sur API_URLS["sofascore"].
API_URLS["sofascore"] = WWW_URLS["sofascore"]

logger.info("Sofascore patché : requêtes via navigateur réel + domaine www.sofascore.com.")

# =============================================================
# RadarPépites — Agent orchestrateur de scraping
# Fichier  : etl/extract/scraping_agent.py
# Rôle     : Enchaîne fbref_scraper.py, datafc_scraper.py et
#            datafc_players_info.py, logge le déroulé dans
#            logs/ et affiche un rapport de synthèse.
# Usage    : python etl/extract/scraping_agent.py
#            python etl/extract/scraping_agent.py --only fbref
#            python etl/extract/scraping_agent.py --skip players
# =============================================================

import argparse
import json
import logging
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
EXTRACT_DIR = ROOT_DIR / "etl" / "extract"
CONFIG_PATH = ROOT_DIR / "config" / "scraping_config.json"
BRONZE_DIR = ROOT_DIR / "data" / "bronze"
LOGS_DIR = ROOT_DIR / "logs"

SCRIPTS = [
    {
        "key": "fbref",
        "file": "fbref_scraper.py",
        "label": "fbref_scraper.py",
        "source": "fbref via soccerdata — Big 5 uniquement",
    },
    {
        "key": "datafc",
        "file": "datafc_scraper.py",
        "label": "datafc_scraper.py",
        "source": "Sofascore via datafc — 10 ligues",
    },
    {
        "key": "players",
        "file": "datafc_players_info.py",
        "label": "datafc_players_info.py",
        "source": "Sofascore via datafc — 10 ligues",
    },
]

BANNER_WIDTH = 71


def setup_logger() -> tuple[logging.Logger, Path]:
    # Console Windows par défaut pas toujours en UTF-8 (accents, emojis du rapport)
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")

    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOGS_DIR / f"scraping_agent_{datetime.now():%Y%m%d_%H%M%S}.log"

    logger = logging.getLogger("scraping_agent")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    formatter = logging.Formatter("%(message)s")

    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger, log_path


def load_active_scope(logger: logging.Logger) -> tuple[list[str], list[str]]:
    if not CONFIG_PATH.exists():
        logger.info(f"  /!\\ {CONFIG_PATH} introuvable — ligues/saisons non affichées")
        return [], []

    try:
        config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        logger.info(f"  /!\\ {CONFIG_PATH} illisible ({e}) — ligues/saisons non affichées")
        return [], []

    ligues = [l["id"] for l in config.get("ligues", []) if l.get("actif")]
    saisons = config.get("saisons", [])
    return ligues, saisons


def count_csv(bronze_dir: Path) -> int:
    if not bronze_dir.exists():
        return 0
    return len(list(bronze_dir.glob("*.csv")))


def get_dir_size_mb(dir_path: Path) -> float:
    if not dir_path.exists():
        return 0.0
    total = sum(f.stat().st_size for f in dir_path.rglob("*") if f.is_file())
    return round(total / (1024 * 1024), 1)


def format_duration(seconds: float) -> str:
    total_seconds = int(round(seconds))
    hours, remainder = divmod(total_seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours > 0:
        return f"{hours}h {minutes}m {secs}s"
    return f"{minutes}m {secs}s"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Agent orchestrateur de scraping RadarPépites"
    )
    parser.add_argument(
        "--only",
        choices=["fbref", "datafc", "players"],
        action="append",
        default=None,
        help="N'exécuter que ce(s) script(s)",
    )
    parser.add_argument(
        "--skip",
        choices=["fbref", "datafc", "players"],
        action="append",
        default=None,
        help="Sauter ce(s) script(s)",
    )
    return parser.parse_args()


def select_scripts(args: argparse.Namespace) -> list[dict]:
    scripts = SCRIPTS
    if args.only:
        only_set = set(args.only)
        scripts = [s for s in scripts if s["key"] in only_set]
    if args.skip:
        skip_set = set(args.skip)
        scripts = [s for s in scripts if s["key"] not in skip_set]
    return scripts


def run_script(script: dict, logger: logging.Logger) -> dict:
    script_path = EXTRACT_DIR / script["file"]

    start_dt = datetime.now()
    logger.info(f"  Début   : {start_dt:%H:%M:%S}")
    logger.info(f"  Source  : {script['source']}")
    logger.info("  ---")

    baseline_csv = count_csv(BRONZE_DIR)
    start_monotonic = time.monotonic()

    if not script_path.exists():
        success = False
        returncode = None
        logger.info(f"  /!\\ Fichier introuvable : {script_path}")
    else:
        try:
            result = subprocess.run([sys.executable, str(script_path)])
            returncode = result.returncode
            success = returncode == 0
        except Exception as e:
            returncode = None
            success = False
            logger.info(f"  /!\\ Erreur au lancement : {e}")

    duration = time.monotonic() - start_monotonic
    end_dt = datetime.now()
    new_csv = count_csv(BRONZE_DIR) - baseline_csv

    logger.info("  ---")
    logger.info(f"  Fin     : {end_dt:%H:%M:%S}")
    logger.info(f"  Durée   : {format_duration(duration)}")
    logger.info(f"  Nouveaux CSV : {new_csv}")
    logger.info(f"  Statut  : {'✅ SUCCÈS' if success else '❌ ÉCHEC'}")

    return {
        "label": script["label"],
        "success": success,
        "returncode": returncode,
        "duration": duration,
        "new_csv": new_csv,
    }


def main() -> None:
    args = parse_args()
    logger, log_path = setup_logger()

    ligues, saisons = load_active_scope(logger)
    baseline_csv = count_csv(BRONZE_DIR)
    scripts_to_run = select_scripts(args)

    sep = "=" * BANNER_WIDTH
    logger.info(sep)
    logger.info("  RadarPépites — Agent de Scraping")
    logger.info(f"  Ligues  : {', '.join(ligues) if ligues else '(non disponible)'}")
    logger.info(f"  Saisons : {', '.join(saisons) if saisons else '(non disponible)'}")
    logger.info(f"  Scripts : {len(scripts_to_run)} à exécuter")
    logger.info(f"  Bronze  : {baseline_csv} fichiers CSV existants")
    logger.info(sep)

    if not scripts_to_run:
        logger.info("\nAucun script à exécuter (voir --only / --skip).")
        return

    overall_start = time.monotonic()
    results = []

    total = len(scripts_to_run)
    for i, script in enumerate(scripts_to_run, start=1):
        logger.info(f"\n[{i}/{total}] {script['label']}")
        results.append(run_script(script, logger))

    overall_duration = time.monotonic() - overall_start

    total_new_csv = sum(r["new_csv"] for r in results)
    success_count = sum(1 for r in results if r["success"])
    bronze_size_mb = get_dir_size_mb(BRONZE_DIR)

    logger.info(f"\n{sep}")
    logger.info("  Rapport final")
    logger.info(f"  Durée totale : {format_duration(overall_duration)}")
    logger.info(f"  Succès       : {success_count}/{total}")
    logger.info(f"  Nouveaux CSV : {total_new_csv}")
    logger.info(f"  Bronze total : {bronze_size_mb:.1f} MB")
    logger.info(sep)
    logger.info(f"\nLog complet : {log_path}")


if __name__ == "__main__":
    main()

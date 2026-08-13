"""
scraping_agent.py
RadarPépites — Pipeline complet Bronze → Silver

Étapes :
  [1/4] etl/extract/fbref_scraper_all.py      — FBref Big 5
  [2/4] etl/extract/datafc_scraper_all.py     — Sofascore 10 ligues
  [3/4] etl/extract/datafc_players_info.py    — Profils joueurs Sofascore
  [4/4] etl/transform/silver_transformer.py   — ETL Bronze → Silver

Usage :
  python scraping_agent.py
  python scraping_agent.py --skip-extract       # transformer seulement
  python scraping_agent.py --only silver        # = --skip-extract
  python scraping_agent.py --only fbref         # étape 1 seulement
  python scraping_agent.py --only sofascore     # étapes 2+3 seulement
"""

import argparse
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# ── Chemins ────────────────────────────────────────────────────────────────────
ROOT     = Path(__file__).resolve().parent
EXTRACT  = ROOT / "etl" / "extract"
TRANSFORM = ROOT / "etl" / "transform"
LOGS_DIR = ROOT / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

STEPS = [
    ("fbref",     "1/4", EXTRACT   / "fbref_scraper_all.py"),
    ("sofascore", "2/4", EXTRACT   / "datafc_scraper_all.py"),
    ("profiles",  "3/4", EXTRACT   / "datafc_players_info.py"),
    ("silver",    "4/4", TRANSFORM / "silver_transformer.py"),
]


# ── Exécution d'une étape ──────────────────────────────────────────────────────
def run_step(label: str, step_num: str, path: Path) -> bool:
    exists = path.exists()
    print(f"\n{'='*65}")
    print(f"  [{step_num}] {label}  ({path.name})")
    print(f"  {datetime.now():%Y-%m-%d %H:%M:%S}")
    if not exists:
        print(f"  [SKIP] Fichier introuvable : {path}")
        print(f"{'='*65}\n")
        return True  # Skip silencieux (fichier optionnel)
    print(f"{'='*65}\n")

    start  = time.monotonic()
    result = subprocess.run(
        [sys.executable, str(path)],
        cwd=str(ROOT),
    )
    elapsed    = time.monotonic() - start
    mins, secs = divmod(int(elapsed), 60)

    if result.returncode == 0:
        print(f"\n  [OK] {label} termine en {mins}m{secs:02d}s")
        return True
    else:
        print(f"\n  [FAIL] {label} — code retour {result.returncode} ({mins}m{secs:02d}s)")
        return False


# ── Point d'entrée ─────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="RadarPepites — Pipeline complet")
    group  = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--skip-extract", action="store_true",
        help="Passer les étapes d'extraction et lancer uniquement le transformer Silver",
    )
    group.add_argument(
        "--only",
        choices=["fbref", "sofascore", "profiles", "silver"],
        help="Lancer une seule étape nommée",
    )
    args = parser.parse_args()

    # Filtrage des étapes à exécuter
    if args.skip_extract or args.only == "silver":
        steps = [(l, n, p) for l, n, p in STEPS if l == "silver"]
    elif args.only:
        steps = [(l, n, p) for l, n, p in STEPS if l == args.only]
    else:
        steps = STEPS

    print(f"\n{'='*65}")
    print(f"  RadarPepites — Pipeline complet")
    print(f"  {datetime.now():%Y-%m-%d %H:%M:%S}")
    print(f"  Etapes : {[l for l, _, _ in steps]}")
    print(f"{'='*65}")

    global_start = time.monotonic()
    results: dict[str, bool] = {}

    for label, step_num, path in steps:
        ok = run_step(label, step_num, path)
        results[label] = ok
        if not ok:
            print(f"\n  Pipeline interrompu apres echec de : {label}")
            break

    # ── Bilan ──────────────────────────────────────────────────────────────────
    total_elapsed    = time.monotonic() - global_start
    mins, secs       = divmod(int(total_elapsed), 60)
    all_ok           = all(results.values())

    print(f"\n{'='*65}")
    print(f"  BILAN GLOBAL  ({mins}m{secs:02d}s)")
    print(f"{'='*65}")
    for label, ok in results.items():
        status = "[OK]  " if ok else "[FAIL]"
        print(f"  {status}  {label}")

    failed = [l for l, ok in results.items() if not ok]
    if failed:
        print(f"\n  {len(failed)} etape(s) en echec : {failed}")
        sys.exit(1)
    else:
        print(f"\n  Pipeline termine avec succes.")
        sys.exit(0)


if __name__ == "__main__":
    main()

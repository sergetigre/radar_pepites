"""
etl/extract/run_all.py
RadarPépites — Orchestrateur d'extraction

Lance dans l'ordre :
  1. fbref_scraper_all.py   (FBref / Big 5)
  2. datafc_scraper_all.py  (Sofascore / 10 ligues)

Usage :
  python etl/extract/run_all.py
  python etl/extract/run_all.py --only fbref
  python etl/extract/run_all.py --only datafc
"""

import argparse
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# ── Chemins ────────────────────────────────────────────────────────────────────
HERE      = Path(__file__).resolve().parent
LOGS_DIR  = HERE.parents[1] / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

SCRIPTS = [
    ("fbref",  HERE / "fbref_scraper_all.py"),
    ("datafc", HERE / "datafc_scraper_all.py"),
]


# ── Exécution d'un script ──────────────────────────────────────────────────────
def run_script(name: str, path: Path) -> bool:
    print(f"\n{'='*65}")
    print(f"  Lancement : {name}  ({path.name})")
    print(f"  {datetime.now():%Y-%m-%d %H:%M:%S}")
    print(f"{'='*65}\n")

    start = time.monotonic()
    result = subprocess.run(
        [sys.executable, str(path)],
        cwd=str(path.parents[2]),   # racine du projet
    )
    elapsed = time.monotonic() - start
    mins, secs = divmod(int(elapsed), 60)

    if result.returncode == 0:
        print(f"\n  [OK] {name} termine en {mins}m{secs:02d}s")
        return True
    else:
        print(f"\n  [FAIL] {name} termine avec code {result.returncode} "
              f"({mins}m{secs:02d}s)")
        return False


# ── Point d'entrée ─────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Orchestrateur RadarPépites")
    parser.add_argument(
        "--only",
        choices=["fbref", "datafc"],
        help="Lancer un seul script (fbref ou datafc)",
    )
    args = parser.parse_args()

    scripts_to_run = [
        (name, path)
        for name, path in SCRIPTS
        if args.only is None or name == args.only
    ]

    print(f"\n{'='*65}")
    print(f"  RadarPepites — Extraction complete")
    print(f"  {datetime.now():%Y-%m-%d %H:%M:%S}")
    print(f"  Scripts : {[n for n, _ in scripts_to_run]}")
    print(f"{'='*65}")

    global_start = time.monotonic()
    results = {}

    for name, path in scripts_to_run:
        ok = run_script(name, path)
        results[name] = ok

    # ── Bilan global ───────────────────────────────────────────────────────────
    total_elapsed = time.monotonic() - global_start
    mins, secs = divmod(int(total_elapsed), 60)

    print(f"\n{'='*65}")
    print(f"  BILAN GLOBAL  ({mins}m{secs:02d}s total)")
    print(f"{'='*65}")
    for name, ok in results.items():
        status = "[OK]  " if ok else "[FAIL]"
        print(f"  {status}  {name}")

    failed = [n for n, ok in results.items() if not ok]
    if failed:
        print(f"\n  {len(failed)} script(s) en echec : {failed}")
        sys.exit(1)
    else:
        print(f"\n  Tous les scripts ont termine avec succes.")
        sys.exit(0)


if __name__ == "__main__":
    main()

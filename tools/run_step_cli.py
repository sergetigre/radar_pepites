"""
tools/run_step_cli.py — Lance une ou plusieurs étapes du pipeline sans
passer par le dashboard Streamlit (utile pour un run long en arrière-plan).
Même config (tools/pipeline_shared.py), même traçabilité dans
public.pipeline_runs que les boutons du dashboard.

Usage :
  python tools/run_step_cli.py fbref sofascore images
  python tools/run_step_cli.py --all-collecte
"""

import argparse
import subprocess
import sys

from pipeline_shared import ROOT, STEPS, STEPS_BY_KEY, insert_run_start, update_run_finish


def run_one(step_conf: dict) -> bool:
    stage, key, label, cmd = step_conf["stage"], step_conf["key"], step_conf["label"], step_conf["cmd"]
    print(f"\n{'='*70}\n  {label}  ({key})\n{'='*70}\n", flush=True)

    run_id = insert_run_start(stage, key)
    lines: list[str] = []
    proc = subprocess.Popen(
        cmd, cwd=str(ROOT), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1
    )
    for raw_line in proc.stdout:  # type: ignore[union-attr]
        print(raw_line, end="", flush=True)
        lines.append(raw_line.rstrip())
    proc.wait()

    full_log = "\n".join(lines)
    if proc.returncode == 0:
        update_run_finish(run_id, "success", full_log, None)
        print(f"\n[OK] {label} terminé (run_id={run_id})")
        return True
    else:
        error_tail = "\n".join(lines[-20:])
        update_run_finish(run_id, "failed", full_log, error_tail)
        print(f"\n[FAIL] {label} a échoué, code {proc.returncode} (run_id={run_id})")
        return False


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("steps", nargs="*", help="Clés d'étapes à lancer dans l'ordre (ex: fbref sofascore images)")
    parser.add_argument("--all-collecte", action="store_true", help="fbref + sofascore + images")
    args = parser.parse_args()

    if args.all_collecte:
        keys = ["fbref", "sofascore", "images"]
    else:
        keys = args.steps

    unknown = [k for k in keys if k not in STEPS_BY_KEY]
    if unknown:
        print(f"Étapes inconnues : {unknown}. Disponibles : {list(STEPS_BY_KEY)}")
        return 1
    if not keys:
        print(f"Aucune étape fournie. Disponibles : {list(STEPS_BY_KEY)}")
        return 1

    all_ok = True
    for key in keys:
        all_ok = run_one(STEPS_BY_KEY[key]) and all_ok

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())

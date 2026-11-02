"""
tools/pipeline_dashboard.py — RadarPépites : tableau de bord local de
pilotage du pipeline ETL.

Outil local, séparé du site public (web-next) : les étapes de collecte
dépendent d'un vrai navigateur (undetected-chromedriver, contournement
Cloudflare Sofascore) et ne peuvent tourner que sur cette machine — jamais
sur Vercel. Affiche l'historique des alimentations (étape, date, statut,
durée) stocké dans public.pipeline_runs, et permet de relancer chaque
étape en un clic avec les logs en direct.

Usage : streamlit run tools/pipeline_dashboard.py
"""

import subprocess
import sys
from datetime import datetime
from pathlib import Path

import psycopg2
import psycopg2.extras
import streamlit as st
from dotenv import load_dotenv
import os

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / "config" / ".env")

STAGE_LABELS = {
    "collecte": "① Collecte",
    "consolidation": "② Consolidation",
    "modelisation": "③ Modélisation",
}

STEPS = [
    {
        "stage": "collecte",
        "key": "fbref",
        "label": "FBref (5 ligues)",
        "cmd": [sys.executable, "etl/extract/scraping_agent.py", "--only", "fbref"],
    },
    {
        "stage": "collecte",
        "key": "sofascore",
        "label": "Sofascore stats + profils (10 ligues)",
        "cmd": [sys.executable, "etl/extract/scraping_agent.py", "--only", "sofascore"],
    },
    {
        "stage": "collecte",
        "key": "images",
        "label": "Images (logos, photos joueurs)",
        "cmd": [sys.executable, "etl/extract/download_media_assets.py"],
    },
    {
        "stage": "consolidation",
        "key": "silver",
        "label": "Bronze → Silver",
        "cmd": [sys.executable, "etl/extract/scraping_agent.py", "--only", "silver"],
    },
    {
        "stage": "modelisation",
        "key": "public",
        "label": "Silver → Public (dim_* + fact_stats)",
        "cmd": [sys.executable, "etl/load/load_public.py"],
    },
    {
        "stage": "modelisation",
        "key": "score",
        "label": "Score Pépite (percentiles, pondération)",
        "cmd": [sys.executable, "etl/load/gold_builder.py"],
    },
    {
        "stage": "modelisation",
        "key": "gold_views",
        "label": "Vues Gold (déploiement DDL)",
        "cmd": [sys.executable, "etl/load/gold_loader.py"],
    },
]


# ── Base de données ──────────────────────────────────────────────────────────
def get_connection():
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL introuvable dans config/.env")
    return psycopg2.connect(database_url)


def insert_run_start(stage: str, step: str) -> int:
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            "INSERT INTO public.pipeline_runs (stage, step, status) VALUES (%s, %s, 'running') RETURNING run_id",
            (stage, step),
        )
        run_id = cur.fetchone()[0]
        conn.commit()
        return run_id


def update_run_finish(run_id: int, status: str, log_tail: str, error: str | None) -> None:
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            UPDATE public.pipeline_runs
            SET status = %s, finished_at = NOW(), log_tail = %s, error = %s
            WHERE run_id = %s
            """,
            (status, log_tail[-4000:] if log_tail else None, error[-2000:] if error else None, run_id),
        )
        conn.commit()


def fetch_history(limit: int = 40):
    with get_connection() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            """
            SELECT run_id, stage, step, status, started_at, finished_at, error
            FROM public.pipeline_runs
            ORDER BY started_at DESC
            LIMIT %s
            """,
            (limit,),
        )
        return cur.fetchall()


def fetch_last_success_by_step():
    with get_connection() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            """
            SELECT DISTINCT ON (step) step, started_at, finished_at
            FROM public.pipeline_runs
            WHERE status = 'success'
            ORDER BY step, started_at DESC
            """
        )
        return {row["step"]: row for row in cur.fetchall()}


# ── Exécution ────────────────────────────────────────────────────────────────
def run_step(step_conf: dict) -> None:
    stage, key, label, cmd = step_conf["stage"], step_conf["key"], step_conf["label"], step_conf["cmd"]
    run_id = insert_run_start(stage, key)

    st.markdown(f"**Exécution : {label}**")
    log_box = st.empty()
    lines: list[str] = []

    proc = subprocess.Popen(
        cmd,
        cwd=str(ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    with st.spinner(f"{label} en cours..."):
        for raw_line in proc.stdout:  # type: ignore[union-attr]
            lines.append(raw_line.rstrip())
            log_box.code("\n".join(lines[-40:]), language="text")
        proc.wait()

    full_log = "\n".join(lines)
    if proc.returncode == 0:
        update_run_finish(run_id, "success", full_log, None)
        st.success(f"{label} terminé avec succès.")
    else:
        error_tail = "\n".join(lines[-20:])
        update_run_finish(run_id, "failed", full_log, error_tail)
        st.error(f"{label} a échoué (code {proc.returncode}). Voir les logs ci-dessus.")


# ── UI ───────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="RadarPépites — Pipeline", page_icon="🛠️", layout="wide")
st.title("🛠️ RadarPépites — Pilotage du pipeline")
st.caption(
    "Outil local uniquement — les étapes de collecte nécessitent un vrai navigateur "
    "(Chrome) et ne peuvent pas tourner depuis le site déployé."
)

last_success = fetch_last_success_by_step()

for stage_key, stage_label in STAGE_LABELS.items():
    st.subheader(stage_label)
    stage_steps = [s for s in STEPS if s["stage"] == stage_key]
    cols = st.columns(len(stage_steps))
    for col, step_conf in zip(cols, stage_steps):
        with col:
            last = last_success.get(step_conf["key"])
            if last and last["finished_at"]:
                st.caption(f"Dernier succès : {last['finished_at']:%d/%m/%Y %H:%M}")
            else:
                st.caption("Jamais exécuté avec succès")
            if st.button(f"▶ {step_conf['label']}", key=f"btn_{step_conf['key']}", width="stretch"):
                run_step(step_conf)
                st.rerun()

st.divider()
st.subheader("Historique des alimentations")

history = fetch_history()
if not history:
    st.info("Aucune exécution enregistrée pour l'instant.")
else:
    status_icon = {"running": "🟡", "success": "🟢", "failed": "🔴"}
    rows = []
    for r in history:
        duration = ""
        if r["finished_at"] and r["started_at"]:
            secs = int((r["finished_at"] - r["started_at"]).total_seconds())
            m, s = divmod(secs, 60)
            duration = f"{m}m{s:02d}s"
        rows.append(
            {
                "": status_icon.get(r["status"], ""),
                "Étape": STAGE_LABELS.get(r["stage"], r["stage"]),
                "Sous-étape": r["step"],
                "Démarré": r["started_at"].strftime("%d/%m/%Y %H:%M:%S") if r["started_at"] else "",
                "Durée": duration,
                "Statut": r["status"],
            }
        )
    st.dataframe(rows, width="stretch", hide_index=True)

    failed_runs = [r for r in history if r["status"] == "failed" and r["error"]]
    if failed_runs:
        with st.expander(f"Voir les erreurs ({len(failed_runs)})"):
            for r in failed_runs:
                st.markdown(f"**{r['step']}** — {r['started_at']:%d/%m/%Y %H:%M}")
                st.code(r["error"], language="text")

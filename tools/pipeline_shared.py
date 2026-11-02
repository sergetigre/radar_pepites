"""
tools/pipeline_shared.py — config des étapes + accès public.pipeline_runs,
partagés entre tools/pipeline_dashboard.py (UI Streamlit) et
tools/run_step_cli.py (exécution en ligne de commande, sans Streamlit).
"""

import os
import sys
from pathlib import Path

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

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

STEPS_BY_KEY = {s["key"]: s for s in STEPS}


def get_connection():
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL introuvable dans config/.env")
    # connect_timeout borne l'établissement de la connexion ; statement_timeout
    # borne l'exécution d'une requête une fois connecté — sans ça, un aléa
    # réseau peut bloquer indéfiniment un run_step_cli.py en arrière-plan
    # (déjà documenté côté silver_transformer.get_engine() : jusqu'à 47 min
    # observées sans connect_timeout).
    return psycopg2.connect(database_url, connect_timeout=10, options="-c statement_timeout=15000")


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

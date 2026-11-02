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

Les mêmes étapes sont lançables sans interface via
tools/run_step_cli.py (utile pour un run long en arrière-plan).
"""

import subprocess

import streamlit as st

from pipeline_shared import (
    ROOT,
    STAGE_LABELS,
    STEPS,
    fetch_history,
    fetch_last_success_by_step,
    insert_run_start,
    update_run_finish,
)


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

import streamlit as st
from utils.db import get_progression_gk
from utils.sidebar import render_sidebar
from utils.search import gk_searchbox
from utils.charts import line_progression, bar_progression
from utils.styles import inject_css, icon, render_html

st.set_page_config(
    page_title="Progression GK · RadarPépites",
    page_icon="📈", layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(inject_css(), unsafe_allow_html=True)
render_sidebar(page_active="gk_prog")

render_html(f"""
    <h1 style="font-size:1.8rem; font-weight:800; margin-bottom:20px;">
        {icon('trending_up', 28)} Progression Gardien
    </h1>
""")

joueur_id, _saison_sel, label = gk_searchbox(
    key="progression_gk_search",
    placeholder="Ex : Donnarumma junior...",
)

if not joueur_id:
    st.info("Tapez le nom d'un gardien pour afficher sa progression (2 lettres min.).")
    st.stop()

nom_gk = label.split(" — ")[0] if label else "Gardien"

df_prog = get_progression_gk(joueur_id)
if df_prog.empty:
    st.warning("Aucune donnée de progression disponible.")
    st.stop()

saisons_dispo = df_prog["saison_courte"].tolist()
saisons_sel = st.multiselect(
    "Saisons à afficher", options=saisons_dispo, default=saisons_dispo,
)
df_filtre = df_prog[df_prog["saison_courte"].isin(saisons_sel)]

if df_filtre.empty:
    st.info("Sélectionnez au moins une saison.")
    st.stop()

if not df_filtre["has_fbref_data"].any():
    st.caption(
        "ℹ️ % Arrêts et Clean sheets % non disponibles "
        "pour cette ligue (données fbref absentes)."
    )

view = st.radio("Type de visualisation", ["Courbe", "Barres groupées"], horizontal=True)

METRIQUES_GK = [
    ("saves_p90",         "Arrêts/90",   "#2DAD7E"),
    ("goals_prevented",   "Buts évités", "#5DCBA0"),
]
labels_dispo = [m[1] for m in METRIQUES_GK]
metrics_sel_labels = st.multiselect(
    "Métriques", options=labels_dispo, default=labels_dispo,
)
metrics_sel = [m for m in METRIQUES_GK if m[1] in metrics_sel_labels]

if view == "Courbe":
    fig = line_progression(df_filtre, nom_gk, metriques=metrics_sel)
else:
    fig = bar_progression(df_filtre, nom_gk, metriques=[m[0] for m in metrics_sel])
st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
st.markdown(f"#### {icon('table_chart')} Détail par saison", unsafe_allow_html=True)
COLS = {
    "saison_courte": "Saison", "minutes": "Minutes",
    "matchs_joues": "Matchs", "saves_p90": "Arrêts/90",
    "goals_prevented": "Buts évités",
    "save_pct": "% Arrêts", "clean_sheets_pct": "Clean sheets %",
    "score_pepite_corrige": "Score ★",
}
st.dataframe(
    df_filtre[list(COLS.keys())].rename(columns=COLS),
    use_container_width=True, hide_index=True,
)

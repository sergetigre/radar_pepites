import streamlit as st
from utils.db import search_gk, get_progression_gk
from utils.sidebar import render_sidebar
from utils.charts import line_progression, bar_progression
from utils.styles import inject_css, icon, render_html

st.set_page_config(
    page_title="Progression GK · RadarPépites",
    page_icon="📈", layout="wide",
)
st.markdown(inject_css(), unsafe_allow_html=True)
render_sidebar(page_active="gk_prog")

render_html(f"""
    <h1 style="font-size:1.8rem; font-weight:800; margin-bottom:20px;">
        {icon('trending_up', 28)} Progression Gardien
    </h1>
""")

nom = st.text_input(
    "Rechercher un gardien",
    placeholder="Ex : Donnarumma junior...",
)
if not nom:
    st.info("Tapez le nom d'un gardien pour afficher sa progression.")
    st.stop()

df_search = search_gk(nom)
if df_search.empty:
    st.warning(f"Aucun gardien trouvé pour '{nom}'.")
    st.stop()

joueurs_uniques = df_search.drop_duplicates(subset=["joueur_id"])
if len(joueurs_uniques) > 1:
    options = (joueurs_uniques["joueur"] + " (" + joueurs_uniques["equipe"] + ")").tolist()
    sel_joueur = st.selectbox("Plusieurs gardiens correspondent — précisez", options)
    idx = options.index(sel_joueur)
    joueur_id = str(joueurs_uniques.iloc[idx]["joueur_id"])
else:
    joueur_id = str(joueurs_uniques.iloc[0]["joueur_id"])

df_prog = get_progression_gk(joueur_id)
if df_prog.empty:
    st.warning("Aucune donnée de progression disponible.")
    st.stop()

nom_gk = df_search.iloc[0]["joueur"]

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

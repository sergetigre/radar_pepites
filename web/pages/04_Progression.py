import streamlit as st
from utils.db import get_progression_joueur
from utils.sidebar import render_sidebar
from utils.search import player_searchbox
from utils.charts import line_progression, bar_progression
from utils.styles import inject_css, icon, render_html

st.set_page_config(
    page_title="Progression · RadarPépites",
    page_icon="📈", layout="wide",
)
st.markdown(inject_css(), unsafe_allow_html=True)
render_sidebar(page_active="progress")

render_html(f"""
    <h1 style="font-size:1.8rem; font-weight:800; margin-bottom:20px;">
        {icon('trending_up', 28)} Progression
    </h1>
    <p style="color:#8A8A8A; font-size:0.9rem; margin-bottom:24px;">
        Visualisez l'évolution des statistiques d'un joueur saison par saison.
    </p>
""")

joueur_id, _saison_sel, label = player_searchbox(
    key="progression_search",
    placeholder="Ex : Saka, Wirtz, Yamal...",
)

if not joueur_id:
    st.info("Tapez le nom d'un joueur pour afficher sa progression (2 lettres min.).")
    st.stop()

nom_joueur = label.split(" — ")[0] if label else "Joueur"

df_prog = get_progression_joueur(joueur_id)
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

view = st.radio("Type de visualisation", ["Courbe", "Barres groupées"], horizontal=True)

METRIQUES_DEFAUT = [
    ("buts_p90",   "Buts/90",    "#2DAD7E"),
    ("xg_p90",     "xG/90",      "#5DCBA0"),
    ("passes_dec_p90", "Assists/90", "#E0B452"),
    ("key_passes_p90", "KP/90",   "#4ECDC4"),
    ("dribbles_p90",   "Drib/90", "#FF6B35"),
    ("tackles_p90",    "Tac/90",  "#E05252"),
]
labels_dispo = [m[1] for m in METRIQUES_DEFAUT]
metrics_sel_labels = st.multiselect(
    "Métriques", options=labels_dispo,
    default=["Buts/90", "xG/90", "Assists/90"],
)
metrics_sel = [m for m in METRIQUES_DEFAUT if m[1] in metrics_sel_labels]

if view == "Courbe":
    fig = line_progression(df_filtre, nom_joueur, metriques=metrics_sel)
else:
    fig = bar_progression(df_filtre, nom_joueur, metriques=[m[0] for m in metrics_sel])

st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
st.markdown(f"#### {icon('table_chart')} Détail par saison", unsafe_allow_html=True)
COLS = {
    "saison_courte": "Saison", "minutes": "Minutes",
    "matchs_joues": "Matchs",
    "buts_p90": "Buts/90", "xg_p90": "xG/90",
    "passes_dec_p90": "Assists/90", "xag_p90": "xAG/90",
    "key_passes_p90": "KP/90", "dribbles_p90": "Drib/90",
    "tackles_p90": "Tac/90", "interceptions_p90": "Int/90",
    "score_pepite_corrige": "Score ★",
}
st.dataframe(
    df_filtre[list(COLS.keys())].rename(columns=COLS),
    use_container_width=True, hide_index=True,
)

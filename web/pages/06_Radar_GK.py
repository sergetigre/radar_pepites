import streamlit as st
from utils.db import get_gk_fiche
from utils.sidebar import render_sidebar
from utils.search import gk_searchbox
from utils.charts import radar_single
from utils.components import (
    render_player_header, render_terrain_svg,
    render_pct_bars, render_strengths_weaknesses,
)
from utils.styles import inject_css, icon, render_html

st.set_page_config(
    page_title="Radar GK · RadarPépites",
    page_icon="🧤", layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(inject_css(), unsafe_allow_html=True)

render_sidebar(page_active="gk_radar")

render_html(f"""
    <h1 style="font-size:1.8rem; font-weight:800; margin-bottom:20px;">
        {icon('radar', 28)} Radar Gardien
    </h1>
""")

prefill_nom = st.session_state.get("prefill_gk", "")

joueur_id, saison, label = gk_searchbox(
    key="radar_gk_search",
    placeholder="Ex : Donnarumma junior...",
    default_searchterm=prefill_nom,
)

if not joueur_id:
    st.info("Tapez le nom d'un gardien pour afficher son profil (2 lettres min.).")
    st.stop()

for k in ["prefill_gk", "prefill_gk_id"]:
    st.session_state.pop(k, None)

df_fiche = get_gk_fiche(joueur_id, saison)
if df_fiche.empty:
    st.warning("Données non disponibles pour cette sélection.")
    st.stop()

row = df_fiche.iloc[0]

render_player_header(row, is_gk=True)

col_terrain, col_radar = st.columns([1, 2], gap="large")

with col_terrain:
    render_html(f"""
        <div class="pitch-container">
            {render_terrain_svg("GK", width=150)}
        </div>
    """)

with col_radar:
    color = row.get("couleur_hex") or "#2DAD7E"
    nom_gk = row.get("nom_court") or row.get("nom_complet", "Gardien")
    fig = radar_single(row, "GK", name=nom_gk, color=color)
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
st.markdown(f"#### {icon('bar_chart')} Percentiles", unsafe_allow_html=True)

metrics = {
    "Arrêts/90":          row.get("pct_saves_p90"),
    "Buts évités":        row.get("pct_goals_prevented"),
    "% Arrêts":           row.get("pct_save_pct"),
    "Clean sheets %":     row.get("pct_clean_sheets_pct"),
    "Passes longues %":   row.get("pct_long_balls_pct"),
}
if not row.get("has_fbref_data"):
    st.caption(
        "ℹ️ % Arrêts et Clean sheets % (source fbref) "
        "non disponibles pour cette ligue."
    )

render_pct_bars(metrics)

st.markdown("---")
render_strengths_weaknesses(row)

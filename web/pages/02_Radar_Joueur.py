import streamlit as st
import pandas as pd
from utils.db import get_joueur_fiche, get_profils_similaires, get_saisons
from utils.sidebar import render_sidebar
from utils.search import player_searchbox
from utils.charts import radar_single
from utils.components import (
    render_player_header, render_terrain_svg,
    render_pct_bars, render_strengths_weaknesses,
    render_similar_players,
)
from utils.styles import inject_css, icon, render_html

st.set_page_config(
    page_title="Radar Joueur · RadarPépites",
    page_icon="📊", layout="wide",
)
st.markdown(inject_css(), unsafe_allow_html=True)

render_sidebar(page_active="radar")

render_html(f"""
    <h1 style="font-size:1.8rem; font-weight:800; margin-bottom:20px;">
        {icon('radar', 28)} Radar Joueur
    </h1>
""")

saisons = get_saisons()

# Pré-remplissage : priorité aux paramètres d'URL (carte du Tableau de
# bord, clic direct), sinon barre de recherche live (navigation libre,
# ou arrivée depuis Explorer via session_state).
qp = st.query_params
qp_joueur_id = qp.get("joueur_id")
qp_saison    = qp.get("saison")

if qp_joueur_id:
    df_fiche = get_joueur_fiche(qp_joueur_id, qp_saison or saisons[0])
    st.query_params.clear()

    if df_fiche.empty:
        st.warning("Données non disponibles pour cette sélection.")
        st.stop()

    row       = df_fiche.iloc[0]
    poste     = row.get("poste_id") or row.get("poste_principal", "CM") or "CM"
    joueur_id = qp_joueur_id
    saison    = qp_saison or saisons[0]

else:
    prefill_nom = st.session_state.get("prefill_joueur", "")

    joueur_id, saison, label = player_searchbox(
        key="radar_joueur_search",
        placeholder="Ex : Saka, Wirtz, Yamal...",
        default_searchterm=prefill_nom,
    )

    if not joueur_id:
        st.info("Tapez le nom d'un joueur pour afficher son profil (2 lettres min.).")
        st.stop()

    for k in ["prefill_joueur", "prefill_joueur_id", "prefill_saison"]:
        st.session_state.pop(k, None)

    df_fiche = get_joueur_fiche(joueur_id, saison)
    if df_fiche.empty:
        st.warning("Données non disponibles pour cette sélection.")
        st.stop()

    row   = df_fiche.iloc[0]
    poste = row.get("poste_id") or row.get("poste_principal", "CM") or "CM"

render_player_header(row)

col_terrain, col_radar, col_sim = st.columns([1, 2, 1], gap="large")

with col_terrain:
    render_html(f"""
        <div style="font-size:0.65rem; font-weight:700;
                    text-transform:uppercase; letter-spacing:2px;
                    color:#8A8A8A; margin-bottom:10px;">
            {icon('sports_soccer', 14)} Position
        </div>
        <div class="pitch-container">
            {render_terrain_svg(poste, width=150)}
        </div>
        <div style="text-align:center; font-size:0.8rem;
                    color:#2DAD7E; margin-top:8px;
                    font-weight:600;">
            {poste}
        </div>
    """)

with col_radar:
    color = row.get("couleur_hex") or "#2DAD7E"
    nom_court = row.get("nom_court") or row.get("nom_complet", "Joueur")
    fig = radar_single(row, poste, name=nom_court, color=color)
    st.plotly_chart(fig, use_container_width=True)

with col_sim:
    df_sim = get_profils_similaires(joueur_id, saison, poste)
    render_similar_players(df_sim)

st.markdown("---")
st.markdown(f"#### {icon('bar_chart')} Percentiles par catégorie", unsafe_allow_html=True)

CATS = {
    "⚽ Offensif": {
        "Buts/90":    row.get("pct_goals_p90"),
        "xG/90":      row.get("pct_xg_p90"),
        "Assists/90": row.get("pct_assists_p90"),
        "xAG/90":     row.get("pct_xag_p90"),
        "Tirs/90":    row.get("pct_shots_p90"),
    },
    "🎯 Passes": {
        "Key Passes/90":  row.get("pct_key_passes_p90"),
        "Précision pass": row.get("pct_passes_pct"),
        "Dribbles/90":    row.get("pct_dribbles_p90"),
    },
    "🛡️ Défense": {
        "Tacles/90":       row.get("pct_tackles_p90"),
        "Interceptions/90":row.get("pct_interceptions_p90"),
        "Dégagements/90":  row.get("pct_degagements_p90"),
        "Duels aériens":   row.get("pct_duels_aeriens_pct"),
    },
}

c1, c2, c3 = st.columns(3, gap="large")
for col_ui, (cat_label, metrics) in zip([c1,c2,c3], CATS.items()):
    with col_ui:
        render_pct_bars(metrics, title=cat_label)

st.markdown("---")
render_strengths_weaknesses(row)

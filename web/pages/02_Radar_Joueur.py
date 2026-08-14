import streamlit as st

from utils.charts import COLORS, radar_chart
from utils.db import get_joueur_radar, get_saisons, search_joueurs
from utils.styles import inject_css

st.set_page_config(page_title="Radar — RadarPépites", layout="wide")
st.markdown(inject_css(), unsafe_allow_html=True)
st.title("📊 Profil Radar d'un Joueur")

saisons = get_saisons()
saison  = st.sidebar.selectbox("Saison", saisons)

nom = st.text_input("Rechercher un joueur", placeholder="Ex: Saka, Wirtz, Yamal...")

if not nom:
    st.info("Tapez le nom d'un joueur pour afficher son radar.")
    st.stop()

df_search = search_joueurs(nom, saison)

if df_search.empty:
    st.warning(f"Aucun joueur trouvé pour '{nom}' en {saison}.")
    st.stop()

joueur_sel = st.selectbox("Sélectionner le joueur", df_search["joueur"].tolist())
row_sel    = df_search[df_search["joueur"] == joueur_sel].iloc[0]

if row_sel["poste_id"] == "GK":
    st.warning(
        "Le radar percentile n'est pas disponible pour les gardiens "
        "(les métriques gardien — arrêts, buts évités... — ne sont pas "
        "encore intégrées à cette vue). Consulte la page **Gardiens** "
        "pour le classement complet des portiers U23."
    )
    st.stop()

df_radar = get_joueur_radar(str(row_sel["joueur_id"]), saison)

if df_radar.empty:
    st.warning("Données radar non disponibles pour ce joueur sur cette saison.")
    st.stop()

row_radar = df_radar.iloc[0]
poste     = row_radar.get("poste_principal") or row_sel["poste_id"]

fig = radar_chart(row=row_radar, poste=poste, color=COLORS["primary"],
                   title=f"{joueur_sel} — {saison}", show_moyenne=True)

if fig is None:
    st.warning(f"Radar non disponible pour le poste {poste}.")
    st.stop()

col_info, col_radar = st.columns([1, 2])

with col_info:
    st.markdown(f"""
        <div class="player-card">
            <div class="ligue-header">{row_radar.get('ligue', '')}</div>
            <h2>{joueur_sel}</h2>
            <p>🏟️ {row_radar.get('team_name', '')}</p>
            <p>📍 Poste : <strong>{poste}</strong></p>
            <p>⏱️ Minutes (saison) : {int(row_sel['minutes'] or 0):,}</p>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("### Métriques clés /90 min")
    metriques = {
        "⚽ xG/90":           row_radar.get("xg_p90"),
        "🎯 Buts/90":        row_radar.get("goals_p90"),
        "🅰️ Assists/90":     row_radar.get("assists_p90"),
        "🔑 Passes clés/90": row_radar.get("key_passes_p90"),
        "🏃 Dribbles/90":    row_radar.get("dribbles_p90"),
        "⚔️ Tacles/90":      row_radar.get("tackles_p90"),
    }
    for label, val in metriques.items():
        if val is not None:
            st.metric(label, f"{float(val):.3f}")

with col_radar:
    st.plotly_chart(fig, use_container_width=True)
    st.caption(
        "Les percentiles sont calculés par rapport aux joueurs "
        "du même poste avec ≥ 450 minutes jouées."
    )

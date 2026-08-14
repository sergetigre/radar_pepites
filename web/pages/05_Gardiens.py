import streamlit as st

from utils.db import get_gk_classement, get_saisons
from utils.styles import inject_css

st.set_page_config(page_title="Gardiens — RadarPépites", layout="wide")
st.markdown(inject_css(), unsafe_allow_html=True)
st.title("🥅 Gardiens U23")

saisons = get_saisons()
saison  = st.sidebar.selectbox("Saison", saisons)

df_gk = get_gk_classement(saison)

if df_gk.empty:
    st.warning("Aucune donnée gardien disponible pour cette saison.")
    st.stop()

c1, c2, c3 = st.columns(3)
c1.metric("Gardiens U23", len(df_gk))
c2.metric("Arrêts/90 max", f"{df_gk['saves_p90'].max():.2f}"
          if df_gk["saves_p90"].notna().any() else "—")
c3.metric("Buts évités max", f"{df_gk['goals_prevented_ss'].max():.2f}"
          if df_gk["goals_prevented_ss"].notna().any() else "—")

st.markdown("---")
st.subheader(f"Classement Gardiens U23 — {saison}")

df_display = df_gk[[
    "player_name", "team_name", "ligue", "age_actuel",
    "minutes_ss", "appearances_ss", "saves_ss", "saves_p90",
    "goals_prevented_ss", "rating_ss", "save_pct_fb", "clean_sheets_pct_fb",
]].rename(columns={
    "player_name":         "Joueur",
    "team_name":           "Équipe",
    "ligue":               "Ligue",
    "age_actuel":          "Âge",
    "minutes_ss":          "Minutes",
    "appearances_ss":      "Matchs",
    "saves_ss":            "Arrêts",
    "saves_p90":           "Arrêts/90",
    "goals_prevented_ss":  "Buts évités",
    "rating_ss":           "Rating",
    "save_pct_fb":         "% Arrêts (fbref)",
    "clean_sheets_pct_fb": "% Clean sheets (fbref)",
})

st.dataframe(df_display, use_container_width=True, hide_index=True)
st.caption(
    "% Arrêts et % Clean sheets ne sont disponibles que pour les gardiens "
    "des 5 grands championnats (source fbref, ~47% de couverture). "
    "L'âge est calculé par rapport à aujourd'hui, pas à la saison affichée — "
    "à interpréter avec prudence pour les saisons passées."
)

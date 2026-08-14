import streamlit as st
import pandas as pd
from utils.db import get_classement
from utils.sidebar import render_sidebar
from utils.charts import scatter_xg_buts
from utils.styles import inject_css, icon, render_html

st.set_page_config(
    page_title="Explorer · RadarPépites",
    page_icon="🔍", layout="wide",
)
st.markdown(inject_css(), unsafe_allow_html=True)

filtres = render_sidebar(page_active="explorer")
saison, ligues, postes = filtres["saison"], filtres["ligues"], filtres["postes"]
min_min, age_max       = filtres["min_min"], filtres["age_max"]

render_html(f"""
    <h1 style="font-size:1.8rem; font-weight:800; margin-bottom:20px;">
        {icon('search', 28)} Explorer
    </h1>
""")

if not ligues or not postes:
    st.warning("Sélectionnez au moins une ligue et un poste dans les filtres.")
    st.stop()

df = get_classement(saison, ligues, postes, age_max, min_min)

if df.empty:
    st.info("Aucun joueur ne correspond aux filtres actuels.")
    st.stop()

recherche = st.text_input(
    "🔍 Recherche rapide",
    placeholder="Filtrer par nom de joueur...",
)
if recherche:
    df = df[df["joueur"].str.contains(recherche, case=False, na=False)]

tab_classement, tab_graphiques = st.tabs(["📋 Classement", "📊 Graphiques"])

COLONNES_AFFICHEES = {
    "rang_global":  "Rang",
    "joueur":       "Joueur",
    "equipe":       "Équipe",
    "ligue":        "Ligue",
    "poste_id":     "Poste",
    "age":          "Âge",
    "score_corrige":"Score ★",
    "xg_p90":       "xG/90",
    "buts_p90":     "Buts/90",
    "minutes":      "Minutes",
}

with tab_classement:
    df_aff = df[list(COLONNES_AFFICHEES.keys())].rename(columns=COLONNES_AFFICHEES)

    event = st.dataframe(
        df_aff,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        key="explorer_table",
    )

    csv = df_aff.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Exporter en CSV", csv,
        file_name=f"radarpepites_classement_{saison}.csv",
        mime="text/csv",
    )

    if event.selection and event.selection.get("rows"):
        idx_sel = event.selection["rows"][0]
        row_sel = df.iloc[idx_sel]
        st.session_state["prefill_joueur"]    = row_sel["joueur"]
        st.session_state["prefill_joueur_id"] = row_sel["joueur_id"]
        st.session_state["prefill_saison"]    = saison
        st.switch_page("pages/02_Radar_Joueur.py")

with tab_graphiques:
    df_g = df.dropna(subset=["xg_p90","buts_p90"])
    if not df_g.empty:
        st.plotly_chart(scatter_xg_buts(df_g), use_container_width=True)
    else:
        st.caption("Données insuffisantes pour le graphique.")

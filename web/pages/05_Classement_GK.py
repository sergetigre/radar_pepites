import streamlit as st
from utils.db import get_classement_gk
from utils.sidebar import render_filters
from utils.styles import icon, render_html

filtres = render_filters()
saison, ligues, min_min = filtres["saison"], filtres["ligues"], filtres["min_min"]

render_html(f"""
    <h1 style="font-size:1.8rem; font-weight:800; margin-bottom:20px;">
        {icon('sports_handball', 28)} Classement Gardiens
    </h1>
""")

if not ligues:
    st.warning("Sélectionnez au moins une ligue dans les filtres.")
    st.stop()

df = get_classement_gk(saison, ligues, min_min)

if df.empty:
    st.info("Aucun gardien ne correspond aux filtres actuels.")
    st.stop()

recherche = st.text_input(
    "🔍 Recherche rapide",
    placeholder="Filtrer par nom...",
)
if recherche and "player_name" in df.columns:
    df = df[df["player_name"].str.contains(recherche, case=False, na=False)]

# Rang dynamique : recalculé selon le classement affiché (après filtres
# sidebar + recherche), sur le même critère de tri que la requête (arrêts/90).
df = df.sort_values("saves_p90", ascending=False, na_position="last").reset_index(drop=True)
df["rang_dynamique"] = df.index + 1

COLONNES_GK = {
    "rang_dynamique": "Rang",
    "player_name": "Gardien", "team_name": "Équipe",
    "ligue_id": "Ligue", "age_actuel": "Âge",
    "saves_p90": "Arrêts/90", "goals_prevented_ss": "Buts évités",
    "save_pct_fb": "% Arrêts", "clean_sheets_fb": "Clean sheets",
    "minutes_ss": "Minutes",
}
cols_dispo = [c for c in COLONNES_GK if c in df.columns]

event = st.dataframe(
    df[cols_dispo].rename(columns={c: COLONNES_GK[c] for c in cols_dispo}),
    use_container_width=True, hide_index=True,
    on_select="rerun", selection_mode="single-row",
    key="gk_table",
)

st.caption(
    "ℹ️ L'âge est calculé par rapport à aujourd'hui, pas à "
    "la saison affichée — à interpréter avec prudence pour les saisons passées."
)

if event.selection and event.selection.get("rows"):
    idx_sel = event.selection["rows"][0]
    row_sel = df.iloc[idx_sel]
    st.session_state["prefill_gk"]     = row_sel.get("player_name")
    st.session_state["prefill_gk_id"]  = row_sel.get("player_id_ss")
    st.session_state["prefill_saison"] = saison
    st.switch_page("pages/06_Radar_GK.py")

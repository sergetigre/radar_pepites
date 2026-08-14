import pandas as pd
import streamlit as st

from utils.charts import radar_comparaison
from utils.db import get_joueur_radar, get_saisons, search_joueurs
from utils.styles import inject_css

st.set_page_config(page_title="Comparer — RadarPépites", layout="wide")
st.markdown(inject_css(), unsafe_allow_html=True)
st.title("⚖️ Comparer 2 Joueurs")

saisons = get_saisons()
saison  = st.sidebar.selectbox("Saison", saisons)

col_a, col_b = st.columns(2)

with col_a:
    st.subheader("Joueur A")
    nom_a    = st.text_input("Rechercher", key="joueur_a", placeholder="Ex: Saka")
    joueur_a = None
    if nom_a:
        df_a = search_joueurs(nom_a, saison)
        if not df_a.empty:
            sel_a    = st.selectbox("Sélectionner", df_a["joueur"], key="sel_a")
            joueur_a = df_a[df_a["joueur"] == sel_a].iloc[0]

with col_b:
    st.subheader("Joueur B")
    nom_b    = st.text_input("Rechercher", key="joueur_b", placeholder="Ex: Wirtz")
    joueur_b = None
    if nom_b:
        df_b = search_joueurs(nom_b, saison)
        if not df_b.empty:
            sel_b    = st.selectbox("Sélectionner", df_b["joueur"], key="sel_b")
            joueur_b = df_b[df_b["joueur"] == sel_b].iloc[0]

if joueur_a is None or joueur_b is None:
    st.info("Sélectionnez deux joueurs pour afficher la comparaison.")
    st.stop()

if joueur_a["poste_id"] == "GK" or joueur_b["poste_id"] == "GK":
    st.warning(
        "La comparaison radar n'est pas disponible pour les gardiens "
        "(métriques gardien non couvertes par cette vue). "
        "Consulte la page **Gardiens** pour leur classement."
    )
    st.stop()

df_ra = get_joueur_radar(str(joueur_a["joueur_id"]), saison)
df_rb = get_joueur_radar(str(joueur_b["joueur_id"]), saison)

if df_ra.empty or df_rb.empty:
    st.warning("Données insuffisantes pour l'un des joueurs sur cette saison.")
    st.stop()

ra = df_ra.iloc[0]
rb = df_rb.iloc[0]

poste = ra.get("poste_principal") or joueur_a["poste_id"]

fig = radar_comparaison(row_a=ra, row_b=rb, poste=poste,
                        name_a=joueur_a["joueur"], name_b=joueur_b["joueur"])

if fig is None:
    st.warning(f"Radar non disponible pour le poste {poste}.")
    st.stop()

st.plotly_chart(fig, use_container_width=True)

st.subheader("Comparaison détaillée")

metriques_comp = {
    "Score Pépite ★":   "score_corrige",
    "xG/90":            "xg_p90",
    "Buts/90":          "goals_p90",
    "Assists/90":       "assists_p90",
    "Passes clés/90":   "key_passes_p90",
    "Dribbles/90":      "dribbles_p90",
    "Tacles/90":        "tackles_p90",
    "Interceptions/90": "interceptions_p90",
    "Minutes":          "minutes",
}

rows_comp = []
for label, col in metriques_comp.items():
    val_a = ra.get(col) if col in ra else joueur_a.get(col)
    val_b = rb.get(col) if col in rb else joueur_b.get(col)
    rows_comp.append({
        "Métrique": label,
        joueur_a["joueur"]: round(float(val_a), 3) if val_a is not None else "—",
        joueur_b["joueur"]: round(float(val_b), 3) if val_b is not None else "—",
    })

st.dataframe(pd.DataFrame(rows_comp), use_container_width=True, hide_index=True)

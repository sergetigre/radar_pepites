import streamlit as st

from utils.charts import line_progression
from utils.db import get_progression, get_saisons, search_joueurs
from utils.styles import inject_css

st.set_page_config(page_title="Progression — RadarPépites", layout="wide")
st.markdown(inject_css(), unsafe_allow_html=True)
st.title("📈 Progression Saison par Saison")

saisons = get_saisons()
saison  = st.sidebar.selectbox("Saison de référence", saisons)

nom = st.text_input("Rechercher un joueur", placeholder="Ex: Yamal, Palmer...")

if not nom:
    st.info("Tapez le nom d'un joueur pour voir sa progression.")
    st.stop()

df_search = search_joueurs(nom, saison)
if df_search.empty:
    st.warning("Joueur non trouvé.")
    st.stop()

joueur_sel = st.selectbox("Sélectionner", df_search["joueur"])
row_sel    = df_search[df_search["joueur"] == joueur_sel].iloc[0]

df_prog = get_progression(str(row_sel["joueur_id"]))

if df_prog.empty:
    st.info(f"{joueur_sel} n'a pas encore de progression sur plusieurs saisons.")
    st.stop()

fig = line_progression(df_prog, joueur_sel)
st.plotly_chart(fig, use_container_width=True)

st.caption(
    "Les deltas représentent la différence entre la saison N "
    "et la saison N-1 pour le même club."
)

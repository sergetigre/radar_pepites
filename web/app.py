import streamlit as st
from utils.sidebar import render_nav
from utils.styles import inject_css

st.set_page_config(
    page_title="RadarPépites",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(inject_css(), unsafe_allow_html=True)

dashboard      = st.Page("pages/00_Tableau_de_bord.py", title="Tableau de bord", url_path="", default=True)
explorer       = st.Page("pages/01_Explorer.py",        title="Explorer")
radar_joueur   = st.Page("pages/02_Radar_Joueur.py",     title="Radar Joueur")
comparaison    = st.Page("pages/03_Comparaison.py",      title="Comparaison")
progression    = st.Page("pages/04_Progression.py",      title="Progression")
classement_gk  = st.Page("pages/05_Classement_GK.py",    title="Classement GK")
radar_gk       = st.Page("pages/06_Radar_GK.py",         title="Radar GK")
comparaison_gk = st.Page("pages/07_Comparaison_GK.py",   title="Comparaison GK")
progression_gk = st.Page("pages/08_Progression_GK.py",   title="Progression GK")

pg = st.navigation(
    [dashboard, explorer, radar_joueur, comparaison, progression,
     classement_gk, radar_gk, comparaison_gk, progression_gk],
    position="hidden",
)

render_nav()
pg.run()

import streamlit as st
import pandas as pd
from utils.db import get_gk_fiche
from utils.sidebar import render_filters
from utils.search import gk_searchbox
from utils.charts import radar_compare, RADAR_AXES
from utils.styles import icon, render_html

render_filters()

render_html(f"""
    <h1 style="font-size:1.8rem; font-weight:800; margin-bottom:20px;">
        {icon('compare_arrows', 28)} Comparaison Gardiens
    </h1>
""")


def select_gk_col(key_prefix):
    joueur_id, saison, label = gk_searchbox(
        key=f"{key_prefix}_searchbox",
        placeholder="Ex: Donnarumma",
    )
    if not joueur_id:
        return None, None
    return joueur_id, saison


col_a, col_sep, col_b = st.columns([5, 1, 5])
with col_a:
    st.markdown('<div style="color:#2DAD7E; font-weight:700;">GK A</div>', unsafe_allow_html=True)
    id_a, saison_a = select_gk_col("a")
with col_sep:
    st.markdown('<div style="text-align:center; padding-top:40px; '
               'color:#8A8A8A;">vs</div>', unsafe_allow_html=True)
with col_b:
    st.markdown('<div style="color:#E05252; font-weight:700;">GK B</div>', unsafe_allow_html=True)
    id_b, saison_b = select_gk_col("b")

if not id_a or not id_b:
    st.info("Sélectionnez les deux gardiens pour lancer la comparaison.")
    st.stop()

df_a = get_gk_fiche(id_a, saison_a)
df_b = get_gk_fiche(id_b, saison_b)

if df_a.empty or df_b.empty:
    st.warning("Données insuffisantes.")
    st.stop()

ra, rb = df_a.iloc[0], df_b.iloc[0]
nom_a = f"{ra.get('nom_court', 'GK A')} — {saison_a}"
nom_b = f"{rb.get('nom_court', 'GK B')} — {saison_b}"

st.markdown("---")
st.markdown(f"#### {icon('radar')} Comparaison radar", unsafe_allow_html=True)

fig = radar_compare(ra, rb, "GK", axes_override=RADAR_AXES["GK"], name_a=nom_a, name_b=nom_b)
st.plotly_chart(fig, use_container_width=True)

st.markdown(f"#### {icon('table_chart')} Statistiques détaillées", unsafe_allow_html=True)

STATS_GK_TABLEAU = {
    "Score Pépite ★":     "score_pepite_corrige",
    "Arrêts/90":          "saves_p90",
    "Buts évités":        "goals_prevented",
    "% Arrêts":           "save_pct",
    "Clean sheets %":     "clean_sheets_pct",
    "Passes longues %":   "long_balls_pct",
    "Minutes":            "minutes",
    "Matchs":             "matchs_joues",
}

rows = []
for label, col in STATS_GK_TABLEAU.items():
    va, vb = ra.get(col), rb.get(col)

    def fmt(v):
        try:
            return round(float(v), 2)
        except (TypeError, ValueError):
            return "—"

    rows.append({"Stat": label, nom_a: fmt(va), nom_b: fmt(vb)})

st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

import streamlit as st
import pandas as pd
from utils.db import get_joueur_fiche
from utils.sidebar import render_sidebar
from utils.search import player_searchbox
from utils.charts import radar_compare, RADAR_LABELS
from utils.components import stat_checkbox_selector
from utils.styles import inject_css, icon, render_html

st.set_page_config(
    page_title="Comparaison · RadarPépites",
    page_icon="⚖️", layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(inject_css(), unsafe_allow_html=True)

render_sidebar(page_active="compare")

render_html(f"""
    <h1 style="font-size:1.8rem; font-weight:800; margin-bottom:20px;">
        {icon('compare_arrows', 28)} Comparaison
    </h1>
    <p style="color:#8A8A8A; font-size:0.9rem; margin-bottom:24px;">
        Comparez deux joueurs ou le même joueur sur différentes saisons.
    </p>
""")


def select_player_col(key_prefix):
    """Sélection joueur + saison via autocomplete live."""
    joueur_id, saison, label = player_searchbox(
        key=f"{key_prefix}_searchbox",
        placeholder="Ex: Saka",
    )
    if not joueur_id:
        return None, None
    return joueur_id, saison


col_a, col_sep, col_b = st.columns([5, 1, 5])

with col_a:
    render_html(f"""
        <div style="color:#2DAD7E; font-weight:700;
                    font-size:1rem; margin-bottom:10px;">
            {icon('circle', 14)} Joueur A
        </div>
    """)
    id_a, saison_a = select_player_col("a")

with col_sep:
    render_html("""
        <div style="display:flex; justify-content:center;
                    align-items:center; height:100%;
                    font-size:1.5rem; color:#8A8A8A;
                    padding-top:40px;">vs</div>
    """)

with col_b:
    render_html(f"""
        <div style="color:#E05252; font-weight:700;
                    font-size:1rem; margin-bottom:10px;">
            {icon('circle', 14)} Joueur B
        </div>
    """)
    id_b, saison_b = select_player_col("b")

if not id_a or not id_b:
    st.info("Sélectionnez les deux joueurs pour lancer la comparaison.")
    st.stop()

df_a = get_joueur_fiche(id_a, saison_a)
df_b = get_joueur_fiche(id_b, saison_b)

if df_a.empty or df_b.empty:
    st.warning("Données insuffisantes.")
    st.stop()

ra = df_a.iloc[0]
rb = df_b.iloc[0]

nom_a = f"{ra.get('nom_court','Joueur A')} — {saison_a}"
nom_b = f"{rb.get('nom_court','Joueur B')} — {saison_b}"
poste_a = ra.get("poste_id", "CM") or "CM"

st.markdown("---")
st.markdown(f"#### {icon('tune')} Choisir les stats à comparer", unsafe_allow_html=True)

ALL_STATS_COMPARE = {
    "⚽ Offensif": [
        "pct_goals_p90", "pct_xg_p90",
        "pct_assists_p90", "pct_xag_p90", "pct_shots_p90",
    ],
    "🎯 Passes": [
        "pct_key_passes_p90", "pct_passes_pct", "pct_dribbles_p90",
    ],
    "🛡️ Défense": [
        "pct_tackles_p90", "pct_interceptions_p90",
        "pct_degagements_p90", "pct_duels_aeriens_pct",
    ],
}

with st.expander("Sélectionner les stats (4 à 8)", expanded=True):
    stats_sel = stat_checkbox_selector(
        {cat: [RADAR_LABELS.get(s, s) for s in stats]
         for cat, stats in ALL_STATS_COMPARE.items()},
        min_sel=4, max_sel=8, key_prefix="cmp",
    )
    label_to_col = {
        RADAR_LABELS.get(c, c): c
        for cat in ALL_STATS_COMPARE.values()
        for c in cat
    }
    axes_sel = [label_to_col[s] for s in stats_sel if s in label_to_col]

if len(axes_sel) < 4:
    st.stop()

st.markdown(f"#### {icon('radar')} Comparaison radar", unsafe_allow_html=True)
fig = radar_compare(ra, rb, poste_a, axes_override=axes_sel, name_a=nom_a, name_b=nom_b)
st.plotly_chart(fig, use_container_width=True)

st.markdown(f"#### {icon('table_chart')} Statistiques détaillées", unsafe_allow_html=True)

STATS_TABLEAU = {
    "Score Pépite ★":    "score_pepite_corrige",
    "Buts/90":          "buts_p90",
    "xG/90":            "xg_p90",
    "Assists/90":       "passes_dec_p90",
    "xAG/90":           "xag_p90",
    "Key Passes/90":    "key_passes_p90",
    "Dribbles/90":      "dribbles_p90",
    "Tacles/90":        "tackles_p90",
    "Interceptions/90": "interceptions_p90",
    "Précision passes": "passes_pct",
    "Minutes":          "minutes",
    "Matchs":           "matchs_joues",
}

rows = []
for label, col in STATS_TABLEAU.items():
    va = ra.get(col)
    vb = rb.get(col)

    def fmt(v):
        try:
            return round(float(v), 3)
        except (TypeError, ValueError):
            return "—"

    va_f, vb_f = fmt(va), fmt(vb)
    better_a = "🟢" if isinstance(va_f, float) and isinstance(vb_f, float) and va_f > vb_f else ""
    better_b = "🟢" if isinstance(va_f, float) and isinstance(vb_f, float) and vb_f > va_f else ""

    rows.append({
        "Stat":  label,
        nom_a:   f"{better_a} {va_f}",
        nom_b:   f"{better_b} {vb_f}",
    })

st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

import pandas as pd
import streamlit as st
from sqlalchemy import text

from utils.charts import bar_top10, scatter_xg_buts
from utils.db import get_engine, get_saisons
from utils.styles import inject_css

st.set_page_config(
    page_title="RadarPépites",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(inject_css(), unsafe_allow_html=True)

# ── Sidebar globale ──────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚽ RadarPépites")
    st.markdown("---")
    saisons    = get_saisons()
    saison_sel = st.selectbox("Saison", saisons, index=0)
    st.markdown("---")
    st.caption("RadarPépites · Analyse U23 · 10 ligues européennes")

# ── Header ───────────────────────────────────────────────────────
st.markdown("""
    <h1 style='text-align:center; font-size:2.5rem;'>
        ⚽ RadarPépites
    </h1>
    <p style='text-align:center; opacity:0.6; font-size:1.1rem;'>
        Analyse statistique des joueurs U23 · 10 championnats européens
    </p>
""", unsafe_allow_html=True)
st.markdown("---")

engine = get_engine()


@st.cache_data(ttl=3600)
def get_kpis(saison: str) -> pd.DataFrame:
    return pd.read_sql(text("""
        SELECT
            COUNT(DISTINCT joueur_id)              as nb_joueurs,
            COUNT(DISTINCT ligue_id)                as nb_ligues,
            ROUND(AVG(score_corrige)::numeric, 1)   as score_moyen,
            MAX(score_corrige)                      as score_max
        FROM gold.vue_score_pepite_ranking
        WHERE est_u23 = TRUE AND saison_id = :saison
    """), engine, params={"saison": saison})


kpis = get_kpis(saison_sel)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Joueurs U23 analysés", f"{int(kpis['nb_joueurs'].iloc[0]):,}")
col2.metric("Championnats", f"{int(kpis['nb_ligues'].iloc[0])}")
col3.metric("Score Pépite moyen", f"{kpis['score_moyen'].iloc[0]}")
col4.metric("Meilleur Score", f"{kpis['score_max'].iloc[0]:.1f}")

st.markdown("---")

# ── Top 10 / Scatter ─────────────────────────────────────────────
col_left, col_right = st.columns([1, 1])

with col_left:
    st.subheader("🏆 Top 10 Pépites U23")

    @st.cache_data(ttl=1800)
    def get_top10(saison: str) -> pd.DataFrame:
        return pd.read_sql(text("""
            SELECT joueur, poste_id, ligue, equipe,
                   age, score_corrige,
                   ROUND(xg_p90::numeric,3) as xg_p90,
                   ROUND(buts_p90::numeric,3) as buts_p90
            FROM gold.vue_score_pepite_ranking
            WHERE est_u23 = TRUE AND saison_id = :saison
              AND poste_id != 'GK'
            ORDER BY score_corrige DESC LIMIT 10
        """), engine, params={"saison": saison})

    df_top10 = get_top10(saison_sel)
    if df_top10.empty:
        st.info("Aucune donnée pour cette saison.")
    else:
        st.plotly_chart(bar_top10(df_top10, f"Top 10 U23 — {saison_sel}"),
                        use_container_width=True)

with col_right:
    st.subheader("📊 xG vs Buts — Finisseurs")

    @st.cache_data(ttl=1800)
    def get_scatter(saison: str) -> pd.DataFrame:
        return pd.read_sql(text("""
            SELECT joueur, equipe, ligue, age,
                   score_corrige, xg_p90, buts_p90
            FROM gold.vue_score_pepite_ranking
            WHERE est_u23 = TRUE AND saison_id = :saison
              AND xg_p90 IS NOT NULL AND buts_p90 IS NOT NULL
              AND minutes >= 900
        """), engine, params={"saison": saison})

    df_scatter = get_scatter(saison_sel)
    if df_scatter.empty:
        st.info("Aucune donnée pour cette saison.")
    else:
        st.plotly_chart(scatter_xg_buts(df_scatter), use_container_width=True)

# ── Top par ligue ─────────────────────────────────────────────────
st.markdown("---")
st.subheader("🌍 Meilleure Pépite par ligue")


@st.cache_data(ttl=1800)
def get_top_par_ligue(saison: str) -> pd.DataFrame:
    return pd.read_sql(text("""
        SELECT DISTINCT ON (ligue_id)
            joueur, poste_id, ligue, equipe,
            age, score_corrige, couleur_hex
        FROM gold.vue_score_pepite_ranking
        WHERE est_u23 = TRUE AND saison_id = :saison
          AND poste_id != 'GK'
        ORDER BY ligue_id, score_corrige DESC
    """), engine, params={"saison": saison})


df_ligue = get_top_par_ligue(saison_sel)

if df_ligue.empty:
    st.info("Aucune donnée pour cette saison.")
else:
    cols = st.columns(5)
    for i, (_, row) in enumerate(df_ligue.iterrows()):
        with cols[i % 5]:
            color = row.get("couleur_hex") or "#1DB954"
            st.markdown(f"""
                <div class="player-card" style="border-left-color:{color}">
                    <div class="ligue-header">{row['ligue']}</div>
                    <div style="font-weight:700; font-size:1rem;">
                        {row['joueur']}
                    </div>
                    <div style="opacity:0.6; font-size:0.85rem;">
                        {row['equipe']} · {row['poste_id']} · {row['age']} ans
                    </div>
                    <div class="score-badge">{row['score_corrige']:.1f}</div>
                </div>
            """, unsafe_allow_html=True)

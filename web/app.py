import streamlit as st
import pandas as pd
from sqlalchemy import bindparam, text
from utils.db import get_engine, get_classement
from utils.sidebar import render_sidebar
from utils.charts import bar_top10, scatter_xg_buts
from utils.styles import inject_css, icon, render_html

st.set_page_config(
    page_title="RadarPépites · Tableau de bord",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(inject_css(), unsafe_allow_html=True)

filtres = render_sidebar(page_active="dashboard")
saison  = filtres["saison"]
ligues  = filtres["ligues"]
postes  = filtres["postes"]
min_min = filtres["min_min"]
age_max = filtres["age_max"]

render_html(f"""
    <div style="padding:10px 0 20px 0;">
        <h1 style="font-size:1.8rem; font-weight:800; margin:0;">
            {icon('dashboard', 28)} Tableau de bord
        </h1>
        <p style="color:#8A8A8A; margin:4px 0 0 0; font-size:0.9rem;">
            Saison {saison} · {len(ligues)} ligue(s) · {len(postes)} poste(s)
        </p>
    </div>
""")

if not ligues or not postes:
    st.warning("Sélectionnez au moins une ligue et un poste dans les filtres.")
    st.stop()

engine = get_engine()


@st.cache_data(ttl=1800)
def get_kpis(saison, ligues, postes, min_min, age_max):
    stmt = text("""
        SELECT
            COUNT(DISTINCT joueur_id)             as nb,
            ROUND(AVG(score_corrige)::numeric,1)  as moy,
            MAX(score_corrige)                    as max,
            COUNT(DISTINCT ligue_id)              as ligues
        FROM gold.vue_score_pepite_ranking
        WHERE est_u23=TRUE AND saison_id=:saison
          AND minutes>=:min_min AND age<=:age_max
          AND ligue_id IN :ligues AND poste_id IN :postes
    """).bindparams(bindparam("ligues", expanding=True), bindparam("postes", expanding=True))
    return pd.read_sql(stmt, engine, params={
        "saison": saison, "min_min": min_min, "age_max": age_max,
        "ligues": ligues, "postes": postes,
    })


kpis = get_kpis(saison, tuple(ligues), tuple(postes), min_min, age_max)

# st.metric() ne rend pas le HTML dans son label — emoji plutôt que icon() ici.
c1,c2,c3,c4 = st.columns(4)
c1.metric("👥 Joueurs U23", f"{int(kpis['nb'].iloc[0]):,}")
c2.metric("🏆 Ligues", f"{int(kpis['ligues'].iloc[0])}")
c3.metric("📊 Score moyen", f"{kpis['moy'].iloc[0]}")
c4.metric("⭐ Meilleur score", f"{kpis['max'].iloc[0]:.1f}")

render_html('<div style="margin:20px 0;"></div>')

col_l, col_r = st.columns(2, gap="large")

df = get_classement(saison, ligues, postes, age_max, min_min)

with col_l:
    st.markdown(f"#### {icon('bar_chart')} Top 10 Score Pépite", unsafe_allow_html=True)
    if not df.empty:
        st.plotly_chart(bar_top10(df.head(10), ""), use_container_width=True)
    else:
        st.caption("Aucune donnée pour ces filtres.")

with col_r:
    st.markdown(f"#### {icon('scatter_plot')} xG vs Buts", unsafe_allow_html=True)
    df_att = df[df["poste_id"].isin(["FW","LW","RW","AM"])].dropna(subset=["xg_p90","buts_p90"])
    if not df_att.empty:
        st.plotly_chart(scatter_xg_buts(df_att), use_container_width=True)
    else:
        st.caption("Aucune donnée pour ces filtres.")

st.markdown("---")
st.markdown(f"#### {icon('public')} Meilleure pépite par ligue", unsafe_allow_html=True)


@st.cache_data(ttl=1800)
def top_par_ligue(saison, ligues, postes, min_min, age_max):
    stmt = text("""
        SELECT DISTINCT ON (ligue_id)
            joueur_id, joueur, poste_id, ligue, ligue_id,
            equipe, age, score_corrige, couleur_hex
        FROM gold.vue_score_pepite_ranking
        WHERE est_u23=TRUE AND saison_id=:saison
          AND ligue_id IN :ligues AND poste_id IN :postes
          AND minutes>=:min_min AND age<=:age_max
        ORDER BY ligue_id, score_corrige DESC
    """).bindparams(bindparam("ligues", expanding=True), bindparam("postes", expanding=True))
    return pd.read_sql(stmt, engine, params={
        "saison": saison, "min_min": min_min, "age_max": age_max,
        "ligues": ligues, "postes": postes,
    })


df_ligue = top_par_ligue(saison, tuple(ligues), tuple(postes), min_min, age_max)

if not df_ligue.empty:
    cols = st.columns(min(len(df_ligue), 5))
    for i, (_, row) in enumerate(df_ligue.iterrows()):
        with cols[i % 5]:
            color = row.get("couleur_hex") or "#2DAD7E"
            if st.button(
                f"⚽ {row['joueur']}",
                key=f"btn_{row['joueur_id']}_{i}",
                use_container_width=True,
            ):
                st.session_state["prefill_joueur"]    = row["joueur"]
                st.session_state["prefill_joueur_id"] = row["joueur_id"]
                st.session_state["prefill_saison"]    = saison
                st.switch_page("pages/02_Radar_Joueur.py")

            render_html(f"""
                <div class="card card-accent"
                     style="border-left-color:{color};
                            margin-top:-8px;">
                    <div style="font-size:0.65rem; color:#8A8A8A;
                                text-transform:uppercase;
                                letter-spacing:1px;">
                        {row['ligue']}
                    </div>
                    <div style="font-size:0.8rem; color:#8A8A8A;">
                        {row['equipe']} · {row['poste_id']}
                        · {row['age']} ans
                    </div>
                    <span class="score-badge-sm">
                        ★ {row['score_corrige']:.1f}
                    </span>
                </div>
            """)
else:
    st.caption("Aucune donnée pour ces filtres.")

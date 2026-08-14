import streamlit as st

from utils.db import get_classement, get_ligues, get_postes, get_saisons
from utils.styles import inject_css

st.set_page_config(page_title="Explorer — RadarPépites", layout="wide")
st.markdown(inject_css(), unsafe_allow_html=True)

# ── Sidebar filtres ────────────────────────────────────────────
with st.sidebar:
    saisons = get_saisons()
    saison  = st.selectbox("Saison", saisons)

    df_ligues  = get_ligues()
    ligues_opt = df_ligues["nom_complet"].tolist()
    ligues_sel = st.multiselect("Ligues", ligues_opt, default=ligues_opt)
    ligues_ids = df_ligues[df_ligues["nom_complet"].isin(ligues_sel)]["ligue_id"].tolist()

    df_postes  = get_postes()
    postes_opt = df_postes[df_postes["poste_id"] != "GK"]["poste_id"].tolist()
    postes_sel = st.multiselect("Postes", postes_opt, default=postes_opt)

    age_max = st.slider("Âge maximum", 16, 23, 23)
    min_min = st.slider("Minutes minimum", 90, 1800, 450, step=90)

# ── Contenu ───────────────────────────────────────────────────
st.title("🔍 Explorer les Pépites U23")

df = get_classement(saison, ligues_ids, postes_sel, age_max, min_min)

if df.empty:
    st.warning("Aucun joueur trouvé avec ces filtres.")
    st.stop()

c1, c2, c3 = st.columns(3)
c1.metric("Joueurs trouvés", len(df))
c2.metric("Score moyen", f"{df['score_corrige'].mean():.1f}")
c3.metric("Score max", f"{df['score_corrige'].max():.1f}")

st.markdown("---")
st.subheader(f"Classement Score Pépite — {saison}")

df_display = df[[
    "rang_global", "joueur", "poste_id", "ligue",
    "equipe", "age", "score_corrige", "score_pepite",
    "xg_p90", "buts_p90", "assists_p90",
    "key_passes_p90", "dribbles_p90",
    "tackles_p90", "interceptions_p90",
    "minutes", "rating_reference",
]].rename(columns={
    "rang_global":       "Rang",
    "joueur":            "Joueur",
    "poste_id":          "Poste",
    "ligue":             "Ligue",
    "equipe":            "Équipe",
    "age":               "Âge",
    "score_corrige":     "Score ★",
    "score_pepite":      "Score brut",
    "xg_p90":            "xG/90",
    "buts_p90":          "Buts/90",
    "assists_p90":       "Ast/90",
    "key_passes_p90":    "KP/90",
    "dribbles_p90":      "Drib/90",
    "tackles_p90":       "Tac/90",
    "interceptions_p90": "Int/90",
    "minutes":           "Minutes",
    "rating_reference":  "Rating réf.",
})

st.dataframe(
    df_display,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Score ★": st.column_config.ProgressColumn(
            "Score ★", min_value=0, max_value=100, format="%.1f",
        ),
    },
)

csv = df_display.to_csv(index=False).encode("utf-8")
st.download_button("⬇️ Télécharger CSV", csv, f"radarpepites_{saison}.csv", "text/csv")

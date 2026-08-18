import streamlit as st
import pandas as pd
from utils.db import get_ligues, get_saisons, get_classement, get_top_gk_score
from utils.sidebar import render_filters
from utils.styles import icon, render_html

# Cette page a ses propres sélecteurs de championnat ET de saison (ci-dessous) —
# la sélection ne se fait pas dans la sidebar, donc on grise Saison/Ligues/
# Postes pour ne pas laisser croire qu'ils affectent la page. Minutes/Âge
# restent actifs : ils sont réellement utilisés comme filtres ici.
filtres = render_filters(disable_saison=True, disable_ligues=True, disable_postes=True)
min_min = filtres["min_min"]
age_max = filtres["age_max"]

render_html(f"""
    <h1 style="font-size:1.8rem; font-weight:800; margin-bottom:4px;">
        {icon('emoji_events', 28)} Championnats
    </h1>
    <p style="color:#8A8A8A; font-size:0.9rem; margin-bottom:20px;">
        Analyse détaillée d'un championnat : meilleurs profils par poste,
        classements par catégorie, onze type et pépites sous-cotées.
    </p>
""")

# ── Sélection du championnat + de la saison, indépendante des filtres
# globaux de la sidebar — ici on veut UNE ligue et UNE saison à la fois ──
df_ligues = get_ligues()
ligue_options = dict(zip(df_ligues["nom_complet"], df_ligues["ligue_id"]))
saisons = get_saisons()

col_ligue, col_saison = st.columns([2, 1])
with col_ligue:
    ligue_nom = st.selectbox(
        "🌍 Choisir un championnat",
        list(ligue_options.keys()),
        key="championnat_select",
    )
with col_saison:
    saison = st.selectbox(
        "📅 Saison",
        saisons,
        key="championnat_saison_select",
    )

ligue_id = ligue_options[ligue_nom]
couleur_ligue = df_ligues[df_ligues["ligue_id"] == ligue_id]["couleur_hex"].iloc[0] or "#2DAD7E"

# DM (Milieu défensif) volontairement absent : aucun joueur n'est jamais
# classé DM dans la base actuelle (le pipeline de classification des
# postes fait retomber tous les DM sur CM avant chargement — problème
# identifié, pas encore corrigé). Formation à 2 CM + 1 AM en attendant.
POSTES_ORDER = ["FW", "LW", "RW", "AM", "CM", "CB", "LB", "RB"]
POSTE_LABELS = {
    "FW": "Avant-centre", "LW": "Ailier gauche", "RW": "Ailier droit",
    "AM": "Milieu offensif", "CM": "Milieu central",
    "CB": "Défenseur central", "LB": "Latéral gauche", "RB": "Latéral droit",
}

df = get_classement(saison, [ligue_id], POSTES_ORDER, age_max, min_min)
df_gk_top = get_top_gk_score(saison, ligue_id, min_min, age_max, n=3)

if df.empty:
    st.info("Aucune donnée pour ce championnat avec les filtres actuels.")
    st.stop()

st.markdown("---")

# ══════════════════════════════════════════════════════════════════
# SECTION 1 — Meilleurs joueurs par poste (titulaire + 2 doublures)
# ══════════════════════════════════════════════════════════════════
st.markdown(f"### {icon('star')} Meilleurs joueurs par poste", unsafe_allow_html=True)
st.caption("Titulaire + 2 doublures proposées, par poste, selon le Score Pépite.")


def top_n_poste(poste: str, n: int = 3) -> pd.DataFrame:
    return (
        df[df["poste_id"] == poste]
        .sort_values("score_corrige", ascending=False)
        .head(n)
    )


def render_poste_rows(df_sub: pd.DataFrame, url_base: str):
    """Liste compacte joueur/score/équipe, pour une colonne de la grille poste."""
    if df_sub.empty:
        st.caption("Aucune donnée")
        return
    rows_html = []
    for rank, (_, row) in enumerate(df_sub.iterrows()):
        medal = "🥇" if rank == 0 else "🔁"
        href = f"{url_base}?joueur_id={row['joueur_id']}&saison={saison}"
        rows_html.append(f"""
            <a href="{href}" target="_self" style="text-decoration:none;">
                <div style="padding:6px 2px; border-bottom:1px solid #1A1A1A;">
                    <div style="display:flex; justify-content:space-between;
                                align-items:baseline; gap:6px;">
                        <span style="font-weight:700; color:#FFFFFF;
                                    font-size:0.82rem; white-space:nowrap;
                                    overflow:hidden; text-overflow:ellipsis;">
                            {medal} {row['joueur']}
                        </span>
                        <span style="color:#2DAD7E; font-weight:700;
                                    font-size:0.76rem; white-space:nowrap;">
                            ★ {row['score_corrige']:.1f}
                        </span>
                    </div>
                    <div style="color:#8A8A8A; font-size:0.7rem; margin-top:1px;">
                        {row['equipe']} · {row['age']} ans
                    </div>
                </div>
            </a>
        """)
    render_html("".join(rows_html))


def render_poste_header(label: str):
    render_html(f"""
        <div style="font-size:0.7rem; font-weight:700;
                    text-transform:uppercase; letter-spacing:1.5px;
                    color:#8A8A8A; margin:16px 0 4px 0;
                    border-bottom:1px solid #1A1A1A; padding-bottom:4px;">
            {label}
        </div>
    """)


cols_postes = st.columns(3)
for i, poste in enumerate(POSTES_ORDER):
    with cols_postes[i % 3]:
        render_poste_header(POSTE_LABELS[poste])
        render_poste_rows(top_n_poste(poste, 3), "/Radar_Joueur")

with cols_postes[len(POSTES_ORDER) % 3]:
    render_poste_header("Gardien")
    render_poste_rows(df_gk_top, "/Radar_GK")

st.markdown("---")

# ══════════════════════════════════════════════════════════════════
# SECTION 2 — Classements Top 5 par catégorie de qualité
# ══════════════════════════════════════════════════════════════════
st.markdown(f"### {icon('leaderboard')} Top 5 par catégorie", unsafe_allow_html=True)
st.caption("Les 5 joueurs les plus performants du championnat sur chaque qualité.")

CATEGORIES = {
    "⚽ Buteurs":     ("buts_p90",         "Buts/90"),
    "🎯 Passeurs":    ("assists_p90",      "Assists/90"),
    "🏃 Dribbleurs":  ("dribbles_p90",     "Dribbles/90"),
    "🛡️ Défenseurs": ("tackles_p90",      "Tacles/90"),
    "🧠 Créateurs":   ("key_passes_p90",   "Passes clés/90"),
}

tabs = st.tabs(list(CATEGORIES.keys()))
for tab, (cat_label, (col, col_label)) in zip(tabs, CATEGORIES.items()):
    with tab:
        top5 = (
            df.dropna(subset=[col])
            .sort_values(col, ascending=False)
            .head(5)
        )
        if top5.empty:
            st.caption("Données insuffisantes.")
            continue

        valeur_max = top5[col].max() or 1
        rows_html = []
        for rank, (_, row) in enumerate(top5.iterrows(), start=1):
            medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(rank, f"{rank}.")
            pct = max(6, round(row[col] / valeur_max * 100))
            href = f"/Radar_Joueur?joueur_id={row['joueur_id']}&saison={saison}"
            rows_html.append(f"""
                <a href="{href}" target="_self" style="text-decoration:none;">
                    <div style="padding:0;">
                    <div class="bar-row">
                        <div style="min-width:28px; text-align:center;
                                    font-size:0.9rem;">{medal}</div>
                        <div style="flex:0 0 200px; min-width:0;">
                            <div style="font-weight:700; color:#FFFFFF;
                                        font-size:0.85rem; white-space:nowrap;
                                        overflow:hidden; text-overflow:ellipsis;">
                                {row['joueur']}
                            </div>
                            <div style="color:#8A8A8A; font-size:0.7rem;
                                        white-space:nowrap; overflow:hidden;
                                        text-overflow:ellipsis;">
                                {row['equipe']} · {row['poste_id']}
                            </div>
                        </div>
                        <div style="flex:1; height:10px; background:#1A1A1A;
                                    border-radius:5px; overflow:hidden;">
                            <div style="width:{pct}%; height:100%;
                                        background:linear-gradient(90deg,#2DAD7E,#5DCBA0);
                                        border-radius:5px;"></div>
                        </div>
                        <div style="min-width:64px; text-align:right;
                                    font-weight:700; color:#FFFFFF;
                                    font-size:0.82rem; white-space:nowrap;">
                            {row[col]:.2f}
                        </div>
                    </div>
                    </div>
                </a>
            """)
        render_html("".join(rows_html))

st.markdown("---")

# ══════════════════════════════════════════════════════════════════
# SECTION 3 — Onze type (4-3-3)
# ══════════════════════════════════════════════════════════════════
st.markdown(f"### {icon('sports_soccer')} Onze type proposé", unsafe_allow_html=True)
st.caption("Formation 4-3-3 — le meilleur profil disponible à chaque poste.")

def onze_card(nom, sous_texte, score=None, href=None):
    score_html = f'<span class="score-badge-sm">★ {score:.1f}</span>' if score is not None else ""
    inner = f"""
        <div class="card" style="padding:8px 12px; text-align:center;
                    min-width:110px;">
            <div style="font-weight:700; color:#FFFFFF; font-size:0.82rem;">
                {nom}
            </div>
            <div style="font-size:0.68rem; color:#8A8A8A; margin:2px 0 6px 0;">
                {sous_texte}
            </div>
            {score_html}
        </div>
    """
    if href:
        return f'<a href="{href}" target="_self" style="text-decoration:none;">{inner}</a>'
    return inner


def ligne_formation(titre, cartes_html):
    render_html(f"""
        <div style="font-size:0.65rem; font-weight:700;
                    text-transform:uppercase; letter-spacing:2px;
                    color:#8A8A8A; margin:16px 0 8px 0;">
            {titre}
        </div>
        <div style="display:flex; gap:10px; flex-wrap:wrap;
                    justify-content:center;">
            {''.join(cartes_html)}
        </div>
    """)


# Gardien — df_gk_top est sourcé de fact_stats (get_top_gk_score), donc
# joueur_id est directement compatible avec Radar GK et score_corrige
# est le vrai Score Pépite, pas besoin de résolution d'ID séparée.
if not df_gk_top.empty:
    g = df_gk_top.iloc[0]
    href_gk = f"/Radar_GK?joueur_id={g['joueur_id']}&saison={saison}"
    cartes = [onze_card(g["joueur"], g["equipe"], g["score_corrige"], href_gk)]
else:
    cartes = [onze_card("—", "Gardien indisponible")]
ligne_formation(f"{icon('sports_handball',14)} Gardien", cartes)


# Défense (LB, CB, CB, RB)
def carte_poste(poste, idx=0):
    tops = top_n_poste(poste, 2)
    if tops.empty or idx >= len(tops):
        return onze_card("—", POSTE_LABELS[poste])
    r = tops.iloc[idx]
    href = f"/Radar_Joueur?joueur_id={r['joueur_id']}&saison={saison}"
    return onze_card(r["joueur"], f"{r['equipe']}", r["score_corrige"], href)


cartes_def = [
    carte_poste("LB"),
    carte_poste("CB", 0),
    carte_poste("CB", 1),
    carte_poste("RB"),
]
ligne_formation(f"{icon('shield',14)} Défense", cartes_def)

# Milieu (2 CM + 1 AM — pas de DM classé dans la base actuelle)
cartes_mil = [carte_poste("CM", 0), carte_poste("CM", 1), carte_poste("AM")]
ligne_formation(f"{icon('sync_alt',14)} Milieu", cartes_mil)

# Attaque (LW, FW, RW)
cartes_att = [carte_poste("LW"), carte_poste("FW"), carte_poste("RW")]
ligne_formation(f"{icon('bolt',14)} Attaque", cartes_att)

st.markdown("---")

# ══════════════════════════════════════════════════════════════════
# SECTION 4 — Pépites sous-cotées
# ══════════════════════════════════════════════════════════════════
st.markdown(f"### {icon('diamond')} Pépites sous-cotées", unsafe_allow_html=True)
st.caption(
    "Score Pépite élevé (top 20% du championnat) mais temps de jeu "
    "encore en dessous de la médiane — potentiel pas encore pleinement exploité."
)

seuil_score = df["score_corrige"].quantile(0.80)
mediane_minutes = df["minutes"].median()

pepites = (
    df[(df["score_corrige"] >= seuil_score) & (df["minutes"] < mediane_minutes)]
    .sort_values("score_corrige", ascending=False)
    .head(6)
)

if pepites.empty:
    st.info("Aucune pépite sous-cotée identifiée avec les filtres actuels.")
else:
    cols_pep = st.columns(3)
    for i, (_, row) in enumerate(pepites.iterrows()):
        with cols_pep[i % 3]:
            href = f"/Radar_Joueur?joueur_id={row['joueur_id']}&saison={saison}"
            render_html(f"""
                <a href="{href}" target="_self" class="player-card-link">
                    <div class="card card-accent player-mini-card"
                         style="border-left-color:#5DCBA0;">
                        <div class="pmc-name">💎 {row['joueur']}</div>
                        <div class="pmc-league">{row['poste_id']} · {row['equipe']}</div>
                        <div class="pmc-details">
                            {row['age']} ans · {int(row['minutes'])} min jouées
                        </div>
                        <span class="score-badge-sm">
                            ★ {row['score_corrige']:.1f}
                        </span>
                    </div>
                </a>
            """)

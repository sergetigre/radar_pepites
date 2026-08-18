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
        Analyse détaillée d'un championnat : classements par catégorie,
        onze type avec doublures et pépites sous-cotées.
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


def top_n_poste(poste: str, n: int = 3) -> pd.DataFrame:
    return (
        df[df["poste_id"] == poste]
        .sort_values("score_corrige", ascending=False)
        .head(n)
    )


st.markdown("---")

# ══════════════════════════════════════════════════════════════════
# SECTION 1 — Classements Top 5 par catégorie de qualité
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
# SECTION 2 — Onze type (4-3-3), titulaire + doublures par poste
# ══════════════════════════════════════════════════════════════════
st.markdown(f"### {icon('sports_soccer')} Onze type proposé", unsafe_allow_html=True)
st.caption("Titulaire (équipe, âge, note) + doublures juste en dessous, par poste.")


def carte_formation(df_sub: pd.DataFrame, url_base: str, poste_label: str = "") -> str:
    """Une carte par poste sur le terrain : titulaire mis en avant
    (équipe, âge, Score Pépite) puis doublures compactes en dessous,
    toutes cliquables vers leur fiche."""
    if df_sub.empty:
        return f"""
            <div class="card" style="padding:10px 12px; min-width:150px; text-align:center;">
                <div style="font-weight:700; color:#FFFFFF; font-size:0.85rem;">—</div>
                <div style="font-size:0.68rem; color:#8A8A8A; margin-top:2px;">
                    {poste_label or "Indisponible"}
                </div>
            </div>
        """

    rows = df_sub.reset_index(drop=True)
    titulaire = rows.iloc[0]
    href_tit = f"{url_base}?joueur_id={titulaire['joueur_id']}&saison={saison}"

    doublures_html = ""
    for _, d in rows.iloc[1:].iterrows():
        href_d = f"{url_base}?joueur_id={d['joueur_id']}&saison={saison}"
        doublures_html += f"""
            <a href="{href_d}" target="_self" style="text-decoration:none;">
                <div style="padding-top:5px; margin-top:5px; border-top:1px solid #1A1A1A;">
                    <div style="font-size:0.72rem; font-weight:600; color:#DADADA;
                                white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">
                        {d['joueur']}
                    </div>
                    <div style="font-size:0.64rem; color:#8A8A8A; white-space:nowrap;
                                overflow:hidden; text-overflow:ellipsis;">
                        {d['equipe']} · {d['age']} ans ·
                        <span style="color:#2DAD7E; font-weight:700;">★ {d['score_corrige']:.1f}</span>
                    </div>
                </div>
            </a>
        """

    return f"""
        <div class="card" style="padding:10px 12px; min-width:160px; max-width:190px;">
            <a href="{href_tit}" target="_self" style="text-decoration:none;">
                <div style="font-weight:700; color:#FFFFFF; font-size:0.86rem;
                            white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">
                    {titulaire['joueur']}
                </div>
                <div style="font-size:0.7rem; color:#8A8A8A; margin:2px 0 6px 0;">
                    {titulaire['equipe']} · {titulaire['age']} ans
                </div>
                <span class="score-badge-sm">★ {titulaire['score_corrige']:.1f}</span>
            </a>
            {doublures_html}
        </div>
    """


def slots_poste(poste: str, n_slots: int = 1, n_total: int = 3) -> list:
    """Découpe le classement d'un poste en n_slots cartes distinctes —
    pour les postes à 2 titulaires dans la formation (CB, CM), le slot 0
    prend les rangs 0/2, le slot 1 les rangs 1/3 (titulaire + 1 doublure
    chacun) plutôt que de partager la même doublure sur les deux cartes."""
    tops = top_n_poste(poste, n_total)
    return [
        carte_formation(tops.iloc[slot::n_slots], "/Radar_Joueur", POSTE_LABELS[poste])
        for slot in range(n_slots)
    ]


def ligne_formation(titre, cartes_html):
    render_html(f"""
        <div style="font-size:0.65rem; font-weight:700;
                    text-transform:uppercase; letter-spacing:2px;
                    color:#8A8A8A; margin:16px 0 8px 0;">
            {titre}
        </div>
        <div style="display:flex; gap:10px; flex-wrap:wrap;
                    justify-content:center; align-items:flex-start;">
            {''.join(cartes_html)}
        </div>
    """)


# Gardien — df_gk_top est sourcé de fact_stats (get_top_gk_score), donc
# joueur_id est directement compatible avec Radar GK et score_corrige
# est le vrai Score Pépite.
ligne_formation(
    f"{icon('sports_handball',14)} Gardien",
    [carte_formation(df_gk_top, "/Radar_GK", "Gardien")],
)

# Défense (LB, CB×2, RB)
cb_slots = slots_poste("CB", n_slots=2, n_total=4)
cartes_def = [
    carte_formation(top_n_poste("LB", 3), "/Radar_Joueur", POSTE_LABELS["LB"]),
    cb_slots[0],
    cb_slots[1],
    carte_formation(top_n_poste("RB", 3), "/Radar_Joueur", POSTE_LABELS["RB"]),
]
ligne_formation(f"{icon('shield',14)} Défense", cartes_def)

# Milieu (2 CM + 1 AM — pas de DM classé dans la base actuelle)
cm_slots = slots_poste("CM", n_slots=2, n_total=4)
cartes_mil = [
    cm_slots[0],
    cm_slots[1],
    carte_formation(top_n_poste("AM", 3), "/Radar_Joueur", POSTE_LABELS["AM"]),
]
ligne_formation(f"{icon('sync_alt',14)} Milieu", cartes_mil)

# Attaque (LW, FW, RW)
cartes_att = [
    carte_formation(top_n_poste("LW", 3), "/Radar_Joueur", POSTE_LABELS["LW"]),
    carte_formation(top_n_poste("FW", 3), "/Radar_Joueur", POSTE_LABELS["FW"]),
    carte_formation(top_n_poste("RW", 3), "/Radar_Joueur", POSTE_LABELS["RW"]),
]
ligne_formation(f"{icon('bolt',14)} Attaque", cartes_att)

st.markdown("---")

# ══════════════════════════════════════════════════════════════════
# SECTION 3 — Pépites sous-cotées
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

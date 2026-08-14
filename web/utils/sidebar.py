import streamlit as st
from utils.db import get_ligues, get_saisons
from utils.styles import icon, render_html

FAMILLES_POSTES = {
    "Attaquants": {
        "FW": "Avant-centre",
        "LW": "Ailier gauche",
        "RW": "Ailier droit",
    },
    "Milieux": {
        "AM": "Milieu offensif",
        "CM": "Milieu central",
        "DM": "Milieu défensif",
    },
    "Défenseurs": {
        "CB": "Défenseur central",
        "LB": "Latéral gauche",
        "RB": "Latéral droit",
    },
}

ALL_POSTES = [p for f in FAMILLES_POSTES.values() for p in f]

# (chemin de page, label, icône Material, en-tête de section)
# Les icônes utilisent le shortcode natif :material/xxx: de st.page_link —
# st.page_link gère lui-même la mise en avant de la page active.
NAV_ITEMS = [
    ("pages/00_Tableau_de_bord.py", "Tableau de bord", "dashboard", None),
    (None, None, None, "JOUEURS DE CHAMP"),
    ("pages/01_Explorer.py",       "Explorer",       "search",               None),
    ("pages/02_Radar_Joueur.py",   "Radar Joueur",   "radar",                None),
    ("pages/03_Comparaison.py",    "Comparaison",    "compare_arrows",       None),
    ("pages/04_Progression.py",    "Progression",    "trending_up",          None),
    (None, None, None, "GARDIENS"),
    ("pages/05_Classement_GK.py",  "Classement GK",  "format_list_bulleted", None),
    ("pages/06_Radar_GK.py",       "Radar GK",       "radar",                None),
    ("pages/07_Comparaison_GK.py", "Comparaison GK", "compare_arrows",       None),
    ("pages/08_Progression_GK.py", "Progression GK", "trending_up",          None),
]


def render_nav():
    """Navigation sidebar (logo + liens). Appelée une seule fois depuis
    app.py, avant st.navigation(...).run() — reste donc affichée sur
    toutes les pages sans se recharger."""
    with st.sidebar:

        render_html("""
            <div style="text-align:center; padding:16px 0 20px 0;">
                <div style="font-size:1.8rem; margin-bottom:4px;">⚽</div>
                <div style="font-size:1.3rem; font-weight:800;
                            color:#2DAD7E; letter-spacing:0.5px;">
                    RadarPépites
                </div>
                <div style="font-size:0.65rem; color:#8A8A8A;
                            margin-top:3px;">
                    Analyse U23 · 10 ligues
                </div>
            </div>
        """)

        render_html('<div style="border-top:1px solid #1A1A1A; margin:0 0 8px 0;"></div>')

        for path, label, icon_name, section in NAV_ITEMS:
            if path is None:
                render_html(f'<div class="nav-section">{section}</div>')
                continue
            st.page_link(path, label=label, icon=f":material/{icon_name}:")

        render_html('<div style="border-top:1px solid #1A1A1A; margin:12px 0 4px 0;"></div>')


def render_filters() -> dict:
    """Filtres globaux persistants (saison, ligues, postes, minutes, âge).
    Appelée par chaque page, en dessous de la nav déjà affichée par app.py.
    Retourne un dict des filtres actifs."""
    with st.sidebar:

        render_html(f"""
            <div style="font-size:0.65rem; font-weight:700;
                        text-transform:uppercase; letter-spacing:2px;
                        color:#8A8A8A; padding:8px 0 10px 2px;">
                {icon('tune', 16)} Filtres
            </div>
        """)

        saisons     = get_saisons()
        saison_def  = st.session_state.get("filtre_saison", saisons[0])
        saison_idx  = saisons.index(saison_def) if saison_def in saisons else 0
        saison      = st.selectbox(
            "Saison", saisons, index=saison_idx, key="filtre_saison"
        )

        df_ligues   = get_ligues()
        all_ligue_ids = df_ligues["ligue_id"].tolist()

        render_html(f"""
            <div style="font-size:0.72rem; font-weight:600;
                        color:#FFFFFF; margin:12px 0 6px 0;">
                {icon('public', 15)} Ligues
            </div>
        """)

        ca, cb = st.columns(2)
        if ca.button("Tout", key="all_l", use_container_width=True):
            for lid in all_ligue_ids:
                st.session_state[f"l_{lid}"] = True
            st.rerun()
        if cb.button("Aucun", key="none_l", use_container_width=True):
            for lid in all_ligue_ids:
                st.session_state[f"l_{lid}"] = False
            st.rerun()

        ligues_sel = []
        for _, row in df_ligues.iterrows():
            lid     = row["ligue_id"]
            default = st.session_state.get(f"l_{lid}", True)
            val     = st.checkbox(
                row["nom_complet"], value=default, key=f"l_{lid}"
            )
            if val:
                ligues_sel.append(lid)

        render_html(f"""
            <div style="font-size:0.72rem; font-weight:600;
                        color:#FFFFFF; margin:12px 0 6px 0;">
                {icon('person', 15)} Postes
            </div>
        """)

        cc, cd = st.columns(2)
        if cc.button("Tout", key="all_p", use_container_width=True):
            for p in ALL_POSTES:
                st.session_state[f"p_{p}"] = True
            st.rerun()
        if cd.button("Aucun", key="none_p", use_container_width=True):
            for p in ALL_POSTES:
                st.session_state[f"p_{p}"] = False
            st.rerun()

        postes_sel = []
        for famille, codes in FAMILLES_POSTES.items():
            with st.expander(famille, expanded=True):
                for code, label in codes.items():
                    default = st.session_state.get(f"p_{code}", True)
                    val     = st.checkbox(
                        label, value=default, key=f"p_{code}"
                    )
                    if val:
                        postes_sel.append(code)

        # Les labels de widgets Streamlit ne rendent pas le HTML —
        # emoji simple plutôt que icon() ici.
        min_min = st.select_slider(
            "⏱️ Minutes min",
            options=[90, 180, 270, 450, 900, 1350, 1800],
            value=st.session_state.get("filtre_minutes", 450),
            key="filtre_minutes",
        )

        age_max = st.slider(
            "🎂 Âge max",
            min_value=16, max_value=23,
            value=st.session_state.get("filtre_age", 23),
            key="filtre_age",
        )

        render_html('<div style="border-top:1px solid #1A1A1A; margin:16px 0 8px 0;"></div>')
        st.caption("RadarPépites v1.0 · 10 ligues · 3 saisons")

    return {
        "saison":  saison,
        "ligues":  ligues_sel,
        "postes":  postes_sel,
        "min_min": min_min,
        "age_max": age_max,
    }

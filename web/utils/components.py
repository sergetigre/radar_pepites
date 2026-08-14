import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utils.styles import icon, render_html

COLORS = {
    "green": "#2DAD7E", "green_dark": "#1A8A5A",
    "black_card": "#111111", "border": "#1A1A1A",
    "white": "#FFFFFF", "gray": "#8A8A8A",
    "bar_low": "#E05252", "bar_mid": "#E0B452",
    "bar_high": "#2DAD7E",
}


def pct_bar_color(value: float) -> str:
    if value is None:
        return COLORS["gray"]
    if value < 33:
        return COLORS["bar_low"]
    if value < 66:
        return COLORS["bar_mid"]
    return COLORS["bar_high"]


def render_pct_bars(metrics: dict, title: str = ""):
    """
    Affiche des barres horizontales de percentiles.
    metrics = {"Label": valeur_percentile, ...}
    """
    if title:
        render_html(f"""
            <div style="font-size:0.7rem; font-weight:700;
                        text-transform:uppercase; letter-spacing:2px;
                        color:#8A8A8A; margin:16px 0 10px 0;">
                {title}
            </div>
        """)

    bars_html = ""
    for label, value in metrics.items():
        if value is None or pd.isna(value):
            continue
        val     = round(float(value), 1)
        color   = pct_bar_color(val)
        bars_html += f"""
        <div class="pct-bar-container">
            <div class="pct-bar-label">
                <span>{label}</span>
                <span>{val:.0f}</span>
            </div>
            <div class="pct-bar-track">
                <div class="pct-bar-fill"
                     style="width:{val}%;
                            background:{color};"></div>
            </div>
        </div>
        """
    if bars_html:
        render_html(bars_html)


def render_player_header(row: pd.Series, is_gk: bool = False):
    """
    Header joueur complet :
    nom, âge, nationalité, taille, pied, équipe, ligue,
    Score Pépite, rang.
    """
    nom      = row.get("nom_complet") or row.get("player_name", "—")
    age      = row.get("age", "—")
    nat      = row.get("nationalite_principale") or row.get("nationalite_id", "—")
    taille   = row.get("taille_cm", "—")
    pied     = row.get("pied_dominant", "—")
    equipe   = row.get("equipe", "—")
    ligue    = row.get("ligue", "—")
    score    = row.get("score_pepite_corrige") or row.get("score_pepite")
    rang_l   = row.get("score_rang_ligue", "—")
    rang_g   = row.get("score_rang_global", "—")
    color    = row.get("couleur_hex") or COLORS["green"]
    poste    = row.get("poste_id") or row.get("poste_principal", "") or ("GK" if is_gk else "")

    score_html = ""
    if score is not None and pd.notna(score):
        score_html = f"""
        <div style="text-align:right;">
            <div style="font-size:0.65rem; color:#8A8A8A;
                        margin-bottom:4px; text-transform:uppercase;
                        letter-spacing:1px;">Score Pépite</div>
            <div class="score-badge">{float(score):.1f}</div>
            <div style="font-size:0.72rem; color:#8A8A8A;
                        margin-top:6px;">
                #{rang_l} {ligue_court(ligue)}
                · #{rang_g} Global
            </div>
        </div>
        """

    badges = ""
    for label, val in [
        (f"{icon('cake')} {age} ans",    age != "—"),
        (f"{icon('flag')} {nat}",        nat != "—"),
        (f"{icon('height')} {taille} cm", taille not in ["—", None]),
        (f"{icon('sports_soccer')} {pied}", pied not in ["—", None]),
        (f"{icon('location_on')} {poste}", bool(poste)),
    ]:
        if val:
            badges += f'<span class="player-badge">{label}</span>'

    render_html(f"""
        <div class="player-header">
            <div style="display:flex; justify-content:space-between;
                        align-items:flex-start; flex-wrap:wrap; gap:16px;">
                <div style="flex:1; min-width:200px;">
                    <div style="font-size:0.75rem; color:{color};
                                font-weight:700; text-transform:uppercase;
                                letter-spacing:1px; margin-bottom:6px;">
                        {equipe} · {ligue}
                    </div>
                    <div class="player-name">{nom}</div>
                    <div style="margin:10px 0;">{badges}</div>
                </div>
                {score_html}
            </div>
        </div>
    """)


def ligue_court(ligue_nom: str) -> str:
    mapping = {
        "Premier League": "PL", "La Liga": "Liga",
        "Bundesliga": "BL", "Serie A": "SerA",
        "Ligue 1": "L1", "Primeira Liga": "PL PT",
        "Eredivisie": "Ere", "Pro League": "JPL",
        "Süper Lig": "SL", "Bundesliga Autriche": "BL AT",
    }
    return mapping.get(ligue_nom, ligue_nom[:3] if ligue_nom else "—")


def render_terrain_svg(poste: str, width: int = 160) -> str:
    """
    Mini terrain SVG avec le poste mis en évidence.
    Retourne le HTML à injecter (via render_html côté appelant).
    """
    # Terrain 100x140, ligne médiane à y=70, but adverse en haut (FW proche
    # de y=5-25) : l'équipe attaque vers y=0. Les défenseurs doivent donc
    # rester nettement sous y=70 (dans leur moitié), pas dessus.
    POSITIONS = {
        "GK":  (50, 122),
        "CB":  (50, 100), "LB": (18, 100), "RB": (82, 100),
        "DM":  (50, 80),
        "CM":  (50, 60), "LM": (18, 60), "RM": (82, 60),
        "AM":  (50, 40),
        "LW":  (15, 25), "RW": (85, 25),
        "FW":  (50, 15),
        "MF":  (50, 60), "DF": (50, 100),
    }

    px, py = POSITIONS.get(poste, (50, 50))
    h      = int(width * 1.4)
    r      = int(width * 0.04)

    return (
        f'<svg width="{width}" height="{h}" viewBox="0 0 100 140" '
        f'xmlns="http://www.w3.org/2000/svg">'
        f'<rect width="100" height="140" rx="4" fill="#0D1A12"/>'
        f'<rect x="5" y="5" width="90" height="130" rx="2" fill="none" '
        f'stroke="#2DAD7E" stroke-width="1.2" opacity="0.6"/>'
        f'<line x1="5" y1="70" x2="95" y2="70" stroke="#2DAD7E" '
        f'stroke-width="0.8" opacity="0.4"/>'
        f'<circle cx="50" cy="70" r="12" fill="none" stroke="#2DAD7E" '
        f'stroke-width="0.8" opacity="0.4"/>'
        f'<rect x="25" y="115" width="50" height="20" fill="none" '
        f'stroke="#2DAD7E" stroke-width="0.8" opacity="0.4"/>'
        f'<rect x="25" y="5" width="50" height="20" fill="none" '
        f'stroke="#2DAD7E" stroke-width="0.8" opacity="0.4"/>'
        f'<circle cx="{px}" cy="{py}" r="{r + 1}" fill="#2DAD7E" opacity="0.25"/>'
        f'<circle cx="{px}" cy="{py}" r="{r}" fill="#2DAD7E"/>'
        f'</svg>'
    )


def render_strengths_weaknesses(row: pd.Series):
    """
    Génère automatiquement points forts et axes d'amélioration
    depuis les percentiles.
    """
    PCT_LABELS = {
        "pct_goals_p90":         "Buts/90",
        "pct_xg_p90":            "xG/90",
        "pct_assists_p90":       "Assists/90",
        "pct_xag_p90":           "xAG/90",
        "pct_shots_p90":         "Tirs/90",
        "pct_tirs_cadres_p90":   "Tirs cadrés/90",
        "pct_key_passes_p90":    "Passes clés/90",
        "pct_dribbles_p90":      "Dribbles/90",
        "pct_tackles_p90":       "Tacles/90",
        "pct_interceptions_p90": "Interceptions/90",
        "pct_degagements_p90":   "Dégagements/90",
        "pct_duels_aeriens_pct": "Duels aériens",
        "pct_passes_pct":        "Précision passes",
        "pct_saves_p90":         "Arrêts/90",
        "pct_goals_prevented":   "Buts évités",
        "pct_save_pct":          "% Arrêts",
        "pct_clean_sheets_pct":  "Clean sheets %",
        "pct_long_balls_pct":    "Passes longues %",
    }

    pcts = {}
    for col, label in PCT_LABELS.items():
        val = row.get(col)
        if val is not None and pd.notna(val):
            pcts[label] = float(val)

    if not pcts:
        return

    sorted_pcts = sorted(pcts.items(), key=lambda x: x[1], reverse=True)
    strengths   = [(l, v) for l, v in sorted_pcts if v >= 75][:3]
    weaknesses  = [(l, v) for l, v in reversed(sorted_pcts) if v <= 30][:3]

    col_s, col_w = st.columns(2)

    with col_s:
        render_html(f"""
            <div style="font-size:0.7rem; font-weight:700;
                        text-transform:uppercase; letter-spacing:2px;
                        color:#2DAD7E; margin-bottom:10px;">
                {icon('trending_up')} Points forts
            </div>
        """)
        items_html = "".join(
            f'<div class="strength-item">Top {100 - int(val)}% · {label}</div>'
            for label, val in strengths
        )
        if items_html:
            render_html(items_html)
        else:
            st.caption("—")

    with col_w:
        render_html(f"""
            <div style="font-size:0.7rem; font-weight:700;
                        text-transform:uppercase; letter-spacing:2px;
                        color:#E05252; margin-bottom:10px;">
                {icon('trending_down')} Axes d'amélioration
            </div>
        """)
        items_html = "".join(
            f'<div class="weakness-item">Bot {int(val)}% · {label}</div>'
            for label, val in weaknesses
        )
        if items_html:
            render_html(items_html)
        else:
            st.caption("—")


def render_similar_players(df_similar: pd.DataFrame):
    """Affiche les profils similaires."""
    if df_similar.empty:
        st.caption("Données insuffisantes.")
        return

    render_html(f"""
        <div style="font-size:0.7rem; font-weight:700;
                    text-transform:uppercase; letter-spacing:2px;
                    color:#8A8A8A; margin-bottom:10px;">
            {icon('group')} Profils similaires
        </div>
    """)

    cards_html = ""
    for _, row in df_similar.iterrows():
        pct = int(row["similarite"] * 100)
        cards_html += f"""
            <div class="similar-card">
                <div>
                    <div style="font-weight:600; font-size:0.9rem;">{row['joueur']}</div>
                    <div style="font-size:0.75rem; color:#8A8A8A;">{row['equipe']} · {row['ligue']}</div>
                </div>
                <div class="similar-pct">{pct}%</div>
            </div>
        """
    render_html(cards_html)


def stat_checkbox_selector(
    stats_disponibles: dict,
    min_sel: int = 4,
    max_sel: int = 8,
    key_prefix: str = "stat",
) -> list:
    """
    Interface de sélection de stats avec checkboxes et compteur.
    stats_disponibles = {"Catégorie": ["stat1", "stat2", ...]}
    Retourne la liste des stats sélectionnées.
    """
    selected = []
    total    = 0

    for categorie, stats in stats_disponibles.items():
        render_html(f'<div style="font-size:0.7rem; font-weight:700; '
                    f'text-transform:uppercase; letter-spacing:1.5px; '
                    f'color:#8A8A8A; margin:10px 0 6px 0;">{categorie}</div>')

        for stat in stats:
            checked = st.session_state.get(
                f"{key_prefix}_{stat}", total < min_sel
            )
            val = st.checkbox(stat, value=checked,
                              key=f"{key_prefix}_{stat}",
                              disabled=(
                                  not checked and total >= max_sel
                              ))
            if val:
                selected.append(stat)
                total += 1

    is_full  = total >= max_sel
    counter_class = "stat-counter full" if is_full else "stat-counter"
    render_html(f"""
        <div style="margin-top:8px; text-align:right;">
            <span class="{counter_class}">{total}/{max_sel} stats</span>
        </div>
    """)

    if total < min_sel:
        st.warning(f"Sélectionnez au moins {min_sel} stats.")

    return selected if total >= min_sel else []

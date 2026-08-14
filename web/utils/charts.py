"""
web/utils/charts.py — RadarPépites Streamlit app
Fonctions graphiques Plotly.

RADAR_AXES n'utilise QUE les colonnes réellement présentes dans
gold.vue_radar_joueur (9 percentiles côté joueur de champ : goals, xg,
assists, key_passes, dribbles, shots, tackles, interceptions, passes_pct).
Cette vue ne couvre pas les gardiens (pas de pct_saves_p90 etc.) — le radar
gardien n'est pas disponible via cette fonction, voir page Gardiens à la
place.
"""

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Couleurs RadarPépites
COLORS = {
    "primary":    "#1DB954",
    "secondary":  "#FF6B35",
    "background": "#0E1117",
    "card":       "#1E2130",
    "text":       "#FAFAFA",
    "grid":       "#2D3250",
}

# Axes radar par poste — restreints aux 9 pct_* réellement calculées dans
# gold.vue_radar_joueur. Les codes détaillés (CB, CM, AM, ...) sont mappés
# pour réutilisation future si la source de données s'enrichit, mais cette
# vue ne renvoie aujourd'hui que poste_principal générique (MF/DF/FW/GK).
RADAR_AXES = {
    "FW": ["pct_goals_p90", "pct_xg_p90", "pct_shots_p90",
           "pct_dribbles_p90", "pct_assists_p90", "pct_key_passes_p90"],
    "LW": ["pct_goals_p90", "pct_xg_p90", "pct_shots_p90",
           "pct_dribbles_p90", "pct_assists_p90", "pct_key_passes_p90"],
    "RW": ["pct_goals_p90", "pct_xg_p90", "pct_shots_p90",
           "pct_dribbles_p90", "pct_assists_p90", "pct_key_passes_p90"],
    "AM": ["pct_xg_p90", "pct_assists_p90", "pct_key_passes_p90",
           "pct_dribbles_p90", "pct_goals_p90", "pct_passes_pct"],
    "CM": ["pct_passes_pct", "pct_key_passes_p90", "pct_tackles_p90",
           "pct_interceptions_p90", "pct_xg_p90", "pct_assists_p90"],
    "MF": ["pct_passes_pct", "pct_key_passes_p90", "pct_tackles_p90",
           "pct_interceptions_p90", "pct_xg_p90", "pct_assists_p90"],
    "DM": ["pct_tackles_p90", "pct_interceptions_p90",
           "pct_passes_pct", "pct_key_passes_p90"],
    "CB": ["pct_tackles_p90", "pct_interceptions_p90",
           "pct_passes_pct", "pct_dribbles_p90"],
    "DF": ["pct_tackles_p90", "pct_interceptions_p90",
           "pct_passes_pct", "pct_dribbles_p90"],
    "LB": ["pct_key_passes_p90", "pct_tackles_p90", "pct_dribbles_p90",
           "pct_passes_pct", "pct_interceptions_p90", "pct_assists_p90"],
    "RB": ["pct_key_passes_p90", "pct_tackles_p90", "pct_dribbles_p90",
           "pct_passes_pct", "pct_interceptions_p90", "pct_assists_p90"],
}

# Postes non couverts par gold.vue_radar_joueur (pas de pct_* calculées)
RADAR_UNSUPPORTED = {"GK"}

RADAR_LABELS = {
    "pct_goals_p90":         "Buts/90",
    "pct_xg_p90":            "xG/90",
    "pct_assists_p90":       "Assists/90",
    "pct_shots_p90":         "Tirs/90",
    "pct_key_passes_p90":    "Passes clés/90",
    "pct_dribbles_p90":      "Dribbles/90",
    "pct_tackles_p90":       "Tacles/90",
    "pct_interceptions_p90": "Interceptions/90",
    "pct_passes_pct":        "Passes %",
}


def radar_chart(
    row: pd.Series,
    poste: str,
    color: str = None,
    title: str = "",
    show_moyenne: bool = True,
) -> go.Figure | None:
    """Radar chart pour un joueur de champ.
    row : ligne de gold.vue_radar_joueur avec les pct_*.
    Retourne None si le poste n'est pas couvert (ex: GK) — à gérer côté appelant.
    """
    if poste in RADAR_UNSUPPORTED or poste not in RADAR_AXES:
        return None

    axes  = RADAR_AXES[poste]
    vals  = [float(row.get(ax) or 0) for ax in axes]
    labs  = [RADAR_LABELS.get(ax, ax) for ax in axes]
    color = color or COLORS["primary"]

    vals_closed = vals + [vals[0]]
    labs_closed = labs + [labs[0]]

    fig = go.Figure()

    if show_moyenne:
        moy = [50] * len(labs)
        fig.add_trace(go.Scatterpolar(
            r=moy + [moy[0]],
            theta=labs_closed,
            fill="toself",
            fillcolor="rgba(255,255,255,0.03)",
            line=dict(color="rgba(255,255,255,0.2)", dash="dash"),
            name="Moyenne poste",
            hoverinfo="skip",
        ))

    fig.add_trace(go.Scatterpolar(
        r=vals_closed,
        theta=labs_closed,
        fill="toself",
        fillcolor=f"rgba({int(color[1:3],16)},{int(color[3:5],16)},{int(color[5:7],16)},0.25)",
        line=dict(color=color, width=2),
        name=title or "Joueur",
        hovertemplate="%{theta}<br>Percentile : %{r:.0f}<extra></extra>",
    ))

    fig.update_layout(
        polar=dict(
            bgcolor=COLORS["card"],
            radialaxis=dict(
                visible=True, range=[0, 100],
                tickfont=dict(size=9, color=COLORS["text"]),
                gridcolor=COLORS["grid"],
            ),
            angularaxis=dict(
                tickfont=dict(size=10, color=COLORS["text"]),
                gridcolor=COLORS["grid"],
            ),
        ),
        paper_bgcolor=COLORS["background"],
        plot_bgcolor=COLORS["background"],
        font=dict(color=COLORS["text"]),
        showlegend=True,
        legend=dict(bgcolor=COLORS["card"], bordercolor=COLORS["grid"]),
        title=dict(text=title, font=dict(size=14, color=COLORS["text"]), x=0.5),
        margin=dict(t=60, b=20, l=60, r=60),
        height=450,
    )
    return fig


def radar_comparaison(
    row_a: pd.Series,
    row_b: pd.Series,
    poste: str,
    name_a: str = "Joueur A",
    name_b: str = "Joueur B",
) -> go.Figure | None:
    """Radar superposé pour comparer 2 joueurs de champ. None si poste non couvert."""
    if poste in RADAR_UNSUPPORTED or poste not in RADAR_AXES:
        return None

    axes  = RADAR_AXES[poste]
    labs  = [RADAR_LABELS.get(ax, ax) for ax in axes]
    vals_a = [float(row_a.get(ax) or 0) for ax in axes]
    vals_b = [float(row_b.get(ax) or 0) for ax in axes]

    labs_c  = labs + [labs[0]]
    vals_ac = vals_a + [vals_a[0]]
    vals_bc = vals_b + [vals_b[0]]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=vals_ac, theta=labs_c, fill="toself",
        fillcolor="rgba(29,185,84,0.2)",
        line=dict(color=COLORS["primary"], width=2),
        name=name_a,
    ))
    fig.add_trace(go.Scatterpolar(
        r=vals_bc, theta=labs_c, fill="toself",
        fillcolor="rgba(255,107,53,0.2)",
        line=dict(color=COLORS["secondary"], width=2),
        name=name_b,
    ))

    fig.update_layout(
        polar=dict(
            bgcolor=COLORS["card"],
            radialaxis=dict(visible=True, range=[0, 100], gridcolor=COLORS["grid"]),
            angularaxis=dict(gridcolor=COLORS["grid"]),
        ),
        paper_bgcolor=COLORS["background"],
        font=dict(color=COLORS["text"]),
        showlegend=True,
        height=500,
        margin=dict(t=40, b=20, l=60, r=60),
    )
    return fig


def bar_top10(df: pd.DataFrame, title: str = "") -> go.Figure:
    """Bar chart horizontal Top 10 joueurs par Score Pépite."""
    df_plot = df.head(10).copy()
    df_plot = df_plot.sort_values("score_corrige", ascending=True)

    fig = go.Figure(go.Bar(
        x=df_plot["score_corrige"],
        y=df_plot["joueur"],
        orientation="h",
        marker=dict(
            color=df_plot["score_corrige"],
            colorscale=[[0, "#1a3a2a"], [0.5, "#1DB954"], [1, "#00ff88"]],
            showscale=False,
        ),
        text=df_plot["score_corrige"].round(1),
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>Score : %{x:.1f}<extra></extra>",
    ))

    fig.update_layout(
        title=dict(text=title, font=dict(size=14), x=0.5),
        paper_bgcolor=COLORS["background"],
        plot_bgcolor=COLORS["background"],
        font=dict(color=COLORS["text"]),
        xaxis=dict(range=[0, 105], gridcolor=COLORS["grid"]),
        yaxis=dict(gridcolor=COLORS["grid"]),
        height=400,
        margin=dict(l=20, r=60, t=50, b=20),
    )
    return fig


def scatter_xg_buts(df: pd.DataFrame) -> go.Figure:
    """Scatter plot xG/90 vs Buts/90 — identifier les finisseurs."""
    df_clean = df.dropna(subset=["xg_p90", "buts_p90"])

    fig = px.scatter(
        df_clean,
        x="xg_p90",
        y="buts_p90",
        color="ligue",
        size="score_corrige",
        hover_name="joueur",
        hover_data={"equipe": True, "age": True,
                    "score_corrige": ":.1f",
                    "xg_p90": ":.3f", "buts_p90": ":.3f"},
        labels={"xg_p90": "xG / 90 min", "buts_p90": "Buts / 90 min"},
        title="xG vs Buts — Identification des finisseurs U23",
    )

    max_val = max(
        df_clean["xg_p90"].max() if not df_clean.empty else 1,
        df_clean["buts_p90"].max() if not df_clean.empty else 1,
    )
    fig.add_shape(
        type="line", x0=0, y0=0, x1=max_val, y1=max_val,
        line=dict(color="rgba(255,255,255,0.3)", dash="dash"),
    )

    fig.update_layout(
        paper_bgcolor=COLORS["background"],
        plot_bgcolor=COLORS["card"],
        font=dict(color=COLORS["text"]),
        height=500,
    )
    return fig


def line_progression(df: pd.DataFrame, joueur: str) -> go.Figure:
    """Graphique de progression saison par saison."""
    if df.empty:
        return go.Figure()

    metriques = {
        "delta_goals_p90":   "Buts/90",
        "delta_xg_p90":      "xG/90",
        "delta_assists_p90": "Assists/90",
        "delta_rating":      "Rating",
    }

    fig = go.Figure()
    colors_list = [COLORS["primary"], COLORS["secondary"], "#4ECDC4", "#FFE66D"]

    for (col, label), color in zip(metriques.items(), colors_list):
        if col in df.columns:
            fig.add_trace(go.Bar(
                x=df["saison_curr"], y=df[col], name=label, marker_color=color,
            ))

    fig.update_layout(
        title=f"Progression de {joueur}",
        barmode="group",
        paper_bgcolor=COLORS["background"],
        plot_bgcolor=COLORS["card"],
        font=dict(color=COLORS["text"]),
        xaxis=dict(title="Saison", gridcolor=COLORS["grid"]),
        yaxis=dict(title="Delta vs saison précédente", gridcolor=COLORS["grid"],
                   zeroline=True, zerolinecolor="rgba(255,255,255,0.3)"),
        height=400,
        legend=dict(bgcolor=COLORS["card"]),
    )
    return fig

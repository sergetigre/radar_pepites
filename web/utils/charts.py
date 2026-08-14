import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np

COLORS = {
    "green": "#2DAD7E", "green_light": "#5DCBA0",
    "black": "#0A0A0A", "black_card": "#111111",
    "white": "#FFFFFF", "gray": "#8A8A8A",
    "border": "#1A1A1A", "orange": "#E05252",
}

LAYOUT_BASE = dict(
    paper_bgcolor="#0A0A0A",
    plot_bgcolor="#111111",
    font=dict(color="#FFFFFF", family="sans-serif"),
    margin=dict(t=50, b=30, l=30, r=30),
)

RADAR_AXES = {
    "GK":  ["pct_saves_p90","pct_goals_prevented","pct_save_pct",
             "pct_clean_sheets_pct","pct_long_balls_pct"],
    "CB":  ["pct_interceptions_p90","pct_tackles_p90",
             "pct_degagements_p90","pct_duels_aeriens_pct","pct_passes_pct"],
    "LB":  ["pct_key_passes_p90","pct_tackles_p90","pct_dribbles_p90",
             "pct_passes_pct","pct_interceptions_p90","pct_assists_p90"],
    "RB":  ["pct_key_passes_p90","pct_tackles_p90","pct_dribbles_p90",
             "pct_passes_pct","pct_interceptions_p90","pct_assists_p90"],
    "DM":  ["pct_tackles_p90","pct_interceptions_p90","pct_passes_pct",
             "pct_key_passes_p90","pct_degagements_p90"],
    "CM":  ["pct_passes_pct","pct_key_passes_p90","pct_tackles_p90",
             "pct_interceptions_p90","pct_xg_p90","pct_assists_p90"],
    "AM":  ["pct_xg_p90","pct_xag_p90","pct_key_passes_p90",
             "pct_assists_p90","pct_dribbles_p90","pct_goals_p90"],
    "LW":  ["pct_goals_p90","pct_xg_p90","pct_dribbles_p90",
             "pct_key_passes_p90","pct_assists_p90","pct_shots_p90"],
    "RW":  ["pct_goals_p90","pct_xg_p90","pct_dribbles_p90",
             "pct_key_passes_p90","pct_assists_p90","pct_shots_p90"],
    "FW":  ["pct_goals_p90","pct_xg_p90","pct_shots_p90",
             "pct_duels_aeriens_pct","pct_assists_p90","pct_dribbles_p90"],
    "MF":  ["pct_passes_pct","pct_key_passes_p90","pct_tackles_p90",
             "pct_interceptions_p90","pct_xg_p90","pct_assists_p90"],
    "DF":  ["pct_interceptions_p90","pct_tackles_p90",
             "pct_degagements_p90","pct_duels_aeriens_pct","pct_passes_pct"],
}

RADAR_LABELS = {
    "pct_goals_p90":         "Buts/90",
    "pct_xg_p90":            "xG/90",
    "pct_assists_p90":       "Assists/90",
    "pct_xag_p90":           "xAG/90",
    "pct_shots_p90":         "Tirs/90",
    "pct_tirs_cadres_p90":   "Tirs cadrés",
    "pct_key_passes_p90":    "Key Passes/90",
    "pct_dribbles_p90":      "Dribbles/90",
    "pct_tackles_p90":       "Tacles/90",
    "pct_interceptions_p90": "Interceptions/90",
    "pct_degagements_p90":   "Dégagements/90",
    "pct_duels_aeriens_pct": "Duels aériens",
    "pct_passes_pct":        "Précision passes",
    "pct_saves_p90":         "Arrêts/90",
    "pct_goals_prevented":   "Buts évités",
    "pct_save_pct":          "% Arrêts",
    "pct_clean_sheets_pct":  "Clean sheets",
    "pct_long_balls_pct":    "Passes longues",
}


def _radar_layout():
    return dict(
        polar=dict(
            bgcolor="#111111",
            radialaxis=dict(
                visible=True, range=[0, 100],
                tickfont=dict(size=8, color="#8A8A8A"),
                gridcolor="#1A1A1A",
                linecolor="#1A1A1A",
            ),
            angularaxis=dict(
                tickfont=dict(size=9, color="#FFFFFF"),
                gridcolor="#1A1A1A",
                linecolor="#1A1A1A",
            ),
        ),
        **LAYOUT_BASE,
        showlegend=True,
        legend=dict(
            bgcolor="#111111",
            bordercolor="#1A1A1A",
            font=dict(color="#FFFFFF"),
        ),
        height=420,
    )


def radar_single(row: pd.Series, poste: str,
                 name: str = "", color: str = "#2DAD7E") -> go.Figure:
    """Radar chart simple pour un joueur."""
    axes  = RADAR_AXES.get(poste, RADAR_AXES["CM"])
    vals  = [float(row.get(a, 0) or 0) for a in axes]
    labs  = [RADAR_LABELS.get(a, a) for a in axes]
    vc    = vals + [vals[0]]
    lc    = labs + [labs[0]]

    r, g, b = int(color[1:3],16), int(color[3:5],16), int(color[5:7],16)

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=[50]*(len(labs)+1), theta=lc, fill="toself",
        fillcolor="rgba(255,255,255,0.02)",
        line=dict(color="rgba(255,255,255,0.15)", dash="dash", width=1),
        name="Moyenne", hoverinfo="skip",
    ))
    fig.add_trace(go.Scatterpolar(
        r=vc, theta=lc, fill="toself",
        fillcolor=f"rgba({r},{g},{b},0.2)",
        line=dict(color=color, width=2),
        name=name or "Joueur",
        hovertemplate="%{theta}<br>Percentile : %{r:.0f}<extra></extra>",
    ))
    fig.update_layout(**_radar_layout())
    return fig


def radar_compare(
    row_a: pd.Series, row_b: pd.Series,
    poste: str, axes_override: list = None,
    name_a: str = "A", name_b: str = "B",
) -> go.Figure:
    """Radar comparatif 2 joueurs — axes personnalisables."""
    axes = axes_override or RADAR_AXES.get(poste, RADAR_AXES["CM"])
    labs = [RADAR_LABELS.get(a, a) for a in axes]
    va   = [float(row_a.get(a, 0) or 0) for a in axes]
    vb   = [float(row_b.get(a, 0) or 0) for a in axes]
    lc   = labs + [labs[0]]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=va+[va[0]], theta=lc, fill="toself",
        fillcolor="rgba(45,173,126,0.2)",
        line=dict(color="#2DAD7E", width=2), name=name_a,
    ))
    fig.add_trace(go.Scatterpolar(
        r=vb+[vb[0]], theta=lc, fill="toself",
        fillcolor="rgba(224,84,82,0.2)",
        line=dict(color="#E05252", width=2), name=name_b,
    ))
    layout = _radar_layout()
    layout["height"] = 480
    fig.update_layout(**layout)
    return fig


def bar_top10(df: pd.DataFrame, title: str = "") -> go.Figure:
    df_p = df.head(10).copy().sort_values("score_corrige", ascending=True)
    fig = go.Figure(go.Bar(
        x=df_p["score_corrige"], y=df_p["joueur"],
        orientation="h",
        marker=dict(
            color=df_p["score_corrige"],
            colorscale=[[0,"#0F5436"],[0.5,"#2DAD7E"],[1,"#5DCBA0"]],
        ),
        text=df_p["score_corrige"].round(1),
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>Score : %{x:.1f}<extra></extra>",
    ))
    fig.update_layout(
        title=dict(text=title, font=dict(size=13), x=0.5),
        xaxis=dict(range=[0,105], gridcolor="#1A1A1A"),
        yaxis=dict(gridcolor="#1A1A1A"),
        height=380,
        **LAYOUT_BASE,
    )
    return fig


def scatter_xg_buts(df: pd.DataFrame) -> go.Figure:
    df = df.dropna(subset=["xg_p90","buts_p90"])
    fig = px.scatter(
        df, x="xg_p90", y="buts_p90",
        color="ligue", size="score_corrige",
        size_max=18,
        hover_name="joueur",
        hover_data={"equipe":True,"age":True,
                    "score_corrige":":.1f",
                    "xg_p90":":.3f","buts_p90":":.3f",
                    "ligue":False},
        labels={"xg_p90":"xG / 90 min",
                "buts_p90":"Buts / 90 min"},
        color_discrete_sequence=[
            "#2DAD7E","#5DCBA0","#1A8A5A",
            "#0F5436","#8A8A8A","#E05252",
            "#E0B452","#4ECDC4","#FFE66D","#FF6B35",
        ],
    )
    if not df.empty:
        mx = max(df["xg_p90"].max(), df["buts_p90"].max()) * 1.1
        fig.add_shape(type="line", x0=0, y0=0, x1=mx, y1=mx,
                      line=dict(color="rgba(255,255,255,0.2)",
                                dash="dash", width=1))
    fig.update_layout(height=400, **LAYOUT_BASE)
    return fig


def line_progression(
    df: pd.DataFrame, joueur: str,
    metriques: list = None,
) -> go.Figure:
    """
    Graphique de progression — valeurs brutes par saison.
    L'utilisateur voit visuellement le delta.
    """
    if df.empty:
        return go.Figure()

    default_metrics = [
        ("buts_p90",   "Buts/90",    "#2DAD7E"),
        ("xg_p90",     "xG/90",      "#5DCBA0"),
        ("passes_dec_p90", "Assists/90", "#E0B452"),
        ("key_passes_p90", "KP/90",   "#4ECDC4"),
        ("dribbles_p90",   "Drib/90", "#FF6B35"),
        ("tackles_p90",    "Tac/90",  "#E05252"),
    ]
    metrics = metriques or default_metrics

    fig = go.Figure()
    for col, label, color in metrics:
        if col in df.columns:
            fig.add_trace(go.Scatter(
                x=df["saison_courte"],
                y=df[col],
                mode="lines+markers+text",
                name=label,
                line=dict(color=color, width=2),
                marker=dict(size=8, color=color),
                text=df[col].round(3),
                textposition="top center",
                textfont=dict(size=9, color=color),
                hovertemplate=(
                    f"<b>{label}</b><br>"
                    "%{x}<br>%{y:.3f}<extra></extra>"
                ),
            ))

    fig.update_layout(
        title=dict(text=f"Progression — {joueur}",
                   font=dict(size=13), x=0.5),
        xaxis=dict(title="Saison", gridcolor="#1A1A1A"),
        yaxis=dict(title="Valeur /90 min",
                   gridcolor="#1A1A1A",
                   zeroline=True,
                   zerolinecolor="#2DAD7E22"),
        height=420,
        legend=dict(bgcolor="#111111", bordercolor="#1A1A1A"),
        **LAYOUT_BASE,
    )
    return fig


def bar_progression(
    df: pd.DataFrame, joueur: str,
    metriques: list = None,
) -> go.Figure:
    """Barres groupées par saison — alternative à line_progression."""
    if df.empty:
        return go.Figure()

    cols = metriques or [
        "buts_p90","xg_p90","passes_dec_p90","key_passes_p90"
    ]
    labels = {
        "buts_p90": "Buts/90", "xg_p90": "xG/90",
        "passes_dec_p90": "Assists/90",
        "key_passes_p90": "KP/90",
        "dribbles_p90": "Drib/90",
        "tackles_p90": "Tac/90",
    }
    colors_list = [
        "#2DAD7E","#5DCBA0","#E0B452",
        "#4ECDC4","#FF6B35","#E05252",
    ]

    fig = go.Figure()
    for col, color in zip(cols, colors_list):
        if col in df.columns:
            fig.add_trace(go.Bar(
                x=df["saison_courte"],
                y=df[col],
                name=labels.get(col, col),
                marker_color=color,
            ))

    fig.update_layout(
        barmode="group",
        title=dict(text=joueur, font=dict(size=13), x=0.5),
        xaxis=dict(gridcolor="#1A1A1A"),
        yaxis=dict(gridcolor="#1A1A1A"),
        height=400,
        legend=dict(bgcolor="#111111"),
        **LAYOUT_BASE,
    )
    return fig

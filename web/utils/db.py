"""
web/utils/db.py — RadarPépites Streamlit app (v2)
Connexion Neon + requêtes vers public.fact_stats / dim_* / gold.*.

Toutes les requêtes utilisateur (recherche libre, filtres) sont paramétrées
via SQLAlchemy (bindparams) plutôt qu'interpolées en f-string, pour éviter
toute injection SQL depuis les champs de recherche.

Fiches gardiens (get_gk_fiche / get_progression_gk / search_gk) : sourcées
depuis public.fact_stats (poste_id='GK'), PAS silver.keepers_combined —
cette dernière ne porte ni les percentiles (pct_*) ni le score_pepite,
qui n'existent que dans fact_stats (calculés par etl/load/gold_builder.py).
Les colonnes _ss/_fb de keepers_combined sont donc exposées ici sous leur
nom fact_stats correspondant (ex: goals_prevented_ss -> goals_prevented),
et clean_sheets (comptage brut, non propagé dans fact_stats) est remplacé
par clean_sheets_pct (le seul disponible côté fact_stats).
"""

import os
from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from sqlalchemy import bindparam, create_engine, text

load_dotenv(Path(__file__).parent.parent.parent / "config" / ".env")


def get_database_url() -> str:
    try:
        if "DATABASE_URL" in st.secrets:
            return st.secrets["DATABASE_URL"]
    except Exception:
        pass
    url = os.getenv("DATABASE_URL")
    if not url:
        st.error("DATABASE_URL introuvable (ni st.secrets, ni config/.env).")
        st.stop()
    return url


@st.cache_resource
def get_engine():
    return create_engine(
        get_database_url(),
        pool_pre_ping=True,
        pool_recycle=280,
        connect_args={"connect_timeout": 10},
    )


# ── Référentiels ─────────────────────────────────────────────────────────
@st.cache_data(ttl=3600)
def get_ligues() -> pd.DataFrame:
    return pd.read_sql(text("""
        SELECT ligue_id, nom_complet, nom_court, pays, couleur_hex
        FROM public.dim_ligues ORDER BY rang_projet
    """), get_engine())


@st.cache_data(ttl=3600)
def get_saisons() -> list:
    df = pd.read_sql(text("""
        SELECT saison_id FROM public.dim_saisons ORDER BY saison_id DESC
    """), get_engine())
    return df["saison_id"].tolist()


@st.cache_data(ttl=3600)
def get_postes() -> pd.DataFrame:
    return pd.read_sql(text("""
        SELECT poste_id, poste_label_fr, famille
        FROM public.dim_postes
        WHERE poste_id != 'GK'
        ORDER BY famille, poste_id
    """), get_engine())


# ── Joueurs de champ ─────────────────────────────────────────────────────
@st.cache_data(ttl=1800)
def get_classement(saison: str, ligues: list, postes: list,
                    age_max: int, min_min: int) -> pd.DataFrame:
    if not ligues or not postes:
        return pd.DataFrame()
    stmt = text("""
        SELECT
            rang_global, rang_ligue, joueur_id,
            joueur, nom_court, poste_id, poste_label_fr,
            ligue, ligue_id, equipe, pays,
            age, nationalite_principale,
            score_pepite, score_corrige,
            buts_p90, xg_p90, assists_p90, xag_p90,
            key_passes_p90, dribbles_p90,
            tackles_p90, interceptions_p90,
            minutes, couleur_hex, rating_reference,
            has_fbref_data, has_sofascore_data
        FROM gold.vue_score_pepite_ranking
        WHERE est_u23 = TRUE
          AND saison_id = :saison
          AND minutes   >= :min_min
          AND age       <= :age_max
          AND ligue_id  IN :ligues
          AND poste_id  IN :postes
        ORDER BY score_corrige DESC NULLS LAST
    """).bindparams(bindparam("ligues", expanding=True), bindparam("postes", expanding=True))
    return pd.read_sql(stmt, get_engine(), params={
        "saison": saison, "min_min": min_min, "age_max": age_max,
        "ligues": ligues, "postes": postes,
    })


@st.cache_data(ttl=1800)
def search_joueurs(nom: str, saison: str = "") -> pd.DataFrame:
    """Recherche joueur par nom, toutes saisons confondues."""
    stmt = text("""
        SELECT DISTINCT
            joueur_id, joueur, equipe, ligue, ligue_id,
            poste_id, age, score_corrige, saison_id,
            CONCAT(joueur, ' — ', equipe, ' — ', saison_id) as joueur_saison
        FROM gold.vue_score_pepite_ranking
        WHERE LOWER(joueur) LIKE LOWER(:pattern)
        ORDER BY joueur, saison_id DESC
        LIMIT 30
    """)
    return pd.read_sql(stmt, get_engine(), params={"pattern": f"%{nom}%"})


@st.cache_data(ttl=1800)
def get_joueur_fiche(joueur_id: str, saison: str) -> pd.DataFrame:
    """Fiche complète d'un joueur de champ (public.fact_stats + dims)."""
    stmt = text("""
        SELECT
            f.stat_id, f.joueur_id, f.ligue_id, f.saison_id,
            f.poste_id, f.est_u23, f.age,
            f.minutes, f.matchs_joues, f.matchs_titulaire,
            f.buts, f.passes_dec, f.xg, f.xag, f.tirs, f.tirs_cadres,
            f.buts_p90, f.passes_dec_p90, f.xg_p90, f.xag_p90,
            f.tirs_p90, f.tirs_cadres_p90,
            f.dribbles_p90, f.key_passes_p90,
            f.tackles_p90, f.interceptions_p90,
            f.degagements_p90, f.duels_aeriens_pct, f.passes_pct,
            f.pct_goals_p90, f.pct_xg_p90,
            f.pct_assists_p90, f.pct_xag_p90,
            f.pct_shots_p90, f.pct_tirs_cadres_p90,
            f.pct_key_passes_p90, f.pct_dribbles_p90,
            f.pct_tackles_p90, f.pct_interceptions_p90,
            f.pct_degagements_p90, f.pct_duels_aeriens_pct,
            f.pct_passes_pct,
            f.score_pepite, f.score_pepite_corrige,
            f.score_rang_ligue, f.score_rang_global,
            f.rating, f.has_fbref_data, f.has_sofascore_data,
            j.nom_complet, j.nom_court, j.date_naissance,
            j.nationalite_principale, j.poste_principal, j.poste_detail,
            j.pied_dominant, j.taille_cm,
            e.nom_complet as equipe,
            l.nom_complet as ligue, l.nom_court as ligue_court, l.couleur_hex,
            s.saison_courte
        FROM public.fact_stats f
        JOIN public.dim_joueurs j ON f.joueur_id = j.joueur_id
        JOIN public.dim_equipes e ON f.equipe_id = e.equipe_id
        JOIN public.dim_ligues  l ON f.ligue_id  = l.ligue_id
        JOIN public.dim_saisons s ON f.saison_id = s.saison_id
        WHERE f.joueur_id = :joueur_id AND f.saison_id = :saison
        LIMIT 1
    """)
    return pd.read_sql(stmt, get_engine(), params={"joueur_id": joueur_id, "saison": saison})


@st.cache_data(ttl=1800)
def get_profils_similaires(joueur_id: str, saison: str, poste: str, n: int = 3) -> pd.DataFrame:
    """Similarité cosinus entre le joueur cible et les autres joueurs du même poste."""
    stmt = text("""
        SELECT
            f.joueur_id, j.nom_complet as joueur,
            e.nom_complet as equipe, l.nom_complet as ligue,
            f.pct_goals_p90, f.pct_xg_p90,
            f.pct_assists_p90, f.pct_xag_p90,
            f.pct_shots_p90, f.pct_key_passes_p90,
            f.pct_dribbles_p90, f.pct_tackles_p90,
            f.pct_interceptions_p90, f.pct_passes_pct
        FROM public.fact_stats f
        JOIN public.dim_joueurs j ON f.joueur_id = j.joueur_id
        JOIN public.dim_equipes e ON f.equipe_id = e.equipe_id
        JOIN public.dim_ligues  l ON f.ligue_id  = l.ligue_id
        WHERE f.saison_id = :saison AND f.poste_id = :poste
          AND f.minutes >= 450 AND f.score_pepite IS NOT NULL
    """)
    df = pd.read_sql(stmt, get_engine(), params={"saison": saison, "poste": poste})
    if df.empty or joueur_id not in df["joueur_id"].values:
        return pd.DataFrame()

    cols_pct = [c for c in df.columns if c.startswith("pct_")]
    df[cols_pct] = df[cols_pct].fillna(50)

    target = df[df["joueur_id"] == joueur_id][cols_pct].values[0]
    others = df[df["joueur_id"] != joueur_id].copy()

    import numpy as np

    def cosine_sim(a, b):
        denom = np.linalg.norm(a) * np.linalg.norm(b)
        return float(np.dot(a, b) / denom) if denom > 0 else 0.0

    others["similarite"] = others[cols_pct].apply(lambda row: cosine_sim(target, row.values), axis=1)
    return (
        others.sort_values("similarite", ascending=False)
        .head(n)[["joueur", "equipe", "ligue", "similarite"]]
        .reset_index(drop=True)
    )


@st.cache_data(ttl=1800)
def get_progression_joueur(joueur_id: str) -> pd.DataFrame:
    stmt = text("""
        SELECT
            f.saison_id, s.saison_courte,
            f.minutes, f.matchs_joues,
            f.buts_p90, f.xg_p90, f.passes_dec_p90, f.xag_p90,
            f.tirs_cadres_p90, f.key_passes_p90,
            f.dribbles_p90, f.tackles_p90, f.interceptions_p90,
            f.score_pepite_corrige, f.rating
        FROM public.fact_stats f
        JOIN public.dim_saisons s ON f.saison_id = s.saison_id
        WHERE f.joueur_id = :joueur_id
        ORDER BY f.saison_id ASC
    """)
    return pd.read_sql(stmt, get_engine(), params={"joueur_id": joueur_id})


# ── Gardiens ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=1800)
def get_classement_gk(saison: str, ligues: list, min_min: int) -> pd.DataFrame:
    """Classement gardiens (gold.vue_top_u23_gk — listing seulement, pas de percentiles)."""
    if not ligues:
        return pd.DataFrame()
    stmt = text("""
        SELECT *
        FROM gold.vue_top_u23_gk
        WHERE saison_id = :saison AND ligue_id IN :ligues
          AND minutes_ss >= :min_min
        ORDER BY saves_p90 DESC NULLS LAST
    """).bindparams(bindparam("ligues", expanding=True))
    return pd.read_sql(stmt, get_engine(), params={
        "saison": saison, "ligues": ligues, "min_min": min_min,
    })


@st.cache_data(ttl=1800)
def search_gk(nom: str) -> pd.DataFrame:
    """Recherche gardien par nom (public.fact_stats, poste_id='GK')."""
    stmt = text("""
        SELECT DISTINCT
            f.joueur_id, j.nom_complet as joueur,
            e.nom_complet as equipe, f.ligue_id, f.saison_id,
            CONCAT(j.nom_complet, ' — ', e.nom_complet, ' — ', f.saison_id) as joueur_saison
        FROM public.fact_stats f
        JOIN public.dim_joueurs j ON f.joueur_id = j.joueur_id
        JOIN public.dim_equipes e ON f.equipe_id = e.equipe_id
        WHERE f.poste_id = 'GK' AND LOWER(j.nom_complet) LIKE LOWER(:pattern)
        ORDER BY j.nom_complet, f.saison_id DESC
        LIMIT 30
    """)
    return pd.read_sql(stmt, get_engine(), params={"pattern": f"%{nom}%"})


@st.cache_data(ttl=1800)
def get_gk_fiche(joueur_id: str, saison: str) -> pd.DataFrame:
    """Fiche complète d'un gardien (public.fact_stats, poste_id='GK' + dims).
    Sourcée de fact_stats (pas keepers_combined) pour disposer des
    percentiles et du score_pepite.
    """
    stmt = text("""
        SELECT
            f.stat_id, f.joueur_id, f.ligue_id, f.saison_id,
            f.est_u23, f.age,
            f.minutes, f.matchs_joues,
            f.saves_p90, f.goals_prevented, f.save_pct, f.clean_sheets_pct,
            f.long_balls_pct, f.rating,
            f.pct_saves_p90, f.pct_goals_prevented, f.pct_save_pct,
            f.pct_clean_sheets_pct, f.pct_long_balls_pct,
            f.score_pepite, f.score_pepite_corrige,
            f.score_rang_ligue, f.score_rang_global,
            f.has_fbref_data, f.has_sofascore_data,
            j.nom_complet, j.nom_court, j.date_naissance,
            j.nationalite_principale, j.pied_dominant, j.taille_cm,
            e.nom_complet as equipe,
            l.nom_complet as ligue, l.nom_court as ligue_court, l.couleur_hex,
            s.saison_courte
        FROM public.fact_stats f
        JOIN public.dim_joueurs j ON f.joueur_id = j.joueur_id
        JOIN public.dim_equipes e ON f.equipe_id = e.equipe_id
        JOIN public.dim_ligues  l ON f.ligue_id  = l.ligue_id
        JOIN public.dim_saisons s ON f.saison_id = s.saison_id
        WHERE f.joueur_id = :joueur_id AND f.saison_id = :saison
          AND f.poste_id = 'GK'
        LIMIT 1
    """)
    return pd.read_sql(stmt, get_engine(), params={"joueur_id": joueur_id, "saison": saison})


@st.cache_data(ttl=1800)
def get_progression_gk(joueur_id: str) -> pd.DataFrame:
    stmt = text("""
        SELECT
            f.saison_id, s.saison_courte,
            f.minutes, f.matchs_joues,
            f.saves_p90, f.goals_prevented, f.save_pct, f.clean_sheets_pct,
            f.rating, f.has_fbref_data, f.score_pepite_corrige
        FROM public.fact_stats f
        JOIN public.dim_saisons s ON f.saison_id = s.saison_id
        WHERE f.joueur_id = :joueur_id AND f.poste_id = 'GK'
        ORDER BY f.saison_id ASC
    """)
    return pd.read_sql(stmt, get_engine(), params={"joueur_id": joueur_id})

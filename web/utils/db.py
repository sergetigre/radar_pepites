"""
web/utils/db.py — RadarPépites Streamlit app
Connexion Neon + requêtes vers les vues gold.* / tables public.dim_*.

Toutes les requêtes utilisateur (recherche, filtres) sont paramétrées via
SQLAlchemy (bindparams) plutôt qu'interpolées dans la chaîne SQL, pour
éviter toute injection SQL depuis les champs de recherche libres.
"""

import os
from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from sqlalchemy import bindparam, create_engine, text

# Charge .env depuis config/ du projet parent (dev local).
# En déploiement Streamlit Cloud, st.secrets prend le pas (voir get_database_url).
load_dotenv(Path(__file__).parent.parent.parent / "config" / ".env")


def get_database_url() -> str:
    try:
        if "DATABASE_URL" in st.secrets:
            return st.secrets["DATABASE_URL"]
    except Exception:
        pass  # pas de secrets.toml en local, on retombe sur .env
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL introuvable (ni st.secrets, ni config/.env)")
    return url


@st.cache_resource
def get_engine():
    """Connexion unique à Neon — réutilisée par toute l'app."""
    return create_engine(
        get_database_url(),
        pool_pre_ping=True,
        pool_recycle=280,
        connect_args={"connect_timeout": 10},
    )


@st.cache_data(ttl=3600)
def get_ligues() -> pd.DataFrame:
    """Référentiel des 10 ligues."""
    query = text("""
        SELECT ligue_id, nom_complet, nom_court, pays, couleur_hex
        FROM public.dim_ligues
        ORDER BY rang_projet
    """)
    return pd.read_sql(query, get_engine())


@st.cache_data(ttl=3600)
def get_saisons() -> list:
    """Liste des saisons disponibles, plus récente d'abord."""
    query = text("""
        SELECT saison_id
        FROM public.dim_saisons
        ORDER BY saison_id DESC
    """)
    df = pd.read_sql(query, get_engine())
    return df["saison_id"].tolist()


@st.cache_data(ttl=3600)
def get_postes() -> pd.DataFrame:
    """Référentiel des postes (11 codes détaillés)."""
    query = text("""
        SELECT poste_id, poste_label_fr, famille
        FROM public.dim_postes
        ORDER BY famille, poste_id
    """)
    return pd.read_sql(query, get_engine())


@st.cache_data(ttl=1800)
def get_classement(
    saison: str,
    ligues: list = None,
    postes: list = None,
    age_max: int = 23,
    min_minutes: int = 450,
) -> pd.DataFrame:
    """Classement Score Pépite filtré (gold.vue_score_pepite_ranking)."""
    conditions = [
        "est_u23 = TRUE",
        "saison_id = :saison",
        "minutes >= :min_minutes",
        "poste_id != 'GK'",
        "age <= :age_max",
    ]
    params = {"saison": saison, "min_minutes": min_minutes, "age_max": age_max}

    query_str = """
        SELECT
            rang_global, rang_ligue,
            joueur, poste_id, poste_label_fr,
            ligue, equipe, pays,
            age, score_pepite, score_corrige,
            buts_p90, xg_p90, assists_p90, xag_p90,
            key_passes_p90, dribbles_p90,
            tackles_p90, interceptions_p90,
            minutes, rating_reference, couleur_hex
        FROM gold.vue_score_pepite_ranking
        WHERE {where}
        ORDER BY score_corrige DESC
    """
    stmt = text(query_str.format(where=" AND ".join(conditions)))

    if ligues:
        conditions.insert(0, "ligue_id IN :ligues")
        stmt = text(query_str.format(where=" AND ".join(conditions))).bindparams(
            bindparam("ligues", expanding=True)
        )
        params["ligues"] = ligues
    if postes:
        conditions.append("poste_id IN :postes")
        stmt = text(query_str.format(where=" AND ".join(conditions)))
        binds = []
        if ligues:
            binds.append(bindparam("ligues", expanding=True))
        binds.append(bindparam("postes", expanding=True))
        stmt = stmt.bindparams(*binds)
        params["postes"] = postes

    return pd.read_sql(stmt, get_engine(), params=params)


@st.cache_data(ttl=1800)
def get_joueur_radar(player_id_ss: str, saison: str) -> pd.DataFrame:
    """Données radar (percentiles) d'un joueur de champ.
    NB: gold.vue_radar_joueur ne couvre que les joueurs de champ — pas de
    colonnes pct_* gardien. Utiliser get_gk_classement() pour les GK.
    """
    query = text("""
        SELECT *
        FROM gold.vue_radar_joueur
        WHERE player_id_ss = :player_id_ss
          AND saison_id = :saison
        LIMIT 1
    """)
    return pd.read_sql(query, get_engine(), params={
        "player_id_ss": int(player_id_ss), "saison": saison,
    })


@st.cache_data(ttl=1800)
def get_progression(player_id_ss: str) -> pd.DataFrame:
    """Progression saison par saison d'un joueur (gold.vue_progression_saison)."""
    query = text("""
        SELECT *
        FROM gold.vue_progression_saison
        WHERE player_id_ss = :player_id_ss
        ORDER BY saison_curr
    """)
    return pd.read_sql(query, get_engine(), params={"player_id_ss": int(player_id_ss)})


@st.cache_data(ttl=1800)
def get_gk_classement(saison: str) -> pd.DataFrame:
    """Classement des gardiens U23 (gold.vue_top_u23_gk)."""
    query = text("""
        SELECT *
        FROM gold.vue_top_u23_gk
        WHERE saison_id = :saison
        ORDER BY saves_p90 DESC NULLS LAST
    """)
    return pd.read_sql(query, get_engine(), params={"saison": saison})


@st.cache_data(ttl=1800)
def search_joueurs(nom: str, saison: str) -> pd.DataFrame:
    """Recherche un joueur par nom (gold.vue_score_pepite_ranking).
    joueur_id renvoyé ici correspond au player_id_ss des autres vues
    (même identifiant, juste casté en texte côté public.dim_joueurs).
    """
    query = text("""
        SELECT DISTINCT ON (joueur_id) joueur_id, joueur, equipe, ligue,
                        poste_id, age, score_corrige, minutes
        FROM gold.vue_score_pepite_ranking
        WHERE LOWER(joueur) LIKE LOWER(:pattern)
          AND saison_id = :saison
        ORDER BY joueur_id, score_corrige DESC NULLS LAST
        LIMIT 20
    """)
    pattern = f"%{nom}%"
    return pd.read_sql(query, get_engine(), params={"pattern": pattern, "saison": saison})

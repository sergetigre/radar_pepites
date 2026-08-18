"""
web/utils/search.py — Recherche autocomplete live (streamlit-searchbox).

Réutilise search_joueurs()/search_gk() de db.py — déjà sourcées correctement
(gold.vue_score_pepite_ranking pour les joueurs, public.fact_stats
poste_id='GK' pour les gardiens — pas silver.keepers_combined, qui n'a ni
percentiles ni score_pepite).
"""

from streamlit_searchbox import st_searchbox

from utils.db import (
    search_gk, search_gk_unique, search_joueurs, search_joueurs_unique,
)


def _search_joueurs_fn(searchterm: str):
    if not searchterm or len(searchterm) < 2:
        return []
    df = search_joueurs(searchterm)
    if df.empty:
        return []
    return [
        (row["joueur_saison"],
         f"{row['joueur_id']}::{row['saison_id']}::{row['joueur']}")
        for _, row in df.iterrows()
    ]


def _search_gk_fn(searchterm: str):
    if not searchterm or len(searchterm) < 2:
        return []
    df = search_gk(searchterm)
    if df.empty:
        return []
    return [
        (row["joueur_saison"],
         f"{row['joueur_id']}::{row['saison_id']}::{row['joueur']}")
        for _, row in df.iterrows()
    ]


def _search_joueurs_unique_fn(searchterm: str):
    if not searchterm or len(searchterm) < 2:
        return []
    df = search_joueurs_unique(searchterm)
    if df.empty:
        return []
    return [
        (row["joueur"], f"{row['joueur_id']}::{row['joueur']}")
        for _, row in df.iterrows()
    ]


def _search_gk_unique_fn(searchterm: str):
    if not searchterm or len(searchterm) < 2:
        return []
    df = search_gk_unique(searchterm)
    if df.empty:
        return []
    return [
        (row["joueur"], f"{row['joueur_id']}::{row['joueur']}")
        for _, row in df.iterrows()
    ]


def player_searchbox(key: str, placeholder: str = "Rechercher un joueur...",
                     default_searchterm: str = ""):
    """Barre de recherche joueur avec suggestions live (dès 2 caractères) —
    une entrée par (joueur, saison, club).
    Retourne (joueur_id, saison_id, nom_joueur) ou (None, None, None)."""
    selected = st_searchbox(
        _search_joueurs_fn,
        key=key,
        placeholder=placeholder,
        default_searchterm=default_searchterm,
        clear_on_submit=False,
    )
    if not selected:
        return None, None, None
    joueur_id, saison_id, nom = selected.split("::", 2)
    return joueur_id, saison_id, nom


def gk_searchbox(key: str, placeholder: str = "Rechercher un gardien...",
                 default_searchterm: str = ""):
    """Barre de recherche gardien avec suggestions live —
    une entrée par (gardien, saison, club).
    Retourne (joueur_id, saison_id, nom_gk) ou (None, None, None)."""
    selected = st_searchbox(
        _search_gk_fn,
        key=key,
        placeholder=placeholder,
        default_searchterm=default_searchterm,
        clear_on_submit=False,
    )
    if not selected:
        return None, None, None
    joueur_id, saison_id, nom = selected.split("::", 2)
    return joueur_id, saison_id, nom


def player_progression_searchbox(key: str,
                                 placeholder: str = "Rechercher un joueur...",
                                 default_searchterm: str = ""):
    """Barre de recherche joueur pour les pages Progression : une seule
    entrée par joueur (pas de doublon par saison/club, non pertinent quand
    on affiche l'évolution sur plusieurs saisons).
    Retourne (joueur_id, nom_joueur) ou (None, None)."""
    selected = st_searchbox(
        _search_joueurs_unique_fn,
        key=key,
        placeholder=placeholder,
        default_searchterm=default_searchterm,
        clear_on_submit=False,
    )
    if not selected:
        return None, None
    joueur_id, nom = selected.split("::", 1)
    return joueur_id, nom


def gk_progression_searchbox(key: str,
                             placeholder: str = "Rechercher un gardien...",
                             default_searchterm: str = ""):
    """Équivalent gardien de player_progression_searchbox."""
    selected = st_searchbox(
        _search_gk_unique_fn,
        key=key,
        placeholder=placeholder,
        default_searchterm=default_searchterm,
        clear_on_submit=False,
    )
    if not selected:
        return None, None
    joueur_id, nom = selected.split("::", 1)
    return joueur_id, nom

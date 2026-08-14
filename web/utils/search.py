"""
web/utils/search.py — Recherche autocomplete live (streamlit-searchbox).

Réutilise search_joueurs()/search_gk() de db.py — déjà sourcées correctement
(gold.vue_score_pepite_ranking pour les joueurs, public.fact_stats
poste_id='GK' pour les gardiens — pas silver.keepers_combined, qui n'a ni
percentiles ni score_pepite).
"""

from streamlit_searchbox import st_searchbox

from utils.db import search_gk, search_joueurs


def _search_joueurs_fn(searchterm: str):
    if not searchterm or len(searchterm) < 2:
        return []
    df = search_joueurs(searchterm)
    if df.empty:
        return []
    return [
        (row["joueur_saison"], f"{row['joueur_id']}::{row['saison_id']}")
        for _, row in df.iterrows()
    ]


def _search_gk_fn(searchterm: str):
    if not searchterm or len(searchterm) < 2:
        return []
    df = search_gk(searchterm)
    if df.empty:
        return []
    return [
        (row["joueur_saison"], f"{row['joueur_id']}::{row['saison_id']}")
        for _, row in df.iterrows()
    ]


def player_searchbox(key: str, placeholder: str = "Rechercher un joueur...",
                     default_searchterm: str = ""):
    """Barre de recherche joueur avec suggestions live (dès 2 caractères).
    Retourne (joueur_id, saison_id, label) ou (None, None, None)."""
    selected = st_searchbox(
        _search_joueurs_fn,
        key=key,
        placeholder=placeholder,
        default_searchterm=default_searchterm,
        clear_on_submit=False,
    )
    if not selected:
        return None, None, None
    joueur_id, saison_id = selected.split("::")
    return joueur_id, saison_id, selected


def gk_searchbox(key: str, placeholder: str = "Rechercher un gardien...",
                 default_searchterm: str = ""):
    """Barre de recherche gardien avec suggestions live.
    Retourne (joueur_id, saison_id, label) ou (None, None, None)."""
    selected = st_searchbox(
        _search_gk_fn,
        key=key,
        placeholder=placeholder,
        default_searchterm=default_searchterm,
        clear_on_submit=False,
    )
    if not selected:
        return None, None, None
    joueur_id, saison_id = selected.split("::")
    return joueur_id, saison_id, selected

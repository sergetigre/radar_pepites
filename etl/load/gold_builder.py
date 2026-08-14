# =============================================================
# RadarPépites — Gold Builder — Score Pépite
# Fichier  : etl/load/gold_builder.py
# Rôle     : Calcule le Score Pépite RadarPépites pour chaque
#            joueur dans public.fact_stats
#            - Percentiles par poste x saison
#            - Pondération par poste (poids définis)
#            - Correction par niveau de ligue
#            - Rangs ligue et global
# Usage    : python etl/load/gold_builder.py
# =============================================================

import os
import sys
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from sqlalchemy import text

# ---------------------------------------------------------------------------
# Chemins et configuration
# ---------------------------------------------------------------------------

DIR_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(DIR_ROOT / "etl" / "transform"))
from silver_transformer import get_engine  # noqa: E402 — pool_pre_ping/retry Neon

engine = get_engine()

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

DIR_LOGS = DIR_ROOT / "logs"
DIR_LOGS.mkdir(exist_ok=True)

log_file = DIR_LOGS / f"gold_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.stream.reconfigure(encoding="utf-8", errors="replace")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        stream_handler,
        logging.FileHandler(log_file, encoding="utf-8"),
    ],
)
log = logging.getLogger("RadarPepites.GoldBuilder")

# ---------------------------------------------------------------------------
# Poids par poste — rating Sofascore EXCLU
# ---------------------------------------------------------------------------

POIDS_PAR_POSTE = {
    "GK": {
        "pct_goals_prevented":  0.25,
        "pct_save_pct":         0.20,
        "pct_saves_p90":        0.15,
        "pct_clean_sheets_pct": 0.15,
        "pct_long_balls_pct":   0.10,
        "pct_passes_pct":       0.15,
    },
    "CB": {
        "pct_interceptions_p90": 0.25,
        "pct_tackles_p90":       0.20,
        "pct_degagements_p90":   0.18,
        "pct_duels_aeriens_pct": 0.20,
        "pct_passes_pct":        0.17,
    },
    "LB": {
        "pct_key_passes_p90":    0.22,
        "pct_tackles_p90":       0.18,
        "pct_dribbles_p90":      0.18,
        "pct_passes_pct":        0.17,
        "pct_interceptions_p90": 0.15,
        "pct_assists_p90":       0.10,
    },
    "RB": {
        "pct_key_passes_p90":    0.22,
        "pct_tackles_p90":       0.18,
        "pct_dribbles_p90":      0.18,
        "pct_passes_pct":        0.17,
        "pct_interceptions_p90": 0.15,
        "pct_assists_p90":       0.10,
    },
    "DM": {
        "pct_tackles_p90":       0.25,
        "pct_interceptions_p90": 0.25,
        "pct_passes_pct":        0.25,
        "pct_key_passes_p90":    0.13,
        "pct_degagements_p90":   0.12,
    },
    "CM": {
        "pct_passes_pct":        0.22,
        "pct_key_passes_p90":    0.22,
        "pct_tackles_p90":       0.18,
        "pct_interceptions_p90": 0.18,
        "pct_xg_p90":            0.10,
        "pct_assists_p90":       0.10,
    },
    "AM": {
        "pct_xg_p90":            0.22,
        "pct_xag_p90":           0.22,
        "pct_key_passes_p90":    0.18,
        "pct_assists_p90":       0.18,
        "pct_dribbles_p90":      0.10,
        "pct_goals_p90":         0.10,
    },
    "LW": {
        "pct_goals_p90":         0.22,
        "pct_xg_p90":            0.20,
        "pct_dribbles_p90":      0.20,
        "pct_key_passes_p90":    0.15,
        "pct_assists_p90":       0.13,
        "pct_shots_p90":         0.10,
    },
    "RW": {
        "pct_goals_p90":         0.22,
        "pct_xg_p90":            0.20,
        "pct_dribbles_p90":      0.20,
        "pct_key_passes_p90":    0.15,
        "pct_assists_p90":       0.13,
        "pct_shots_p90":         0.10,
    },
    "FW": {
        "pct_goals_p90":         0.28,
        "pct_xg_p90":            0.22,
        "pct_shots_p90":         0.15,
        "pct_duels_aeriens_pct": 0.15,
        "pct_assists_p90":       0.10,
        "pct_dribbles_p90":      0.10,
    },
    "MF":    "CM",
    "DF":    "CB",
    "FW,MF": "AM",
    "MF,FW": "CM",
    "DF,MF": "DM",
    "DF,FW": "FW",
}

COEFF_LIGUE = {
    "ENG": 1.00, "ESP": 0.98, "GER": 0.96,
    "ITA": 0.94, "FRA": 0.92, "POR": 0.89,
    "NED": 0.86, "BEL": 0.83, "TUR": 0.80, "AUT": 0.77,
}

MIN_MINUTES_JOUEURS = 450
MIN_MINUTES_GK      = 270

# ---------------------------------------------------------------------------
# Fonctions
# ---------------------------------------------------------------------------

def prepare_columns():
    log.info("Preparation des colonnes Score Pepite...")
    sql = """
        ALTER TABLE public.fact_stats
            ADD COLUMN IF NOT EXISTS pct_goals_p90          FLOAT,
            ADD COLUMN IF NOT EXISTS pct_xg_p90             FLOAT,
            ADD COLUMN IF NOT EXISTS pct_assists_p90        FLOAT,
            ADD COLUMN IF NOT EXISTS pct_xag_p90            FLOAT,
            ADD COLUMN IF NOT EXISTS pct_shots_p90          FLOAT,
            ADD COLUMN IF NOT EXISTS pct_tirs_cadres_p90    FLOAT,
            ADD COLUMN IF NOT EXISTS pct_key_passes_p90     FLOAT,
            ADD COLUMN IF NOT EXISTS pct_dribbles_p90       FLOAT,
            ADD COLUMN IF NOT EXISTS pct_tackles_p90        FLOAT,
            ADD COLUMN IF NOT EXISTS pct_interceptions_p90  FLOAT,
            ADD COLUMN IF NOT EXISTS pct_degagements_p90    FLOAT,
            ADD COLUMN IF NOT EXISTS pct_duels_aeriens_pct  FLOAT,
            ADD COLUMN IF NOT EXISTS pct_passes_pct         FLOAT,
            ADD COLUMN IF NOT EXISTS pct_goals_prevented    FLOAT,
            ADD COLUMN IF NOT EXISTS pct_save_pct           FLOAT,
            ADD COLUMN IF NOT EXISTS pct_saves_p90          FLOAT,
            ADD COLUMN IF NOT EXISTS pct_clean_sheets_pct   FLOAT,
            ADD COLUMN IF NOT EXISTS pct_long_balls_pct     FLOAT,
            ADD COLUMN IF NOT EXISTS score_pepite           FLOAT,
            ADD COLUMN IF NOT EXISTS score_pepite_corrige   FLOAT,
            ADD COLUMN IF NOT EXISTS score_rang_ligue       INT,
            ADD COLUMN IF NOT EXISTS score_rang_global      INT;
    """
    with engine.connect() as conn:
        conn.execute(text(sql))
        conn.commit()
    log.info("  Colonnes creees / verifiees")


def load_fact_stats() -> pd.DataFrame:
    query = """
        SELECT
            f.stat_id, f.joueur_id, f.ligue_id, f.saison_id,
            f.poste_id, f.est_u23, f.minutes, f.minutes_p90,
            f.matchs_joues, f.matchs_titulaire,
            f.buts_p90, f.passes_dec_p90, f.xg_p90, f.xag_p90,
            f.tirs_p90, f.tirs_cadres_p90,
            f.dribbles_p90, f.key_passes_p90,
            f.tackles_p90, f.interceptions_p90,
            f.degagements_p90, f.duels_aeriens_pct, f.passes_pct,
            f.saves_p90, f.goals_prevented, f.save_pct,
            f.clean_sheets_pct, f.long_balls_pct,
            f.rating
        FROM public.fact_stats f
        WHERE f.poste_id IS NOT NULL
    """
    df = pd.read_sql(query, engine)
    log.info(f"  {len(df)} lignes lues depuis public.fact_stats")
    return df


def compute_percentiles(df: pd.DataFrame) -> pd.DataFrame:
    mapping = {
        "buts_p90":          "pct_goals_p90",
        "xg_p90":            "pct_xg_p90",
        "passes_dec_p90":    "pct_assists_p90",
        "xag_p90":           "pct_xag_p90",
        "tirs_p90":          "pct_shots_p90",
        "tirs_cadres_p90":   "pct_tirs_cadres_p90",
        "key_passes_p90":    "pct_key_passes_p90",
        "dribbles_p90":      "pct_dribbles_p90",
        "tackles_p90":       "pct_tackles_p90",
        "interceptions_p90": "pct_interceptions_p90",
        "degagements_p90":   "pct_degagements_p90",
        "duels_aeriens_pct": "pct_duels_aeriens_pct",
        "passes_pct":        "pct_passes_pct",
        "goals_prevented":   "pct_goals_prevented",
        "save_pct":          "pct_save_pct",
        "saves_p90":         "pct_saves_p90",
        "clean_sheets_pct":  "pct_clean_sheets_pct",
        "long_balls_pct":    "pct_long_balls_pct",
    }

    mask_joueurs  = df["minutes"] >= MIN_MINUTES_JOUEURS
    mask_gk       = (df["poste_id"] == "GK") & (df["minutes"] >= MIN_MINUTES_GK)
    mask_eligible = mask_joueurs | mask_gk

    for col_brut, col_pct in mapping.items():
        df[col_pct] = np.nan
        if col_brut in df.columns:
            idx = df[mask_eligible].index
            df.loc[idx, col_pct] = (
                df.loc[idx]
                .groupby(["poste_id", "saison_id"])[col_brut]
                .rank(pct=True, na_option="keep") * 100
            )
        else:
            log.warning(f"  Colonne {col_brut} absente")

    log.info(f"  Percentiles calcules pour {len(mapping)} metriques")
    return df


def resolve_poids(poste_id: str) -> dict:
    poids = POIDS_PAR_POSTE.get(poste_id, {})
    if isinstance(poids, str):
        poids = POIDS_PAR_POSTE.get(poids, {})
    return poids


def compute_score_pepite(df: pd.DataFrame) -> pd.DataFrame:
    mask_joueurs  = df["minutes"] >= MIN_MINUTES_JOUEURS
    mask_gk       = (df["poste_id"] == "GK") & (df["minutes"] >= MIN_MINUTES_GK)
    mask_eligible = mask_joueurs | mask_gk

    scores = []
    scores_corr = []

    for idx, row in df.iterrows():
        if not mask_eligible.loc[idx]:
            scores.append(None)
            scores_corr.append(None)
            continue

        poids = resolve_poids(row.get("poste_id", ""))
        if not poids:
            scores.append(None)
            scores_corr.append(None)
            continue

        num  = 0.0
        deno = 0.0
        for col_pct, poids_val in poids.items():
            valeur = row.get(col_pct)
            if pd.notna(valeur):
                num  += valeur * poids_val
                deno += poids_val

        score      = round(num / deno, 2) if deno > 0 else None
        coeff      = COEFF_LIGUE.get(row.get("ligue_id", ""), 1.0)
        score_corr = min(round(score * coeff, 2), 100.0) if score is not None else None

        scores.append(score)
        scores_corr.append(score_corr)

    df["score_pepite"]         = scores
    df["score_pepite_corrige"] = scores_corr
    log.info(f"  Score Pepite calcule pour {df['score_pepite'].notna().sum()} joueurs")
    return df


def compute_rangs(df: pd.DataFrame) -> pd.DataFrame:
    df["score_rang_ligue"] = (
        df.groupby(["ligue_id", "saison_id", "poste_id"])
        ["score_pepite_corrige"]
        .rank(ascending=False, method="min", na_option="bottom")
        .astype("Int64")
    )
    df["score_rang_global"] = (
        df.groupby(["saison_id", "poste_id"])
        ["score_pepite_corrige"]
        .rank(ascending=False, method="min", na_option="bottom")
        .astype("Int64")
    )
    log.info("  Rangs calcules")
    return df


def update_fact_stats(df: pd.DataFrame):
    all_cols = [
        "pct_goals_p90", "pct_xg_p90", "pct_assists_p90",
        "pct_xag_p90", "pct_shots_p90", "pct_tirs_cadres_p90",
        "pct_key_passes_p90", "pct_dribbles_p90",
        "pct_tackles_p90", "pct_interceptions_p90",
        "pct_degagements_p90", "pct_duels_aeriens_pct",
        "pct_passes_pct", "pct_goals_prevented",
        "pct_save_pct", "pct_saves_p90",
        "pct_clean_sheets_pct", "pct_long_balls_pct",
        "score_pepite", "score_pepite_corrige",
        "score_rang_ligue", "score_rang_global",
    ]

    cols_dispo = [c for c in all_cols if c in df.columns]
    df_update  = df[["stat_id"] + cols_dispo].copy()

    for col in ["score_rang_ligue", "score_rang_global"]:
        if col in df_update.columns:
            df_update[col] = df_update[col].astype(float)

    log.info(f"  Chargement de {len(df_update)} lignes dans tmp_score_pepite...")
    df_update.to_sql(
        "tmp_score_pepite", engine,
        schema="public", if_exists="replace", index=False
    )

    set_clause = ", ".join([f"{c} = t.{c}" for c in cols_dispo])
    with engine.connect() as conn:
        conn.execute(text(f"""
            UPDATE public.fact_stats f
            SET {set_clause}
            FROM public.tmp_score_pepite t
            WHERE f.stat_id = t.stat_id
        """))
        conn.execute(text("DROP TABLE IF EXISTS public.tmp_score_pepite"))
        conn.commit()

    log.info(f"  {len(df_update)} lignes mises a jour dans fact_stats")


def create_score_view():
    sql = """
        CREATE OR REPLACE VIEW gold.vue_score_pepite_ranking AS
        SELECT
            j.joueur_id,
            j.nom_complet                               AS joueur,
            j.nom_court,
            j.date_naissance,
            f.age,
            f.poste_id,
            p.poste_label_fr,
            p.famille,
            j.nationalite_principale,
            e.nom_complet                               AS equipe,
            f.ligue_id,
            l.nom_complet                               AS ligue,
            l.pays,
            l.couleur_hex,
            f.saison_id,
            s.saison_courte,
            f.minutes,
            f.matchs_joues,
            f.matchs_titulaire,
            ROUND(f.score_pepite::numeric, 1)           AS score_pepite,
            ROUND(f.score_pepite_corrige::numeric, 1)   AS score_corrige,
            f.score_rang_ligue                          AS rang_ligue,
            f.score_rang_global                         AS rang_global,
            ROUND(f.buts_p90::numeric, 3)               AS buts_p90,
            ROUND(f.xg_p90::numeric, 3)                AS xg_p90,
            ROUND(f.passes_dec_p90::numeric, 3)         AS assists_p90,
            ROUND(f.xag_p90::numeric, 3)               AS xag_p90,
            ROUND(f.tirs_cadres_p90::numeric, 3)        AS tirs_cadres_p90,
            ROUND(f.key_passes_p90::numeric, 3)         AS key_passes_p90,
            ROUND(f.dribbles_p90::numeric, 3)           AS dribbles_p90,
            ROUND(f.tackles_p90::numeric, 3)            AS tackles_p90,
            ROUND(f.interceptions_p90::numeric, 3)      AS interceptions_p90,
            ROUND(f.pct_goals_p90::numeric, 1)          AS pct_goals,
            ROUND(f.pct_xg_p90::numeric, 1)            AS pct_xg,
            ROUND(f.pct_assists_p90::numeric, 1)        AS pct_assists,
            ROUND(f.pct_dribbles_p90::numeric, 1)       AS pct_dribbles,
            ROUND(f.pct_tackles_p90::numeric, 1)        AS pct_tackles,
            ROUND(f.rating::numeric, 2)                 AS rating_reference,
            f.est_u23,
            f.has_fbref_data,
            f.has_sofascore_data
        FROM public.fact_stats  f
        JOIN public.dim_joueurs j ON f.joueur_id  = j.joueur_id
        JOIN public.dim_equipes e ON f.equipe_id  = e.equipe_id
        JOIN public.dim_ligues  l ON f.ligue_id   = l.ligue_id
        JOIN public.dim_saisons s ON f.saison_id  = s.saison_id
        JOIN public.dim_postes  p ON f.poste_id   = p.poste_id
        WHERE f.score_pepite IS NOT NULL
        ORDER BY f.score_pepite_corrige DESC;
    """
    with engine.connect() as conn:
        conn.execute(text(sql))
        conn.commit()
    log.info("  Vue gold.vue_score_pepite_ranking creee")


def verify():
    q_stats = """
        SELECT COUNT(*) as total,
               COUNT(score_pepite) as avec_score,
               COUNT(CASE WHEN est_u23=TRUE AND score_pepite IS NOT NULL THEN 1 END) as u23_score
        FROM public.fact_stats
    """
    q_top10 = """
        SELECT rang_global AS rang, joueur, poste_id, ligue, equipe,
               score_pepite, score_corrige,
               ROUND(xg_p90::numeric,3) as xg_p90,
               ROUND(buts_p90::numeric,3) as buts_p90, age::int as age
        FROM gold.vue_score_pepite_ranking
        WHERE est_u23 = TRUE AND saison_id = '2024-2025' AND poste_id != 'GK'
        ORDER BY score_corrige DESC LIMIT 10
    """
    q_gk = """
        SELECT rang_global AS rang, joueur, ligue, equipe,
               score_pepite, score_corrige, age::int as age
        FROM gold.vue_score_pepite_ranking
        WHERE est_u23 = TRUE AND saison_id = '2024-2025' AND poste_id = 'GK'
        ORDER BY score_corrige DESC LIMIT 5
    """

    with engine.connect() as conn:
        stats = pd.read_sql(q_stats, conn)
        top10 = pd.read_sql(q_top10, conn)
        topgk = pd.read_sql(q_gk, conn)

    log.info("\n" + "=" * 65)
    log.info("  VERIFICATION FINALE")
    log.info("=" * 65)
    log.info(f"  Total fact_stats    : {stats['total'].iloc[0]}")
    log.info(f"  Avec Score Pepite   : {stats['avec_score'].iloc[0]}")
    log.info(f"  U23 avec Score      : {stats['u23_score'].iloc[0]}")
    log.info("\n=== TOP 10 PEPITES U23 — 2024-2025 ===")
    log.info(top10.to_string(index=False))
    log.info("\n=== TOP 5 GARDIENS U23 — 2024-2025 ===")
    log.info(topgk.to_string(index=False))
    log.info("=" * 65)


def run():
    start = datetime.now()
    log.info("=" * 65)
    log.info("  RadarPepites - Gold Builder - Score Pepite")
    log.info(f"  Demarrage : {start.strftime('%Y-%m-%d %H:%M:%S')}")
    log.info("=" * 65)

    try:
        prepare_columns()
        df = load_fact_stats()
        df = compute_percentiles(df)
        df = compute_score_pepite(df)
        df = compute_rangs(df)
        update_fact_stats(df)
        create_score_view()
        verify()
        duree = datetime.now() - start
        log.info(f"\n  Termine en {duree.seconds // 60}m {duree.seconds % 60}s")
    except Exception as e:
        log.error(f"ERREUR FATALE : {e}")
        import traceback
        log.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    run()

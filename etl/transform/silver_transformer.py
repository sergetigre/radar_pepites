"""
etl/transform/silver_transformer.py
RadarPépites — ETL Bronze → Silver

Étapes :
  1. load_fbref_players()         — players_fbref
  2. load_sofascore_players()     — players_sofascore
  3. build_players_combined()     — players_combined
  4. load_fbref_keepers()         — keepers_fbref
  5. load_sofascore_keepers()     — keepers_sofascore
  6. build_keepers_combined()     — keepers_combined
  7. verify()                     — affiche les row counts

Usage :
  python etl/transform/silver_transformer.py
"""

import logging
import re
import time
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from sqlalchemy.exc import OperationalError

import os

# ── Chemins ────────────────────────────────────────────────────────────────────
ROOT         = Path(__file__).resolve().parents[2]
BRONZE_DIR   = ROOT / "data" / "bronze"
BRONZE_ARCHIVES_DIR = BRONZE_DIR / "_Archives"
LOGS_DIR     = ROOT / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

load_dotenv(ROOT / "config" / ".env")

# Année de référence pour le calcul is_u23 (né après 2002 → U23 en 2025/26)
U23_BIRTH_YEAR = 2002

SAISON_MAP = {
    "2022-2023": "22/23",
    "2023-2024": "23/24",
    "2024-2025": "24/25",
    "2025-2026": "25/26",
}

STAT_TYPES_FIELD  = ["standard", "shooting", "playing_time", "misc"]
STAT_TYPES_KEEPER = ["keeper", "keeper_adv"]


# ── Logging ────────────────────────────────────────────────────────────────────
def setup_logger() -> logging.Logger:
    run_ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = LOGS_DIR / f"silver_{run_ts}.log"

    fmt = "%(asctime)s [%(levelname)s] %(message)s"
    stream_handler = logging.StreamHandler()
    stream_handler.setStream(__import__("sys").stdout)
    stream_handler.stream.reconfigure(encoding="utf-8", errors="replace")
    logging.basicConfig(
        level=logging.INFO,
        format=fmt,
        handlers=[
            stream_handler,
            logging.FileHandler(log_file, encoding="utf-8"),
        ],
    )
    logger = logging.getLogger("silver_transformer")
    logger.info(f"Log : {log_file}")
    return logger


# ── Utilitaires ────────────────────────────────────────────────────────────────
def normalize_name(name: str) -> str:
    """Strip accents, lowercase, remove non-alphanum/spaces."""
    if not isinstance(name, str):
        return ""
    nfkd = unicodedata.normalize("NFKD", name)
    ascii_str = nfkd.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9 ]", "", ascii_str.lower()).strip()


def calc_p90(value, minutes) -> Optional[float]:
    try:
        v = float(value)
        m = float(minutes)
        if m > 0:
            return round((v / m) * 90, 3)
    except (TypeError, ValueError):
        pass
    return None


def get_engine():
    # pool_pre_ping : Neon (endpoint pooler) ferme parfois les connexions
    # inactives côté serveur ; sans ce test, SQLAlchemy réutilise une
    # connexion morte du pool et l'upsert échoue avec
    # "server closed the connection unexpectedly". pool_recycle borne
    # aussi la durée de vie d'une connexion en pool par précaution.
    # connect_timeout (côté libpq) : sans ça, une tentative de connexion
    # sur un état réseau anormal peut rester bloquée des dizaines de
    # minutes avant d'échouer (observé : 47 min) au lieu d'échouer vite
    # et de laisser execute_with_retry() retenter proprement.
    engine_kwargs = dict(
        pool_pre_ping=True,
        pool_recycle=280,
        connect_args={"connect_timeout": 10},
    )

    database_url = os.environ.get("DATABASE_URL")
    if database_url:
        return create_engine(database_url, **engine_kwargs)

    required = ["DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD"]
    missing = [v for v in required if not os.environ.get(v)]
    if missing:
        raise RuntimeError(
            "Variables manquantes dans config/.env : " + ", ".join(missing) +
            " (ou renseigner DATABASE_URL directement)"
        )
    url = URL.create(
        drivername="postgresql+psycopg2",
        username=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        host=os.environ["DB_HOST"],
        port=int(os.environ["DB_PORT"]),
        database=os.environ["DB_NAME"],
    )
    return create_engine(url, **engine_kwargs)


def execute_with_retry(engine, sql, rows, logger: logging.Logger, max_retries: int = 4, delay: float = 5.0) -> None:
    """Le pooler Neon coupe parfois la connexion en cours de requête
    (pas seulement au repos, ce que pool_pre_ping ne couvre pas).
    On retente la même transaction quelques fois avant d'abandonner."""
    last_exc: Optional[Exception] = None
    for attempt in range(1, max_retries + 1):
        try:
            with engine.begin() as conn:
                conn.execute(sql, rows)
            return
        except OperationalError as e:
            last_exc = e
            logger.warning(
                f"    Connexion DB perdue (tentative {attempt}/{max_retries}), "
                f"nouvel essai dans {delay:.0f}s..."
            )
            time.sleep(delay)
    raise last_exc


def to_records(df: pd.DataFrame) -> list:
    """DataFrame -> liste de dicts avec NaN -> None.
    df.where(pd.notna(df), None) seul ne suffit pas : sur une colonne
    float64, pandas recase silencieusement None en NaN. Il faut passer
    en dtype object d'abord pour que None soit réellement conservé."""
    return df.astype(object).where(pd.notna(df), None).to_dict(orient="records")


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Les CSV fbref ont des en-têtes 'Title Case avec espaces'
    (ex: 'Playing Time_MP') alors que les mappings de ce script
    attendent du snake_case ('playing_time_mp')."""
    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
    return df


def saison_from_filename(fname: str) -> Optional[str]:
    """Extrait la saison depuis le nom de fichier bronze.
    Formats supportés :
      '..._20232024_...'  (fichiers actuels, concaténé)
      '..._2023_2024_...' (anciens fichiers, avec séparateur)
    """
    m = re.search(r"_(\d{4})(\d{4})_", fname)
    if m:
        return f"{m.group(1)}-{m.group(2)}"
    m = re.search(r"_(\d{4})_(\d{4})_", fname)
    if m:
        return f"{m.group(1)}-{m.group(2)}"
    return None


def league_from_filename(fname: str) -> Optional[str]:
    """Extrait le league_id depuis le nom de fichier bronze.
    Ex: '20240101_120000_ENG_20232024_standard.csv' → 'ENG'
    Le nom de fichier commence directement par l'horodatage
    (pas de '_' en tête) → pattern ancré en début de chaîne.
    """
    m = re.match(r"\d{8}_\d{6}_([A-Z]{3})_", fname)
    return m.group(1) if m else None


# ── 0. Infos bio joueurs (players_info) ────────────────────────────────────────
POSITION_MAP = {"G": "GK", "D": "DF", "M": "MF", "F": "FW"}


def load_players_info(engine, logger: logging.Logger):
    """Charge silver.players_info depuis *_players_info.csv.
    Ces fichiers ont été archivés lors de la régénération bronze du 10/08 —
    on les cherche aussi bien à la racine que dans data/bronze/_Archives/,
    car les données bio (naissance, nationalité, poste, pied, taille) sont
    stables et n'ont pas besoin d'être re-scrapées à chaque run.
    """
    logger.info("[0/7] Chargement infos bio joueurs → silver.players_info")

    files = sorted(BRONZE_DIR.glob("*_players_info.csv"))
    if not files:
        files = sorted(BRONZE_ARCHIVES_DIR.glob("*_players_info.csv"))
        if files:
            logger.info(f"  (aucun *_players_info.csv en racine, utilisation de {BRONZE_ARCHIVES_DIR})")
    if not files:
        logger.warning("  Aucun fichier *_players_info.csv trouvé (racine ou _Archives) — silver.players_info non alimenté")
        return

    # Table de correspondance nom pays anglais -> code pays, pour résoudre
    # nationalite_id depuis la colonne texte 'nationality' du CSV
    # (la colonne 'nationality_id' du CSV est vide côté source).
    with engine.connect() as conn:
        df_pays = pd.read_sql(text("SELECT pays_id, nom_en FROM silver.ref_pays"), conn)
    nom_en_to_id = {
        str(r.nom_en).strip().lower(): r.pays_id
        for r in df_pays.itertuples()
        if pd.notna(r.nom_en)
    }

    total_upserted = 0
    unique_ids: set = set()

    for f in files:
        try:
            df = pd.read_csv(f, low_memory=False)
        except Exception as e:
            logger.error(f"  Lecture {f.name}: {e}")
            continue

        if "player_id" not in df.columns:
            logger.warning(f"  Colonne 'player_id' absente de {f.name} — ignoré")
            continue

        dob = pd.to_datetime(df.get("date_of_birth"), errors="coerce")
        df["date_naissance"]  = dob.dt.date
        df["annee_naissance"] = dob.dt.year
        df["is_u23"] = df["annee_naissance"].apply(
            lambda y: bool(y > U23_BIRTH_YEAR) if pd.notna(y) else None
        )
        df["nationalite_id"] = df.get("nationality", pd.Series(dtype=object)).apply(
            lambda n: nom_en_to_id.get(str(n).strip().lower()) if pd.notna(n) else None
        )
        df["poste_principal"]   = df.get("position", pd.Series(dtype=object)).map(POSITION_MAP)
        df["poste_detail"]      = df.get("position_detailed")
        df["pied_dominant"]     = df.get("preferred_foot")
        df["taille_cm"]         = pd.to_numeric(df.get("height"), errors="coerce")
        df["poids_kg"]          = pd.to_numeric(df.get("weight"), errors="coerce")
        df["nom_court"]         = None
        df["nationalite2_id"]   = None
        df["player_name_fbref"] = None
        df["born_fbref"]        = None
        df["date_maj"]          = datetime.now(timezone.utc)
        df = df.rename(columns={"player_id": "player_id_ss"})

        silver_cols = [
            "player_id_ss","player_name","nom_court","date_naissance","annee_naissance",
            "is_u23","nationalite_id","nationalite2_id","poste_principal","poste_detail",
            "pied_dominant","taille_cm","poids_kg","player_name_fbref","born_fbref","date_maj",
        ]
        for c in silver_cols:
            if c not in df.columns:
                df[c] = None
        df_out = df[silver_cols].dropna(subset=["player_id_ss"]).copy()
        if df_out.empty:
            continue
        df_out["player_id_ss"] = df_out["player_id_ss"].astype("int64")

        rows = to_records(df_out)
        sql = text("""
            INSERT INTO silver.players_info
                (player_id_ss, player_name, nom_court, date_naissance, annee_naissance,
                 is_u23, nationalite_id, nationalite2_id, poste_principal, poste_detail,
                 pied_dominant, taille_cm, poids_kg, player_name_fbref, born_fbref, date_maj)
            VALUES
                (:player_id_ss, :player_name, :nom_court, :date_naissance, :annee_naissance,
                 :is_u23, :nationalite_id, :nationalite2_id, :poste_principal, :poste_detail,
                 :pied_dominant, :taille_cm, :poids_kg, :player_name_fbref, :born_fbref, :date_maj)
            ON CONFLICT (player_id_ss) DO UPDATE SET
                player_name      = EXCLUDED.player_name,
                date_naissance    = EXCLUDED.date_naissance,
                annee_naissance   = EXCLUDED.annee_naissance,
                is_u23            = EXCLUDED.is_u23,
                nationalite_id    = EXCLUDED.nationalite_id,
                poste_principal   = EXCLUDED.poste_principal,
                poste_detail      = EXCLUDED.poste_detail,
                pied_dominant     = EXCLUDED.pied_dominant,
                taille_cm         = EXCLUDED.taille_cm,
                poids_kg          = EXCLUDED.poids_kg,
                date_maj          = EXCLUDED.date_maj
        """)
        execute_with_retry(engine, sql, rows, logger)

        total_upserted += len(rows)
        unique_ids.update(df_out["player_id_ss"].tolist())
        logger.info(f"  [OK] {f.name} — {len(rows)} lignes")

    logger.info(f"  Total players_info : {total_upserted} lignes upsertées ({len(unique_ids)} joueurs uniques)")


# ── 1. FBref joueurs de champ ──────────────────────────────────────────────────
def load_fbref_players(engine, logger: logging.Logger):
    logger.info("[1/7] Chargement FBref joueurs de champ → silver.players_fbref")

    # Grouper les fichiers par (league_id, saison)
    groups: dict[tuple, dict[str, Path]] = {}
    for f in sorted(BRONZE_DIR.glob("*_standard.csv")):
        league_id = league_from_filename(f.name)
        saison    = saison_from_filename(f.name)
        if league_id and saison:
            key = (league_id, saison)
            groups.setdefault(key, {})["standard"] = f

    for f in sorted(BRONZE_DIR.glob("*_shooting.csv")):
        league_id = league_from_filename(f.name)
        saison    = saison_from_filename(f.name)
        if league_id and saison:
            key = (league_id, saison)
            groups.setdefault(key, {})["shooting"] = f

    for f in sorted(BRONZE_DIR.glob("*_playing_time.csv")):
        league_id = league_from_filename(f.name)
        saison    = saison_from_filename(f.name)
        if league_id and saison:
            key = (league_id, saison)
            groups.setdefault(key, {})["playing_time"] = f

    for f in sorted(BRONZE_DIR.glob("*_misc.csv")):
        league_id = league_from_filename(f.name)
        saison    = saison_from_filename(f.name)
        if league_id and saison:
            key = (league_id, saison)
            groups.setdefault(key, {})["misc"] = f

    total_upserted = 0

    for (league_id, saison), files in sorted(groups.items()):
        if "standard" not in files:
            logger.warning(f"  Pas de fichier standard pour {league_id}|{saison} — ignoré")
            continue

        try:
            df_std = normalize_columns(pd.read_csv(files["standard"], low_memory=False))
        except Exception as e:
            logger.error(f"  Lecture standard échouée {league_id}|{saison}: {e}")
            continue

        # Colonnes de base depuis standard
        col_map = {
            "player": "player_name", "born": "born", "team": "team",
            "nation": "nation", "pos": "pos",
            "playing_time_mp": "matches_played",
            "playing_time_starts": "starts",
            "playing_time_min": "minutes",
            "playing_time_90s": "minutes_90s",
            "performance_gls": "goals",
            "performance_ast": "assists",
            "performance_g-pk": "goals_no_pk",
            "performance_crdy": "yellow_cards",
            "performance_crdr": "red_cards",
        }
        df = df_std.rename(columns={k: v for k, v in col_map.items() if k in df_std.columns})

        # Merge shooting
        if "shooting" in files:
            try:
                df_sh = normalize_columns(pd.read_csv(files["shooting"], low_memory=False))
                sh_map = {
                    "player": "player_name", "born": "born", "team": "team",
                    "standard_sh": "shots",
                    "standard_sot": "shots_on_target",
                    "standard_sot%": "shots_on_target_pct",
                    "standard_sh/90": "shots_p90",
                    "standard_sot/90": "shots_on_target_p90",
                }
                df_sh = df_sh.rename(columns={k: v for k, v in sh_map.items() if k in df_sh.columns})
                keep_sh = ["player_name", "born", "team"] + [
                    c for c in ["shots","shots_on_target","shots_on_target_pct",
                                "shots_p90","shots_on_target_p90"]
                    if c in df_sh.columns
                ]
                df = df.merge(df_sh[keep_sh], on=["player_name","born","team"], how="left", suffixes=("","_sh"))
            except Exception as e:
                logger.warning(f"  Merge shooting {league_id}|{saison}: {e}")

        # Merge misc
        if "misc" in files:
            try:
                df_mi = normalize_columns(pd.read_csv(files["misc"], low_memory=False))
                mi_map = {
                    "player": "player_name", "born": "born", "team": "team",
                    "performance_fls": "fouls_committed",
                    "performance_fld": "fouls_drawn",
                    "performance_int": "interceptions",
                    "performance_tklw": "tackles_won",
                    "aerial_duels_won": "aerial_won",
                    "aerial_duels_lost": "aerial_lost",
                    "aerial_duels_won%": "aerial_won_pct",
                }
                df_mi = df_mi.rename(columns={k: v for k, v in mi_map.items() if k in df_mi.columns})
                keep_mi = ["player_name", "born", "team"] + [
                    c for c in ["fouls_committed","fouls_drawn","interceptions",
                                "tackles_won","aerial_won","aerial_lost","aerial_won_pct"]
                    if c in df_mi.columns
                ]
                df = df.merge(df_mi[keep_mi], on=["player_name","born","team"], how="left", suffixes=("","_mi"))
            except Exception as e:
                logger.warning(f"  Merge misc {league_id}|{saison}: {e}")

        # Colonnes obligatoires
        for col in ["player_name", "born", "team"]:
            if col not in df.columns:
                logger.error(f"  Colonne manquante '{col}' dans {league_id}|{saison} — ignoré")
                continue

        df["ligue_id"]  = league_id
        df["saison_id"] = saison
        df["is_u23"]    = df["born"].apply(
            lambda b: bool(int(b) > U23_BIRTH_YEAR) if pd.notna(b) else None
        )
        df["source"]   = "fbref"
        df["date_maj"] = datetime.now(timezone.utc)

        # Filtrer les gardiens (on les traite séparément)
        if "pos" in df.columns:
            df = df[df["pos"].fillna("").str.upper() != "GK"]

        silver_cols = [
            "player_name","born","team","nation","pos","ligue_id","saison_id",
            "matches_played","starts","minutes","minutes_90s",
            "goals","assists","goals_no_pk","yellow_cards","red_cards",
            "shots","shots_on_target","shots_on_target_pct","shots_p90","shots_on_target_p90",
            "fouls_committed","fouls_drawn","interceptions","tackles_won",
            "aerial_won","aerial_lost","aerial_won_pct","is_u23","source","date_maj",
        ]
        for c in silver_cols:
            if c not in df.columns:
                df[c] = None
        df_out = df[silver_cols].copy()
        # UNIQUE(player_name, born, team, saison_id) ne bloque pas les doublons
        # quand born est NULL (NULL != NULL en SQL) -> dédup applicative ici.
        # pandas traite NaN == NaN comme égaux dans drop_duplicates, donc ça
        # fonctionne même pour les lignes sans born.
        df_out = df_out.drop_duplicates(subset=["player_name", "born", "team", "saison_id"], keep="last")

        upserted = _upsert_fbref_players(df_out, engine, logger)
        total_upserted += upserted
        logger.info(f"  [OK] {league_id}|{saison} — {upserted} lignes upsertées")

    logger.info(f"  Total players_fbref : {total_upserted} lignes")


def _upsert_fbref_players(df: pd.DataFrame, engine, logger) -> int:
    if df.empty:
        return 0
    rows = to_records(df)
    sql = text("""
        INSERT INTO silver.players_fbref
            (player_name, born, team, nation, pos, ligue_id, saison_id,
             matches_played, starts, minutes, minutes_90s,
             goals, assists, goals_no_pk, yellow_cards, red_cards,
             shots, shots_on_target, shots_on_target_pct, shots_p90, shots_on_target_p90,
             fouls_committed, fouls_drawn, interceptions, tackles_won,
             aerial_won, aerial_lost, aerial_won_pct, is_u23, source, date_maj)
        VALUES
            (:player_name, :born, :team, :nation, :pos, :ligue_id, :saison_id,
             :matches_played, :starts, :minutes, :minutes_90s,
             :goals, :assists, :goals_no_pk, :yellow_cards, :red_cards,
             :shots, :shots_on_target, :shots_on_target_pct, :shots_p90, :shots_on_target_p90,
             :fouls_committed, :fouls_drawn, :interceptions, :tackles_won,
             :aerial_won, :aerial_lost, :aerial_won_pct, :is_u23, :source, :date_maj)
        ON CONFLICT (player_name, born, team, saison_id) DO UPDATE SET
            matches_played      = EXCLUDED.matches_played,
            starts              = EXCLUDED.starts,
            minutes             = EXCLUDED.minutes,
            minutes_90s         = EXCLUDED.minutes_90s,
            goals               = EXCLUDED.goals,
            assists             = EXCLUDED.assists,
            goals_no_pk         = EXCLUDED.goals_no_pk,
            yellow_cards        = EXCLUDED.yellow_cards,
            red_cards           = EXCLUDED.red_cards,
            shots               = EXCLUDED.shots,
            shots_on_target     = EXCLUDED.shots_on_target,
            shots_on_target_pct = EXCLUDED.shots_on_target_pct,
            shots_p90           = EXCLUDED.shots_p90,
            shots_on_target_p90 = EXCLUDED.shots_on_target_p90,
            fouls_committed     = EXCLUDED.fouls_committed,
            fouls_drawn         = EXCLUDED.fouls_drawn,
            interceptions       = EXCLUDED.interceptions,
            tackles_won         = EXCLUDED.tackles_won,
            aerial_won          = EXCLUDED.aerial_won,
            aerial_lost         = EXCLUDED.aerial_lost,
            aerial_won_pct      = EXCLUDED.aerial_won_pct,
            is_u23              = EXCLUDED.is_u23,
            date_maj            = EXCLUDED.date_maj
    """)
    execute_with_retry(engine, sql, rows, logger)
    return len(rows)


# ── 2. Sofascore joueurs de champ ──────────────────────────────────────────────
def load_sofascore_players(engine, logger: logging.Logger):
    logger.info("[2/7] Chargement Sofascore joueurs → silver.players_sofascore")

    files = sorted(BRONZE_DIR.glob("*_sofascore_players.csv"))
    if not files:
        logger.warning("  Aucun fichier *_sofascore_players.csv trouvé dans bronze/")
        return

    total_upserted = 0

    for f in files:
        league_id = league_from_filename(f.name)
        saison    = saison_from_filename(f.name)
        if not league_id or not saison:
            logger.warning(f"  Impossible de parser league/saison depuis : {f.name}")
            continue

        try:
            df = pd.read_csv(f, low_memory=False)
        except Exception as e:
            logger.error(f"  Lecture {f.name}: {e}")
            continue

        # Le CSV a déjà player_name/team_name/team_id en snake_case ;
        # seul l'id joueur ("player_id") doit être renommé en player_id_ss.
        col_rename = {
            "player_id": "player_id_ss",
            "expectedGoals": "expected_goals", "expectedAssists": "expected_assists",
            "shotsOnTarget": "shots_on_target", "totalShots": "total_shots",
            "bigChancesCreated": "big_chances_created", "bigChancesMissed": "big_chances_missed",
            "accuratePasses": "accurate_passes",
            "accuratePassesPercentage": "accurate_passes_pct",
            "keyPasses": "key_passes",
            "accurateLongBalls": "accurate_long_balls",
            "accurateLongBallsPercentage": "accurate_long_balls_pct",
            "successfulDribbles": "successful_dribbles",
            "successfulDribblesPercentage": "successful_dribbles_pct",
            "possessionLost": "possession_lost",
            "minutesPlayed": "minutes_played",
            "yellowCards": "yellow_cards", "redCards": "red_cards",
        }
        df = df.rename(columns={k: v for k, v in col_rename.items() if k in df.columns})

        df["ligue_id"]  = league_id
        df["saison_id"] = saison
        df["source"]    = "sofascore"
        df["date_maj"]  = datetime.now(timezone.utc)

        # Calcul métriques /90
        mins = pd.to_numeric(df.get("minutes_played"), errors="coerce")
        for raw, p90 in [
            ("goals","goals_p90"), ("assists","assists_p90"),
            ("expected_goals","xg_p90"), ("expected_assists","xa_p90"),
            ("shots_on_target","shots_on_target_p90"), ("key_passes","key_passes_p90"),
            ("tackles","tackles_p90"), ("interceptions","interceptions_p90"),
        ]:
            if raw in df.columns:
                df[p90] = [calc_p90(v, m) for v, m in zip(df[raw], mins)]
            else:
                df[p90] = None

        # is_u23 : pas de date de naissance dans sofascore → None par défaut
        df["is_u23"] = None

        silver_cols = [
            "player_id_ss","player_name","team_name","team_id","ligue_id","saison_id",
            "rating","goals","assists","expected_goals","expected_assists",
            "shots_on_target","total_shots","big_chances_created","big_chances_missed",
            "accurate_passes","accurate_passes_pct","key_passes",
            "accurate_long_balls","accurate_long_balls_pct",
            "successful_dribbles","successful_dribbles_pct",
            "tackles","interceptions","clearances","possession_lost",
            "minutes_played","appearances","yellow_cards","red_cards",
            "goals_p90","assists_p90","xg_p90","xa_p90",
            "shots_on_target_p90","key_passes_p90","tackles_p90","interceptions_p90",
            "is_u23","source","date_maj",
        ]
        for c in silver_cols:
            if c not in df.columns:
                df[c] = None
        df_out = df[silver_cols].copy()

        upserted = _upsert_sofascore_players(df_out, engine, logger)
        total_upserted += upserted
        logger.info(f"  [OK] {f.name} — {upserted} lignes")

    logger.info(f"  Total players_sofascore : {total_upserted} lignes")


def _upsert_sofascore_players(df: pd.DataFrame, engine, logger) -> int:
    if df.empty:
        return 0
    rows = to_records(df)
    sql = text("""
        INSERT INTO silver.players_sofascore
            (player_id_ss, player_name, team_name, team_id, ligue_id, saison_id,
             rating, goals, assists, expected_goals, expected_assists,
             shots_on_target, total_shots, big_chances_created, big_chances_missed,
             accurate_passes, accurate_passes_pct, key_passes,
             accurate_long_balls, accurate_long_balls_pct,
             successful_dribbles, successful_dribbles_pct,
             tackles, interceptions, clearances, possession_lost,
             minutes_played, appearances, yellow_cards, red_cards,
             goals_p90, assists_p90, xg_p90, xa_p90,
             shots_on_target_p90, key_passes_p90, tackles_p90, interceptions_p90,
             is_u23, source, date_maj)
        VALUES
            (:player_id_ss, :player_name, :team_name, :team_id, :ligue_id, :saison_id,
             :rating, :goals, :assists, :expected_goals, :expected_assists,
             :shots_on_target, :total_shots, :big_chances_created, :big_chances_missed,
             :accurate_passes, :accurate_passes_pct, :key_passes,
             :accurate_long_balls, :accurate_long_balls_pct,
             :successful_dribbles, :successful_dribbles_pct,
             :tackles, :interceptions, :clearances, :possession_lost,
             :minutes_played, :appearances, :yellow_cards, :red_cards,
             :goals_p90, :assists_p90, :xg_p90, :xa_p90,
             :shots_on_target_p90, :key_passes_p90, :tackles_p90, :interceptions_p90,
             :is_u23, :source, :date_maj)
        ON CONFLICT (player_id_ss, team_id, saison_id) DO UPDATE SET
            rating                  = EXCLUDED.rating,
            goals                   = EXCLUDED.goals,
            assists                 = EXCLUDED.assists,
            expected_goals          = EXCLUDED.expected_goals,
            expected_assists        = EXCLUDED.expected_assists,
            shots_on_target         = EXCLUDED.shots_on_target,
            total_shots             = EXCLUDED.total_shots,
            big_chances_created     = EXCLUDED.big_chances_created,
            big_chances_missed      = EXCLUDED.big_chances_missed,
            accurate_passes         = EXCLUDED.accurate_passes,
            accurate_passes_pct     = EXCLUDED.accurate_passes_pct,
            key_passes              = EXCLUDED.key_passes,
            accurate_long_balls     = EXCLUDED.accurate_long_balls,
            accurate_long_balls_pct = EXCLUDED.accurate_long_balls_pct,
            successful_dribbles     = EXCLUDED.successful_dribbles,
            successful_dribbles_pct = EXCLUDED.successful_dribbles_pct,
            tackles                 = EXCLUDED.tackles,
            interceptions           = EXCLUDED.interceptions,
            clearances              = EXCLUDED.clearances,
            possession_lost         = EXCLUDED.possession_lost,
            minutes_played          = EXCLUDED.minutes_played,
            appearances             = EXCLUDED.appearances,
            yellow_cards            = EXCLUDED.yellow_cards,
            red_cards               = EXCLUDED.red_cards,
            goals_p90               = EXCLUDED.goals_p90,
            assists_p90             = EXCLUDED.assists_p90,
            xg_p90                  = EXCLUDED.xg_p90,
            xa_p90                  = EXCLUDED.xa_p90,
            shots_on_target_p90     = EXCLUDED.shots_on_target_p90,
            key_passes_p90          = EXCLUDED.key_passes_p90,
            tackles_p90             = EXCLUDED.tackles_p90,
            interceptions_p90       = EXCLUDED.interceptions_p90,
            is_u23                  = EXCLUDED.is_u23,
            date_maj                = EXCLUDED.date_maj
    """)
    execute_with_retry(engine, sql, rows, logger)
    return len(rows)


# ── 3. players_combined ────────────────────────────────────────────────────────
def build_players_combined(engine, logger: logging.Logger):
    logger.info("[3/7] Construction silver.players_combined")

    sql_ss = text("""
        SELECT
            ps.player_id_ss, ps.player_name, ps.team_name, ps.team_id,
            ps.ligue_id, ps.saison_id,
            ps.rating AS rating_ss,
            ps.goals           AS goals_ss,
            ps.assists         AS assists_ss,
            ps.expected_goals  AS xg_ss,
            ps.expected_assists AS xa_ss,
            ps.shots_on_target AS shots_on_target_ss,
            ps.key_passes      AS key_passes_ss,
            ps.accurate_passes AS accurate_passes_ss,
            ps.accurate_passes_pct AS accurate_passes_pct_ss,
            ps.successful_dribbles AS successful_dribbles_ss,
            ps.tackles         AS tackles_ss,
            ps.interceptions   AS interceptions_ss,
            ps.clearances      AS clearances_ss,
            ps.minutes_played  AS minutes_ss,
            ps.appearances     AS appearances_ss,
            ps.goals_p90, ps.assists_p90, ps.xg_p90, ps.xa_p90,
            ps.shots_on_target_p90, ps.key_passes_p90,
            ps.tackles_p90, ps.interceptions_p90,
            ps.successful_dribbles / NULLIF(ps.minutes_played, 0) * 90 AS dribbles_p90,
            ps.clearances / NULLIF(ps.minutes_played, 0) * 90 AS degagements_p90,
            pi.annee_naissance AS born, pi.date_naissance, pi.is_u23,
            pi.nationalite_id, pi.poste_principal, pi.pied_dominant, pi.taille_cm
        FROM silver.players_sofascore ps
        LEFT JOIN silver.players_info pi
            ON ps.player_id_ss = pi.player_id_ss
    """)

    sql_fb = text("""
        SELECT
            normalize_name(player_name) AS name_norm,
            born, ligue_id, saison_id,
            goals           AS goals_fb,
            assists         AS assists_fb,
            shots           AS shots_fb,
            shots_on_target AS shots_on_target_fb,
            tackles_won     AS tackles_won_fb,
            interceptions   AS interceptions_fb,
            aerial_won_pct  AS aerial_won_pct_fb,
            minutes         AS minutes_fb,
            shots_p90       AS shots_p90_fb
        FROM silver.players_fbref
    """)

    with engine.connect() as conn:
        df_ss = pd.read_sql(sql_ss, conn)
        # FBref: on fait le join en Python avec normalize_name
        df_fb_raw = pd.read_sql(
            text("""
                SELECT
                    player_name, born, ligue_id, saison_id,
                    goals, assists, shots, shots_on_target,
                    tackles_won, interceptions, aerial_won_pct, minutes, shots_p90
                FROM silver.players_fbref
            """),
            conn,
        )

    df_fb_raw["name_norm"] = df_fb_raw["player_name"].apply(normalize_name)
    df_ss["name_norm"]     = df_ss["player_name"].apply(normalize_name)

    df_fb = df_fb_raw.rename(columns={
        "goals": "goals_fb", "assists": "assists_fb", "shots": "shots_fb",
        "shots_on_target": "shots_on_target_fb", "tackles_won": "tackles_won_fb",
        "interceptions": "interceptions_fb", "aerial_won_pct": "aerial_won_pct_fb",
        "minutes": "minutes_fb", "shots_p90": "shots_p90_fb",
    })

    df_merged = df_ss.merge(
        df_fb[["name_norm","born","ligue_id","saison_id",
               "goals_fb","assists_fb","shots_fb","shots_on_target_fb",
               "tackles_won_fb","interceptions_fb","aerial_won_pct_fb",
               "minutes_fb","shots_p90_fb"]],
        on=["name_norm","born","ligue_id","saison_id"],
        how="left",
    )

    df_merged["has_fbref_data"]     = df_merged["minutes_fb"].notna()
    df_merged["has_sofascore_data"] = df_merged["minutes_ss"].notna()
    df_merged["shots_p90"] = df_merged.apply(
        lambda r: r.get("shots_p90_fb") or calc_p90(r.get("shots_fb"), r.get("minutes_fb")),
        axis=1,
    )
    df_merged["date_maj"] = datetime.now(timezone.utc)

    silver_cols_final = [
        "player_id_ss","player_name","born","date_naissance","is_u23",
        "nationalite_id","poste_principal","pied_dominant","taille_cm",
        "team_name","team_id","ligue_id","saison_id",
        "rating_ss","goals_ss","assists_ss","xg_ss","xa_ss",
        "shots_on_target_ss","key_passes_ss","accurate_passes_ss","accurate_passes_pct_ss",
        "successful_dribbles_ss","tackles_ss","interceptions_ss","clearances_ss",
        "minutes_ss","appearances_ss",
        "goals_fb","assists_fb","shots_fb","shots_on_target_fb",
        "tackles_won_fb","interceptions_fb","aerial_won_pct_fb","minutes_fb",
        "goals_p90","assists_p90","xg_p90","xa_p90","shots_p90",
        "key_passes_p90","tackles_p90","interceptions_p90","dribbles_p90","degagements_p90",
        "has_fbref_data","has_sofascore_data","date_maj",
    ]
    df_out = df_merged

    for c in silver_cols_final:
        if c not in df_out.columns:
            df_out[c] = None

    df_out = df_out[silver_cols_final].copy()

    sql_upsert = text("""
        INSERT INTO silver.players_combined
            (player_id_ss, player_name, born, date_naissance, is_u23,
             nationalite_id, poste_principal, pied_dominant, taille_cm,
             team_name, team_id, ligue_id, saison_id,
             rating_ss, goals_ss, assists_ss, xg_ss, xa_ss,
             shots_on_target_ss, key_passes_ss, accurate_passes_ss, accurate_passes_pct_ss,
             successful_dribbles_ss, tackles_ss, interceptions_ss, clearances_ss,
             minutes_ss, appearances_ss,
             goals_fb, assists_fb, shots_fb, shots_on_target_fb,
             tackles_won_fb, interceptions_fb, aerial_won_pct_fb, minutes_fb,
             goals_p90, assists_p90, xg_p90, xa_p90, shots_p90,
             key_passes_p90, tackles_p90, interceptions_p90, dribbles_p90, degagements_p90,
             has_fbref_data, has_sofascore_data, date_maj)
        VALUES
            (:player_id_ss, :player_name, :born, :date_naissance, :is_u23,
             :nationalite_id, :poste_principal, :pied_dominant, :taille_cm,
             :team_name, :team_id, :ligue_id, :saison_id,
             :rating_ss, :goals_ss, :assists_ss, :xg_ss, :xa_ss,
             :shots_on_target_ss, :key_passes_ss, :accurate_passes_ss, :accurate_passes_pct_ss,
             :successful_dribbles_ss, :tackles_ss, :interceptions_ss, :clearances_ss,
             :minutes_ss, :appearances_ss,
             :goals_fb, :assists_fb, :shots_fb, :shots_on_target_fb,
             :tackles_won_fb, :interceptions_fb, :aerial_won_pct_fb, :minutes_fb,
             :goals_p90, :assists_p90, :xg_p90, :xa_p90, :shots_p90,
             :key_passes_p90, :tackles_p90, :interceptions_p90, :dribbles_p90, :degagements_p90,
             :has_fbref_data, :has_sofascore_data, :date_maj)
        ON CONFLICT (player_id_ss, saison_id, team_id) DO UPDATE SET
            player_name             = EXCLUDED.player_name,
            born                    = EXCLUDED.born,
            date_naissance          = EXCLUDED.date_naissance,
            is_u23                  = EXCLUDED.is_u23,
            nationalite_id          = EXCLUDED.nationalite_id,
            poste_principal         = EXCLUDED.poste_principal,
            pied_dominant           = EXCLUDED.pied_dominant,
            taille_cm               = EXCLUDED.taille_cm,
            rating_ss               = EXCLUDED.rating_ss,
            goals_ss                = EXCLUDED.goals_ss,
            assists_ss              = EXCLUDED.assists_ss,
            xg_ss                   = EXCLUDED.xg_ss,
            xa_ss                   = EXCLUDED.xa_ss,
            shots_on_target_ss      = EXCLUDED.shots_on_target_ss,
            key_passes_ss           = EXCLUDED.key_passes_ss,
            accurate_passes_ss      = EXCLUDED.accurate_passes_ss,
            accurate_passes_pct_ss  = EXCLUDED.accurate_passes_pct_ss,
            successful_dribbles_ss  = EXCLUDED.successful_dribbles_ss,
            tackles_ss              = EXCLUDED.tackles_ss,
            interceptions_ss        = EXCLUDED.interceptions_ss,
            clearances_ss           = EXCLUDED.clearances_ss,
            minutes_ss              = EXCLUDED.minutes_ss,
            appearances_ss          = EXCLUDED.appearances_ss,
            goals_fb                = EXCLUDED.goals_fb,
            assists_fb              = EXCLUDED.assists_fb,
            shots_fb                = EXCLUDED.shots_fb,
            shots_on_target_fb      = EXCLUDED.shots_on_target_fb,
            tackles_won_fb          = EXCLUDED.tackles_won_fb,
            interceptions_fb        = EXCLUDED.interceptions_fb,
            aerial_won_pct_fb       = EXCLUDED.aerial_won_pct_fb,
            minutes_fb              = EXCLUDED.minutes_fb,
            goals_p90               = EXCLUDED.goals_p90,
            assists_p90             = EXCLUDED.assists_p90,
            xg_p90                  = EXCLUDED.xg_p90,
            xa_p90                  = EXCLUDED.xa_p90,
            shots_p90               = EXCLUDED.shots_p90,
            key_passes_p90          = EXCLUDED.key_passes_p90,
            tackles_p90             = EXCLUDED.tackles_p90,
            interceptions_p90       = EXCLUDED.interceptions_p90,
            dribbles_p90            = EXCLUDED.dribbles_p90,
            degagements_p90         = EXCLUDED.degagements_p90,
            has_fbref_data          = EXCLUDED.has_fbref_data,
            has_sofascore_data      = EXCLUDED.has_sofascore_data,
            date_maj                = EXCLUDED.date_maj
    """)

    rows = to_records(df_out)
    execute_with_retry(engine, sql_upsert, rows, logger)

    logger.info(f"  [OK] players_combined — {len(rows)} lignes upsertées")


# ── 4. FBref gardiens ──────────────────────────────────────────────────────────
def load_fbref_keepers(engine, logger: logging.Logger):
    logger.info("[4/7] Chargement FBref gardiens → silver.keepers_fbref")

    groups: dict[tuple, dict[str, Path]] = {}
    for tag, glob_pat in [("keeper", "*_keeper.csv"), ("keeper_adv", "*_keeper_adv.csv")]:
        for f in sorted(BRONZE_DIR.glob(glob_pat)):
            league_id = league_from_filename(f.name)
            saison    = saison_from_filename(f.name)
            if league_id and saison:
                key = (league_id, saison)
                groups.setdefault(key, {})[tag] = f

    total_upserted = 0

    for (league_id, saison), files in sorted(groups.items()):
        if "keeper" not in files:
            continue

        try:
            df = normalize_columns(pd.read_csv(files["keeper"], low_memory=False))
        except Exception as e:
            logger.error(f"  Lecture keeper {league_id}|{saison}: {e}")
            continue

        col_map = {
            "player": "player_name", "born": "born", "team": "team", "nation": "nation",
            "playing_time_mp": "matches_played",
            "playing_time_min": "minutes",
            "performance_ga": "goals_against",
            "performance_ga90": "goals_against_p90",
            "performance_sota": "shots_on_target_against",
            "performance_saves": "saves",
            "performance_save%": "save_pct",
            "performance_w": "wins",
            "performance_d": "draws",
            "performance_l": "losses",
            "performance_cs": "clean_sheets",
            "performance_cs%": "clean_sheets_pct",
            "penalty_kicks_pkatt": "pk_attempted",
            "penalty_kicks_pka": "pk_allowed",
            "penalty_kicks_pksv": "pk_saved",
            "penalty_kicks_pkm": "pk_missed",
            "penalty_kicks_save%": "pk_save_pct",
        }
        df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})
        df["ligue_id"]  = league_id
        df["saison_id"] = saison
        df["is_u23"]    = df["born"].apply(
            lambda b: bool(int(b) > U23_BIRTH_YEAR) if pd.notna(b) else None
        )
        df["source"]   = "fbref"
        df["date_maj"] = datetime.now(timezone.utc)

        silver_cols = [
            "player_name","born","team","nation","ligue_id","saison_id",
            "matches_played","minutes","goals_against","goals_against_p90",
            "shots_on_target_against","saves","save_pct",
            "wins","draws","losses","clean_sheets","clean_sheets_pct",
            "pk_attempted","pk_allowed","pk_saved","pk_missed","pk_save_pct",
            "is_u23","source","date_maj",
        ]
        for c in silver_cols:
            if c not in df.columns:
                df[c] = None
        df_out = df[silver_cols].copy()
        # Même dédup applicative que players_fbref : UNIQUE(...) ne bloque pas
        # les doublons quand born est NULL.
        df_out = df_out.drop_duplicates(subset=["player_name", "born", "team", "saison_id"], keep="last")

        rows = to_records(df_out)
        sql = text("""
            INSERT INTO silver.keepers_fbref
                (player_name, born, team, nation, ligue_id, saison_id,
                 matches_played, minutes, goals_against, goals_against_p90,
                 shots_on_target_against, saves, save_pct,
                 wins, draws, losses, clean_sheets, clean_sheets_pct,
                 pk_attempted, pk_allowed, pk_saved, pk_missed, pk_save_pct,
                 is_u23, source, date_maj)
            VALUES
                (:player_name, :born, :team, :nation, :ligue_id, :saison_id,
                 :matches_played, :minutes, :goals_against, :goals_against_p90,
                 :shots_on_target_against, :saves, :save_pct,
                 :wins, :draws, :losses, :clean_sheets, :clean_sheets_pct,
                 :pk_attempted, :pk_allowed, :pk_saved, :pk_missed, :pk_save_pct,
                 :is_u23, :source, :date_maj)
            ON CONFLICT (player_name, born, team, saison_id) DO UPDATE SET
                matches_played          = EXCLUDED.matches_played,
                minutes                 = EXCLUDED.minutes,
                goals_against           = EXCLUDED.goals_against,
                goals_against_p90       = EXCLUDED.goals_against_p90,
                shots_on_target_against = EXCLUDED.shots_on_target_against,
                saves                   = EXCLUDED.saves,
                save_pct                = EXCLUDED.save_pct,
                wins                    = EXCLUDED.wins,
                draws                   = EXCLUDED.draws,
                losses                  = EXCLUDED.losses,
                clean_sheets            = EXCLUDED.clean_sheets,
                clean_sheets_pct        = EXCLUDED.clean_sheets_pct,
                pk_attempted            = EXCLUDED.pk_attempted,
                pk_allowed              = EXCLUDED.pk_allowed,
                pk_saved                = EXCLUDED.pk_saved,
                pk_missed               = EXCLUDED.pk_missed,
                pk_save_pct             = EXCLUDED.pk_save_pct,
                is_u23                  = EXCLUDED.is_u23,
                date_maj                = EXCLUDED.date_maj
        """)
        execute_with_retry(engine, sql, rows, logger)

        total_upserted += len(rows)
        logger.info(f"  [OK] {league_id}|{saison} — {len(rows)} gardiens fbref")

    logger.info(f"  Total keepers_fbref : {total_upserted} lignes")


# ── 5. Sofascore gardiens ──────────────────────────────────────────────────────
def load_sofascore_keepers(engine, logger: logging.Logger):
    logger.info("[5/7] Chargement Sofascore gardiens → silver.keepers_sofascore")

    files = sorted(BRONZE_DIR.glob("*_sofascore_keepers.csv"))
    if not files:
        logger.warning("  Aucun fichier *_sofascore_keepers.csv trouvé dans bronze/")
        return

    total_upserted = 0

    for f in files:
        league_id = league_from_filename(f.name)
        saison    = saison_from_filename(f.name)
        if not league_id or not saison:
            continue

        try:
            df = pd.read_csv(f, low_memory=False)
        except Exception as e:
            logger.error(f"  Lecture {f.name}: {e}")
            continue

        col_rename = {
            "player_id": "player_id_ss",
            "goalsPrevented": "goals_prevented",
            "minutesPlayed": "minutes_played",
            "accuratePasses": "accurate_passes",
            "accurateLongBalls": "accurate_long_balls",
            "accurateLongBallsPercentage": "accurate_long_balls_pct",
            "yellowCards": "yellow_cards", "redCards": "red_cards",
        }
        df = df.rename(columns={k: v for k, v in col_rename.items() if k in df.columns})
        df["ligue_id"]  = league_id
        df["saison_id"] = saison
        df["is_u23"]    = None
        df["source"]    = "sofascore"
        df["date_maj"]  = datetime.now(timezone.utc)

        mins = pd.to_numeric(df.get("minutes_played"), errors="coerce")
        df["saves_p90"] = [calc_p90(v, m) for v, m in zip(df.get("saves", [None]*len(df)), mins)]

        silver_cols = [
            "player_id_ss","player_name","team_name","team_id","ligue_id","saison_id",
            "saves","goals_prevented","rating","minutes_played","appearances",
            "accurate_passes","accurate_long_balls","accurate_long_balls_pct",
            "yellow_cards","red_cards","saves_p90","is_u23","source","date_maj",
        ]
        for c in silver_cols:
            if c not in df.columns:
                df[c] = None
        df_out = df[silver_cols].copy()

        rows = to_records(df_out)
        sql = text("""
            INSERT INTO silver.keepers_sofascore
                (player_id_ss, player_name, team_name, team_id, ligue_id, saison_id,
                 saves, goals_prevented, rating, minutes_played, appearances,
                 accurate_passes, accurate_long_balls, accurate_long_balls_pct,
                 yellow_cards, red_cards, saves_p90, is_u23, source, date_maj)
            VALUES
                (:player_id_ss, :player_name, :team_name, :team_id, :ligue_id, :saison_id,
                 :saves, :goals_prevented, :rating, :minutes_played, :appearances,
                 :accurate_passes, :accurate_long_balls, :accurate_long_balls_pct,
                 :yellow_cards, :red_cards, :saves_p90, :is_u23, :source, :date_maj)
            ON CONFLICT (player_id_ss, team_id, saison_id) DO UPDATE SET
                saves                   = EXCLUDED.saves,
                goals_prevented         = EXCLUDED.goals_prevented,
                rating                  = EXCLUDED.rating,
                minutes_played          = EXCLUDED.minutes_played,
                appearances             = EXCLUDED.appearances,
                accurate_passes         = EXCLUDED.accurate_passes,
                accurate_long_balls     = EXCLUDED.accurate_long_balls,
                accurate_long_balls_pct = EXCLUDED.accurate_long_balls_pct,
                yellow_cards            = EXCLUDED.yellow_cards,
                red_cards               = EXCLUDED.red_cards,
                saves_p90               = EXCLUDED.saves_p90,
                date_maj                = EXCLUDED.date_maj
        """)
        execute_with_retry(engine, sql, rows, logger)

        total_upserted += len(rows)
        logger.info(f"  [OK] {f.name} — {len(rows)} gardiens sofascore")

    logger.info(f"  Total keepers_sofascore : {total_upserted} lignes")


# ── 6. keepers_combined ────────────────────────────────────────────────────────
def build_keepers_combined(engine, logger: logging.Logger):
    logger.info("[6/7] Construction silver.keepers_combined")

    with engine.connect() as conn:
        df_ss = pd.read_sql(text("""
            SELECT
                ks.player_id_ss, ks.player_name, ks.team_name, ks.team_id,
                ks.ligue_id, ks.saison_id,
                ks.saves AS saves_ss, ks.goals_prevented AS goals_prevented_ss,
                ks.rating AS rating_ss,
                ks.minutes_played AS minutes_ss,
                ks.appearances AS appearances_ss,
                ks.saves_p90, ks.accurate_long_balls_pct AS long_balls_pct,
                pi.annee_naissance AS born, pi.date_naissance, pi.is_u23, pi.nationalite_id
            FROM silver.keepers_sofascore ks
            LEFT JOIN silver.players_info pi ON ks.player_id_ss = pi.player_id_ss
        """), conn)

        df_fb_raw = pd.read_sql(text("""
            SELECT player_name, born, ligue_id, saison_id,
                   saves AS saves_fb, save_pct AS save_pct_fb,
                   goals_against AS goals_against_fb,
                   goals_against_p90 AS goals_against_p90_fb,
                   clean_sheets AS clean_sheets_fb,
                   clean_sheets_pct AS clean_sheets_pct_fb,
                   pk_saved AS pk_saved_fb
            FROM silver.keepers_fbref
        """), conn)

    df_fb_raw["name_norm"] = df_fb_raw["player_name"].apply(normalize_name)
    df_ss["name_norm"]     = df_ss["player_name"].apply(normalize_name)

    df_merged = df_ss.merge(
        df_fb_raw[["name_norm","born","ligue_id","saison_id",
                   "saves_fb","save_pct_fb","goals_against_fb","goals_against_p90_fb",
                   "clean_sheets_fb","clean_sheets_pct_fb","pk_saved_fb"]],
        on=["name_norm","born","ligue_id","saison_id"],
        how="left",
    )

    df_merged["has_fbref_data"]     = df_merged["saves_fb"].notna()
    df_merged["has_sofascore_data"] = df_merged["saves_ss"].notna()
    df_merged["date_maj"]           = datetime.now(timezone.utc)

    silver_cols = [
        "player_id_ss","player_name","born","date_naissance","is_u23","nationalite_id",
        "team_name","team_id","ligue_id","saison_id",
        "saves_ss","goals_prevented_ss","rating_ss","minutes_ss","appearances_ss",
        "saves_fb","save_pct_fb","goals_against_fb","goals_against_p90_fb",
        "clean_sheets_fb","clean_sheets_pct_fb","pk_saved_fb","saves_p90","long_balls_pct",
        "has_fbref_data","has_sofascore_data","date_maj",
    ]
    for c in silver_cols:
        if c not in df_merged.columns:
            df_merged[c] = None
    df_out = df_merged[silver_cols].copy()

    sql = text("""
        INSERT INTO silver.keepers_combined
            (player_id_ss, player_name, born, date_naissance, is_u23, nationalite_id,
             team_name, team_id, ligue_id, saison_id,
             saves_ss, goals_prevented_ss, rating_ss, minutes_ss, appearances_ss,
             saves_fb, save_pct_fb, goals_against_fb, goals_against_p90_fb,
             clean_sheets_fb, clean_sheets_pct_fb, pk_saved_fb, saves_p90, long_balls_pct,
             has_fbref_data, has_sofascore_data, date_maj)
        VALUES
            (:player_id_ss, :player_name, :born, :date_naissance, :is_u23, :nationalite_id,
             :team_name, :team_id, :ligue_id, :saison_id,
             :saves_ss, :goals_prevented_ss, :rating_ss, :minutes_ss, :appearances_ss,
             :saves_fb, :save_pct_fb, :goals_against_fb, :goals_against_p90_fb,
             :clean_sheets_fb, :clean_sheets_pct_fb, :pk_saved_fb, :saves_p90, :long_balls_pct,
             :has_fbref_data, :has_sofascore_data, :date_maj)
        ON CONFLICT (player_id_ss, saison_id, team_id) DO UPDATE SET
            player_name         = EXCLUDED.player_name,
            born                = EXCLUDED.born,
            date_naissance      = EXCLUDED.date_naissance,
            is_u23              = EXCLUDED.is_u23,
            nationalite_id      = EXCLUDED.nationalite_id,
            saves_ss            = EXCLUDED.saves_ss,
            goals_prevented_ss  = EXCLUDED.goals_prevented_ss,
            rating_ss           = EXCLUDED.rating_ss,
            minutes_ss          = EXCLUDED.minutes_ss,
            appearances_ss      = EXCLUDED.appearances_ss,
            saves_fb            = EXCLUDED.saves_fb,
            save_pct_fb         = EXCLUDED.save_pct_fb,
            goals_against_fb    = EXCLUDED.goals_against_fb,
            goals_against_p90_fb= EXCLUDED.goals_against_p90_fb,
            clean_sheets_fb     = EXCLUDED.clean_sheets_fb,
            clean_sheets_pct_fb = EXCLUDED.clean_sheets_pct_fb,
            pk_saved_fb         = EXCLUDED.pk_saved_fb,
            saves_p90           = EXCLUDED.saves_p90,
            long_balls_pct      = EXCLUDED.long_balls_pct,
            has_fbref_data      = EXCLUDED.has_fbref_data,
            has_sofascore_data  = EXCLUDED.has_sofascore_data,
            date_maj            = EXCLUDED.date_maj
    """)

    rows = to_records(df_out)
    execute_with_retry(engine, sql, rows, logger)

    logger.info(f"  [OK] keepers_combined — {len(rows)} lignes upsertées")


# ── 7. Vérification ────────────────────────────────────────────────────────────
def verify(engine, logger: logging.Logger):
    tables = [
        "silver.ref_ligues", "silver.ref_saisons", "silver.ref_postes",
        "silver.ref_pays", "silver.ref_nationalites",
        "silver.players_info", "silver.players_fbref", "silver.players_sofascore",
        "silver.players_combined", "silver.keepers_fbref", "silver.keepers_sofascore",
        "silver.keepers_combined",
    ]
    logger.info("")
    logger.info("=" * 55)
    logger.info("  VERIFICATION — Row counts Silver")
    logger.info("=" * 55)
    with engine.connect() as conn:
        for tbl in tables:
            try:
                result = conn.execute(text(f"SELECT COUNT(*) FROM {tbl}"))
                count  = result.scalar()
                logger.info(f"  {tbl:<40} {count:>7} lignes")
            except Exception as e:
                logger.warning(f"  {tbl:<40} ERREUR: {e}")
    logger.info("=" * 55)


# ── Point d'entrée ─────────────────────────────────────────────────────────────
def run():
    logger = setup_logger()
    engine = get_engine()

    logger.info("=" * 65)
    logger.info("  RadarPepites — Silver Transformer")
    logger.info(f"  {datetime.now():%Y-%m-%d %H:%M:%S}")
    logger.info("=" * 65)

    load_players_info(engine, logger)
    load_fbref_players(engine, logger)
    load_sofascore_players(engine, logger)
    build_players_combined(engine, logger)
    load_fbref_keepers(engine, logger)
    load_sofascore_keepers(engine, logger)
    build_keepers_combined(engine, logger)
    verify(engine, logger)

    logger.info("")
    logger.info("  Silver Transformer termine avec succes.")


if __name__ == "__main__":
    run()

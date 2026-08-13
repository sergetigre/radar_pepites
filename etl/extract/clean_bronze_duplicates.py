"""
etl/extract/clean_bronze_duplicates.py
RadarPépites — archive les doublons bronze (mêmes ligue x saison x suffixe).

Pour chaque combinaison (ligue, saison, suffixe), ne garde à la racine que le
fichier le plus récent (timestamp dans le nom) ; les autres sont déplacés
(jamais supprimés) vers data/bronze/_ARCHIVES_DOUBLONS/.

Usage :
  python etl/extract/clean_bronze_duplicates.py
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BRONZE_DIR = ROOT / "data" / "bronze"
ARCHIVE_DIR = BRONZE_DIR / "_ARCHIVES_DOUBLONS"

# {ts}_{LIGUE}_{SAISON}_{suffixe}.csv  ex: 20260811_164442_ENG_20232024_sofascore_players.csv
PATTERN = re.compile(r"^(\d{8}_\d{6})_([A-Z]{3})_(\d{8})_(.+)\.csv$")


def clean_bronze_duplicates(bronze_dir: Path = BRONZE_DIR, archive_dir: Path = ARCHIVE_DIR):
    archive_dir.mkdir(exist_ok=True)

    groups: dict[str, list[tuple[str, Path]]] = {}
    unmatched = []
    for f in bronze_dir.glob("*.csv"):
        m = PATTERN.match(f.name)
        if not m:
            unmatched.append(f.name)
            continue
        ts, ligue, saison, suffixe = m.groups()
        key = f"{ligue}_{saison}_{suffixe}"
        groups.setdefault(key, []).append((ts, f))

    archived = 0
    for key, files in groups.items():
        if len(files) <= 1:
            continue
        files.sort(key=lambda x: x[0], reverse=True)
        for ts, f in files[1:]:
            f.rename(archive_dir / f.name)
            archived += 1

    print(f"Combinaisons ligue/saison/suffixe : {len(groups)}")
    print(f"Fichiers archives dans {archive_dir.name}/ : {archived}")
    if unmatched:
        print(f"Fichiers ignores (nom hors pattern) : {len(unmatched)}")
        for name in unmatched:
            print(f"  - {name}")
    return archived


if __name__ == "__main__":
    clean_bronze_duplicates()

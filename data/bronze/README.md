# data/bronze — Données brutes RadarPépites

Fichiers CSV horodatés (`YYYYMMDD_HHMMSS_<LIGUE>_<SAISON>_<type>.csv`), un fichier par extraction. En cas de re-scraping, garder la version la plus récente par (ligue, saison, type) et archiver/supprimer les précédentes (voir historique de nettoyage des doublons).

## Fichiers par type

| Suffixe | Source | Script d'origine | Contenu | Couverture | Nb fichiers | Taille |
|---------|--------|-------------------|---------|------------|-------------|--------|
| `_standard.csv` | fbref via soccerdata | `etl/extract/fbref_scraper.py` | Stats standard (buts, passes déc., minutes, cartons...) | Big 5 (ENG, ESP, GER, ITA, FRA), 2023-2024 à 2025-2026 | 15 | 1.33 MB |
| `_shooting.csv` | fbref via soccerdata | `etl/extract/fbref_scraper.py` | Stats de tir (tirs, tirs cadrés, xG...) | Big 5, 2023-2024 à 2025-2026 | 15 | 1.19 MB |
| `_playing_time.csv` | fbref via soccerdata | `etl/extract/fbref_scraper.py` | Temps de jeu (titularisations, minutes, remplacements) | Big 5, 2023-2024 à 2025-2026 | 15 | 1.66 MB |
| `_misc.csv` | fbref via soccerdata | `etl/extract/fbref_scraper.py` | Stats diverses (fautes, duels aériens, tacles...) | Big 5, 2023-2024 à 2025-2026 | 15 | 1.11 MB |
| `_datafc.csv` | Sofascore via datafc | `etl/extract/datafc_scraper.py` | Stats avancées par joueur (rating, xG, passes, dribbles, tacles, interceptions, clearances, minutes...) | 10 ligues, 2023-2024 à 2025-2026 | 30 | 24.56 MB |
| `_standings.csv` | Sofascore via datafc | `etl/extract/datafc_scraper.py` | Classements par championnat/saison | 10 ligues, 2023-2024 à 2025-2026 | 30 | 0.25 MB |
| `_squad.csv` | Sofascore via datafc | `etl/extract/datafc_scraper.py` | Effectifs par équipe/saison | 10 ligues, 2023-2024 à 2025-2026 | 30 | 3.29 MB |
| `_players_info.csv` | Sofascore via datafc | `etl/extract/datafc_players_info.py` | Infos bio joueurs (nom, date de naissance, nationalité, poste, taille, pied) et infos équipes | 10 ligues, 2023-2024 à 2025-2026 | 30 | 2.58 MB |

**Total : 180 fichiers CSV, 37.45 MB**

## Ligues et saisons couvertes
10 championnats (ENG, ESP, GER, ITA, FRA, POR, NED, BEL, TUR, AUT), saisons 2023-2024, 2024-2025, 2025-2026.

> Note : les stats fbref (standard/shooting/playing_time/misc) ne couvrent que le Big 5 (ENG, ESP, GER, ITA, FRA) — fbref n'expose pas ces stats détaillées pour POR/NED/BEL/TUR/AUT (voir `etl/extract/README.md`).

## Fichiers hors schéma
- `Fbref TOP 5.zip` (1.5 MB) — archive zip, ne suit pas la convention de nommage CSV horodaté. À vérifier manuellement (contenu non audité automatiquement) avant de décider de le conserver, l'extraire ou le supprimer.

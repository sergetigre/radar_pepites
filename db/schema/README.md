# db/schema — RadarPépites

## Architecture 3 schémas

### Schéma public (Gold)
Tables finales consommées par Power BI et Streamlit.
dim_* + fact_stats

### Schéma silver
Données nettoyées et transformées.
ref_* (référentiels) + players_* + keepers_*

### Schéma gold
Vues agrégées pour analyses.
vue_top_u23_par_ligue, vue_radar_joueur, vue_progression_saison

## Ordre d'exécution
01_create_schemas.sql
02_create_silver_referentiels.sql
03_insert_silver_referentiels.sql
04_create_silver_tables.sql
05_create_public_tables.sql
06_create_gold_views.sql
07_create_indexes.sql

## Sources de données
- fbref via soccerdata → Big 5 (ENG, ESP, GER, ITA, FRA)
- Sofascore via datafc → 10 ligues
- Saisons couvertes : 2022-2023 à 2025-2026

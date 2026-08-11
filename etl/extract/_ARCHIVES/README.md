# etl/extract — Scripts d'extraction RadarPépites

## Scripts actifs

| Script | Source | Ligues | Stats |
|--------|--------|--------|-------|
| fbref_scraper.py | fbref via soccerdata | Big 5 (ENG, ESP, GER, ITA, FRA) | standard, shooting, playing_time, misc |
| datafc_scraper.py | Sofascore via datafc | 10 ligues | rating, goals, assists, xG, passes, dribbles, tacles, interceptions, clearances, minutes... |
| datafc_players_info.py | Sofascore via datafc | 10 ligues | Infos bio : nom, DOB, nationalité, poste, taille, pied |

## Sources abandonnées (voir _ARCHIVES/)
- FotMob : endpoints API instables (404)
- Sofascore direct : HTTP 403 systématique
- fbref avancé (requests/BS4) : HTTP 403 Cloudflare
- fbref Playwright : Cloudflare trop agressif même avec profil Chrome
- Anciennes versions (`_old_*`) : versions antérieures des 3 scripts actifs, conservées pour référence

## Données manquantes
- Passes progressives, courses progressives : non disponibles sur Sofascore pour ligues 6-10
- Stats avancées fbref (passing, defense, possession) pour POR, NED, BEL, TUR, AUT

## Configuration
Tous les scripts lisent config/scraping_config.json pour :
- La liste des ligues actives (actif: true/false)
- Les saisons à scraper
- Les types de stats

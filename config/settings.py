# RadarPépites - Configuration globale

PROJECT_NAME = "RadarPépites"
SEASON = "2024-2025"
BIRTH_YEAR_CUTOFF = 2002  # Joueurs nés après cette année

LEAGUES = [
    "ENG-Premier League",
    "ESP-La Liga",
    "GER-Bundesliga",
    "ITA-Serie A",
    "FRA-Ligue 1",
    "POR-Primeira Liga",
    "NED-Eredivisie",
    "BEL-First Division A",
    "TUR-Super Lig",
    "AUT-Bundesliga",
]

# Répertoires
DIR_BRONZE = "data/bronze"
DIR_SILVER = "data/silver"
DIR_GOLD   = "data/gold"
DIR_LOGS   = "logs"

# Délai entre requêtes scraping (secondes) - respecter le rate-limit fbref
SCRAPING_DELAY = 3

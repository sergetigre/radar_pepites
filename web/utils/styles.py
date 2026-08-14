def inject_css():
    """CSS custom injecté dans toutes les pages."""
    return """
    <style>
        /* Score Pépite badge */
        .score-badge {
            display: inline-block;
            background: linear-gradient(135deg, #1DB954, #00ff88);
            color: #000;
            font-weight: 800;
            font-size: 1.4rem;
            padding: 8px 20px;
            border-radius: 50px;
            margin: 8px 0;
        }

        /* Carte joueur */
        .player-card {
            background: #1E2130;
            border-radius: 12px;
            padding: 16px;
            border-left: 4px solid #1DB954;
            margin-bottom: 12px;
        }

        /* Header ligue coloré */
        .ligue-header {
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
            opacity: 0.7;
        }

        /* Metric positive/negative */
        .delta-pos { color: #1DB954; font-weight: 700; }
        .delta-neg { color: #FF6B35; font-weight: 700; }

        /* Masquer le menu Streamlit en prod */
        #MainMenu { visibility: hidden; }
        footer     { visibility: hidden; }

        /* Tableau stylé */
        .dataframe tbody tr:hover {
            background-color: #2D3250 !important;
        }
    </style>
    """

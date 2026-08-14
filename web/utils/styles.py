def get_material_icons_link() -> str:
    return """
    <link href="https://fonts.googleapis.com/icon?family=Material+Icons+Outlined"
          rel="stylesheet">
    """


def icon(name: str, size: int = 20, color: str = "#2DAD7E") -> str:
    """Retourne un Material Icon inline (une seule ligne — voir render_html)."""
    return (
        f'<span class="material-icons-outlined" '
        f'style="font-size:{size}px;color:{color};'
        f'vertical-align:middle;line-height:1;">{name}</span>'
    )


def render_html(html: str):
    """st.markdown(unsafe_allow_html=True) sur du HTML multi-lignes indenté
    est parfois réinterprété par le parser Markdown comme un bloc de code
    indenté (les balises se retrouvent alors échappées et affichées en
    texte brut). On aplatit chaque bloc HTML sur une ligne par élément,
    sans indentation ni ligne vide, avant de le passer à st.markdown."""
    import streamlit as st
    flat = " ".join(line.strip() for line in html.strip().splitlines() if line.strip())
    st.markdown(flat, unsafe_allow_html=True)


def inject_css() -> str:
    return get_material_icons_link() + """
    <style>

    /* ── Base ─────────────────────────────────────────── */
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
        max-width: 1400px;
    }

    /* ── Sidebar ─────────────────────────────────────── */
    [data-testid="stSidebar"] {
        background: #0D0D0D;
        min-width: 260px !important;
        max-width: 280px !important;
        border-right: 1px solid #1A1A1A;
    }
    [data-testid="stSidebar"] .stCheckbox label {
        font-size: 0.82rem;
        color: #FFFFFF;
    }

    /* ── Masquer la navigation native Streamlit (doublon avec le nav custom) */
    [data-testid="stSidebarNav"] {
        display: none;
    }

    /* ── Nav item ────────────────────────────────────── */
    .nav-item {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 9px 8px;
        border-radius: 8px;
        margin: 2px 0;
        font-size: 0.9rem;
        font-weight: 500;
        transition: all 0.15s ease;
        cursor: pointer;
    }
    /* Spécificité renforcée : le style de lien par défaut de Streamlit
       (bleu souligné, injecté sur [data-testid="stMarkdownContainer"] a)
       l'emporte sinon sur .nav-item seul. */
    [data-testid="stSidebar"] a.nav-item,
    [data-testid="stSidebar"] a.nav-item:visited {
        color: #8A8A8A !important;
        text-decoration: none !important;
    }
    [data-testid="stSidebar"] a.nav-item:hover {
        background: #111111;
        color: #FFFFFF !important;
    }
    [data-testid="stSidebar"] a.nav-item.active {
        background: #2DAD7E;
        color: #000000 !important;
        font-weight: 700;
    }
    .nav-item.active .material-icons-outlined {
        color: #000000 !important;
    }
    .nav-section {
        font-size: 0.65rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 2px;
        color: #8A8A8A;
        padding: 14px 8px 6px 8px;
        margin-top: 4px;
    }

    /* ── Cards ───────────────────────────────────────── */
    .card {
        background: #111111;
        border-radius: 12px;
        padding: 16px;
        border: 1px solid #1A1A1A;
        margin-bottom: 12px;
    }
    .card-accent {
        border-left: 3px solid #2DAD7E;
    }
    .card:hover {
        border-color: #2DAD7E;
        transition: border-color 0.2s;
    }

    /* ── Carte pépite cliquable (lien enveloppant) ───────────────────── */
    a.player-card-link {
        text-decoration: none;
        display: block;
    }
    .player-mini-card {
        cursor: pointer;
        transition: border-color 0.2s, transform 0.15s;
    }
    .player-mini-card:hover {
        border-color: #2DAD7E;
        transform: translateY(-2px);
    }
    .player-mini-card .pmc-name {
        display: flex;
        align-items: center;
        gap: 6px;
        font-weight: 700;
        color: #FFFFFF;
        font-size: 0.95rem;
        margin-bottom: 8px;
    }
    .player-mini-card .pmc-league {
        font-size: 0.65rem;
        color: #8A8A8A;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .player-mini-card .pmc-details {
        font-size: 0.8rem;
        color: #8A8A8A;
        margin: 4px 0 10px 0;
    }

    /* ── Score badge ─────────────────────────────────── */
    .score-badge {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        background: linear-gradient(135deg, #2DAD7E, #5DCBA0);
        color: #000000;
        font-weight: 800;
        font-size: 1.5rem;
        width: 64px;
        height: 64px;
        border-radius: 12px;
    }
    .score-badge-sm {
        display: inline-block;
        background: #2DAD7E;
        color: #000000;
        font-weight: 700;
        font-size: 0.85rem;
        padding: 3px 10px;
        border-radius: 6px;
    }

    /* ── Barre percentile ────────────────────────────── */
    .pct-bar-container {
        margin: 6px 0;
    }
    .pct-bar-label {
        display: flex;
        justify-content: space-between;
        font-size: 0.8rem;
        color: #8A8A8A;
        margin-bottom: 3px;
    }
    .pct-bar-label span:last-child {
        color: #FFFFFF;
        font-weight: 600;
    }
    .pct-bar-track {
        height: 6px;
        background: #1A1A1A;
        border-radius: 3px;
        overflow: hidden;
    }
    .pct-bar-fill {
        height: 100%;
        border-radius: 3px;
        transition: width 0.3s ease;
    }

    /* ── Header joueur ───────────────────────────────── */
    .player-header {
        background: #111111;
        border: 1px solid #1A1A1A;
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 24px;
    }
    .player-name {
        font-size: 1.8rem;
        font-weight: 800;
        color: #FFFFFF;
        margin: 0 0 4px 0;
    }
    .player-club {
        font-size: 0.9rem;
        color: #8A8A8A;
    }
    .player-badge {
        display: inline-block;
        background: #1A1A1A;
        border: 1px solid #2DAD7E22;
        color: #FFFFFF;
        font-size: 0.8rem;
        padding: 4px 10px;
        border-radius: 6px;
        margin: 3px 3px 3px 0;
    }

    /* ── Profil similaire ────────────────────────────── */
    .similar-card {
        background: #111111;
        border: 1px solid #1A1A1A;
        border-radius: 10px;
        padding: 12px 14px;
        margin-bottom: 8px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .similar-pct {
        color: #2DAD7E;
        font-weight: 700;
        font-size: 1rem;
    }

    /* ── Points forts / axes ─────────────────────────── */
    .strength-item {
        background: #0F5436;
        border-left: 3px solid #2DAD7E;
        border-radius: 0 8px 8px 0;
        padding: 8px 12px;
        margin: 5px 0;
        font-size: 0.85rem;
        color: #FFFFFF;
    }
    .weakness-item {
        background: #3D1A1A;
        border-left: 3px solid #E05252;
        border-radius: 0 8px 8px 0;
        padding: 8px 12px;
        margin: 5px 0;
        font-size: 0.85rem;
        color: #FFFFFF;
    }

    /* ── Terrain SVG wrapper ─────────────────────────── */
    .pitch-container {
        display: flex;
        justify-content: center;
        align-items: center;
    }

    /* ── Tableau ─────────────────────────────────────── */
    .dataframe { font-size: 0.83rem !important; }
    [data-testid="metric-container"] {
        background: #111111;
        border-radius: 10px;
        padding: 12px;
        border: 1px solid #1A1A1A;
    }

    /* ── Stat counter ────────────────────────────────── */
    .stat-counter {
        display: inline-block;
        background: #2DAD7E22;
        border: 1px solid #2DAD7E;
        color: #2DAD7E;
        font-size: 0.8rem;
        font-weight: 700;
        padding: 2px 10px;
        border-radius: 20px;
        margin-left: 8px;
    }
    .stat-counter.full { background: #2DAD7E; color: #000; }

    /* ── Tabs ────────────────────────────────────────── */
    .stTabs [data-baseweb="tab-list"] {
        background: #111111;
        border-radius: 10px;
        padding: 4px;
        gap: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        color: #8A8A8A;
        padding: 8px 20px;
    }
    .stTabs [aria-selected="true"] {
        background: #2DAD7E !important;
        color: #000000 !important;
        font-weight: 700;
    }

    /* ── Style du composant streamlit-searchbox (autocomplete) ──────── */
    div[data-baseweb="select"] {
        background: #111111 !important;
        border-radius: 8px !important;
    }
    div[data-baseweb="select"] > div {
        background: #111111 !important;
        border-color: #1A1A1A !important;
        color: #FFFFFF !important;
    }
    div[data-baseweb="popover"] ul {
        background: #111111 !important;
        border: 1px solid #2DAD7E !important;
    }
    div[data-baseweb="popover"] li {
        color: #FFFFFF !important;
    }
    div[data-baseweb="popover"] li:hover {
        background: #1A1A1A !important;
        color: #2DAD7E !important;
    }

    /* ── Masquer éléments Streamlit ──────────────────── */
    #MainMenu { visibility: hidden; }
    footer    { visibility: hidden; }
    header    { visibility: hidden; }
    /* Le bouton pour rouvrir la sidebar une fois repliée vit dans ce même
       <header> masqué ci-dessus — sans cette ligne, impossible de la
       rouvrir une fois fermée. */
    [data-testid="stExpandSidebarButton"] {
        visibility: visible !important;
    }

    /* Réduire légèrement la police des checkboxes de ligues pour accueillir
       les noms complets sans retour à la ligne */
    [data-testid="stSidebar"] .stCheckbox label p {
        font-size: 0.78rem !important;
        line-height: 1.2;
    }

    /* ── Boutons ─────────────────────────────────────── */
    .stButton button {
        border-radius: 8px;
        font-weight: 600;
        border: 1px solid #2DAD7E;
        color: #2DAD7E;
        background: transparent;
    }
    .stButton button:hover {
        background: #2DAD7E;
        color: #000;
    }

    /* ── Responsive ──────────────────────────────────── */
    @media (max-width: 768px) {
        .block-container {
            padding-left: 0.5rem;
            padding-right: 0.5rem;
        }
        [data-testid="stSidebar"] {
            min-width: 100% !important;
        }
        /* Streamlit masque la sidebar repliée avec un décalage fixe
           (-300px), calibré pour sa largeur desktop (~280px). Sur mobile
           elle fait 100% de l'écran (ci-dessus), donc ce décalage fixe ne
           suffit plus à la sortir entièrement de l'écran — on le remplace
           par un décalage relatif à sa propre largeur, qui reste correct
           quelle que soit la taille d'écran. */
        [data-testid="stSidebar"][aria-expanded="false"] {
            transform: translateX(-100%) !important;
        }
        .player-name { font-size: 1.3rem; }
    }

    </style>
    """

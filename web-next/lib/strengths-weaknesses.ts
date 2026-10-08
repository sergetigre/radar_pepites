// Portage 1:1 de web/utils/components.py::render_strengths_weaknesses()
// PCT_INTERPRETATIONS — col -> [label court, phrase point fort, phrase point faible].
export const PCT_INTERPRETATIONS: Record<string, [string, string, string]> = {
  pct_goals_p90: [
    "Buts/90",
    "Finisseur redoutable — il marque bien plus que la moyenne à son poste.",
    "Peu efficace devant le but — ses buts marqués restent rares pour son poste.",
  ],
  pct_xg_p90: [
    "xG/90",
    "Se crée énormément d'occasions de qualité — souvent bien placé pour marquer.",
    "Se crée peu d'occasions franches — rarement dans une position dangereuse.",
  ],
  pct_assists_p90: [
    "Assists/90",
    "Excellent passeur décisif — il offre beaucoup de buts à ses coéquipiers.",
    "Peu de passes décisives — il contribue peu directement aux buts de l'équipe.",
  ],
  pct_xag_p90: [
    "xAG/90",
    "Toujours impliqué dans les occasions créées — un vrai facteur offensif.",
    "Peu impliqué dans la création d'occasions pour ses coéquipiers.",
  ],
  pct_shots_p90: [
    "Tirs/90",
    "Très présent devant le but — il n'hésite pas à tenter sa chance.",
    "Tire peu au but — il cherche rarement à conclure lui-même.",
  ],
  pct_tirs_cadres_p90: [
    "Tirs cadrés/90",
    "Précis dans ses tentatives — une grande partie de ses tirs cadre le but.",
    "Manque de précision — peu de ses tirs trouvent le cadre.",
  ],
  pct_key_passes_p90: [
    "Passes clés/90",
    "Grand créateur — ses passes amènent souvent une occasion de but.",
    "Peu de passes clés — il participe peu à la construction des occasions.",
  ],
  pct_dribbles_p90: [
    "Dribbles/90",
    "Très à l'aise balle au pied — il élimine souvent son adversaire direct.",
    "Dribble peu — il préfère les solutions simples plutôt que le un-contre-un.",
  ],
  pct_tackles_p90: [
    "Tacles/90",
    "Très actif défensivement — il multiplie les tacles pour récupérer le ballon.",
    "Peu engagé dans les duels au sol — il tacle rarement pour reprendre le ballon.",
  ],
  pct_interceptions_p90: [
    "Interceptions/90",
    "Excellent lecteur du jeu — il coupe souvent les lignes de passes adverses.",
    "Anticipe peu les passes adverses — ses interceptions restent rares.",
  ],
  pct_degagements_p90: [
    "Dégagements/90",
    "Très présent pour dégager le danger — un vrai pilier défensif.",
    "Peu de dégagements — il intervient rarement pour repousser le danger.",
  ],
  pct_duels_aeriens_pct: [
    "Duels aériens",
    "Dominant dans les airs — il gagne la grande majorité de ses duels aériens.",
    "Fragile dans le jeu aérien — il perd souvent ses duels en l'air.",
  ],
  pct_passes_pct: [
    "Précision passes",
    "Très fiable techniquement — il perd très peu de ballons dans ses passes.",
    "Manque de précision dans les passes — il perd le ballon plus souvent que la moyenne.",
  ],
  pct_saves_p90: [
    "Arrêts/90",
    "Très sollicité et efficace — il multiplie les arrêts décisifs.",
    "Peu d'arrêts marquants comparé aux autres gardiens à son niveau.",
  ],
  pct_goals_prevented: [
    "Buts évités",
    "Change le cours des matchs — il évite nettement plus de buts que la moyenne attendue.",
    "Concède plus de buts que ce qu'un gardien moyen aurait laissé passer dans la même situation.",
  ],
  pct_save_pct: [
    "% Arrêts",
    "Taux d'arrêt impressionnant — il détourne une très grande majorité des tirs cadrés.",
    "Taux d'arrêt en retrait — il détourne moins de tirs que la moyenne des gardiens.",
  ],
  pct_clean_sheets_pct: [
    "Clean sheets %",
    "Garde souvent sa cage inviolée — un vrai gage de solidité défensive.",
    "Garde rarement sa cage inviolée comparé aux autres gardiens.",
  ],
  pct_long_balls_pct: [
    "Passes longues %",
    "Très précis dans le jeu long — une vraie arme pour relancer ou changer le jeu.",
    "Peu fiable sur les longues relances — ses passes longues aboutissent rarement.",
  ],
};

# RadarPépites — Notice d'utilisation

Site : **https://radarpepites.vercel.app**

RadarPépites analyse les joueurs U23 (moins de 23 ans) de 10 championnats
européens et calcule pour chacun un **Score Pépite** — une note unique qui
permet de comparer des joueurs à des postes différents et dans des ligues de
niveaux différents.

---

## 1. Prise en main

### Langue et thème

En haut de la barre latérale gauche :
- **FR / EN / ES** — change la langue de toute l'interface (sauf le jargon
  foot : xG, CB, RW, Key Passes... reste identique dans les 3 langues,
  volontairement).
- **Clair / Sombre** — bascule le thème.

Les deux choix sont mémorisés (cookie), pas besoin de les refaire à chaque
visite.

### Filtres

Dans le panneau **Filtres** (repliable) de la barre latérale :
- **Saison** — une des 4 saisons disponibles (2023-2024 → 2026-2027).
- **Ligues** — les 10 championnats, cochables individuellement ou via
  *Tout* / *Aucun*.
- **Postes** — regroupés par famille (Attaquants / Milieux / Défenseurs),
  mêmes boutons *Tout* / *Aucun*.

Ces filtres s'appliquent au Tableau de bord, à Explorer, à Golden boys et au
Classement Gardiens. Les pages Radar/Comparaison/Progression n'en ont pas
besoin : on y cherche un joueur précis par son nom.

---

## 2. Les pages

### Tableau de bord (`/`)

Vue d'ensemble sur la sélection filtrée : nombre de joueurs U23, nombre de
ligues, score moyen, meilleur score, le classement **Top 10 Score Pépite**,
le nuage de points **xG vs Buts** (logo du club comme marqueur), et une carte
par ligue montrant sa meilleure pépite du moment.

### Golden boys (`/championnats`)

Vue recrutement, sur une ou plusieurs ligues à la fois, avec un filtre
**Nationalité** en plus des filtres globaux :
- **Top 5 par catégorie** — Buteurs, Passeurs, Dribbleurs, Défenseurs,
  Créateurs, Gardiens (Arrêts/90), onglet par onglet.
- **Onze type proposé** — un titulaire + des doublures par poste, toutes
  ligues/nationalités sélectionnées confondues.
- **Pépites sous-cotées** — Score Pépite dans le top 20 % de la sélection
  mais temps de jeu sous la médiane : des joueurs au potentiel pas encore
  pleinement exploité (peu de minutes).

### Radar Joueur / Radar GK

Recherchez un joueur par son nom (2 lettres minimum). La fiche affiche :
position sur le terrain, radar des stats clés du poste (comparé à la
moyenne), percentiles détaillés par catégorie (Offensif/Passes/Défense),
points forts et axes d'amélioration en langage clair, et les profils de
joueurs similaires.

### Comparaison / Comparaison GK

Choisissez deux joueurs (ou le même joueur sur deux saisons différentes) :
radar superposé + tableau de stats détaillées. Pour les joueurs de champ, un
sélecteur libre permet de choisir 4 à 8 stats à comparer.

### Progression / Progression GK

Suivez l'évolution saison par saison d'un joueur : courbe ou barres
groupées, saisons et métriques sélectionnables, tableau détaillé en dessous
(meilleure valeur en vert, pire en rouge atténué).

### Explorer et Classement Gardiens — accès direct uniquement

Ces deux pages ne sont **pas dans le menu** (comportement hérité de
l'ancienne version du site) :
- Explorer : **https://radarpepites.vercel.app/explorer**
- Classement Gardiens : **https://radarpepites.vercel.app/classement-gk**

Explorer liste tous les joueurs filtrés en tableau triable, exportable en
CSV, avec un onglet Graphiques. Classement Gardiens trie par Arrêts/90 (pas
par Score Pépite, volontairement, pour rester fidèle à l'original).

---

## 3. Comprendre le Score Pépite

Un joueur n'obtient un Score Pépite pour une saison donnée **qu'à partir de
450 minutes jouées** (270 minutes pour un gardien). En dessous, pas assez de
matchs pour un score fiable — le joueur reste invisible dans les classements
tant qu'il n'a pas atteint ce seuil, même s'il apparaît déjà dans les listes
Radar/Comparaison/Progression (ces pages-là n'ont pas besoin d'un score).

Une fois le seuil franchi, le score combine :
- des **percentiles par poste et par saison** (chaque stat comparée aux
  autres joueurs du même poste, pas à tout le monde),
- une **pondération propre à chaque poste** (un latéral et un attaquant ne
  sont pas jugés sur les mêmes critères),
- une **correction par niveau de ligue**.

Plus de détail technique dans `etl/load/gold_builder.py`.

---

## 4. Problème connu

Les logos clubs/ligues et photos joueurs sont hébergés directement en base
(`public.media_assets`) — pas de dépendance à un service externe au moment
où vous consultez le site. S'il manque un logo ou une photo, c'est que
Sofascore n'en fournit tout simplement pas pour cette entité (pas une panne
du site).

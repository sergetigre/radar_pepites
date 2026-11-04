# Pipeline RadarPépites — Notice d'utilisation

Outil **local uniquement**, séparé du site public (`web-next`) : la
collecte ouvre un vrai navigateur Chrome pour contourner la protection
Cloudflare de Sofascore, ce qui ne peut tourner que sur votre machine —
jamais sur Vercel, jamais depuis le site déployé.

---

## 1. Prérequis

- Python avec les dépendances du projet (`pip install -r requirements.txt`).
- Google Chrome installé (utilisé par `undetected-chromedriver`).
- `config/.env` avec `DATABASE_URL` renseignée (même base Neon que le site).
- Pour la vue visuelle (section 2) : Node.js + `npm install` une première
  fois dans `tools/pipeline-ui/` (même `DATABASE_URL` à copier dans
  `tools/pipeline-ui/.env.local`).
- Si le bouton ▶ ne fait rien (exécution instantanée sans logs) : ajouter
  `PYTHON_BIN=<chemin complet vers python.exe>` dans
  `tools/pipeline-ui/.env.local`. Sur certaines installs Windows, la
  commande `python` nue pointe vers le stub "App Execution Alias" du
  Microsoft Store, qui plante silencieusement quand il est lancé depuis
  Node.js (pas depuis un terminal) — trouver le vrai chemin avec
  `where python` en PowerShell (prendre l'entrée qui n'est **pas** dans
  `AppData\Local\Microsoft\WindowsApps`).

---

## 2. Vue visuelle (recommandé)

Les étapes affichées comme des nœuds reliés par des flèches (ordre réel des
dépendances), cliquables pour voir le détail et lancer :

```bash
cd tools/pipeline-ui
npm run dev
```

Ouvre `http://localhost:3000`. Chaque nœud a son propre bouton **▶** (lance
l'étape directement) qui devient **⏹** pendant l'exécution (arrête
proprement — tue tout l'arbre de processus, y compris le navigateur
Chrome si l'étape en avait ouvert un). Cliquer sur le nœud (pas sur le
bouton) ouvre un panneau à droite avec sa description, son dernier succès,
les logs en direct pendant l'exécution, et ses derniers runs. Le point de
couleur sur chaque nœud indique son état : gris = jamais exécuté, jaune =
en cours, vert = succès, rouge = échec, gris foncé = arrêté manuellement.

Pas de **Pause** : les scripts Python n'ont pas de mécanisme pour
suspendre puis reprendre une collecte en cours (contrairement à Images,
qui est incrémental et peut être relancé sans tout refaire, FBref/Sofascore
repartiraient de zéro). Arrêter puis relancer plus tard est l'équivalent
pratique.

C'est un **outil d'affichage/déclenchement, pas un éditeur** : la structure
du pipeline (quelles étapes existent, dans quel ordre) est fixe, définie
dans `tools/pipeline-ui/lib/pipelineConfig.ts` — on n'y glisse-dépose pas de
nouvelles étapes.

Comme le reste de l'outillage pipeline, c'est **local uniquement** : les
clics sur ▶ Lancer passent par un petit serveur Next.js local qui exécute
`tools/run_step_cli.py` (même mécanisme, même traçabilité que ci-dessous),
jamais déployé publiquement.

---

## 3. Alternative : tableau de bord Streamlit

Depuis la racine du projet :

```bash
streamlit run tools/pipeline_dashboard.py
```

Ouvre automatiquement un onglet navigateur (`http://localhost:8501`, ou le
port suivant disponible si occupé). Laissez le terminal ouvert tant que vous
l'utilisez ; `Ctrl+C` pour l'arrêter.

L'écran est organisé en 3 blocs, dans l'ordre où ils doivent être lancés :

### ① Collecte

| Bouton | Ce qu'il fait | Durée observée |
|---|---|---|
| FBref (5 ligues) | Scrape fbref.com (Big 5) | ~15-20 min |
| Sofascore stats + profils (10 ligues) | Scrape Sofascore (stats + bios joueurs), via navigateur réel | ~30 min |
| Images (logos, photos joueurs) | Télécharge les médias manquants vers `public.media_assets` | Rapide une fois la base déjà peuplée (ne retélécharge que les nouveaux) |

### ② Consolidation

| Bouton | Ce qu'il fait |
|---|---|
| Bronze → Silver | Nettoie et fusionne les CSV bruts dans `silver.*` |

### ③ Modélisation

| Bouton | Ce qu'il fait |
|---|---|
| Silver → Public | Reconstruit `dim_*` et `fact_stats` |
| Score Pépite | Recalcule percentiles + pondération + Score Pépite |
| Vues Gold | Redéploie les vues `gold.*` (rapide, pas de scraping) |

**Ordre recommandé pour une mise à jour complète :** les 3 blocs de haut en
bas, de gauche à droite dans chaque bloc. Chaque étape attend la fin de la
précédente — un bouton reste bloqué/grisé pendant qu'une étape tourne.

### Historique

En bas de page : chaque lancement (manuel ou en ligne de commande, voir
plus bas) apparaît avec sa date, sa durée et son statut (🟢 succès /
🔴 échec / 🟡 en cours). En cas d'échec, un expander affiche les logs
d'erreur.

---

## 4. Alternative en ligne de commande

Pour un run long sans garder l'onglet Streamlit ouvert (ex. lancer le soir
et vérifier le lendemain) :

```bash
cd tools
python run_step_cli.py fbref sofascore images     # étapes dans l'ordre donné
python run_step_cli.py --all-collecte              # raccourci : fbref + sofascore + images
python run_step_cli.py silver public score gold_views
```

Même traçabilité que les boutons du dashboard (même table
`public.pipeline_runs`) — l'historique du dashboard reflète aussi les runs
lancés en ligne de commande.

---

## 5. Problèmes connus

- **Un `[FAIL]` sur `keeper_adv` pendant FBref** : n'existe plus — ce type
  de stat n'était pas supporté par la bibliothèque `soccerdata` et a été
  retiré (voir commit `ae26543`). Si vous le revoyez, quelque chose a
  régressé.
- **Un bouton qui semble bloqué après une étape pourtant terminée dans les
  logs** : bug corrigé (connexion DB sans timeout, commits `ab9c72c` /
  `722315a`). Si ça se reproduit, c'est un nouvel incident réseau/Neon, pas
  le même bug.
- **Challenge Cloudflare qui traîne au démarrage de Sofascore** : normal,
  le navigateur résout le challenge une fois au lancement (quelques
  secondes à ~15s), puis enchaîne les requêtes sans le re-déclencher.

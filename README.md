# Assistant cinéphile

Projet majeur IA générative 2026, parcours Texte. Un assistant qui répond sur les films et
les séries, puis gère une liste « à voir » partagée. Chaque niveau est comparé aux précédents
sur le même protocole de test.

**Vidéo de démonstration (3 min 18) : [Google Drive](https://drive.google.com/file/d/18P1T7it7NbQVt_wL2N-pJSrxf_yWK4EM/view?usp=sharing)**

Le RAG puise dans **trois sources**, sur trois plateformes différentes :

| Source | Ce qu'elle apporte | Fichier |
|---|---|---|
| Wikipédia (fr) | 156 pages encyclopédiques : production, tournage, box-office, réception | `data/corpus.jsonl` |
| TMDB | une fiche par œuvre (synopsis, slogan, équipe, budget, recettes, mots-clés) et des critiques d'utilisateurs | `data/corpus_tmdb.jsonl` |
| IMDb | la note moyenne du public et le nombre de votes | `data/corpus_imdb.jsonl` |

`python scripts/build_corpus.py` télécharge Wikipédia ; `python scripts/build_sources.py` construit
les fiches TMDB et IMDb (il faut une clé TMDB, et il télécharge le jeu de données public des notes
IMDb dans `data/sources/`, non versionné).

| Niveau | Contenu | État |
|---|---|---|
| 0 | LLM seul | Évalué (46 cas) |
| 1 | RAG, sources citées, abstention | Évalué (46 cas), juge calibré (95 % d'accord sur 20 cas) |
| 2 | Agent outillé (7 outils), confirmation des actions | Évalué (46 cas + 11 tâches × 3 essais) |
| 3 | Agent + RAG avancé (recherche hybride BM25 + dense, reranking) | Évalué contre le niveau 2 (mêmes 57 cas) |

## Installation

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Collez ensuite vos clés dans `.env`, puis vérifiez-les :

```bash
python scripts/check_keys.py
```

- Clé Gemini : https://aistudio.google.com/apikey
- Clé TMDB (API v3) : https://www.themoviedb.org/settings/api

## Lancer l'interface

```bash
python scripts/telecharger_affiches.py
streamlit run app.py
```

La première commande télécharge une fois les affiches des 156 œuvres depuis TMDB (dossier
`data/affiches/`, non versionné). Sans elle, l'interface fonctionne mais sans affiches.

L'interface s'ouvre sur http://localhost:8501. On y choisit le niveau (0 à 3), puis on voit la réponse, les œuvres citées avec leur affiche, les sources citées,
le coût de la requête (tokens, latence, appels au modèle) et la trace de chaque étape (outil,
arguments, tokens, durée). Au niveau 2, chaque ajout ou retrait dans la liste « à voir » attend un clic sur
« Accepter » ou « Refuser ». La liste est partagée dans `data/liste_a_voir.json` et chaque
requête est tracée dans `traces/interface.jsonl`.

## Reproduire les résultats

```bash
python eval.py
```

Le tableau est écrit dans `results/tableau.md`. Les réponses déjà obtenues sont relues dans
`cache/`, donc aucune clé n'est nécessaire tant que les tests et les prompts n'ont pas changé.

## Organisation

| Chemin | Rôle |
|---|---|
| `app.py` | Interface Streamlit |
| `data/films.csv` | Œuvres retenues et strate (populaire, peu connu, récent) |
| `data/corpus.jsonl` | Source 1 : pages Wikipédia téléchargées, avec leur révision |
| `data/corpus_tmdb.jsonl`, `data/corpus_imdb.jsonl` | Sources 2 et 3 : fiches TMDB et notes IMDb (`scripts/build_sources.py`) |
| `tests.jsonl` | Jeu de test commun à tous les niveaux (57 cas : 34 questions document, 6 sans réponse, 6 ambiguës, 11 tâches) |
| `eval.py` | Exécute les niveaux et produit le tableau |
| `src/llm.py` | Appel au modèle, cache, tokens et latence |
| `src/metrics.py` | Règles de notation |
| `src/traces.py` | Traces JSONL de chaque exécution |
| `src/levels/` | Un fichier par niveau |
| `src/rag.py` | Découpage, index de vecteurs et recherche dense |
| `src/hybride.py` | Niveau 3 : BM25, fusion et reranking (choix dans `results/choix_hybride.md`) |
| `src/juge.py` | Juge LLM de fidélité aux sources |
| `src/tmdb.py` | Accès à l'API TMDB, avec cache (`cache/tmdb/`) |
| `src/liste.py` | Liste « à voir » et règles métier vérifiées par le code |
| `src/affiches.py`, `data/affiches.json` | Affiches TMDB et correspondance page Wikipédia → fiche TMDB (interface seulement) |
| `assets/style.css` | Apparence de l'interface |
| `data/index/` | Vecteurs des passages (configuration retenue) |
| `scripts/` | Corpus, contrôle des clés et des tests, comparaison de la recherche (dense, puis hybride), calibration du juge, affiches |
| `results/`, `traces/` | Résultats bruts et traces |
| `rapport/rapport.pdf` | Rapport (4 pages), généré par `python rapport/generer_rapport.py` à partir des résultats |
| `video/` | Sources de la vidéo (le rendu MP4 est sur [Google Drive](https://drive.google.com/file/d/18P1T7it7NbQVt_wL2N-pJSrxf_yWK4EM/view?usp=sharing)) |

## Licences des sources et des affiches

Les textes de `data/corpus.jsonl` proviennent de Wikipédia en français, sous licence
[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/deed.fr). L'URL et la révision de
chaque page sont conservées dans le fichier.

Les affiches et les données de films viennent de [TMDB](https://www.themoviedb.org). Ce produit
utilise l'API TMDB mais n'est ni approuvé ni certifié par TMDB. Les affiches ne sont pas versionnées.

Les notes de `data/corpus_imdb.jsonl` viennent des jeux de données publics d'IMDb
(https://datasets.imdbws.com), réservés à un usage personnel et non commercial.
Information courtesy of IMDb (https://www.imdb.com). Used with permission.

## Vidéo

La vidéo de démonstration (3 min 18) : [regarder sur Google Drive](https://drive.google.com/file/d/18P1T7it7NbQVt_wL2N-pJSrxf_yWK4EM/view?usp=sharing)

Les sources de la vidéo sont dans `video/cinephile/` (projet HyperFrames) ; le rendu se lance avec
`npx hyperframes render` depuis ce dossier. Musique : « Ambient Piano Loop 9_14 » par Erokia
(Freesound), sous licence CC BY 4.0 (détails dans `video/cinephile/assets/musique/CREDITS.md`).

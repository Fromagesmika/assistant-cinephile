# Assistant cinéphile

Projet majeur IA générative 2026, parcours Texte. Un assistant qui répond sur les films et
les séries, puis gère une liste « à voir » partagée. Chaque niveau est comparé aux précédents
sur le même protocole de test.

| Niveau | Contenu | État |
|---|---|---|
| 0 | LLM seul | Évalué (40 cas) |
| 1 | RAG, sources citées, abstention | Évalué (40 cas), juge calibré (95 % d'accord sur 20 cas) |
| 2 | Agent outillé (7 outils), confirmation des actions | Évalué (40 cas + 11 tâches × 3 essais) |
| 3 | Agent + RAG avancé (recherche hybride BM25 + dense, reranking) | Évalué contre le niveau 2 (mêmes 51 cas) |

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
| `data/corpus.jsonl` | Pages Wikipédia téléchargées, avec leur révision |
| `tests.jsonl` | Jeu de test commun à tous les niveaux (51 cas, dont 3 questions et 1 tâche sur le box-office) |
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
| `video/` | Sources de la vidéo |

## Licence du corpus et des affiches

Les textes de `data/corpus.jsonl` proviennent de Wikipédia en français, sous licence
[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/deed.fr). L'URL et la révision de
chaque page sont conservées dans le fichier.

Les affiches et les données de films viennent de [TMDB](https://www.themoviedb.org). Ce produit
utilise l'API TMDB mais n'est ni approuvé ni certifié par TMDB. Les affiches ne sont pas versionnées.

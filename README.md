# Assistant cinéphile

Projet majeur IA générative 2026, parcours Texte. Un assistant qui répond sur les films et
les séries, puis gère une liste « à voir » partagée. Chaque niveau est comparé aux précédents
sur le même protocole de test.

| Niveau | Contenu | État |
|---|---|---|
| 0 | LLM seul | Évalué (37 cas) |
| 1 | RAG, sources citées, abstention | Évalué (37 cas), juge à calibrer |
| 2 | Agent outillé, confirmation des actions | Semaine 3 |
| 3 | Extension mesurée | Semaine 4 |

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

## Reproduire les résultats

```bash
python eval.py
```

Le tableau est écrit dans `results/tableau.md`. Les réponses déjà obtenues sont relues dans
`cache/`, donc aucune clé n'est nécessaire tant que les tests et les prompts n'ont pas changé.

## Organisation

| Chemin | Rôle |
|---|---|
| `data/films.csv` | Œuvres retenues et strate (populaire, peu connu, récent) |
| `data/corpus.jsonl` | Pages Wikipédia téléchargées, avec leur révision |
| `tests.jsonl` | Jeu de test commun à tous les niveaux |
| `eval.py` | Exécute les niveaux et produit le tableau |
| `src/llm.py` | Appel au modèle, cache, tokens et latence |
| `src/metrics.py` | Règles de notation |
| `src/traces.py` | Traces JSONL de chaque exécution |
| `src/levels/` | Un fichier par niveau |
| `src/rag.py` | Découpage, index de vecteurs et recherche |
| `src/juge.py` | Juge LLM de fidélité aux sources |
| `data/index/` | Vecteurs des passages (configuration retenue) |
| `scripts/` | Corpus, contrôle des clés et des tests, comparaison de la recherche, calibration du juge |
| `results/`, `traces/` | Résultats bruts et traces |
| `rapport/`, `video/` | Rapport PDF et sources de la vidéo |

## Licence du corpus

Les textes de `data/corpus.jsonl` proviennent de Wikipédia en français, sous licence
[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/deed.fr). L'URL et la révision de
chaque page sont conservées dans le fichier.

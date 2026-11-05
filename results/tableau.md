| Niveau | Recall@5 | MRR | Exactitude | Source citée | Fidélité | Abstention | Précision/refus | Succès tâches | pass^3 | Tokens / requête | Latence (s) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 · LLM seul | — | — | 64% | — | — | 100% | 83% | — | — | 280 | 2.22 |
| 1 · RAG | 96% | 0.738 | 96% | 100% | 100% | 100% | 83% | — | — | 1121 | 2.44 |

Source citée et fidélité portent sur les réponses données aux cas `document`. La fidélité vient du juge LLM (voir results/calibration_juge.md pour sa fiabilité).

Exactitude par strate :

| Niveau | Populaire | Peu connu | Récent |
|---|---|---|---|
| 0 · LLM seul | 88% | 100% | 11% |
| 1 · RAG | 100% | 100% | 89% |

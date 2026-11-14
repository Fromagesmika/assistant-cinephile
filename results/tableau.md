| Niveau | Recall@5 | MRR | Exactitude | Source citée | Phrases citées | Fidélité | Abstention | Précision/refus | Succès tâches | pass^3 | Tokens / requête | Latence (s) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 · LLM seul | — | — | 64% | — | — | — | 100% | 83% | — | — | 280 | 2.22 |
| 1 · RAG | 96% | 0.738 | 96% | 100% | 100% | 100% | 100% | 83% | — | — | 1148 | 2.17 |
| 2 · Agent | 84% | 0.655 | 92% | 96% | 100% | 100% | 100% | 100% | 100% | 100% | 4403 | 6.14 |

Source citée, phrases citées et fidélité portent sur les réponses données aux cas `document`. La fidélité vient du juge LLM (voir results/calibration_juge.md pour sa fiabilité).
Succès tâches : part des 3 × 10 essais dont l'état final de la liste est correct ; pass^3 : part des tâches réussies aux 3 essais.

Exactitude par strate :

| Niveau | Populaire | Peu connu | Récent |
|---|---|---|---|
| 0 · LLM seul | 88% | 100% | 11% |
| 1 · RAG | 100% | 100% | 89% |
| 2 · Agent | 88% | 100% | 89% |

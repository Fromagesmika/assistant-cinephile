| Niveau | Recall@5 | MRR | Exactitude | Source citée | Phrases citées | Fidélité | Abstention | Précision/refus | Succès tâches | pass^3 | Tokens / requête | Latence (s) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 · LLM seul | — | — | 57% | — | — | — | 100% | 83% | — | — | 282 | 2.14 |
| 1 · RAG | 93% | 0.684 | 93% | 100% | 100% | 100% | 100% | 83% | — | — | 1158 | 2.14 |
| 2 · Agent | 71% | 0.586 | 89% | 89% | 89% | 100% | 100% | 100% | 100% | 100% | 4510 | 4.80 |

Source citée, phrases citées et fidélité portent sur les réponses données aux cas `document`. La fidélité vient du juge LLM (voir results/calibration_juge.md pour sa fiabilité).
Succès tâches : part des 3 × 11 essais dont l'état final de la liste est correct ; pass^3 : part des tâches réussies aux 3 essais.

Exactitude par strate :

| Niveau | Populaire | Peu connu | Récent |
|---|---|---|---|
| 0 · LLM seul | 78% | 89% | 10% |
| 1 · RAG | 100% | 89% | 90% |
| 2 · Agent | 89% | 100% | 80% |

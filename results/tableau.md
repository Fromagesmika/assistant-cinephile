| Niveau | Recall@5 | MRR | Exactitude | Source citée | Phrases citées | Fidélité | Abstention | Précision/refus | Succès tâches | pass^3 | Tokens / requête | Latence (s) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 · LLM seul | — | — | 47% | — | — | — | 100% | 83% | — | — | 282 | 3.04 |
| 1 · RAG | 88% | 0.616 | 82% | 94% | 97% | 100% | 100% | 83% | — | — | 1214 | 5.40 |
| 2 · Agent | 71% | 0.597 | 88% | 91% | 79% | 100% | 100% | 100% | 100% | 100% | 4771 | 17.77 |
| 3 · Agent + RAG avancé | 88% | 0.674 | 94% | 94% | 88% | 100% | 100% | 83% | 100% | 100% | 4393 | 19.30 |

Source citée, phrases citées et fidélité portent sur les réponses données aux cas `document`. La fidélité vient du juge LLM (voir results/calibration_juge.md pour sa fiabilité).
Succès tâches : part des 3 × 11 essais dont l'état final de la liste est correct ; pass^3 : part des tâches réussies aux 3 essais.

Exactitude par strate :

| Niveau | Populaire | Peu connu | Récent |
|---|---|---|---|
| 0 · LLM seul | 64% | 73% | 8% |
| 1 · RAG | 82% | 73% | 92% |
| 2 · Agent | 91% | 91% | 83% |
| 3 · Agent + RAG avancé | 91% | 100% | 92% |

# Choix du découpage et des embeddings (top 5, 25 questions)

| Modèle | Taille | Passages | Encodage (s) | Recall@5 page | Recall@5 fait | MRR fait | Score haut min (document) | Score haut max (absent) |
|---|---|---|---|---|---|---|---|---|
| e5 | 800 | 7860 | 875 | 100% | 96% | 0.738 | 0.867 | 0.877 |
| minilm | 800 | 7860 | 629 | 84% | 60% | 0.490 | 0.521 | 0.643 |
| e5 | 400 | 14688 | 1002 | 100% | 92% | 0.728 | 0.867 | 0.877 |
| e5 | 1500 | 5005 | 634 | 100% | 96% | 0.731 | 0.858 | 0.877 |

Questions dont le fait n'est pas retrouvé :

- e5 / 800 : doc-17
- minilm / 800 : doc-03, doc-05, doc-06, doc-07, doc-14, doc-15, doc-17, doc-19, doc-20, doc-23
- e5 / 400 : doc-05, doc-17
- e5 / 1500 : doc-05

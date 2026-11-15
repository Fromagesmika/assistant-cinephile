# Recherche hybride et reranking : mesure hors ligne

Recall@5 : le fait attendu est dans un des 5 extraits. MRR : moyenne de 1 / rang.
dense : e5 seul (niveaux 1 et 2). bm25 : mots seuls. hybride : fusion RRF des deux.
dense_rerank / hybride_rerank : 20 meilleurs candidats dense (et BM25), reclassés par le cross-encoder.
Configuration retenue pour le niveau 3 : hybride_rerank.

## Questions d'origine (28 requêtes)

| Recherche | Recall@5 | MRR | Échecs |
|---|---|---|---|
| dense | 93% | 0.684 | doc-17, doc-27 |
| bm25 | 68% | 0.525 | doc-01, doc-03, doc-07, doc-11, doc-14, doc-17, doc-20, doc-26, doc-27 |
| hybride | 82% | 0.629 | doc-03, doc-11, doc-17, doc-20, doc-27 |
| dense_rerank | 96% | 0.911 | doc-03 |
| hybride_rerank | 96% | 0.911 | doc-03 |

## Requêtes écrites par l'agent (niveau 2) (25 requêtes)

| Recherche | Recall@5 | MRR | Échecs |
|---|---|---|---|
| dense | 80% | 0.656 | doc-04, doc-11, doc-17, doc-26, doc-28 |
| bm25 | 76% | 0.598 | doc-01, doc-07, doc-11, doc-14, doc-17, doc-26 |
| hybride | 88% | 0.701 | doc-11, doc-17, doc-26 |
| dense_rerank | 96% | 0.820 | doc-26 |
| hybride_rerank | 100% | 0.860 | aucun |

Requêtes de l'agent, pour mémoire :

- doc-01 : Inception Christopher Nolan compositeur musique
- doc-02 : Inception directeur de la photographie
- doc-04 : Le Fabuleux Destin d Amelie Poulain tournage studio ville allemande
- doc-05 : La Haine Mathieu Kassovitz musique groupe crédité
- doc-06 : Le Dîner de cons Juste Leblanc footballeur prénom
- doc-07 : Kaamelott nombre d'épisodes
- doc-08 : budget par episode serie Breaking Bad
- doc-09 : Le Samourai Jean Pierre Melville musique compositeur
- doc-10 : Le Salaire de la peur Clouzot livre romancier auteur
- doc-11 : Cleo de 5 a 7 date de l action Agnes Varda
- doc-12 : Divines Houda Benyamina festival de Cannes 2016 récompense
- doc-13 : Mon oncle Jacques Tati usine Monsieur Arpel fabrique
- doc-14 : Mon oncle Jacques Tati Oscar du meilleur film en langue étrangère annee
- doc-16 : La Tortue rouge film d animation ecrit realise
- doc-17 : Flow Gints Zilbalodis budget
- doc-18 : Un simple accident Jafar Panahi festival de Cannes 2025
- doc-19 : Sirāt Óliver Laxe musique compositeur
- doc-21 : L Amour ouf Gilles Lellouche roman auteur ecrivain
- doc-22 : prix d interpretation feminine Cannes 2025 La Petite Derniere
- doc-23 : Valeur sentimentale Joachim Trier musique compositeur
- doc-24 : Adolescence mini-série mise en scène particularité
- doc-25 : Une bataille après l'autre Thomas Pynchon roman adaptation
- doc-26 : Le Fabuleux Destin d Amelie Poulain entrees France
- doc-27 : Le Salaire de la peur entrées France
- doc-28 : Un p'tit truc en plus entrées jour de sortie Artus

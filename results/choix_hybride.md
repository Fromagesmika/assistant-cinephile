# Recherche hybride et reranking : mesure hors ligne

Recall@5 : le fait attendu est dans un des 5 extraits. MRR : moyenne de 1 / rang.
dense : e5 seul (niveaux 1 et 2). bm25 : mots seuls. hybride : fusion RRF des deux.
dense_rerank / hybride_rerank : 20 meilleurs candidats dense (et BM25), reclassés par le cross-encoder.
Configuration retenue pour le niveau 3 : hybride_rerank.

## Questions d'origine (34 requêtes)

| Recherche | Recall@5 | MRR | Échecs |
|---|---|---|---|
| dense | 88% | 0.616 | doc-11, doc-17, doc-27, doc-32 |
| bm25 | 62% | 0.439 | doc-01, doc-03, doc-07, doc-11, doc-14, doc-15, doc-17, doc-20, doc-26, doc-27, doc-28, doc-32, doc-33 |
| hybride | 82% | 0.610 | doc-03, doc-11, doc-17, doc-20, doc-27, doc-32 |
| dense_rerank | 97% | 0.892 | doc-03 |
| hybride_rerank | 97% | 0.892 | doc-03 |

## Requêtes écrites par l'agent (niveau 2) (32 requêtes)

| Recherche | Recall@5 | MRR | Échecs |
|---|---|---|---|
| dense | 75% | 0.634 | doc-04, doc-11, doc-17, doc-26, doc-27, doc-32, doc-33, doc-34 |
| bm25 | 69% | 0.462 | doc-01, doc-07, doc-11, doc-14, doc-15, doc-17, doc-26, doc-27, doc-32, doc-33 |
| hybride | 78% | 0.584 | doc-11, doc-17, doc-26, doc-27, doc-32, doc-33, doc-34 |
| dense_rerank | 94% | 0.716 | doc-27, doc-32 |
| hybride_rerank | 94% | 0.716 | doc-27, doc-32 |

Requêtes de l'agent, pour mémoire :

- doc-01 : compositeur musique film Inception Christopher Nolan
- doc-02 : directeur de la photographie Inception
- doc-04 : Amelie Poulain studio ville allemande
- doc-05 : La Haine Mathieu Kassovitz musique groupe crédité
- doc-06 : Le Dîner de cons footballeur Juste Leblanc prénom inspiré
- doc-07 : Kaamelott nombre d'épisodes
- doc-08 : Breaking Bad budget par épisode
- doc-09 : Le Samouraï Jean-Pierre Melville musique compositeur
- doc-10 : Le Salaire de la peur Clouzot romancier auteur livre
- doc-11 : date action Cleo de 5 a 7 Agnes Varda
- doc-12 : Divines Houda Benyamina Festival de Cannes 2016 recompense prix
- doc-13 : Mon oncle Jacques Tati usine Monsieur Arpel fabrique
- doc-14 : Mon oncle Jacques Tati Oscar du meilleur film en langue étrangère année
- doc-15 : Le Bureau des légendes combien d'épisodes
- doc-16 : La Tortue rouge réalisateur scénariste
- doc-17 : Flow Gints Zilbalodis budget
- doc-18 : Un simple accident Jafar Panahi festival de Cannes 2025 récompense
- doc-19 : Sirat Oliver Laxe musique compositeur
- doc-21 : L Amour ouf Gilles Lellouche roman ecrivain auteur
- doc-22 : prix interpretation feminine Cannes 2025 La Petite Derniere
- doc-23 : Valeur sentimentale Joachim Trier musique compositeur
- doc-24 : Adolescence mini-série mise en scène particularité épisodes
- doc-25 : Une bataille après l'autre Thomas Pynchon
- doc-26 : Le Fabuleux Destin d'Amélie Poulain entrées France
- doc-27 : Le Salaire de la peur entrées France Clouzot
- doc-28 : Un p'tit truc en plus Artus entrées premier jour sortie
- doc-29 : Inception affiche française slogan
- doc-30 : slogan Le Septième Sceau Ingmar Bergman
- doc-31 : slogan du film Conclave Edward Berger
- doc-32 : Parasite Bong Joon ho votes IMDb
- doc-33 : Le Samouraï Jean-Pierre Melville note IMDb
- doc-34 : Anora Sean Baker note IMDb

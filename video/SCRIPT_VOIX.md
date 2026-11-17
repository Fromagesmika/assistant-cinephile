# Script de la voix off — à générer sur ElevenLabs

## Réglages conseillés

- **Modèle** : Eleven Multilingual v2 (le meilleur en français ; il comprend les balises de pause).
- **Voix** : une voix française posée, type documentaire, ni publicitaire ni robotique.
  Dans la bibliothèque, filtrez *Language : French* et *Use case : Narration*, et essayez-en deux ou trois
  sur la première scène avant de tout générer.
- **Stability** 50 % · **Similarity** 75 % · **Style** 0 à 15 % · **Speed** 1,0.
- **Un seul fichier** : collez le texte entre les deux traits ci-dessous, en entier, dans un seul
  générateur. Les balises `<break time="…" />` créent les silences entre les scènes ; laissez-les.
- Téléchargez en **MP3, 44,1 kHz**, et déposez le fichier dans `video/cinephile/assets/voix.mp3`
  (ou envoyez-le-moi). Je le découpe ensuite par scène et je cale chaque animation sur la voix.

Les nombres sont écrits en toutes lettres pour qu'ils soient bien prononcés.
Durée attendue : environ 3 min 20 de voix, soit 3 min 30 à 3 min 45 de vidéo avec les respirations.

---

Quel est le budget du film d'animation Flow ? Une question toute simple. <break time="0.6s" /> Nous l'avons posée à quatre versions de notre assistant cinéphile.
<break time="1.2s" />

Quatre niveaux, un même jeu de cinquante et un tests, et une seule règle : chaque niveau doit prouver, par une mesure, ce qu'il apporte.
<break time="1.2s" />

Niveau zéro : le modèle de langage, seul. <break time="0.4s" /> Niveau un : il lit Wikipédia avant de répondre. <break time="0.4s" /> Niveau deux : un agent, qui choisit ses outils. <break time="0.4s" /> Et niveau trois : le même agent, avec une recherche améliorée.
<break time="1.2s" />

Le modèle seul ne connaît pas Flow, sorti en deux mille vingt-quatre. Il a le bon réflexe : il s'abstient plutôt que d'inventer. Mais sur les films récents, il ne répond juste qu'une fois sur dix.
<break time="1.0s" />

Le niveau un cherche cinq extraits parmi cent cinquante-six pages Wikipédia. Il trouve la bonne page… mais pas le passage qui parle du budget. Il s'abstient, lui aussi.
<break time="1.0s" />

L'agent, lui, multiplie les recherches. Neuf étapes, plus de douze mille tokens… et toujours rien. C'est son point faible : il formule mal ses requêtes.
<break time="1.0s" />

Le niveau trois cherche de deux façons à la fois, par le sens et par les mots, puis un second modèle relit les candidats. Le bon passage remonte. <break time="0.5s" /> Réponse : trois millions et demi d'euros. Avec sa source.
<break time="1.0s" />

Et rien n'est caché. Chaque réponse garde sa trace : chaque appel au modèle, chaque outil, ses arguments, ses tokens et sa durée.
<break time="1.2s" />

Mais que se passe-t-il quand la réponse n'existe pas ? Nous avons inventé un film : Les Horloges de Valparaíso. L'assistant ne trouve rien… et il le dit.
<break time="1.2s" />

Deuxième usage : agir. On lui demande d'ajouter Grave et Titane, les deux films de Julia Ducournau, à la liste à voir. L'agent cherche chaque film, vérifie qu'il existe, qu'il n'est pas déjà dans la liste…
<break time="0.5s" />

… puis il s'arrête, et il demande la permission. Rien n'est écrit sans un clic sur « Accepter ». Si on refuse, la liste ne bouge pas.
<break time="1.0s" />

Grave et Titane rejoignent la liste partagée. Sur nos onze tâches, lancées trois fois chacune, l'agent réussit à chaque fois.
<break time="1.2s" />

Le bilan. Le RAG fait passer l'exactitude de cinquante-sept à quatre-vingt-treize pour cent. L'agent sait agir, mais il consomme quatre fois plus de tokens, et sa recherche tombe à soixante et onze pour cent. Le niveau trois la remonte à quatre-vingt-neuf.
<break time="1.0s" />

Il reste une faille. Quand Wikipédia et TMDB se contredisent sur un budget, l'agent peut croire la mauvaise source. C'est notre prochaine étape.
<break time="1.2s" />

Plus d'autonomie, oui. Mais chaque pas, mesuré. <break time="0.6s" /> Assistant cinéphile, par Michaël Lopez et Rayan Daoudi.

---

## Découpage par scène (pour info)

| Scène | Ce qu'on voit | Durée prévue |
|---|---|---|
| 1 | L'affiche de Flow, la question qui s'écrit | 0:00 – 0:10 |
| 2 | Titre, quatre niveaux, 51 tests | 0:10 – 0:20 |
| 3 | La question se divise en quatre colonnes | 0:20 – 0:36 |
| 4 | Niveau 0 : abstention, « 10 % sur les films récents » | 0:36 – 0:50 |
| 5 | Niveau 1 : cinq extraits, aucun ne parle du budget | 0:50 – 1:03 |
| 6 | Niveau 2 : 9 étapes, 12 141 tokens, toujours rien | 1:03 – 1:16 |
| 7 | Niveau 3 : la recherche hybride, la réponse 3,5 M€ | 1:16 – 1:34 |
| 8 | La trace, ligne par ligne | 1:34 – 1:46 |
| 9 | L'abstention sur un film inventé | 1:46 – 1:59 |
| 10 | La tâche Grave et Titane, l'agent cherche et vérifie | 1:59 – 2:16 |
| 11 | La carte de confirmation, le clic sur Accepter | 2:16 – 2:28 |
| 12 | Les affiches rejoignent la liste, 33 essais sur 33 | 2:28 – 2:39 |
| 13 | Le tableau des quatre niveaux se construit | 2:39 – 3:00 |
| 14 | La faille : deux sources qui se contredisent | 3:00 – 3:11 |
| 15 | Fin : « Plus d'autonomie, mais chaque pas mesuré » | 3:11 – 3:24 |

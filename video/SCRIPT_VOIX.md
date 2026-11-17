# Script de la voix off (version 2, trois sources) — à générer sur ElevenLabs

## Pourquoi une version 2

Le RAG puise maintenant dans trois sources (Wikipédia, TMDB, IMDb) et le jeu de test compte
57 cas. Les réponses sur Flow et les chiffres du bilan ont changé : les scènes 2, 3, 4, 5, 6, 7,
13 et 14 ont un nouveau texte (marqué ✱ dans le découpage en bas).

## Réglages conseillés

- **Modèle** : Eleven Multilingual v2 (il respecte les balises de pause, contrairement au v3/v4).
- **Voix** : de préférence une **voix française native** (filtre *Language : French*, *Use case :
  Narration*). La voix « Adam » est anglophone : la transcription y entendait des « and » et des
  « the ». Si vous gardez Adam, ça marchera quand même.
- **Stability** 50 % · **Similarity** 75 % · **Style** 0 à 15 % · **Speed** 1,0.
- **Un seul fichier**, tout le texte entre les deux traits, balises comprises.
- Déposez le MP3 dans `video/cinephile/assets/voix.mp3` (ou envoyez-le) : je le transcris et je
  recale chaque scène automatiquement.

---

Quel est le budget du film d'animation Flow ? Une question toute simple. <break time="0.6s" /> Nous l'avons posée à quatre versions de notre assistant cinéphile.
<break time="1.2s" />

Quatre niveaux, un même jeu de cinquante-sept tests, et une seule règle : chaque niveau doit prouver, par une mesure, ce qu'il apporte.
<break time="1.2s" />

Niveau zéro : le modèle de langage, seul. <break time="0.4s" /> Niveau un : il lit trois sources avant de répondre, Wikipédia, TMDB et IMDb. <break time="0.4s" /> Niveau deux : un agent, qui choisit ses outils. <break time="0.4s" /> Et niveau trois : le même agent, avec une recherche améliorée.
<break time="1.2s" />

Le modèle seul ne connaît pas Flow, sorti en deux mille vingt-quatre. Il a le bon réflexe : il s'abstient plutôt que d'inventer. Mais sur les films récents, il répond juste moins d'une fois sur dix.
<break time="1.0s" />

Le niveau un cherche cinq extraits dans ses trois sources. Il trouve la fiche TMDB, et répond : trois millions sept cent mille dollars. <break time="0.4s" /> Mais Wikipédia, elle, annonce trois millions et demi d'euros.
<break time="1.0s" />

L'agent, lui, multiplie les recherches. Sept étapes, près de huit mille tokens… et il s'arrête au même chiffre. Son point faible : il formule mal ses requêtes, et le passage de Wikipédia lui échappe.
<break time="1.0s" />

Le niveau trois cherche de deux façons à la fois, par le sens et par les mots, puis un second modèle relit les candidats. Cette fois, les deux passages remontent. <break time="0.5s" /> Et il cite les deux sources : TMDB, et Wikipédia.
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

Le bilan. Le RAG fait passer l'exactitude de quarante-sept à quatre-vingt-deux pour cent. L'agent sait agir, mais il consomme quatre fois plus de tokens, et sa recherche tombe à soixante et onze pour cent. Le niveau trois la remonte à quatre-vingt-huit, et atteint quatre-vingt-quatorze pour cent d'exactitude.
<break time="1.0s" />

Il reste une faille. Plus de sources, c'est aussi plus de contradictions. Quand Wikipédia et TMDB ne donnent pas le même budget, l'agent peut croire la mauvaise source. C'est notre prochaine étape.
<break time="1.2s" />

Plus d'autonomie, oui. Mais chaque pas, mesuré. <break time="0.6s" /> Assistant cinéphile, par Michaël Lopez et Rayan Daoudi.

---

## Découpage par scène

| Scène | Ce qu'on voit | Texte |
|---|---|---|
| 1 | L'affiche de Flow, la question qui s'écrit, les quatre niveaux | inchangé |
| 2 | Titre, 4 niveaux, 57 tests, 1 règle | ✱ 57 tests |
| 3 | Les quatre colonnes de niveau | ✱ trois sources |
| 4 | Niveau 0 : abstention, « 8 % sur les films récents » | ✱ moins d'une fois sur dix |
| 5 | Niveau 1 : la fiche TMDB, 3,7 M$, et Wikipédia qui dit 3,5 M€ | ✱ nouveau |
| 6 | Niveau 2 : 7 étapes, 7 915 tokens, le même chiffre | ✱ nouveau |
| 7 | Niveau 3 : recherche hybride, les deux sources citées | ✱ nouveau |
| 8 | La trace | inchangé |
| 9 | L'abstention sur un film inventé | inchangé |
| 10 | La tâche Grave et Titane | inchangé |
| 11 | La confirmation, le clic sur Accepter | inchangé |
| 12 | La liste, 33 essais sur 33 | inchangé |
| 13 | Le bilan des quatre niveaux | ✱ nouveaux chiffres |
| 14 | La faille : deux sources qui se contredisent | ✱ légèrement modifié |
| 15 | Fin | inchangé |

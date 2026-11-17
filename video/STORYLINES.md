# Vidéo de démonstration : trois scénarios

Contraintes du sujet : 3 à 5 minutes, et la vidéo doit montrer un cas réussi, une abstention,
une tâche en plusieurs étapes avec sa trace, et une action validée.
Commun aux trois : 1920 × 1080, 30 images/s, environ 3 min 30, voix off en français
(générée par vous sur ElevenLabs à partir du script), musique libre de droits, vrais écrans de
l'interface capturés dans l'application.

## B · « Une question, quatre niveaux » (recommandé)

Pourquoi : il raconte la vraie histoire du projet, chaque niveau répare l'échec du précédent,
sur une seule question que le spectateur suit du début à la fin.

- **Dispositif** : un fil rouge, la question « Quel est le budget du film Flow ? », posée aux
  quatre niveaux. **Forme** : écran partagé en quatre, qui se resserre sur le niveau qui compte.
- **Ce qu'on voit** : la même question part vers quatre colonnes. Le LLM seul ne sait pas, le RAG
  ne trouve pas, l'agent cherche mal, et le niveau 3 répond « 3,5 millions d'euros », source à
  l'appui. Ensuite, on quitte Flow pour la liste à voir : une tâche en plusieurs étapes, la trace
  qui se déroule, et l'action validée d'un clic.
- **Deux premières secondes** : l'affiche de Flow plein écran, la question tapée par-dessus, et
  un point d'interrogation qui se fend en quatre.
- **Rythme** : question → quatre réponses côte à côte → pourquoi chacune échoue (une phrase
  chacune) → le niveau 3 répond → abstention sur un film inventé → tâche « Grave et Titane » avec
  sa trace → confirmation Accepter → le tableau des quatre niveaux qui se construit → la phrase
  finale.
- **Look** : le ciel violet et rose de l'interface, les affiches comme matière, typographie Inter.
- **Son** : nappe cinématographique douce, un léger « clic » à chaque action, la voix au premier plan.

## A · « Ce soir, on regarde quoi ? »

- **Dispositif** : un moment dans la journée de quelqu'un. Un samedi soir, deux amis cherchent
  un film. **Forme** : chaîne d'objets, où chaque plan se termine sur ce qui ouvre le suivant
  (l'affiche devient la question, la réponse devient la liste…).
- **Ce qu'on voit** : la conversation des deux amis en bulles, puis l'assistant dans l'interface
  qui répond, s'abstient, ajoute des films avec leur accord, et les affiches qui tombent dans la
  liste. On termine sur la liste du soir, puis sur les chiffres.
- **Deux premières secondes** : un écran de messagerie, « on regarde quoi ce soir ? », avec un mur
  d'affiches qui défile derrière.
- **Rythme** : le besoin → une question réussie → une abstention → la tâche et sa trace →
  l'accord → la liste du soir → comment c'est construit (4 niveaux) → les chiffres → fin.
- **Look** : chambre éclairée par l'écran, tons nuit, affiches lumineuses.
- **Son** : ambiance de soirée feutrée, notifications de messages, voix posée.

## C · « Dans la tête de l'agent » (le plus audacieux)

- **Dispositif** : l'objet est l'explication. Une seule requête de l'agent, vue de l'intérieur.
  **Forme** : un zoom sans fin, où la caméra plonge dans chaque étape de la trace, qui devient le
  monde suivant.
- **Ce qu'on voit** : on entre dans la question, puis dans l'appel au modèle, puis dans la
  recherche (les 7 860 extraits qui défilent, cinq qui s'allument), puis dans TMDB, puis dans la
  règle métier qui bloque un doublon, puis dans la carte de confirmation. On ressort par le
  tableau des résultats.
- **Deux premières secondes** : un curseur qui clique « Envoyer », et la caméra qui plonge
  directement dans le bouton.
- **Rythme** : clic → plongée dans la boucle → recherche → outils → règle et confirmation →
  remontée → les quatre niveaux comparés → fin.
- **Look** : schéma vivant, traits fins violets sur fond nuit, affiches en vignettes.
- **Son** : pulsation électronique lente, un « tic » à chaque étape de la trace.

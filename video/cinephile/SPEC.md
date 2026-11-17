# SPEC · « Une question, quatre niveaux »

GOAL: à la fin, le spectateur a compris que chaque niveau corrige l'échec du précédent, et il a
vu les quatre preuves demandées par le sujet (un cas réussi, une abstention, une tâche en
plusieurs étapes avec sa trace, une action validée).

OUTPUT: HyperFrames, 1920 × 1080, 30 images/s.

TIME: environ 204 s × 30 = 6 120 images (provisoire). La voix off est l'horloge : quand
`assets/voix.mp3` arrive, chaque scène est recalée sur ses mots-repères (constantes `T` en tête
de chaque script de scène).

LOOK (le matériau de la marque, c'est-à-dire l'interface elle-même) :
- Sol : le ciel de crépuscule de l'application. Dégradé vertical #3a2e7c → #8f6cc4 (46 %) →
  #c48bbf (58 %) → #2b2350 (84 %) → #151129, avec une lueur de couchant (#ffd696, 85 % de
  l'opacité, ellipse 18 % × 10 % à 86 %/63 %) et des collines en silhouette (#2c2150, #161129).
  Pas de vide noir.
- Encre : #f4f1fb pour tout ce qui se lit ; texte secondaire à 68 % d'opacité.
- Accent : violet #8b5cf6 / #a78bfa, réservé au niveau en cours, au chiffre-clé et à la réponse
  finale. Statuts repris de l'interface : vert #4ade80 (Réponse), orange #fb923c (Abstention).
- Typographie : Inter. Titre 96 px poids 700, interlettrage -2 %. Ligne secondaire 40 px poids 400.
  Chiffres-clés 220 px poids 900. Étiquettes 26 px poids 700 en capitales, interlettrage +8 %,
  violet clair. Rien en dessous de 28 px qui doive être lu, sauf l'interface capturée.
- Médium : les vraies cartes de l'interface (captures PNG à l'échelle 1,5), posées sur le ciel,
  coins 18 px, ombre 0 30 80 rgba(10,5,25,0,55). Les affiches de films, coins 12 px.

OBJETS : l'affiche de Flow (le fil rouge) ; une « pilule question » (la question en blanc dans une
capsule sombre translucide, 34 px) qui voyage de scène en scène ; quatre colonnes de niveau
(0 à 3) ; les cartes-réponses capturées ; la carte « Action à confirmer » ; un curseur de souris
réel (flèche blanche bordée de noir) ; la liste à voir (deux affiches) ; le tableau final.

MOTION :
- Arrivées : expo.out 0,7 s (cartes), power4.out 0,5 s (texte). Sorties 40 % plus courtes, power3.in.
- Caméra (wrapper `.cam`) : power2.inOut, 1,2 à 2,4 s, un seul mouvement par plan.
- Titres : mot par mot, flou 6 px → 0 et opacité 0 → 1 en 0,13 s, 0,07 s d'écart, sans translation.
- Chiffres : comptent jusqu'à leur valeur en 0,8 s (expo.out), puis immobiles.
- Transitions : (1) l'objet devient le monde (une colonne de niveau grandit jusqu'à la carte),
  (2) carry across (la pilule question se pose dans la scène suivante), (3) blur swap sur le même
  ciel, (4) iris depuis le clic sur Accepter. Jamais de fondu enchaîné entre deux mondes.

SHOTS : voir SCRIPT_VOIX.md (15 scènes) ; une idée par scène, révélée quand la voix la nomme.

BANNED : vide noir ; lueurs, néons, particules décoratives ; tout centré ; tout qui apparaît en
fondu-glissé vers le haut ; titres qui bougent pendant la lecture ; trois cartes en rang ;
logo en coin ; boucles de « respiration » ; chiffres inventés (tout chiffre vient de results/).

QA : 0 s (vignette : affiche de Flow + question), 30 s (quatre colonnes), 85 s (réponse 3,5 M€),
100 s (trace lisible), 140 s (bouton Accepter), 170 s (tableau), dernière image (phrase finale
+ noms).

"""Génère rapport/rapport.pdf (4 pages maximum).

Le tableau des niveaux est recalculé à partir de results/niveauN.jsonl avec les fonctions
d'eval.py : le rapport ne peut pas diverger des résultats bruts.
Lancement : python rapport/generer_rapport.py
"""
import json
import sys
from pathlib import Path

from reportlab.graphics.shapes import Drawing, Line, Polygon, Rect, String
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Image, KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))
from eval import recall_et_mrr, taux  # noqa: E402
from src.metrics import moyenne  # noqa: E402

AUTEURS = "[Noms de l'équipe]"  # à remplacer par vos noms, puis relancer le script
SORTIE = RACINE / "rapport" / "rapport.pdf"

# --- Mise en forme -------------------------------------------------------------------------

POLICES = Path("C:/Windows/Fonts")
pdfmetrics.registerFont(TTFont("Texte", str(POLICES / "segoeui.ttf")))
pdfmetrics.registerFont(TTFont("Gras", str(POLICES / "segoeuib.ttf")))
pdfmetrics.registerFont(TTFont("Italique", str(POLICES / "segoeuii.ttf")))
pdfmetrics.registerFontFamily("Texte", normal="Texte", bold="Gras", italic="Italique", boldItalic="Gras")

VIOLET = colors.HexColor("#4c3591")
VIOLET_CLAIR = colors.HexColor("#ece7f8")
GRIS = colors.HexColor("#5f5b6b")
LIGNE = colors.HexColor("#cfc8e3")

corps = ParagraphStyle("corps", fontName="Texte", fontSize=8.8, leading=11.6, spaceAfter=3.5, alignment=4)
titre = ParagraphStyle("titre", fontName="Gras", fontSize=16, leading=19, textColor=VIOLET, spaceAfter=1)
sous_titre = ParagraphStyle("sous", fontName="Texte", fontSize=9, leading=12, textColor=GRIS, spaceAfter=6)
h1 = ParagraphStyle("h1", fontName="Gras", fontSize=11, leading=14, textColor=VIOLET, spaceBefore=7, spaceAfter=3)
cellule = ParagraphStyle("cellule", fontName="Texte", fontSize=7.6, leading=9.4)
cellule_gras = ParagraphStyle("cellule_gras", parent=cellule, fontName="Gras")
legende = ParagraphStyle("legende", fontName="Italique", fontSize=7.6, leading=9.6, textColor=GRIS, spaceAfter=4,
                         alignment=TA_CENTER)


def p(texte, style=corps):
    return Paragraph(texte, style)


def tableau(lignes, largeurs, entete=True, gras_premiere_colonne=False):
    donnees = [[p(str(c), cellule_gras if (entete and i == 0) or (gras_premiere_colonne and j == 0) else cellule)
                for j, c in enumerate(ligne)] for i, ligne in enumerate(lignes)]
    t = Table(donnees, colWidths=[l * cm for l in largeurs], repeatRows=1 if entete else 0)
    style = [("GRID", (0, 0), (-1, -1), 0.4, LIGNE), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
             ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
             ("LEFTPADDING", (0, 0), (-1, -1), 3), ("RIGHTPADDING", (0, 0), (-1, -1), 3)]
    if entete:
        style.append(("BACKGROUND", (0, 0), (-1, 0), VIOLET_CLAIR))
    t.setStyle(TableStyle(style))
    return t


# --- Données -------------------------------------------------------------------------------

def lire(chemin):
    with open(chemin, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


resultats = {n: lire(RACINE / "results" / f"niveau{n}.jsonl") for n in range(4)}
tests = lire(RACINE / "tests.jsonl")


def pct(v):
    return "—" if v is None else f"{v:.0%}".replace("%", " %")


def ligne_niveau(n, nom):
    lignes = resultats[n]
    recall, mrr = recall_et_mrr(lignes)
    fideles = [l["fidele"] for l in lignes if "fidele" in l]
    essais = [ok for l in lignes for ok in l.get("succes_essais", [])]
    return [nom, pct(recall), "—" if mrr is None else f"{mrr:.2f}".replace(".", ","), pct(taux(lignes, "exactitude")),
            pct(moyenne(fideles)), pct(taux(lignes, "abstention")), pct(taux(lignes, "precision_refus")),
            pct(moyenne(essais)), pct(taux(lignes, "tache")),
            f"{moyenne(l['tokens'] for l in lignes):,.0f}".replace(",", " "),
            f"{moyenne(l['latence'] for l in lignes):.1f}".replace(".", ",")]


# --- Schéma d'architecture -----------------------------------------------------------------

def boite(d, x, y, l, h, titre_boite, detail="", fond=colors.white, bord=VIOLET):
    d.add(Rect(x, y, l, h, rx=4, ry=4, fillColor=fond, strokeColor=bord, strokeWidth=0.8))
    d.add(String(x + 5, y + h - 11, titre_boite, fontName="Gras", fontSize=7.6, fillColor=VIOLET))
    for i, ligne in enumerate(detail.split("\n") if detail else []):
        d.add(String(x + 5, y + h - 21 - 9 * i, ligne, fontName="Texte", fontSize=6.6, fillColor=GRIS))


def fleche(d, x1, y1, x2, y2):
    d.add(Line(x1, y1, x2, y2, strokeColor=GRIS, strokeWidth=0.7))
    import math
    a = math.atan2(y2 - y1, x2 - x1)
    pointe = [x2, y2, x2 - 5 * math.cos(a - 0.4), y2 - 5 * math.sin(a - 0.4),
              x2 - 5 * math.cos(a + 0.4), y2 - 5 * math.sin(a + 0.4)]
    d.add(Polygon(pointe, fillColor=GRIS, strokeColor=GRIS, strokeWidth=0.3))


def schema():
    d = Drawing(18 * cm, 6.7 * cm)
    w = 18 * cm
    # Colonne de gauche : utilisateur et interface
    boite(d, 0, 140, 90, 34, "Utilisateur", "question, accord\nou refus")
    boite(d, 0, 62, 90, 58, "Interface Streamlit", "choix du niveau 0-3\nréponse, sources\ncoût, trace\nAccepter / Refuser")
    fleche(d, 45, 140, 45, 121)
    # Colonne centrale : les quatre niveaux
    xn, ln = 112, 210
    niveaux = [
        ("Niveau 0 · LLM seul", "prompt soigné → Gemini 3.5 Flash-Lite"),
        ("Niveau 1 · RAG", "e5 (7 860 passages de 800 car.) → 5 extraits → réponse citée [n]"),
        ("Niveau 2 · Agent", "boucle bornée (8 appels, 40 k tokens), 7 outils JSON"),
        ("Niveau 3 · Agent + RAG avancé", "niveau 2 avec recherche hybride BM25 + dense et reranking"),
    ]
    for i, (t, det) in enumerate(niveaux):
        y = 150 - i * 34
        boite(d, xn, y, ln, 28, t, det, fond=VIOLET_CLAIR if i >= 2 else colors.white)
        fleche(d, 90, 91, xn, y + 14)
    # Colonne de droite : sources et actions
    xd, ld = 346, w - 346
    boite(d, xd, 150, ld, 28, "Wikipédia FR · 156 pages", "révision figée, CC BY-SA 4.0")
    boite(d, xd, 116, ld, 28, "API TMDB (cache disque)", "recherche, fiche, box-office, recommandations")
    boite(d, xd, 48, ld, 62, "Écriture dans la liste", "1. arguments validés contre le schéma\n2. règles métier (doublon, existence)\n3. confirmation dans l'interface\n4. écriture dans la liste partagée")
    # Niveau 1 : Wikipédia seulement. Niveaux 2 et 3 (accolade) : Wikipédia, TMDB et écriture.
    fleche(d, xn + ln, 130, xd, 158)
    xa = xn + ln + 10
    d.add(Line(xn + ln, 96, xa, 96, strokeColor=GRIS, strokeWidth=0.7))
    d.add(Line(xn + ln, 62, xa, 62, strokeColor=GRIS, strokeWidth=0.7))
    d.add(Line(xa, 62, xa, 96, strokeColor=GRIS, strokeWidth=0.7))
    fleche(d, xa, 90, xd, 150)
    fleche(d, xa, 79, xd, 128)
    fleche(d, xa, 70, xd, 79)
    # Bas : traces et évaluation
    boite(d, 0, 0, w, 36, "Traces JSONL et évaluation",
          "chaque exécution : étapes, outils, arguments, tokens, durée (traces/) · python eval.py : 51 cas × 4 niveaux, réponses relues\n"
          "dans cache/ (LLM et TMDB) → results/niveauN.jsonl et results/tableau.md, reproductible sans clé d'API")
    return d


# --- Contenu -------------------------------------------------------------------------------

nb = {t: sum(c["type"] == t for c in tests) for t in ("document", "absent", "tache", "ambigu")}
histoire = []
histoire += [
    p("Assistant cinéphile : un système génératif qui se mesure", titre),
    p(f"Projet IA générative 2026 · Parcours Texte · Thème Cinéphile · {AUTEURS} · "
      "dépôt github.com/Fromagesmika/assistant-cinephile", sous_titre),

    p("1. Cas d'usage et données", h1),
    p("L'assistant répond à des questions sur des films et des séries en citant ses sources, puis gère une "
      "<b>liste « à voir » partagée</b> ; tout ajout ou retrait est une action à faire valider par l'utilisateur. "
      "Le système est construit en quatre niveaux, tous disponibles dans l'interface et dans <i>eval.py</i>, et "
      "comparés sur le même jeu de test."),
    p("<b>Corpus</b> : 156 pages Wikipédia en français (136 films, 20 séries), téléchargées par l'API avec leur "
      "numéro de révision. Les œuvres sont réparties en trois strates pour tester des situations différentes : "
      "68 <i>populaires</i> (le LLM les connaît), 58 <i>peu connues</i> et 30 <i>récentes</i> (2024-2025, après "
      "l'entraînement du modèle). <b>Outils</b> : l'API TMDB (recherche, fiche, budget et recettes, "
      "recommandations). <b>Modèle</b> : Gemini 3.5 Flash-Lite (API, offre gratuite), température 0."),

    p("2. Architecture", h1),
    schema(),
    p("Figure 1 · Les niveaux 2 et 3 partagent la boucle, les outils et les règles ; seule la recherche documentaire change.",
      legende),
    p("Trois composants sont écrits sans framework : la <b>boucle de l'agent</b> (pause et reprise sur confirmation), "
      "la <b>validation des actions</b> (schéma, règles métier, confirmation) et l'<b>évaluation</b> (règles de "
      "notation, Recall@k, MRR, pass^3), ainsi que BM25 au niveau 3. Les outils sont classés par effet : cinq en "
      "lecture (recherche Wikipédia, recherche et fiche TMDB, recommandations, lecture de la liste), deux en écriture "
      "(ajout, retrait). Une écriture n'est jamais exécutée directement : le code vérifie d'abord les arguments et les "
      "règles (pas de doublon, œuvre existante sur TMDB, retrait d'une œuvre présente), puis la session se met en pause "
      "jusqu'à la décision de l'utilisateur. Les erreurs d'outils sont renvoyées au modèle comme résultat d'outil."),
    p("<b>Interface</b> (Streamlit, figure 2) : choix du niveau 0 à 3, réponse avec son statut, œuvres citées avec leur "
      "affiche, sources citées, coût de la requête (tokens, latence, appels au modèle) et trace de chaque exécution "
      "(étape, outil, arguments, tokens, durée), enregistrée en JSONL. Au niveau 2 ou 3, toute écriture s'affiche comme "
      "une action à confirmer, avec les boutons Accepter et Refuser."),
    Table([[Image(str(RACINE / "rapport" / "figures" / "interface_accueil.jpg"), width=8.7 * cm, height=5.44 * cm),
            Image(str(RACINE / "rapport" / "figures" / "interface_reponse.jpg"), width=8.7 * cm, height=5.44 * cm)]],
          colWidths=[9 * cm, 9 * cm]),
    p("Figure 2 · À gauche, l'accueil et le choix du niveau. À droite, une réponse du niveau 3 : réponse citée, coût, "
      "œuvre citée et onglets Sources et Trace. Le premier appel du niveau 3 inclut le chargement du modèle de reranking.",
      legende),

    p("3. Protocole d'évaluation", h1),
    p(f"<b>Jeu de test</b> (<i>tests.jsonl</i>, {len(tests)} cas, défini en semaine 1 puis complété de 4 cas sur le "
      f"box-office en semaine 3, tous niveaux réévalués) : {nb['document']} questions dont la réponse est dans le corpus "
      f"(faits attendus vérifiés dans la page source par <i>scripts/check_tests.py</i>), {nb['absent']} questions sans "
      f"réponse (œuvres inventées, absentes aussi de TMDB, ou détails qu'aucune source ne donne), {nb['tache']} tâches en "
      f"plusieurs étapes et {nb['ambigu']} demandes ambiguës ou hors sujet."),
    p("<b>Métriques</b>. Recherche : Recall@5 et MRR, un extrait comptant comme pertinent s'il vient de la bonne page "
      "<i>et</i> contient le fait attendu. Réponse : exactitude par règles (chaque fait attendu présent, variantes "
      "admises), source citée, chaque phrase citée, fidélité aux extraits par un <b>juge LLM</b>. Tâches : l'état final "
      "de la liste est comparé par le code à l'état attendu ; l'utilisateur est simulé (il accepte ou refuse selon le "
      "cas) ; chaque tâche est lancée 3 fois pour le pass^3. Coût : tokens (y compris raisonnement) et latence par requête."),
    p("<b>Calibration du juge</b> sur 20 réponses annotées (10 du niveau 0, qui contiennent de vraies erreurs, et 10 du "
      "niveau 1) : <b>95 % d'accord</b>, 10 réponses fidèles sur 10 reconnues, 9 non fidèles sur 10 repérées. Le seul "
      "désaccord est un cas limite (« célèbre footballeur <i>français</i> », qualificatif absent des extraits) : le juge "
      "tolère les petits ajouts. Protocole : pré-annotation par un LLM avec justification, sans voir le verdict du juge, "
      "puis validation humaine face aux extraits."),
]

histoire += [
    p("4. Choix justifiés par des mesures", h1),
    p("<b>Découpage et embeddings</b> (25 questions, 4 configurations). e5-small multilingue domine MiniLM (Recall@5 "
      "du fait 96 % contre 60 %). Avec e5, des passages de 400, 800 ou 1 500 caractères donnent 92 à 96 % : nous gardons "
      "800 (meilleur MRR, 0,74). Chaque passage commence par le titre de l'œuvre et la section, sans quoi « Musique : "
      "Hans Zimmer » ne dit pas de quel film il parle. Le score de similarité ne sépare pas les questions sans réponse "
      "(score maximal 0,877) des autres (score minimal 0,867) : un seuil d'abstention est impossible, l'abstention est "
      "donc décidée par le modèle et contrôlée par le code (une réponse sans citation valide est remplacée par une "
      "abstention)."),
    p("<b>Extension du niveau 3, choisie à partir d'un défaut mesuré.</b> Au niveau 2, le Recall@5 tombe de 93 % à "
      "71 %. Les traces montrent deux causes : l'agent reformule la question en mots-clés, souvent sans accents "
      "(« Cleo de 5 a 7 date action Agnes Varda »), que la recherche dense retrouve mal ; et il saute parfois Wikipédia "
      "au profit de TMDB. La première cause relève du RAG avancé. Nous avons comparé hors ligne cinq recherches sur les "
      "vraies requêtes de l'agent (<i>results/choix_hybride.md</i>) :"),
    tableau([["Recherche", "Questions d'origine", "Requêtes de l'agent"],
             ["Dense e5 (niveaux 1 et 2)", "93 % · MRR 0,68", "80 % · MRR 0,66"],
             ["BM25 seul (écrit sans framework)", "68 % · MRR 0,53", "76 % · MRR 0,60"],
             ["Hybride, fusion RRF", "82 % · MRR 0,63", "88 % · MRR 0,70"],
             ["Dense + reranking", "96 % · MRR 0,91", "96 % · MRR 0,82"],
             ["<b>Hybride + reranking (retenu)</b>", "<b>96 % · MRR 0,91</b>", "<b>100 % · MRR 0,86</b>"]],
            [6.2, 5.2, 5.2]),
    Spacer(1, 3),
    p("La fusion RRF seule <b>dégrade</b> les questions bien formulées : BM25, sans racinisation, rapproche mal "
      "« compositeur » de « composée » (une racinisation par préfixe n'a rien changé). Le reranking par un cross-encoder "
      "multilingue (mMiniLM entraîné sur mMARCO), appliqué à l'union des 20 meilleurs candidats dense et BM25, garde ce "
      "que trouvent les deux recherches sans cet inconvénient. Aucun paramètre n'a été ajusté sur le jeu de test "
      "(valeurs usuelles : k1 = 1,5, b = 0,75, RRF à 60)."),
]

histoire += [
    p("5. Résultats des quatre niveaux", h1),
    tableau([["Niveau", "Recall@5", "MRR", "Exactitude", "Fidélité", "Abstention", "Précision / refus",
              "Succès tâches", "pass^3", "Tokens / requête", "Latence (s)"],
             ligne_niveau(0, "0 · LLM seul"), ligne_niveau(1, "1 · RAG"), ligne_niveau(2, "2 · Agent"),
             ligne_niveau(3, "3 · Agent + RAG avancé")],
            [3.4, 1.55, 1.0, 1.6, 1.35, 1.7, 1.55, 1.45, 1.2, 1.45, 1.6], gras_premiere_colonne=True),
    p("Tableau 1 · Généré à partir de results/niveauN.jsonl. Exactitude sur les 28 cas document, abstention sur les 6 "
      "cas absents, précision/refus sur les 6 cas ambigus, tâches sur 11 tâches × 3 essais. Fidélité : juge calibré.",
      legende),
]
strates = [["Exactitude par strate", "Populaire", "Peu connu", "Récent"]]
for n, nom in enumerate(["0 · LLM seul", "1 · RAG", "2 · Agent", "3 · Agent + RAG avancé"]):
    strates.append([nom] + [pct(taux(resultats[n], "exactitude", s)) for s in ("populaire", "peu_connu", "recent")])
histoire += [
    tableau(strates, [5, 2.2, 2.2, 2.2], gras_premiere_colonne=True),
    Spacer(1, 4),
    p("<b>Niveau 0.</b> Référence à battre : bon sur les œuvres connues, mais <b>10 % sur les films récents</b>, et "
      "aucun moyen de vérifier ses réponses. Il s'abstient correctement sur les œuvres inventées. "
      "<b>Niveau 1.</b> Le RAG apporte le plus grand gain (exactitude de 57 % à 93 %, récents de 10 % à 90 %), "
      "chaque phrase est citée et le juge ne trouve aucune réponse infidèle, pour 4 fois plus de tokens et la même "
      "latence. <b>Niveau 2.</b> L'agent réussit les 11 tâches aux 3 essais, y compris les pièges (doublon, film "
      "inexistant, ajout refusé, retrait refusé), et gère les demandes ambiguës (100 %) en voyant sur TMDB qu'il existe "
      "plusieurs « Nosferatu ». En contrepartie : <b>4 fois plus de tokens que le RAG</b>, 2 fois plus de latence, et "
      "une recherche moins bonne (71 %). <b>Niveau 3.</b> La recherche hybride avec reranking remonte le Recall@5 de "
      "71 % à 89 %, le MRR de 0,59 à 0,77 et l'exactitude de 89 % à 93 %, avec un peu moins de tokens (l'agent relance "
      "moins ses recherches) mais 2 s de plus par requête. Les 11 % de Recall@5 manquants sont les 3 questions où "
      "l'agent n'a pas interrogé Wikipédia : sur les 25 où il l'a fait, le fait est toujours dans les 5 extraits."),
]

echecs = [
    ["#", "Niveau · cas", "Ce qui s'est passé", "Cause", "Ce qui le corrige"],
    ["1", "0 · doc-20", "Budget d'<i>Un p'tit truc en plus</i> : « environ 5,5 millions d'euros », réponse assurée "
     "mais fausse (6,1 M€).", "Connaissances figées, film de 2024 ; rien ne signale l'incertitude.",
     "Niveau 1 : réponse exacte et citée."],
    ["2", "1 · amb-02", "« Qui joue dans Frankenstein ? » : le RAG répond pour l'adaptation de 2025 au lieu de "
     "demander laquelle.", "Le corpus ne contient qu'un Frankenstein : l'ambiguïté se juge sur le monde, pas sur "
     "les extraits.", "Niveaux 2 et 3 : TMDB montre plusieurs œuvres, l'agent demande."],
    ["3", "1 · doc-27", "Entrées du <i>Salaire de la peur</i> : abstention alors que le chiffre est dans la page.",
     "Le passage « Box-office » n'est pas dans les 5 extraits de la recherche dense.",
     "Niveaux 2 et 3 : retrouvé (rang 5, puis rang 3 avec le reranking)."],
    ["4", "2 · doc-17", "Budget de <i>Flow</i> : deux recherches (« Flow Gints Zilbalodis budget »), aucune ne "
     "remonte le passage ; abstention.", "Requêtes en mots-clés de l'agent, mal servies par la recherche dense.",
     "Niveau 3 : passage trouvé au rang 3, réponse exacte."],
    ["5", "2 et 3 · doc-20", "« 6 400 000 dollars » au lieu de 6,1 M€ : l'agent lit le budget TMDB sans consulter "
     "Wikipédia. Le juge la déclare fidèle.", "Conflit entre deux sources ; la fidélité à une source ne garantit "
     "pas l'exactitude.", "Non corrigé : il faudrait imposer Wikipédia d'abord ou signaler les écarts."],
]
histoire += [
    KeepTogether([p("6. Analyse de cinq échecs", h1),
                  tableau(echecs, [0.6, 2.1, 5.6, 4.6, 4.1])]),
    Spacer(1, 3),
    p("Les échecs 1 à 4 sont corrigés par le niveau suivant, ce qui justifie chaque niveau par une mesure. L'échec 5 "
      "est apparu en ajoutant les données de box-office de TMDB : enrichir les outils a introduit un conflit de sources "
      "que ni le juge ni la recherche ne détectent. doc-03 (durée de <i>Parasite</i> : 135 min sur TMDB, 132 min sur "
      "Wikipédia) en est un second exemple."),

    p("7. Limites et coût", h1),
    p("<b>Coût.</b> Par requête : 282 tokens au niveau 0, 1 158 au niveau 1, environ 4 200 à 4 500 pour l'agent, soit "
      "15 fois le niveau 0 ; la latence passe de 2,1 s à 6,9 s au niveau 3 (reranking sur CPU, environ 2 s par recherche, "
      "et 27 s de chargement du modèle au démarrage). Le juge consomme ses propres tokens, exclus du tableau. Coûts "
      "fixes : encodage du corpus (875 s une fois), téléchargement du corpus et des affiches. Tout tourne sans GPU, "
      "dans l'offre gratuite de Gemini."),
    p("<b>Limites.</b> (1) Le jeu de test est petit : un cas document vaut 3,6 points d'exactitude, et les écarts de "
      "4 points entre niveaux tiennent à un ou deux cas. (2) Hors tâches, chaque cas n'est lancé qu'une fois ; à "
      "température 0, Gemini n'est pas totalement déterministe. Le cache garantit la reproduction exacte du tableau, "
      "pas la stabilité du modèle. (3) Le choix du niveau 3 est mesuré sur les requêtes du même jeu de test ; nous "
      "avons limité le risque de sur-ajustement en n'ajustant aucun paramètre. (4) La latence des niveaux 2 et 3 inclut "
      "la recherche locale, chronométrée en direct, et varie légèrement d'une exécution à l'autre. (5) Les tests et "
      "l'annotation du juge sont faits par nous, avec une pré-annotation par un LLM. (6) L'agent ne garde pas la "
      "mémoire d'une question à l'autre : « Et la suite ? » appelle une demande de précision."),

    p("8. Reproduire les résultats", h1),
    p("<i>pip install -r requirements.txt</i>, puis <b><i>python eval.py</i></b> : la commande rejoue les 51 cas pour "
      "les 4 niveaux et réécrit <i>results/tableau.md</i>. Les réponses du modèle et de TMDB sont relues dans "
      "<i>cache/</i>, ce qui reproduit le tableau sans clé d'API. Le dépôt contient aussi <i>tests.jsonl</i>, les "
      "résultats bruts par niveau (<i>results/niveauN.jsonl</i>), les traces (<i>traces/</i>), les comparaisons de "
      "recherche (<i>results/choix_retrieval.md</i>, <i>results/choix_hybride.md</i>), la calibration du juge "
      "(<i>results/calibration_juge.md</i>) et <i>.env.example</i> ; aucune clé n'est versionnée. Interface : "
      "<i>streamlit run app.py</i>. Ce rapport est généré par <i>rapport/generer_rapport.py</i> à partir des résultats "
      "bruts."),
]


def pied(canvas, doc):
    canvas.saveState()
    canvas.setFont("Texte", 7)
    canvas.setFillColor(GRIS)
    canvas.drawString(1.5 * cm, 0.9 * cm, "Assistant cinéphile · Projet IA générative 2026")
    canvas.drawRightString(A4[0] - 1.5 * cm, 0.9 * cm, f"{doc.page}")
    canvas.restoreState()


doc = SimpleDocTemplate(str(SORTIE), pagesize=A4, leftMargin=1.5 * cm, rightMargin=1.5 * cm,
                        topMargin=1.3 * cm, bottomMargin=1.4 * cm, title="Assistant cinéphile",
                        author=AUTEURS, subject="Projet IA générative 2026, parcours Texte")
doc.build(histoire, onFirstPage=pied, onLaterPages=pied)
print(f"Écrit : {SORTIE}")

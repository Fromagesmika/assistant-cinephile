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

AUTEURS = "Michaël LOPEZ et Rayan DAOUDI"
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

corps = ParagraphStyle("corps", fontName="Texte", fontSize=9.4, leading=13.2, spaceAfter=5, alignment=4)
titre = ParagraphStyle("titre", fontName="Gras", fontSize=18, leading=22, textColor=VIOLET, spaceAfter=3)
sous_titre = ParagraphStyle("sous", fontName="Texte", fontSize=9.4, leading=13, textColor=GRIS, spaceAfter=8)
h1 = ParagraphStyle("h1", fontName="Gras", fontSize=12, leading=15, textColor=VIOLET, spaceBefore=10, spaceAfter=4)
cellule = ParagraphStyle("cellule", fontName="Texte", fontSize=8, leading=10)
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
    p(f"Projet IA générative 2026 · Parcours Texte · Thème Cinéphile<br/>{AUTEURS} · "
      "dépôt : github.com/Fromagesmika/assistant-cinephile", sous_titre),

    p("1. Ce que fait l'assistant", h1),
    p("Notre assistant répond à des questions sur les films et les séries, et il gère une <b>liste « à voir »</b> "
      "partagée. On peut lui demander qui a composé la musique d'un film, combien d'entrées il a faites, ou encore "
      "« ajoute Grave et Titane à ma liste ». Dès qu'une demande modifie la liste, l'assistant doit d'abord obtenir "
      "l'accord de l'utilisateur."),
    p("Nous l'avons construit en quatre niveaux, du plus simple au plus autonome : un LLM seul, puis un RAG qui "
      "s'appuie sur des documents, puis un agent qui utilise des outils, et enfin une extension. Les quatre niveaux "
      "restent disponibles dans l'interface et dans le script d'évaluation, et ils passent exactement le même jeu de "
      "test. C'est ce qui nous permet de dire, chiffres à l'appui, ce que chaque niveau apporte et ce qu'il coûte."),

    p("2. Les données", h1),
    p("<b>Le corpus</b> rassemble 156 pages Wikipédia en français : 136 films et 20 séries. Nous les avons "
      "téléchargées avec l'API de Wikipédia en gardant le numéro de révision de chaque page, pour savoir exactement "
      "quelle version du texte a servi à l'évaluation. Les œuvres sont réparties en trois groupes, choisis pour "
      "mettre le système en difficulté de façons différentes : 68 œuvres <i>populaires</i>, que le modèle connaît "
      "déjà ; 58 œuvres <i>peu connues</i> ; et 30 œuvres <i>récentes</i> (2024-2025), sorties après les données "
      "d'entraînement du modèle."),
    p("<b>Les outils</b> de l'agent passent par l'API TMDB, une base de films gratuite : recherche d'une œuvre, fiche "
      "détaillée (dont le budget et les recettes au box-office), recommandations. <b>Le modèle</b> est Gemini 3.5 "
      "Flash-Lite, utilisé par API dans l'offre gratuite, avec une température de 0."),

    p("3. Architecture", h1),
    schema(),
    p("Figure 1 · Les niveaux 2 et 3 partagent la même boucle, les mêmes outils et les mêmes règles : seule la "
      "recherche dans les documents change.", legende),
    p("Le sujet demande qu'au moins un composant soit écrit sans framework. Chez nous, il y en a quatre : la "
      "<b>boucle de l'agent</b>, la <b>validation des actions</b>, l'<b>évaluation</b> et l'algorithme BM25 du "
      "niveau 3. La boucle est bornée : huit appels au modèle et 40 000 tokens au maximum par requête. Quand un outil "
      "échoue, l'erreur est renvoyée au modèle comme un résultat normal, pour qu'il puisse se corriger."),
    p("Les sept outils sont classés selon leur effet. Cinq ne font que lire (recherche Wikipédia, recherche et fiche "
      "TMDB, recommandations, lecture de la liste) et deux écrivent (ajout et retrait). Une écriture n'est jamais "
      "exécutée directement. Le code vérifie d'abord les arguments et les règles métier : pas de doublon, une œuvre "
      "qui existe vraiment sur TMDB, un retrait qui porte sur une œuvre présente. Ensuite seulement, la session se "
      "met en pause et attend que l'utilisateur clique sur « Accepter » ou « Refuser »."),
    p("<b>L'interface</b> (Streamlit, figure 2) montre tout ce que demande le sujet : le choix du niveau de 0 à 3, la "
      "réponse et son statut, les sources citées, le coût de la requête (tokens, latence, appels au modèle) et la "
      "trace de chaque exécution, étape par étape, avec l'outil appelé, ses arguments, les tokens et la durée. "
      "Chaque trace est aussi enregistrée en JSONL pour l'analyse des erreurs."),
    Table([[Image(str(RACINE / "rapport" / "figures" / "interface_accueil.jpg"), width=8.7 * cm, height=5.44 * cm),
            Image(str(RACINE / "rapport" / "figures" / "interface_reponse.jpg"), width=8.7 * cm, height=5.44 * cm)]],
          colWidths=[9 * cm, 9 * cm]),
    p("Figure 2 · À gauche, l'accueil et le choix du niveau. À droite, une réponse du niveau 3, avec l'œuvre citée, "
      "le coût de la requête et les onglets Sources et Trace.", legende),
]

histoire += [
    p("4. Comment nous évaluons", h1),
    p(f"Le jeu de test (<i>tests.jsonl</i>) compte {len(tests)} cas. Nous l'avons écrit en semaine 1, puis complété "
      f"en semaine 3 par quatre cas sur le box-office ; à ce moment-là, tous les niveaux ont été réévalués. On y "
      f"trouve {nb['document']} questions dont la réponse est dans le corpus, {nb['absent']} questions sans réponse "
      f"possible (des films inventés, ou des détails qu'aucune source ne donne), {nb['tache']} tâches en plusieurs "
      f"étapes sur la liste, et {nb['ambigu']} demandes ambiguës ou hors sujet. Un script vérifie que chaque réponse "
      f"attendue se trouve bien dans la page source : sans ce contrôle, une erreur dans les tests passerait pour une "
      f"erreur du modèle."),
    p("Pour la <b>recherche</b>, nous mesurons le Recall@5 et le MRR. Un extrait ne compte comme pertinent que s'il "
      "vient de la bonne page <i>et</i> contient le fait attendu : trouver la bonne page ne suffit pas. Pour les "
      "<b>réponses</b>, l'exactitude est vérifiée par des règles (chaque fait attendu doit apparaître, avec ses "
      "variantes d'écriture), et la fidélité aux sources par un juge LLM. Pour les <b>tâches</b>, le code compare "
      "l'état final de la liste à l'état attendu. L'utilisateur est simulé : selon le cas, il accepte ou refuse les "
      "actions. Chaque tâche est lancée trois fois, et le pass^3 compte les tâches réussies aux trois essais. Le "
      "<b>coût</b> se mesure en tokens et en secondes par requête."),
    p("<b>Le juge a été calibré</b> sur 20 réponses annotées : 10 du niveau 0, qui contiennent de vraies erreurs, et "
      "10 du niveau 1. Il est d'accord avec l'annotation humaine dans 95 % des cas. Il reconnaît les 10 réponses "
      "fidèles et repère 9 des 10 réponses infidèles. Le seul désaccord est un cas limite (« célèbre footballeur "
      "<i>français</i> », un qualificatif absent des extraits) : le juge tolère les petits ajouts. Pour annoter, un LLM "
      "a d'abord proposé un avis justifié, sans connaître le verdict du juge, puis nous avons validé chaque cas en "
      "relisant les extraits."),
]

histoire += [
    p("5. Les choix, et les mesures qui les justifient", h1),
    p("<b>Découpage et embeddings.</b> Nous avons comparé quatre configurations sur 25 questions. Le modèle e5-small "
      "multilingue l'emporte nettement sur MiniLM (le fait est retrouvé dans 96 % des cas, contre 60 %). Avec e5, des "
      "passages de 400, 800 ou 1 500 caractères donnent des résultats proches (92 à 96 %) ; nous avons gardé 800, qui "
      "a le meilleur MRR (0,74). Un détail s'est révélé important : chaque passage commence par le titre de l'œuvre "
      "et la section. Sans cela, un extrait comme « Musique : Hans Zimmer » ne dit pas de quel film il parle."),
    p("Cette comparaison nous a aussi appris qu'on ne peut pas décider d'une abstention avec un simple seuil de "
      "similarité : les questions sans réponse obtiennent des scores aussi hauts que les autres (0,877 contre 0,867). "
      "C'est donc le modèle qui décide de s'abstenir, et le code qui contrôle : une réponse qui ne cite aucun extrait "
      "valide est remplacée par une abstention."),
    p("<b>L'extension du niveau 3 part d'un défaut mesuré.</b> En passant du RAG à l'agent, le Recall@5 chute de "
      "93 % à 71 %. Les traces montrent pourquoi. D'abord, l'agent reformule la question en mots-clés, souvent sans "
      "accents (« Cleo de 5 a 7 date action Agnes Varda »), et la recherche par vecteurs retrouve mal ce genre de "
      "requête. Ensuite, il lui arrive de sauter Wikipédia pour aller directement sur TMDB. La première cause relève "
      "du RAG avancé, l'une des extensions proposées par le sujet. Avant de construire quoi que ce soit, nous avons "
      "comparé cinq façons de chercher, sur les vraies requêtes écrites par l'agent :"),
    KeepTogether([tableau([["Recherche", "Questions d'origine", "Requêtes de l'agent"],
             ["Dense e5 (niveaux 1 et 2)", "93 % · MRR 0,68", "80 % · MRR 0,66"],
             ["BM25 seul (écrit sans framework)", "68 % · MRR 0,53", "76 % · MRR 0,60"],
             ["Hybride, fusion RRF", "82 % · MRR 0,63", "88 % · MRR 0,70"],
             ["Dense + reranking", "96 % · MRR 0,91", "96 % · MRR 0,82"],
             ["<b>Hybride + reranking (retenu)</b>", "<b>96 % · MRR 0,91</b>", "<b>100 % · MRR 0,86</b>"]],
            [6.4, 5.4, 5.4]),
    p("Tableau 1 · Recall@5 et MRR sur les 28 questions document (détail dans results/choix_hybride.md).", legende)]),
    p("Le résultat nous a surpris. La recherche hybride seule aide l'agent, mais elle <b>dégrade</b> les questions "
      "bien formulées : BM25 ne voit aucun rapport entre « compositeur » et « composée », et une racinisation simple "
      "n'y a rien changé. Ce qui fonctionne, c'est d'ajouter un reranking : on réunit les 20 meilleurs candidats de "
      "chaque recherche, puis un petit modèle (un cross-encoder multilingue) relit chaque paire question-extrait pour "
      "les reclasser. Nous n'avons réglé aucun paramètre sur le jeu de test et avons gardé les valeurs usuelles."),
]

histoire += [
    p("6. Résultats des quatre niveaux", h1),
    tableau([["Niveau", "Recall@5", "MRR", "Exactitude", "Fidélité", "Abstention", "Précision / refus",
              "Succès tâches", "pass^3", "Tokens / requête", "Latence (s)"],
             ligne_niveau(0, "0 · LLM seul"), ligne_niveau(1, "1 · RAG"), ligne_niveau(2, "2 · Agent"),
             ligne_niveau(3, "3 · Agent + RAG avancé")],
            [3.5, 1.55, 0.95, 1.8, 1.35, 1.7, 1.45, 1.4, 1.15, 1.35, 1.35], gras_premiere_colonne=True),
    p("Tableau 2 · Calculé à partir de results/niveauN.jsonl. Exactitude sur les 28 cas document, abstention sur les 6 "
      "cas absents, précision ou refus sur les 6 cas ambigus, tâches sur 11 tâches × 3 essais.", legende),
]
strates = [["Exactitude par groupe d'œuvres", "Populaires", "Peu connues", "Récentes"]]
for n, nom in enumerate(["0 · LLM seul", "1 · RAG", "2 · Agent", "3 · Agent + RAG avancé"]):
    strates.append([nom] + [pct(taux(resultats[n], "exactitude", s)) for s in ("populaire", "peu_connu", "recent")])
histoire += [
    tableau(strates, [5.4, 2.4, 2.4, 2.4], gras_premiere_colonne=True),
    Spacer(1, 6),
    p("<b>Niveau 0, le LLM seul.</b> C'est la référence à battre. Il s'en sort bien sur les œuvres connues, mais il "
      "tombe à <b>10 % sur les films récents</b>, et rien dans ses réponses ne permet de les vérifier. Point positif : "
      "il ne s'invente pas de réponse sur les films qui n'existent pas."),
    p("<b>Niveau 1, le RAG.</b> C'est le plus grand pas en avant. L'exactitude passe de 57 % à 93 %, et de 10 % à "
      "90 % sur les films récents. Chaque phrase cite sa source, et le juge ne trouve aucune réponse infidèle. Le prix "
      "à payer : quatre fois plus de tokens, pour une latence identique."),
    p("<b>Niveau 2, l'agent.</b> Il réussit les 11 tâches aux trois essais, y compris les pièges que nous lui avions "
      "tendus : un doublon, un film qui n'existe pas, un ajout refusé, un retrait refusé. Il gère aussi les demandes "
      "ambiguës : sur TMDB, il voit qu'il existe plusieurs « Nosferatu » et demande lequel. En contrepartie, il "
      "consomme quatre fois plus de tokens que le RAG, il met deux fois plus de temps, et il retrouve moins bien les "
      "documents (71 %)."),
    p("<b>Niveau 3, l'agent avec le RAG avancé.</b> Il corrige précisément ce dernier point : le Recall@5 remonte de "
      "71 % à 89 %, le MRR de 0,59 à 0,77, et l'exactitude de 89 % à 93 %. Il consomme même un peu moins de tokens, "
      "parce que l'agent relance moins souvent ses recherches. En revanche, chaque requête prend environ deux "
      "secondes de plus. Les 11 % qui manquent au Recall@5 correspondent aux trois questions où l'agent n'a pas "
      "consulté Wikipédia : chaque fois qu'il l'a fait, le bon extrait figurait parmi les cinq premiers."),
]

echecs = [
    ("Le niveau 0 invente un chiffre (doc-20).",
     "Interrogé sur le budget d'<i>Un p'tit truc en plus</i>, le modèle répond avec assurance « environ 5,5 millions "
     "d'euros ». Le vrai chiffre est 6,1 millions. Le film date de 2024 : le modèle ne le connaît pas, et rien dans "
     "sa réponse ne trahit son incertitude. Le RAG corrige l'erreur en allant lire la page du film."),
    ("Le RAG ne voit pas l'ambiguïté (amb-02).",
     "À la question « Qui joue dans Frankenstein ? », le niveau 1 répond pour l'adaptation de 2025 au lieu de "
     "demander de laquelle on parle. La raison est simple : notre corpus ne contient qu'un seul Frankenstein. "
     "L'ambiguïté existe dans le monde, pas dans les extraits. L'agent, lui, la voit sur TMDB et pose la question."),
    ("Le bon passage n'est pas dans les cinq extraits (doc-27).",
     "Le nombre d'entrées du <i>Salaire de la peur</i> figure bien dans sa page Wikipédia, mais la recherche du "
     "niveau 1 ne remonte pas la section « Box-office ». Le modèle s'abstient, ce qui est le bon réflexe, mais la "
     "réponse existait. L'agent la retrouve au rang 5, et le reranking du niveau 3 la fait remonter au rang 3."),
    ("L'agent cherche mal (doc-17).",
     "Pour le budget de <i>Flow</i>, l'agent lance deux recherches en mots-clés, « Flow Gints Zilbalodis budget » "
     "puis une variante. Aucune ne fait remonter le bon passage, et il s'abstient. C'est exactement le défaut qui a "
     "motivé le niveau 3, où le passage arrive au rang 3 et la réponse devient exacte."),
    ("Deux sources se contredisent (doc-20, niveaux 2 et 3).",
     "L'agent répond « 6 400 000 dollars » pour le budget d'<i>Un p'tit truc en plus</i> : il a pris le chiffre de "
     "TMDB sans consulter Wikipédia, qui indique 6,1 millions d'euros. Le juge déclare la réponse fidèle, et il a "
     "raison : elle est fidèle à sa source. Mais elle est fausse par rapport à notre référence. Cet échec est apparu "
     "quand nous avons ajouté les données de box-office de TMDB : enrichir les outils a créé un conflit que ni le "
     "juge ni la recherche ne détectent. La durée de <i>Parasite</i> (135 minutes sur TMDB, 132 sur Wikipédia) en "
     "est un deuxième exemple. Le niveau 3 ne le corrige pas : il faudrait obliger l'agent à consulter Wikipédia "
     "d'abord, ou lui faire signaler les écarts entre sources."),
]
histoire.append(p("7. Cinq échecs, regardés de près", h1))
histoire.append(p("Les quatre premiers échecs sont corrigés par le niveau suivant, ce qui montre que chaque niveau "
                  "a une raison d'exister. Le cinquième ne l'est pas, et c'est sans doute le plus instructif."))
for i, (titre_echec, texte_echec) in enumerate(echecs, start=1):
    histoire.append(p(f"<b>{i}. {titre_echec}</b> {texte_echec}"))

histoire += [
    p("8. Ce que ça coûte, et les limites", h1),
    p("<b>Le coût.</b> Une requête consomme 282 tokens au niveau 0, 1 158 au niveau 1 et entre 4 200 et 4 500 pour "
      "l'agent, soit environ quinze fois plus que le LLM seul. La latence passe de 2,1 secondes à 6,9 secondes au "
      "niveau 3, dont environ deux secondes de reranking sur processeur, sans compter les 27 secondes de chargement "
      "du modèle au démarrage. Le juge consomme ses propres tokens, que nous n'avons pas comptés dans le tableau, car "
      "ils servent à l'évaluation et non au système. Il faut aussi compter quelques coûts payés une seule fois, "
      "comme l'encodage du corpus (875 secondes). Tout le projet tourne sans GPU, dans l'offre gratuite de Gemini."),
    p("<b>Les limites.</b> Notre jeu de test est petit : une question document pèse 3,6 points d'exactitude, et un "
      "écart de 4 points entre deux niveaux tient à un ou deux cas. En dehors des tâches, chaque cas n'est lancé "
      "qu'une fois, et même à température 0, Gemini n'est pas parfaitement déterministe : le cache garantit qu'on "
      "retrouve exactement notre tableau, pas que le modèle répondrait pareil demain. Le niveau 3 a été choisi en "
      "regardant les requêtes de ce même jeu de test ; nous avons limité le risque de sur-ajustement en ne réglant "
      "aucun paramètre. La latence des niveaux 2 et 3 varie légèrement d'une exécution à l'autre, car la recherche "
      "locale est chronométrée en direct. Les tests et l'annotation du juge ont été faits par nous, avec l'aide d'un "
      "LLM pour la pré-annotation. Enfin, l'agent n'a pas de mémoire d'une question à l'autre : à « Et la suite, elle "
      "sort quand ? », il demande de quelle œuvre on parle."),

    p("9. Reproduire les résultats", h1),
    p("Après <i>pip install -r requirements.txt</i>, la commande <b><i>python eval.py</i></b> rejoue les 51 cas sur "
      "les quatre niveaux et réécrit <i>results/tableau.md</i>. Les réponses du modèle et de TMDB sont relues dans le "
      "dossier <i>cache/</i>, si bien qu'aucune clé d'API n'est nécessaire pour retrouver nos chiffres. Le dépôt "
      "contient aussi le jeu de test, les résultats bruts et les traces de chaque niveau, les comparaisons de "
      "recherche, la calibration du juge et le fichier <i>.env.example</i> ; aucune clé n'y est versionnée. "
      "L'interface se lance avec <i>streamlit run app.py</i>. Ce rapport est lui-même généré par "
      "<i>rapport/generer_rapport.py</i> à partir des résultats bruts, ce qui garantit que ses tableaux "
      "correspondent à ce que produit <i>eval.py</i>."),

    p("10. En résumé", h1),
    p("Chaque niveau a gagné sa place par une mesure. Le RAG rend l'assistant fiable sur les films qu'il ne connaît "
      "pas et lui fait citer ses sources. L'agent sait agir sur la liste sans jamais le faire dans le dos de "
      "l'utilisateur, et il repère les demandes ambiguës. Le RAG avancé répare la recherche que l'agent avait "
      "dégradée. Mais chaque pas vers plus d'autonomie se paie en tokens et en secondes, et ouvre de nouvelles façons "
      "de se tromper, comme le conflit entre deux sources. Si nous devions continuer, c'est par là que nous "
      "commencerions : apprendre à l'agent à confronter ses sources plutôt qu'à faire confiance à la première."),
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

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

corps = ParagraphStyle("corps", fontName="Texte", fontSize=9.4, leading=12.9, spaceAfter=4.6, alignment=4)
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
        ("Niveau 1 · RAG", "e5 (8 748 extraits, 3 sources) → 5 extraits → réponse citée [n]"),
        ("Niveau 2 · Agent", "boucle bornée (8 appels, 40 k tokens), 7 outils JSON"),
        ("Niveau 3 · Agent + RAG avancé", "niveau 2 avec recherche hybride BM25 + dense et reranking"),
    ]
    for i, (t, det) in enumerate(niveaux):
        y = 150 - i * 34
        boite(d, xn, y, ln, 28, t, det, fond=VIOLET_CLAIR if i >= 2 else colors.white)
        fleche(d, 90, 91, xn, y + 14)
    # Colonne de droite : sources et actions
    xd, ld = 346, w - 346
    boite(d, xd, 150, ld, 28, "Wikipédia · TMDB · IMDb", "156 œuvres, 3 sources, 8 748 extraits")
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
          "chaque exécution : étapes, outils, arguments, tokens, durée (traces/) · python eval.py : 57 cas × 4 niveaux, réponses relues\n"
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
    p("Notre assistant répond à des questions sur les films et les séries, et il gère une liste « à voir » "
      "partagée. On peut lui demander qui a composé la musique d'un film, combien d'entrées il a faites, ou "
      "« ajoute Grave et Titane à ma liste ». Toute modification de la liste attend l'accord de l'utilisateur."),
    p("Nous l'avons construit en quatre niveaux, du plus simple au plus autonome : un LLM seul, un RAG qui s'appuie "
      "sur des documents, un agent qui utilise des outils, puis une extension. Les quatre niveaux restent disponibles "
      "dans l'interface et dans le script d'évaluation, et ils passent le même jeu de test, ce qui permet de comparer "
      "ce que chacun apporte et ce qu'il coûte."),

    p("2. Les données : trois sources", h1),
    p("Le corpus couvre 156 œuvres (136 films et 20 séries) et puise dans trois plateformes. La première est "
      "Wikipédia en français : 156 pages, téléchargées avec l'API de Wikipédia. Nous gardons le numéro de révision "
      "de chaque page pour savoir quelle version du texte a servi à l'évaluation. Les œuvres sont réparties en trois "
      "groupes : 68 œuvres populaires, que le modèle connaît déjà, 58 œuvres peu connues, et 30 œuvres récentes "
      "(2024-2025), sorties après les données d'entraînement du modèle."),
    p("La deuxième source est TMDB, une base de films collaborative. Pour chaque œuvre, nous en tirons une fiche en "
      "français (synopsis, slogan, équipe, budget, recettes, mots-clés) et jusqu'à deux critiques d'utilisateurs. La "
      "troisième est IMDb, dont les jeux de données publics donnent la note moyenne du public et le nombre de votes. "
      "Les trois sources sont découpées et indexées ensemble, soit 8 748 extraits. Chaque extrait garde le nom de sa "
      "plateforme, et une réponse indique donc d'où vient chaque information. Les fiches TMDB et IMDb sont "
      "reconstruites par <i>scripts/build_sources.py</i>."),
    p("Les outils de l'agent interrogent aussi l'API TMDB en direct : recherche d'une œuvre, fiche détaillée, "
      "recommandations. Le modèle est Gemini 3.5 Flash-Lite, utilisé par API dans l'offre gratuite, avec une "
      "température de 0."),

    p("3. Architecture", h1),
    schema(),
    p("Figure 1 · Les niveaux 2 et 3 partagent la même boucle, les mêmes outils et les mêmes règles ; seule la "
      "recherche dans les documents change.", legende),
    p("Le sujet demande qu'au moins un composant soit écrit sans framework. Nous en avons écrit quatre : la boucle "
      "de l'agent, la validation des actions, l'évaluation et l'algorithme BM25 du niveau 3. La boucle s'arrête au "
      "plus tard après huit appels au modèle ou 40 000 tokens. Quand un outil échoue, l'erreur revient au modèle "
      "comme un résultat ordinaire, et il peut se corriger."),
    p("Les sept outils sont classés selon leur effet. Cinq ne font que lire (recherche dans les documents, recherche "
      "et fiche TMDB, recommandations, lecture de la liste) et deux écrivent (ajout et retrait). Avant toute écriture, "
      "le code vérifie les arguments et les règles métier : pas de doublon, une œuvre qui existe sur TMDB, un retrait "
      "qui porte sur une œuvre de la liste. Si tout est conforme, la session se met en pause jusqu'à ce que "
      "l'utilisateur clique sur « Accepter » ou « Refuser »."),
    p("L'interface Streamlit (figure 2) affiche le choix du niveau de 0 à 3, la réponse et son statut, les sources "
      "citées, le coût de la requête (tokens, latence, appels au modèle) et la trace de chaque exécution : chaque "
      "étape, l'outil appelé, ses arguments, les tokens et la durée. Chaque trace est aussi enregistrée en JSONL pour "
      "l'analyse des erreurs."),
    Table([[Image(str(RACINE / "rapport" / "figures" / "interface_accueil.jpg"), width=8.7 * cm, height=5.44 * cm),
            Image(str(RACINE / "rapport" / "figures" / "interface_reponse.jpg"), width=8.7 * cm, height=5.44 * cm)]],
          colWidths=[9 * cm, 9 * cm]),
    p("Figure 2 · À gauche, l'accueil et le choix du niveau. À droite, une réponse du niveau 3, avec l'œuvre citée, "
      "le coût de la requête et les onglets Sources et Trace.", legende),
]

histoire += [
    p("4. Protocole d'évaluation", h1),
    p(f"Le jeu de test (<i>tests.jsonl</i>) compte {len(tests)} cas. Nous l'avons écrit en semaine 1, puis complété "
      f"en semaine 3 par quatre cas sur le box-office, et en semaine 4 par six cas dont la réponse ne se trouve que "
      f"sur TMDB ou sur IMDb (un slogan, une note, un nombre de votes). Après chaque ajout, nous avons réévalué tous "
      f"les niveaux. Le jeu contient {nb['document']} questions dont la réponse est dans le corpus, {nb['absent']} "
      f"questions sans réponse possible (des films inventés, ou des détails qu'aucune source ne donne), "
      f"{nb['tache']} tâches en plusieurs étapes sur la liste, et {nb['ambigu']} demandes ambiguës ou hors sujet. Un "
      f"script vérifie que chaque réponse attendue se trouve bien dans le document source, pour qu'une erreur dans "
      f"les tests ne soit pas comptée comme une erreur du modèle."),
    p("Pour la recherche, nous mesurons le Recall@5 et le MRR. Un extrait ne compte comme pertinent que s'il vient du "
      "bon document et contient le fait attendu. Pour les réponses, des règles vérifient l'exactitude (chaque fait "
      "attendu doit apparaître, avec ses variantes d'écriture), et un juge LLM vérifie la fidélité aux sources. Pour "
      "les tâches, le code compare l'état final de la liste à l'état attendu, avec un utilisateur simulé qui accepte "
      "ou refuse les actions selon le cas. Chaque tâche est lancée trois fois, et le pass^3 compte les tâches "
      "réussies aux trois essais. Le coût se mesure en tokens et en secondes par requête."),
    p("Nous avons calibré le juge sur 20 réponses annotées : 10 du niveau 0, qui contiennent de vraies erreurs, et "
      "10 du niveau 1. Il est d'accord avec l'annotation humaine dans 95 % des cas : il reconnaît les 10 réponses "
      "fidèles et repère 9 des 10 réponses infidèles. Le seul désaccord porte sur un cas limite (« célèbre "
      "footballeur <i>français</i> », un qualificatif absent des extraits), ce qui montre que le juge tolère les "
      "petits ajouts. Pour l'annotation, un LLM a d'abord proposé un avis justifié, sans connaître le verdict du juge, "
      "puis nous avons validé chaque cas en relisant les extraits."),
]

histoire += [
    p("5. Choix et mesures", h1),
    p("Découpage et embeddings. Avant l'ajout de TMDB et d'IMDb, nous avons comparé quatre configurations sur 25 "
      "questions. Le modèle e5-small multilingue retrouve le fait dans 96 % des cas, contre 60 % pour MiniLM. Avec e5, "
      "des passages de 400, 800 ou 1 500 caractères donnent 92 à 96 % ; nous avons gardé 800, qui a le meilleur MRR "
      "(0,74). Chaque passage commence par le titre de l'œuvre et la section, sinon un extrait comme « Musique : Hans "
      "Zimmer » ne dit pas de quel film il parle."),
    p("Un seuil de similarité ne suffit pas à décider d'une abstention : les questions sans réponse obtiennent des "
      "scores aussi hauts que les autres (0,877 contre 0,867). Le modèle décide donc de s'abstenir, et le code "
      "remplace par une abstention toute réponse qui ne cite aucun extrait valide."),
    p("Extension du niveau 3. En passant du RAG à l'agent, le Recall@5 chute de 88 % à 71 %. Les traces en donnent "
      "deux causes. L'agent reformule la question en mots-clés, souvent sans accents (« Cleo de 5 a 7 date action "
      "Agnes Varda »), et la recherche par vecteurs retrouve mal ce genre de requête. Il lui arrive aussi de sauter "
      "les documents pour aller directement sur TMDB. La première cause relève du RAG avancé, l'une des extensions "
      "proposées par le sujet. Nous avons comparé cinq façons de chercher sur les requêtes réellement écrites par "
      "l'agent :"),
    KeepTogether([tableau([["Recherche", "Questions d'origine", "Requêtes de l'agent"],
             ["Dense e5 (niveaux 1 et 2)", "88 % · MRR 0,62", "75 % · MRR 0,63"],
             ["BM25 seul (écrit sans framework)", "62 % · MRR 0,44", "69 % · MRR 0,46"],
             ["Hybride, fusion RRF", "82 % · MRR 0,61", "78 % · MRR 0,58"],
             ["Dense + reranking", "97 % · MRR 0,89", "94 % · MRR 0,72"],
             ["<b>Hybride + reranking (retenu)</b>", "<b>97 % · MRR 0,89</b>", "<b>94 % · MRR 0,72</b>"]],
            [6.4, 5.4, 5.4]),
    p("Tableau 1 · Recall@5 et MRR sur les 34 questions document, corpus à trois sources (results/choix_hybride.md).", legende)]),
    p("La recherche hybride seule aide l'agent mais dégrade les questions bien formulées : BM25 ne rapproche pas "
      "« compositeur » de « composée », et une racinisation simple n'y a rien changé. Le reranking, lui, améliore les "
      "deux : on réunit les 20 meilleurs candidats de chaque recherche, puis un petit modèle (un cross-encoder "
      "multilingue) relit chaque paire question-extrait pour les reclasser. Sur le corpus Wikipédia seul, l'union avec "
      "BM25 donnait un peu plus que le reranking seul (100 % contre 96 % sur les requêtes de l'agent) ; avec les "
      "trois sources, les deux font jeu égal. Nous avons gardé l'hybride, sans régler aucun paramètre sur le jeu de "
      "test."),
]

histoire += [
    p("6. Résultats des quatre niveaux", h1),
    tableau([["Niveau", "Recall@5", "MRR", "Exactitude", "Fidélité", "Abstention", "Précision / refus",
              "Succès tâches", "pass^3", "Tokens / requête", "Latence (s)"],
             ligne_niveau(0, "0 · LLM seul"), ligne_niveau(1, "1 · RAG"), ligne_niveau(2, "2 · Agent"),
             ligne_niveau(3, "3 · Agent + RAG avancé")],
            [3.5, 1.55, 0.95, 1.8, 1.35, 1.7, 1.45, 1.4, 1.15, 1.35, 1.35], gras_premiere_colonne=True),
    p("Tableau 2 · Calculé à partir de results/niveauN.jsonl. Exactitude sur les 34 cas document, abstention sur les 6 "
      "cas absents, précision ou refus sur les 6 cas ambigus, tâches sur 11 tâches × 3 essais. La latence dépend aussi "
      "de la charge de l'API au moment de la mesure (voir section 8).", legende),
]
strates = [["Exactitude par groupe d'œuvres", "Populaires", "Peu connues", "Récentes"]]
for n, nom in enumerate(["0 · LLM seul", "1 · RAG", "2 · Agent", "3 · Agent + RAG avancé"]):
    strates.append([nom] + [pct(taux(resultats[n], "exactitude", s)) for s in ("populaire", "peu_connu", "recent")])
histoire += [
    tableau(strates, [5.4, 2.4, 2.4, 2.4], gras_premiere_colonne=True),
    Spacer(1, 6),
    p("<b>Niveau 0, le LLM seul.</b> Il répond correctement sur une partie des œuvres connues, mais tombe à 8 % sur "
      "les films récents. Il ne connaît ni les slogans ni les notes du public, et ses réponses ne citent rien. Il "
      "s'abstient en revanche sur les six questions sans réponse, au lieu d'inventer un film."),
    p("<b>Niveau 1, le RAG.</b> L'exactitude passe de 47 % à 82 %, et de 8 % à 92 % sur les films récents. Les "
      "réponses citent leurs sources et le juge n'en trouve aucune infidèle. Les nouvelles sources répondent à des "
      "questions qu'aucune page Wikipédia ne couvre, et quand elles se contredisent, le RAG donne parfois les deux "
      "valeurs (« 135 minutes selon TMDB, ou 132 minutes selon la fiche technique »). Elles ajoutent aussi des "
      "extraits concurrents : avec Wikipédia seul, le RAG atteignait 93 % d'exactitude. Il consomme quatre fois plus "
      "de tokens que le LLM seul."),
    p("<b>Niveau 2, l'agent.</b> Il réussit les 11 tâches aux trois essais, y compris celles qui testent les règles : "
      "un doublon, un film qui n'existe pas, un ajout refusé, un retrait refusé. Il traite aussi les demandes "
      "ambiguës : sur TMDB, il voit plusieurs « Nosferatu » et demande lequel. Son exactitude monte à 88 %. Il "
      "consomme quatre fois plus de tokens que le RAG, il est beaucoup plus lent, et il retrouve moins bien les "
      "documents (Recall@5 de 71 %)."),
    p("<b>Niveau 3, l'agent avec le RAG avancé.</b> Le Recall@5 remonte de 71 % à 88 %, le MRR de 0,60 à 0,67, et "
      "l'exactitude de 88 % à 94 %, le meilleur score des quatre niveaux. Il consomme un peu moins de tokens que le "
      "niveau 2, parce que l'agent relance moins souvent ses recherches, mais le reranking ajoute environ deux "
      "secondes par recherche. Sur les quatre questions où le bon extrait manque, l'agent n'a pas consulté les "
      "documents dans deux cas. Il perd aussi un cas ambigu que le niveau 2 réussissait (« Qui joue dans "
      "Frankenstein ? »), d'où 83 % en précision ou refus."),
]

echecs = [
    ("Le niveau 0 invente un chiffre (doc-20).",
     "Interrogé sur le budget d'<i>Un p'tit truc en plus</i>, le modèle répond « environ 5,5 millions d'euros », sans "
     "signaler le moindre doute. Le vrai chiffre est 6,1 millions. Le film date de 2024 et le modèle ne le connaît "
     "pas. Le RAG trouve le budget dans la page du film."),
    ("Le RAG ne voit pas l'ambiguïté (amb-02).",
     "À la question « Qui joue dans Frankenstein ? », le niveau 1 répond pour l'adaptation de 2025 au lieu de "
     "demander de laquelle on parle, parce que notre corpus ne contient que celle-là. L'agent du niveau 2 trouve "
     "plusieurs Frankenstein sur TMDB et pose la question ; celui du niveau 3, dont les extraits les mieux classés "
     "parlent tous du film de 2025, répond directement."),
    ("Le bon passage n'est pas dans les cinq extraits (doc-27).",
     "Le nombre d'entrées du <i>Salaire de la peur</i> figure dans sa page Wikipédia, mais la recherche du niveau 1 "
     "ne remonte pas la section « Box-office ». Le modèle s'abstient, alors que la réponse existait. L'agent des "
     "niveaux 2 et 3 relance ses recherches, finit par trouver le passage et répond juste."),
    ("Trois sources, deux budgets (doc-17).",
     "Pour le budget de <i>Flow</i>, Wikipédia indique 3,5 millions d'euros et TMDB 3,7 millions de dollars. Le RAG "
     "et l'agent ne retrouvent que la fiche TMDB et répondent « 3 700 000 dollars ». Le niveau 3 remonte aussi le "
     "passage Wikipédia grâce au reranking et cite les deux sources. Avec Wikipédia seul, le RAG et l'agent "
     "s'abstenaient sur cette question."),
    ("Deux sources se contredisent (doc-20, niveaux 2 et 3).",
     "L'agent répond « 6 400 000 dollars » pour le budget d'<i>Un p'tit truc en plus</i> : il a lu le chiffre de TMDB "
     "en direct, sans consulter les documents, alors que Wikipédia indique 6,1 millions d'euros. Le juge déclare la "
     "réponse fidèle, à juste titre puisqu'elle reprend sa source, mais elle ne correspond pas à notre référence. "
     "Cet échec est apparu quand nous avons ajouté le box-office de TMDB, et ni le juge ni la recherche ne détectent "
     "ce genre de conflit. La durée de <i>Parasite</i> (135 minutes sur TMDB, 132 sur Wikipédia) en est un deuxième "
     "exemple. Le niveau 3 ne le corrige pas ; il faudrait obliger l'agent à consulter les documents d'abord, ou lui "
     "faire signaler les écarts entre sources."),
]
histoire.append(p("7. Analyse de cinq échecs", h1))
histoire.append(p("Un niveau supérieur corrige les échecs 1, 3 et 4. Les échecs 4 et 5 viennent tous deux des "
                  "contradictions entre sources, apparues avec l'ajout de TMDB et d'IMDb."))
for i, (titre_echec, texte_echec) in enumerate(echecs, start=1):
    histoire.append(p(f"<b>{i}. {titre_echec}</b> {texte_echec}"))

histoire += [
    p("8. Coût et limites", h1),
    p("Une requête consomme 282 tokens au niveau 0, 1 214 au niveau 1 et entre 4 400 et 4 800 pour l'agent, soit "
      "environ seize fois plus que le LLM seul. Le reranking ajoute environ deux secondes par recherche sur "
      "processeur, plus 27 secondes de chargement du modèle au démarrage. Les latences du tableau mélangent deux "
      "journées : les réponses déjà en cache gardent la latence de leur première mesure, et la réévaluation après "
      "l'ajout des sources a eu lieu un jour où l'API répondait lentement (de 2 à 5 secondes par appel, avec des "
      "erreurs 503). Il faut donc les lire comme des ordres de grandeur. Le juge consomme ses propres tokens, que le "
      "tableau ne compte pas puisqu'ils servent à l'évaluation. L'encodage du corpus (875 secondes) n'est payé "
      "qu'une fois. Tout le projet tourne sans GPU, dans l'offre gratuite de Gemini."),
    p("Notre jeu de test est petit : une question document pèse 2,9 points d'exactitude, et un écart de 4 points "
      "entre deux niveaux tient à un ou deux cas. En dehors des tâches, chaque cas n'est lancé qu'une fois. Même à "
      "température 0, Gemini n'est pas parfaitement déterministe ; le cache permet de retrouver exactement notre "
      "tableau, mais le modèle pourrait répondre autrement demain. Nous avons choisi le niveau 3 en regardant les "
      "requêtes de ce même jeu de test, et nous n'avons réglé aucun paramètre pour limiter le sur-ajustement. La "
      "latence des niveaux 2 et 3 varie un peu d'une exécution à l'autre, car la recherche locale est chronométrée en "
      "direct. Les tests et l'annotation du juge sont de nous, avec un LLM pour la pré-annotation. Les notes IMDb "
      "changent avec le temps ; nos tests portent sur les données du 17 novembre 2026. Enfin, l'agent ne garde pas "
      "la mémoire d'une question à l'autre : à « Et la suite, elle sort quand ? », il demande de quelle œuvre on "
      "parle."),

    p("9. Reproduire les résultats", h1),
    p("Après <i>pip install -r requirements.txt</i>, la commande <i>python eval.py</i> rejoue les 57 cas sur les "
      "quatre niveaux et réécrit <i>results/tableau.md</i>. Les réponses du modèle et de TMDB sont relues dans le "
      "dossier <i>cache/</i>, et aucune clé d'API n'est nécessaire pour retrouver nos chiffres. Le dépôt contient "
      "aussi les trois sources, le jeu de test, les résultats bruts et les traces de chaque niveau, les comparaisons "
      "de recherche, la calibration du juge et le fichier <i>.env.example</i> ; aucune clé n'y est versionnée. "
      "L'interface se lance avec <i>streamlit run app.py</i>. Ce rapport est généré par "
      "<i>rapport/generer_rapport.py</i> à partir des résultats bruts, et ses tableaux correspondent donc à ceux "
      "d'<i>eval.py</i>."),

    p("10. Conclusion", h1),
    p("Le RAG rend l'assistant fiable sur les films qu'il ne connaît pas et lui fait citer ses sources. L'agent "
      "modifie la liste seulement avec l'accord de l'utilisateur, et il repère les demandes ambiguës. Le RAG avancé "
      "corrige la recherche que l'agent avait dégradée. Avec trois sources, l'assistant répond à plus de questions, "
      "mais il rencontre aussi des chiffres qui se contredisent. Chaque niveau plus autonome coûte davantage de "
      "tokens et de secondes. La suite logique serait d'apprendre à l'agent à comparer ses sources quand elles "
      "divergent, au lieu de reprendre la première trouvée."),
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

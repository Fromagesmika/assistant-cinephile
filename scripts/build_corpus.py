"""Télécharge le corpus : une page Wikipédia (fr) par titre de data/films.csv.

Résultat : data/corpus.jsonl, une ligne par page. On garde le numéro de révision
pour pouvoir dire exactement quelle version du texte a servi à l'évaluation.

Lancement : python scripts/build_corpus.py
"""
import csv
import json
import time
from pathlib import Path

import requests

RACINE = Path(__file__).resolve().parent.parent
API = "https://fr.wikipedia.org/w/api.php"
ENTETES = {"User-Agent": "CinephileProjetEtudiant/0.1 (projet de cours)"}
TAILLE_MIN = 500  # en dessous, c'est une ébauche ou une page d'homonymie
MAX_ESSAIS = 6
PAUSE = 2.0  # secondes entre deux pages : l'API publique limite le débit


def telecharger_page(titre):
    """Renvoie le texte brut, le titre final et la révision, ou None si la page n'existe pas."""
    params = {
        "action": "query",
        "format": "json",
        "titles": titre,
        "prop": "extracts|revisions",
        "explaintext": 1,
        "rvprop": "ids",
        "redirects": 1,  # suit les redirections, sinon une page redirigée revient vide
    }
    for essai in range(MAX_ESSAIS):
        reponse = requests.get(API, params=params, headers=ENTETES, timeout=30)
        if reponse.status_code == 429:  # trop de requêtes : on attend le délai demandé par le serveur
            time.sleep(int(reponse.headers.get("Retry-After", 15 * (essai + 1))))
            continue
        reponse.raise_for_status()
        page = next(iter(reponse.json()["query"]["pages"].values()))
        if "missing" in page or not page.get("extract"):
            return None
        return {
            "titre": page["title"],
            "revision": page["revisions"][0]["revid"],
            "texte": page["extract"],
        }
    raise RuntimeError(f"Wikipédia refuse encore après {MAX_ESSAIS} essais : {titre}")


def main():
    with open(RACINE / "data" / "films.csv", encoding="utf-8", newline="") as f:
        lignes = list(csv.DictReader(f))

    # Reprise : les pages déjà présentes ne sont pas retéléchargées.
    chemin_corpus = RACINE / "data" / "corpus.jsonl"
    deja_la = {}
    if chemin_corpus.exists():
        with open(chemin_corpus, encoding="utf-8") as f:
            deja_la = {d["titre_wiki"]: d for d in map(json.loads, f)}

    documents, problemes = [], []
    for ligne in lignes:
        if ligne["titre_wiki"] in deja_la:
            documents.append(deja_la[ligne["titre_wiki"]])
            continue
        page = telecharger_page(ligne["titre_wiki"])
        time.sleep(PAUSE)
        if page is None:
            problemes.append((ligne["titre_wiki"], "page absente"))
        elif len(page["texte"]) < TAILLE_MIN or "homonymie" in page["titre"].lower():
            problemes.append((ligne["titre_wiki"], f"trop courte ou homonymie : {page['titre']}"))
        else:
            documents.append({
                "doc_id": page["titre"],
                "titre_wiki": ligne["titre_wiki"],
                "strate": ligne["strate"],
                "type": ligne["type"],
                "revision": page["revision"],
                "url": "https://fr.wikipedia.org/wiki/" + page["titre"].replace(" ", "_"),
                "texte": page["texte"],
            })

    with open(chemin_corpus, "w", encoding="utf-8") as f:
        for doc in documents:
            f.write(json.dumps(doc, ensure_ascii=False) + "\n")

    print(f"{len(documents)} documents enregistrés, {len(problemes)} problèmes")
    for titre, raison in problemes:
        print(f"  - {titre} : {raison}")


if __name__ == "__main__":
    main()

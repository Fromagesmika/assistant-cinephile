"""Construit les deux sources documentaires qui complètent Wikipédia dans le RAG.

- TMDB (themoviedb.org) : une fiche par œuvre, en français (synopsis, slogan, équipe, budget,
  recettes, mots-clés), suivie d'au plus deux critiques d'utilisateurs (souvent en anglais).
- IMDb (imdb.com) : la note moyenne des utilisateurs et le nombre de votes, tirés du jeu de
  données public title.ratings (https://datasets.imdbws.com, usage non commercial).

Chaque document reprend le titre de la page Wikipédia de l'œuvre (data/corpus.jsonl) suivi de sa
source, par exemple « Parasite (film, 2019) · TMDB » : on sait toujours de quelle œuvre et de
quelle plateforme vient un extrait.

Résultat : data/corpus_tmdb.jsonl et data/corpus_imdb.jsonl
Lancement : python scripts/build_sources.py
"""
import csv
import gzip
import io
import json
import sys
import time
from pathlib import Path

import requests

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))
from src import tmdb  # noqa: E402

URL_IMDB = "https://datasets.imdbws.com/title.ratings.tsv.gz"
FICHIER_IMDB = RACINE / "data" / "sources" / "title.ratings.tsv.gz"
DATE = time.strftime("%Y-%m-%d")


def nombre(n):
    return f"{n:,}".replace(",", " ")


def fiche_film(info):
    d, _ = tmdb.appeler(f"/movie/{info['tmdb_id']}", append_to_response="credits,keywords,external_ids")
    equipe = d.get("credits", {}).get("crew", [])
    lignes = [
        "== Fiche TMDB ==",
        f"Titre : {d.get('title')} (titre original : {d.get('original_title')})",
    ]
    if d.get("tagline"):
        lignes.append(f"Slogan : {d['tagline']}")
    if d.get("release_date"):
        lignes.append(f"Date de sortie : {d['release_date']}")
    if d.get("runtime"):
        lignes.append(f"Durée : {d['runtime']} minutes")
    for nom, valeurs in [
        ("Genres", [g["name"] for g in d.get("genres", [])]),
        ("Pays de production", [p["name"] for p in d.get("production_countries", [])]),
        ("Réalisation", [p["name"] for p in equipe if p.get("job") == "Director"]),
        ("Scénario", [p["name"] for p in equipe if p.get("job") in ("Screenplay", "Writer")][:4]),
        ("Musique", [p["name"] for p in equipe if p.get("job") == "Original Music Composer"][:3]),
        ("Acteurs principaux", [f"{a['name']} ({a.get('character')})" for a in d.get("credits", {}).get("cast", [])[:6]]),
        ("Sociétés de production", [c["name"] for c in d.get("production_companies", [])][:5]),
    ]:
        if valeurs:
            lignes.append(f"{nom} : {', '.join(valeurs)}")
    if d.get("budget"):
        lignes.append(f"Budget : {nombre(d['budget'])} dollars")
    if d.get("revenue"):
        lignes.append(f"Recettes mondiales au box-office : {nombre(d['revenue'])} dollars")
    if d.get("vote_count"):
        lignes.append(f"Note moyenne des utilisateurs TMDB : {str(round(d['vote_average'], 1)).replace('.', ',')}/10 ({nombre(d['vote_count'])} votes)")
    if d.get("overview"):
        lignes += ["== Synopsis ==", d["overview"]]
    mots = [k["name"] for k in d.get("keywords", {}).get("keywords", [])][:15]
    if mots:
        lignes += ["== Mots-clés ==", ", ".join(mots)]
    critiques, _ = tmdb.appeler(f"/movie/{info['tmdb_id']}/reviews", language="en-US")
    return lignes, critiques, d.get("external_ids", {}).get("imdb_id"), f"https://www.themoviedb.org/movie/{info['tmdb_id']}"


def fiche_serie(info):
    d, _ = tmdb.appeler(f"/tv/{info['tmdb_id']}", append_to_response="credits,keywords,external_ids")
    lignes = [
        "== Fiche TMDB ==",
        f"Titre : {d.get('name')} (titre original : {d.get('original_name')})",
    ]
    if d.get("tagline"):
        lignes.append(f"Slogan : {d['tagline']}")
    for nom, valeur in [
        ("Première diffusion", d.get("first_air_date")),
        ("Dernière diffusion", d.get("last_air_date")),
        ("Nombre de saisons", d.get("number_of_seasons")),
        ("Nombre d'épisodes", d.get("number_of_episodes")),
        ("Statut", d.get("status")),
    ]:
        if valeur:
            lignes.append(f"{nom} : {valeur}")
    for nom, valeurs in [
        ("Genres", [g["name"] for g in d.get("genres", [])]),
        ("Création", [c["name"] for c in d.get("created_by", [])]),
        ("Chaînes", [n["name"] for n in d.get("networks", [])]),
        ("Acteurs principaux", [f"{a['name']} ({a.get('character')})" for a in d.get("credits", {}).get("cast", [])[:6]]),
    ]:
        if valeurs:
            lignes.append(f"{nom} : {', '.join(valeurs)}")
    if d.get("vote_count"):
        lignes.append(f"Note moyenne des utilisateurs TMDB : {str(round(d['vote_average'], 1)).replace('.', ',')}/10 ({nombre(d['vote_count'])} votes)")
    if d.get("overview"):
        lignes += ["== Synopsis ==", d["overview"]]
    mots = [k["name"] for k in d.get("keywords", {}).get("results", [])][:15]
    if mots:
        lignes += ["== Mots-clés ==", ", ".join(mots)]
    critiques, _ = tmdb.appeler(f"/tv/{info['tmdb_id']}/reviews", language="en-US")
    return lignes, critiques, d.get("external_ids", {}).get("imdb_id"), f"https://www.themoviedb.org/tv/{info['tmdb_id']}"


def notes_imdb():
    """Charge (en le téléchargeant une fois) le jeu de données public des notes IMDb."""
    if not FICHIER_IMDB.exists():
        FICHIER_IMDB.parent.mkdir(parents=True, exist_ok=True)
        reponse = requests.get(URL_IMDB, timeout=120)
        reponse.raise_for_status()
        FICHIER_IMDB.write_bytes(reponse.content)
    with gzip.open(FICHIER_IMDB, "rt", encoding="utf-8") as f:
        return {l["tconst"]: (float(l["averageRating"]), int(l["numVotes"])) for l in csv.DictReader(f, delimiter="\t")}


def main():
    with open(RACINE / "data" / "corpus.jsonl", encoding="utf-8") as f:
        wiki = [json.loads(l) for l in f]
    affiches = json.loads((RACINE / "data" / "affiches.json").read_text(encoding="utf-8"))
    notes = notes_imdb()

    docs_tmdb, docs_imdb, sans_imdb = [], [], []
    for page in wiki:
        info = affiches.get(page["doc_id"])
        if not info:
            continue
        lignes, critiques, imdb_id, url = (fiche_serie if info["type"] == "serie" else fiche_film)(info)
        avis = [c for c in critiques.get("results", []) if len(c.get("content", "")) > 200][:2]
        if avis:
            lignes.append("== Critiques d'utilisateurs TMDB ==")
            for c in avis:
                note = c.get("author_details", {}).get("rating")
                texte = " ".join(c["content"].split())[:700]
                lignes.append(f"Critique de {c['author']}" + (f" (note {note}/10)" if note else "") + f" : {texte}")
        commun = {"strate": page["strate"], "type": page["type"], "titre_wiki": page["titre_wiki"], "date": DATE}
        docs_tmdb.append({"doc_id": f"{page['doc_id']} · TMDB", "source": "TMDB", "url": url,
                          "texte": "\n".join(lignes), "page_wiki": page["doc_id"], **commun})
        if imdb_id and imdb_id in notes:
            moyenne, votes = notes[imdb_id]
            texte = "\n".join([
                "== Notes des utilisateurs IMDb ==",
                f"Note moyenne des utilisateurs IMDb : {str(moyenne).replace('.', ',')}/10",
                f"Nombre de votes sur IMDb : {nombre(votes)}",
                f"Identifiant IMDb : {imdb_id}",
                f"Données IMDb relevées le {DATE}.",
            ])
            docs_imdb.append({"doc_id": f"{page['doc_id']} · IMDb", "source": "IMDb", "url": f"https://www.imdb.com/title/{imdb_id}/",
                              "texte": texte, "page_wiki": page["doc_id"], **commun})
        else:
            sans_imdb.append(page["doc_id"])

    for nom, docs in (("corpus_tmdb.jsonl", docs_tmdb), ("corpus_imdb.jsonl", docs_imdb)):
        with open(RACINE / "data" / nom, "w", encoding="utf-8") as f:
            for d in docs:
                f.write(json.dumps(d, ensure_ascii=False) + "\n")
    print(f"TMDB : {len(docs_tmdb)} fiches, dont {sum('Critiques' in d['texte'] for d in docs_tmdb)} avec critiques")
    print(f"IMDb : {len(docs_imdb)} fiches ; sans note IMDb : {sans_imdb or 'aucune'}")


if __name__ == "__main__":
    main()

"""Associe chaque œuvre du corpus à sa fiche TMDB et télécharge son affiche.

Résultat :
- data/affiches.json : page Wikipédia -> identifiant TMDB, titre, année, chemin de l'affiche ;
- data/affiches/<type>_<tmdb_id>.jpg : les affiches (non versionnées, voir .gitignore).

Les affiches servent seulement à l'interface ; elles n'entrent dans aucune mesure.
Lancement : python scripts/telecharger_affiches.py
"""
import csv
import json
import re
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))
from src import affiches, tmdb  # noqa: E402
from src.metrics import normaliser  # noqa: E402


def titre_recherche(titre_wiki):
    """« Parasite (film, 2019) » devient « Parasite » : TMDB ne connaît pas les précisions de Wikipédia."""
    return re.sub(r"\s*\([^)]*\)\s*$", "", titre_wiki).strip()


def annee_probable(texte):
    """Première année plausible du résumé Wikipédia (souvent l'année de sortie)."""
    m = re.search(r"\b(18[89]\d|19\d\d|20[0-2]\d)\b", texte[:400])
    return int(m.group(1)) if m else None


def choisir(resultats, titre, annee):
    """Titre identique d'abord (l'année Wikipédia peut différer d'un an de celle de TMDB), puis année."""
    exacts = [r for r in resultats if normaliser(titre) in (normaliser(r["titre"] or ""), normaliser(r["titre_original"] or ""))]
    for groupe in (exacts, resultats):
        if annee:
            proches = [r for r in groupe if r["annee"] and abs(r["annee"] - annee) <= 1]
            if proches:
                return min(proches, key=lambda r: abs(r["annee"] - annee))
    return (exacts or resultats)[0]


def main():
    with open(RACINE / "data" / "corpus.jsonl", encoding="utf-8") as f:
        corpus = {d["doc_id"]: d for d in map(json.loads, f)}
    with open(RACINE / "data" / "films.csv", encoding="utf-8") as f:
        oeuvres = list(csv.DictReader(f))

    table, manquantes = {}, []
    for oeuvre in oeuvres:
        document = next((d for d in corpus.values() if d["titre_wiki"] == oeuvre["titre_wiki"]), None)
        if document is None:
            continue
        type_oeuvre = "serie" if oeuvre["type"] == "serie" else "film"
        titre = titre_recherche(document["doc_id"])
        # L'année du titre Wikipédia (« Les Misérables (film, 2019) ») est la plus sûre.
        dans_titre = re.search(r"\((?:film|série[^,]*), (\d{4})\)", document["doc_id"])
        annee = int(dans_titre.group(1)) if dans_titre else annee_probable(document["texte"])
        resultats, _ = tmdb.rechercher(titre, type_oeuvre, annee)
        if not resultats:  # l'année devinée peut être fausse : on réessaie sans
            resultats, _ = tmdb.rechercher(titre, type_oeuvre)
        if not resultats and "," in titre:  # titres très longs : TMDB n'en garde que le début
            resultats, _ = tmdb.rechercher(titre.split(",")[0], type_oeuvre)
        if not resultats:
            manquantes.append(document["doc_id"])
            continue
        choix = choisir(resultats, titre, annee)
        chemin = affiches.telecharger(choix["tmdb_id"], type_oeuvre)
        table[document["doc_id"]] = {
            "tmdb_id": choix["tmdb_id"], "type": type_oeuvre, "titre": choix["titre"], "annee": choix["annee"],
            "affiche": chemin.relative_to(RACINE).as_posix() if chemin else None,
        }
        print(f"  {'ok ' if chemin else 'sans affiche'} {document['doc_id']} -> {choix['titre']} ({choix['annee']})")

    (RACINE / "data" / "affiches.json").write_text(json.dumps(table, ensure_ascii=False, indent=1), encoding="utf-8")
    avec = sum(1 for v in table.values() if v["affiche"])
    print(f"\n{len(table)} œuvres associées, {avec} affiches ; introuvables : {manquantes or 'aucune'}")


if __name__ == "__main__":
    main()

"""Interface Streamlit de l'assistant cinéphile.

Ce que le sujet demande, et où on le trouve sur la page :
- choix du niveau 0 à 3 ............ bandeau « Niveau » en haut, toujours visible ;
- réponse et sources citées ........ carte de réponse, rubrique « Sources citées » ;
- coûts ........................... rubrique « Coût de la requête » (tokens, latence, appels) ;
- trace de chaque exécution ....... onglet « Trace » (étapes, outils, arguments, tokens, durée),
                                     enregistrée en JSONL dans traces/interface.jsonl ;
- confirmation des actions ........ carte « Action à confirmer », boutons Accepter / Refuser.

Lancement : streamlit run app.py
"""
import json
import re
import time
from pathlib import Path

import streamlit as st

from src import affiches, tmdb
from src.levels import level0, level1, level2, level3
from src.liste import ListeAVoir
from src.rag import charger_corpus
from src.traces import ecrire_trace_interface

RACINE = Path(__file__).resolve().parent
FICHIER_LISTE = RACINE / "data" / "liste_a_voir.json"

NIVEAUX = {
    0: ("Niveau 0 · LLM seul", "Répond de mémoire, sans document ni outil."),
    1: ("Niveau 1 · RAG", "Cherche 5 extraits (Wikipédia, TMDB, IMDb) et les cite."),
    2: ("Niveau 2 · Agent", "Choisit ses outils et gère la liste à voir, avec votre accord."),
    3: ("Niveau 3 · Agent + RAG avancé", "L'agent du niveau 2, avec une recherche hybride et un reranking."),
}
NIVEAUX_PRETS = {0, 1, 2, 3}
STATUTS = {
    "reponse": ("Réponse", "green", "Réponse appuyée sur les sources citées."),
    "abstention": ("Abstention", "orange", "Les sources ne contiennent pas la réponse : l'assistant préfère ne pas inventer."),
    "precision": ("Question de précision", "blue", "La demande est ambiguë : l'assistant demande de préciser."),
    "refus": ("Refus", "red", "La demande sort du cinéma et des séries."),
}
SUGGESTIONS = {
    "Musique d'un film": "Qui a composé la musique de Valeur sentimentale de Joachim Trier ?",
    "Box-office": "Combien d'entrées Un p'tit truc en plus d'Artus a-t-il réalisées le jour de sa sortie ?",
    "Demande ambiguë": "Qui a réalisé Nosferatu ?",
    "Modifier la liste": "Ajoute Grave et Titane, les deux films de Julia Ducournau, à la liste à voir.",
}
NOMS_OUTILS = {
    "rechercher_documents": "Recherche documents", "rechercher_oeuvre": "Recherche TMDB",
    "details_oeuvre": "Fiche TMDB", "recommander_oeuvres": "Recommandations TMDB", "lire_liste": "Lecture de la liste",
    "ajouter_a_la_liste": "Ajout à la liste", "retirer_de_la_liste": "Retrait de la liste",
}


# --- Données ----------------------------------------------------------------------------------

@st.cache_data
def corpus():
    """Les trois sources (Wikipédia, TMDB, IMDb), indexées par identifiant de document."""
    return {d["doc_id"]: {"url": d["url"], "strate": d["strate"], "source": d["source"],
                          "page": d.get("page_wiki", d["doc_id"])} for d in charger_corpus()}


@st.cache_data
def table_affiches():
    chemin = RACINE / "data" / "affiches.json"
    return json.loads(chemin.read_text(encoding="utf-8")) if chemin.exists() else {}


def oeuvre_de_source(doc_id):
    """Œuvre (titre, année, affiche, lien) correspondant à une source citée, Wikipédia ou TMDB."""
    if doc_id.startswith("TMDB:"):
        tmdb_id = int(doc_id.removeprefix("TMDB:"))
        connue = next((o for o in table_affiches().values() if o["tmdb_id"] == tmdb_id), None)
        type_oeuvre = connue["type"] if connue else "film"
        if connue is None:  # œuvre hors corpus : on lit son titre sur TMDB (réponse mise en cache)
            try:
                fiche, _ = tmdb.appeler(f"/movie/{tmdb_id}")
                connue = {"titre": fiche.get("title") or f"Œuvre TMDB {tmdb_id}",
                          "annee": int(fiche["release_date"][:4]) if fiche.get("release_date") else None}
            except Exception:
                connue = {"titre": f"Œuvre TMDB {tmdb_id}", "annee": None}
        return {"cle": (type_oeuvre, tmdb_id), "titre": connue["titre"],
                "annee": connue["annee"], "affiche": affiches.affiche(tmdb_id, type_oeuvre),
                "lien": ("TMDB", f"https://www.themoviedb.org/{'tv' if type_oeuvre == 'serie' else 'movie'}/{tmdb_id}")}
    info = corpus().get(doc_id, {})
    oeuvre = table_affiches().get(info.get("page", doc_id))
    lien = (info.get("source", "Wikipédia"), info.get("url"))
    if not oeuvre:
        return {"cle": ("wiki", doc_id), "titre": doc_id, "annee": None, "affiche": None, "lien": lien}
    return {"cle": (oeuvre["type"], oeuvre["tmdb_id"]), "titre": oeuvre["titre"], "annee": oeuvre["annee"],
            "affiche": affiches.affiche(oeuvre["tmdb_id"], oeuvre["type"]), "lien": lien}


def numeros_cites(texte):
    return {int(n) for groupe in re.findall(r"\[([\d\s,]+)\]", texte) for n in re.findall(r"\d+", groupe)}


def nombre(valeur):
    return f"{valeur:,.0f}".replace(",", " ")


# --- Trace ------------------------------------------------------------------------------------

def lignes_trace(sortie):
    """Une ligne par étape : ce que le sujet demande (étape, outil, arguments, tokens, durée)."""
    lignes = []
    un_seul_appel = sum(e["type"] == "llm" for e in sortie["etapes"]) == 1
    for numero, etape in enumerate(sortie["etapes"], start=1):
        ligne = {"N°": numero, "Étape": "", "Outil": "", "Arguments": "", "Tokens": None, "Durée (s)": None, "Résultat": ""}
        genre = etape["type"]
        if genre == "llm":
            demandes = ", ".join(NOMS_OUTILS.get(n, n) for n in etape.get("outils_demandes", []))
            ligne.update({"Étape": "Appel au modèle", "Outil": etape.get("modele", ""),
                          "Résultat": f"demande : {demandes}" if demandes else "réponse finale",
                          # Niveaux 0 et 1 : un seul appel, ses coûts sont ceux de la requête.
                          "Tokens": etape.get("tokens", sortie["tokens"] if un_seul_appel else None),
                          "Durée (s)": etape.get("latence", round(sortie["latence"], 3) if un_seul_appel else None)})
        elif genre == "recherche":
            ligne.update({"Étape": "Recherche dans les documents", "Outil": "Recherche documents",
                          "Arguments": f"k = {etape['k']}",
                          "Résultat": ", ".join(f"{pid} ({score:.2f})" for pid, score in etape["resultats"])})
        elif genre == "outil":
            ligne.update({"Étape": "Outil · écriture" if etape["effet"] == "ecriture" else "Outil · lecture",
                          "Outil": NOMS_OUTILS.get(etape["nom"], etape["nom"]),
                          "Arguments": json.dumps(etape["arguments"], ensure_ascii=False),
                          "Durée (s)": etape.get("duree"), "Résultat": etape.get("resultat", "")})
        elif genre == "confirmation":
            ligne.update({"Étape": "Confirmation de l'utilisateur", "Arguments": etape["action"], "Résultat": etape["decision"]})
        elif genre == "ecriture":
            ligne.update({"Étape": "Écriture dans la liste", "Arguments": f"{etape['action']} {etape['tmdb_id']}",
                          "Résultat": "faite" if etape["ok"] else "échec"})
        else:
            ligne.update({"Étape": "Règle du code" if genre == "regle" else "Limite de la boucle",
                          "Résultat": etape.get("detail", "")})
        # Cases vides affichées « — » plutôt que « None ».
        lignes.append({cle: ("—" if valeur in (None, "") else valeur) for cle, valeur in ligne.items()})
    return lignes


# --- Affichage --------------------------------------------------------------------------------

def cartes_oeuvres(oeuvres, colonnes=6):
    if not oeuvres:
        return
    grille = st.columns(colonnes)
    for i, oeuvre in enumerate(oeuvres):
        with grille[i % colonnes]:
            if oeuvre["affiche"]:
                st.image(str(oeuvre["affiche"]), width="stretch")
            titre = oeuvre["titre"] + (f" ({oeuvre['annee']})" if oeuvre["annee"] else "")
            nom, url = oeuvre["lien"]
            st.markdown(f"**{titre}**  \n[{nom}]({url})" if url else f"**{titre}**")


def afficher_reponse(entree):
    sortie = entree["sortie"]
    libelle, couleur, explication = STATUTS.get(sortie["statut"], (sortie["statut"], "gray", ""))
    if entree["niveau"] == 0 and sortie["statut"] in ("reponse", "abstention"):
        explication = ("Réponse de mémoire, sans source : rien ne permet de la vérifier." if sortie["statut"] == "reponse"
                       else "Le modèle ne connaît pas la réponse : il préfère ne pas inventer.")
    passages = sortie.get("passages") or []
    cites = sorted(n for n in numeros_cites(sortie["texte"]) if 1 <= n <= len(passages)) if sortie["statut"] == "reponse" else []
    oeuvres, vues = [], set()
    for n in cites:
        oeuvre = oeuvre_de_source(passages[n - 1]["doc_id"])
        if oeuvre["cle"] not in vues:
            vues.add(oeuvre["cle"])
            oeuvres.append(oeuvre)
    # Actions réellement faites sur la liste (niveau 2) : on montre les œuvres concernées.
    ecritures = [e for e in sortie["etapes"] if e["type"] == "ecriture" and e["ok"]]
    if ecritures and not cites:
        explication = "Compte rendu des modifications de la liste, faites après votre accord."
        oeuvres = []
        for e in ecritures:
            oeuvre = oeuvre_de_source(f"TMDB:{e['tmdb_id']}")
            oeuvre["titre"] = ("Ajouté : " if e["action"] == "ajouter" else "Retiré : ") + oeuvre["titre"]
            oeuvres.append(oeuvre)
    titre_oeuvres = "Liste modifiée" if ecritures and not cites else "Œuvres citées"

    # Réponse et coût à gauche, affiches des œuvres à droite.
    gauche, droite = st.columns([3, 1.1]) if oeuvres else (st.container(), None)
    with gauche:
        st.markdown(f":{couleur}-badge[{libelle}] &nbsp; :violet-badge[{NIVEAUX[entree['niveau']][0]}]")
        st.markdown(f'<div class="texte-reponse">{sortie["texte"] or "(réponse vide)"}</div>', unsafe_allow_html=True)
        st.caption(explication)
        st.markdown('<div class="rubrique">Coût de la requête</div>', unsafe_allow_html=True)
        tuiles = st.columns(4)
        tuiles[0].metric("Tokens", nombre(sortie["tokens"]))
        tuiles[1].metric("Latence", f"{sortie['latence']:.1f} s")
        tuiles[2].metric("Appels au modèle", sortie.get("appels_llm", 1))
        tuiles[3].metric("Étapes", len(sortie["etapes"]))
    if droite is not None:
        with droite:
            st.markdown(f'<div class="rubrique">{titre_oeuvres}</div>', unsafe_allow_html=True)
            cartes_oeuvres(oeuvres, colonnes=min(2, len(oeuvres)))

    onglet_sources, onglet_trace = st.tabs([f"Sources citées ({len(cites)} sur {len(passages)} consultées)",
                                            f"Trace ({len(sortie['etapes'])} étapes)"])
    with onglet_sources:
        if not passages:
            st.caption("Niveau 0 : le modèle répond de mémoire, il n'a aucune source à citer.")
        elif not cites and len(passages) > 8:
            st.caption(f"{len(passages)} résultats consultés, aucun cité : le détail est dans l'onglet Trace.")
        for numero, passage in enumerate(passages, start=1):
            if numero not in cites and len(passages) > 8:
                continue  # l'agent consulte parfois des dizaines de résultats : on montre ceux qu'il cite
            oeuvre = oeuvre_de_source(passage["doc_id"])
            nom, url = oeuvre["lien"]
            etat = ":green-badge[citée]" if numero in cites else ":gray-badge[consultée, non citée]"
            st.markdown(f"**[{numero}]** {passage['doc_id']} · [{nom}]({url}) {etat}" if url else f"**[{numero}]** {passage['doc_id']} {etat}")
            st.caption(passage["texte"][:500] + ("…" if len(passage["texte"]) > 500 else ""))
    with onglet_trace:
        st.dataframe(lignes_trace(sortie), hide_index=True, width="stretch",
                     column_config={"Arguments": st.column_config.TextColumn(width="medium"),
                                    "Résultat": st.column_config.TextColumn(width="large")})
        st.caption("Chaque exécution est enregistrée en JSONL dans traces/interface.jsonl.")
        st.download_button("Télécharger la trace (JSON)", json.dumps(entree["trace"], ensure_ascii=False, indent=1),
                           file_name=f"trace_{entree['horodatage']}.json", key=f"trace_{entree['horodatage']}")


# --- Exécution d'une requête ------------------------------------------------------------------

def enregistrer(question, niveau, sortie):
    horodatage = time.strftime("%Y%m%d-%H%M%S")
    trace = {"horodatage": horodatage, "niveau": niveau, "question": question, **sortie}
    ecrire_trace_interface(trace)
    st.session_state.historique.append(
        {"question": question, "niveau": niveau, "sortie": sortie, "trace": trace, "horodatage": horodatage}
    )


def lancer(question, niveau):
    with st.chat_message("user", avatar=":material/person:"):
        st.markdown(question)
    if niveau in (0, 1):
        module = level0 if niveau == 0 else level1
        with st.spinner("Le modèle cherche la réponse…"):
            enregistrer(question, niveau, module.repondre(question))
        return
    # Niveau 2 : la session peut s'arrêter pour demander une confirmation ; on la garde
    # en mémoire entre deux affichages de la page.
    classe = level3.Session if niveau == 3 else level2.Session
    session = classe(question, ListeAVoir(chemin=FICHIER_LISTE))
    with st.spinner("L'agent consulte ses outils…"):
        session.avancer()
    poursuivre(session, question)


def poursuivre(session, question):
    if session.attente is not None:
        st.session_state.en_attente = {"session": session, "question": question}
    else:
        st.session_state.en_attente = None
        enregistrer(question, session.niveau, session.sortie())


def decider(accepte):
    attente = st.session_state.en_attente
    with st.spinner("L'agent reprend…"):
        attente["session"].avancer(accepte)
    poursuivre(attente["session"], attente["question"])


# --- Page -------------------------------------------------------------------------------------

st.set_page_config(page_title="Assistant cinéphile", page_icon=":material/movie:", layout="wide",
                   initial_sidebar_state="collapsed")
st.markdown(f"<style>{(RACINE / 'assets' / 'style.css').read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)
st.session_state.setdefault("historique", [])
st.session_state.setdefault("en_attente", None)
st.session_state.setdefault("niveau", 2)

attente = st.session_state.en_attente
accueil = not st.session_state.historique and attente is None
liste = ListeAVoir(chemin=FICHIER_LISTE)

# Barre du haut : marque, liste à voir et coût de la session.
marque, _, droite = st.columns([3, 2, 1.6], vertical_alignment="center")
marque.markdown('<div class="marque"><span class="logo"></span>Assistant cinéphile</div>', unsafe_allow_html=True)
with droite.container(key="nav_liste"):
    with st.popover(f"Liste à voir · {len(liste.films)}", width="stretch"):
        st.markdown("**Liste à voir partagée**")
        if liste.films:
            cartes_oeuvres([
                {"cle": None, "titre": f["titre"], "annee": f.get("annee"),
                 "affiche": affiches.affiche(f["tmdb_id"], f.get("type", "film")),
                 "lien": ("TMDB", f"https://www.themoviedb.org/{'tv' if f.get('type') == 'serie' else 'movie'}/{f['tmdb_id']}")}
                for f in liste.films], colonnes=3)
        else:
            st.caption("Vide pour l'instant. Au niveau 2, demandez par exemple : « Ajoute Titane à la liste à voir ».")
        historique = st.session_state.historique
        st.divider()
        st.metric("Tokens consommés pendant la session", nombre(sum(e["sortie"]["tokens"] for e in historique)))
        st.caption(f"{len(historique)} requête(s), toutes tracées dans traces/interface.jsonl")
        if historique and st.button("Nouvelle conversation", width="stretch"):
            st.session_state.historique = []
            st.rerun()

# Choix du niveau, toujours visible : c'est le cœur de la comparaison demandée par le sujet.
with st.container(key="niveau_choix"):
    st.markdown('<div class="rubrique">Niveau du système · les quatre niveaux sont comparés sur le même jeu de test</div>',
                unsafe_allow_html=True)
    niveau = st.radio(
        "Niveau", list(NIVEAUX), key="niveau", horizontal=True, format_func=lambda n: NIVEAUX[n][0],
        captions=[NIVEAUX[n][1] for n in NIVEAUX], label_visibility="collapsed", disabled=attente is not None,
    )
pret = niveau in NIVEAUX_PRETS
if not pret:
    st.info("Le niveau 3 (extension mesurée contre l'agent) est en préparation. Choisissez un niveau de 0 à 2.")

if accueil:
    st.markdown('<div class="titre-accueil">Une question de cinéma ? On vous répond.</div>', unsafe_allow_html=True)
    st.markdown('<div class="sous-titre-accueil">Chaque réponse cite ses sources, affiche son coût et sa trace.</div>',
                unsafe_allow_html=True)
    _, milieu, _ = st.columns([0.5, 4, 0.5])
    with milieu.container(key="carte"):
        with st.form("demande", clear_on_submit=True, border=False):
            ligne_saisie, ligne_bouton = st.columns([12, 1], vertical_alignment="center")
            question = ligne_saisie.text_input("Question", placeholder="Posez une question sur un film ou une série…",
                                               label_visibility="collapsed")
            envoyer = ligne_bouton.form_submit_button("→", key="envoyer", disabled=not pret)
            st.markdown('<div class="libelle-suggestions">Exemples</div>', unsafe_allow_html=True)
            colonnes = st.columns(len(SUGGESTIONS))
            choix = None
            for colonne, (libelle, exemple) in zip(colonnes, SUGGESTIONS.items()):
                if colonne.form_submit_button(libelle, width="stretch", disabled=not pret):
                    choix = exemple
    texte = choix or (question.strip() if envoyer else "")
    if texte:
        lancer(texte, niveau)
        st.rerun()

    # Mur d'affiches : un aperçu du corpus sur lequel l'assistant s'appuie.
    oeuvres = [o for o in table_affiches().values() if o.get("affiche")]
    if oeuvres:
        strates = {}
        pages = [info for info in corpus().values() if info["source"] == "Wikipédia"]
        for info in pages:
            strates[info["strate"]] = strates.get(info["strate"], 0) + 1
        st.markdown(
            f'<div class="rubrique centre">Le corpus : {len(pages)} films et séries · '
            f'{strates.get("populaire", 0)} populaires, {strates.get("peu_connu", 0)} peu connus, '
            f'{strates.get("recent", 0)} récents · 3 sources : Wikipédia, TMDB, IMDb</div>', unsafe_allow_html=True)
        pas = max(1, len(oeuvres) // 16)
        selection = oeuvres[::pas][:16]
        with st.container(key="mur"):
            grille = st.columns(8)
            for i, oeuvre in enumerate(selection):
                grille[i % 8].image(str(RACINE / oeuvre["affiche"]), width="stretch")
else:
    for entree in st.session_state.historique:
        with st.chat_message("user", avatar=":material/person:"):
            st.markdown(entree["question"])
        with st.chat_message("assistant", avatar=":material/movie:"):
            afficher_reponse(entree)

    if attente is not None:
        action = attente["session"].attente["action"]
        with st.chat_message("user", avatar=":material/person:"):
            st.markdown(attente["question"])
        with st.container(key="confirmation"):
            image, texte_action = st.columns([1, 6], vertical_alignment="center")
            fiche = action.get("fiche") or {}
            chemin = affiches.affiche(action["tmdb_id"], fiche.get("type", action.get("type_oeuvre", "film")))
            if chemin:
                image.image(str(chemin), width="stretch")
            texte_action.markdown('<div class="rubrique">Action à confirmer</div>', unsafe_allow_html=True)
            texte_action.markdown(f"**{action['texte']}**")
            texte_action.caption("L'agent ne modifie la liste qu'avec votre accord. Rien n'est encore écrit.")
            gauche, droite, _ = texte_action.columns([1, 1, 3])
            if gauche.button("Accepter", type="primary", width="stretch"):
                decider(True)
                st.rerun()
            if droite.button("Refuser", width="stretch"):
                decider(False)
                st.rerun()

    question = st.chat_input("Posez une autre question…", disabled=attente is not None or not pret)
    if question:
        lancer(question, niveau)
        st.rerun()

st.markdown('<div class="pied">Sources : Wikipédia (CC BY-SA 4.0), TMDB et IMDb. Ce produit utilise l\'API TMDB '
            'mais n\'est ni approuvé ni certifié par TMDB. Modèle : Gemini.</div>', unsafe_allow_html=True)

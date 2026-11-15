"""Interface Streamlit : choix du niveau, réponse, sources, coûts, trace et confirmation des actions.

Lancement : streamlit run app.py
Chaque requête est enregistrée dans traces/interface.jsonl. La liste « à voir » est partagée
dans data/liste_a_voir.json : tous les onglets ouverts voient la même liste.
"""
import json
import re
import time
from pathlib import Path

import streamlit as st

from src.levels import level0, level1, level2
from src.liste import ListeAVoir
from src.traces import ecrire_trace_interface

RACINE = Path(__file__).resolve().parent
FICHIER_LISTE = RACINE / "data" / "liste_a_voir.json"

NIVEAUX = {
    0: ("0 · LLM seul", "Le modèle répond de mémoire, sans documents ni outils."),
    1: ("1 · RAG", "Le modèle répond à partir de 5 extraits Wikipédia et les cite."),
    2: ("2 · Agent", "Le modèle choisit ses outils (Wikipédia, TMDB, liste à voir). Chaque modification de la liste attend votre accord."),
    3: ("3 · Extension", "Pas encore construit."),
}
STATUTS = {
    "reponse": ("Réponse", "green"),
    "abstention": ("Abstention", "orange"),
    "precision": ("Question de précision", "blue"),
    "refus": ("Refus", "red"),
}
EXEMPLES = [
    "Qui a composé la musique de Valeur sentimentale de Joachim Trier ?",
    "Combien d'entrées Un p'tit truc en plus d'Artus a-t-il réalisées le jour de sa sortie ?",
    "Qui a réalisé Nosferatu ?",
    "Ajoute Grave et Titane, les deux films de Julia Ducournau, à la liste à voir.",
]


@st.cache_data
def urls_wikipedia():
    with open(RACINE / "data" / "corpus.jsonl", encoding="utf-8") as f:
        return {d["doc_id"]: d["url"] for d in map(json.loads, f)}


def lien_source(doc_id):
    if doc_id.startswith("TMDB:"):
        return f"[{doc_id}](https://www.themoviedb.org/movie/{doc_id.removeprefix('TMDB:')})"
    url = urls_wikipedia().get(doc_id)
    return f"[{doc_id}]({url})" if url else doc_id


def numeros_cites(texte):
    return {int(n) for groupe in re.findall(r"\[([\d\s,]+)\]", texte) for n in re.findall(r"\d+", groupe)}


# --- Affichage d'une réponse ----------------------------------------------------------------

def afficher_reponse(entree):
    sortie = entree["sortie"]
    libelle, couleur = STATUTS.get(sortie["statut"], (sortie["statut"], "gray"))
    st.markdown(f":{couleur}-badge[{libelle}] &nbsp; :gray[niveau {NIVEAUX[entree['niveau']][0]}]")
    st.markdown(sortie["texte"] or "_(réponse vide)_")

    colonnes = st.columns(4)
    colonnes[0].metric("Tokens", f"{sortie['tokens']:,}".replace(",", " "))
    colonnes[1].metric("Latence", f"{sortie['latence']:.1f} s")
    colonnes[2].metric("Appels au modèle", sortie.get("appels_llm", 1))
    colonnes[3].metric("Sources citées", len(sortie["sources"]))

    passages = sortie.get("passages") or []
    if passages:
        cites = numeros_cites(sortie["texte"])
        with st.expander(f"Sources : {len(passages)} extraits consultés, {len(cites)} cités"):
            for numero, passage in enumerate(passages, start=1):
                marque = "**cité**" if numero in cites else ":gray[non cité]"
                st.markdown(f"**[{numero}]** {lien_source(passage['doc_id'])} · {marque}")
                st.caption(passage["texte"][:600] + ("…" if len(passage["texte"]) > 600 else ""))

    with st.expander(f"Trace : {len(sortie['etapes'])} étapes"):
        for etape in sortie["etapes"]:
            afficher_etape(etape)
        st.download_button("Télécharger la trace (JSON)", json.dumps(entree["trace"], ensure_ascii=False, indent=1),
                           file_name=f"trace_{entree['horodatage']}.json", key=f"trace_{entree['horodatage']}")


def afficher_etape(etape):
    genre = etape["type"]
    if genre == "llm":
        outils = ", ".join(etape.get("outils_demandes", [])) or "réponse finale"
        detail = f"{etape.get('tokens', '?')} tokens" if "tokens" in etape else etape.get("modele", "")
        st.markdown(f"🧠 **Modèle** · {detail} → {outils}")
    elif genre == "outil":
        icone = "✏️" if etape["effet"] == "ecriture" else "🔎"
        st.markdown(f"{icone} **{etape['nom']}** `{json.dumps(etape['arguments'], ensure_ascii=False)}`")
        if etape.get("resultat"):
            st.caption(etape["resultat"])
    elif genre == "recherche":
        st.markdown(f"🔎 **Recherche** dans Wikipédia · {etape['k']} extraits")
    elif genre == "confirmation":
        st.markdown(f"🙋 **Confirmation** · {etape['action']} → **{etape['decision']}**")
    elif genre == "ecriture":
        st.markdown(f"💾 **Liste modifiée** · {etape['action']} {etape['tmdb_id']} → {'ok' if etape['ok'] else 'échec'}")
    else:
        st.markdown(f"⚠️ **{genre}** · {etape.get('detail', '')}")


# --- Exécution d'une requête ----------------------------------------------------------------

def enregistrer(question, niveau, sortie):
    horodatage = time.strftime("%Y%m%d-%H%M%S")
    trace = {"horodatage": horodatage, "niveau": niveau, "question": question, **sortie}
    ecrire_trace_interface(trace)
    st.session_state.historique.append(
        {"question": question, "niveau": niveau, "sortie": sortie, "trace": trace, "horodatage": horodatage}
    )


def lancer(question, niveau):
    with st.chat_message("user"):
        st.markdown(question)
    if niveau in (0, 1):
        module = level0 if niveau == 0 else level1
        with st.spinner("Le modèle réfléchit…"):
            enregistrer(question, niveau, module.repondre(question))
        return
    # Niveau 2 : la session peut s'arrêter pour demander une confirmation ; on la garde
    # en mémoire entre deux affichages de la page.
    session = level2.Session(question, ListeAVoir(chemin=FICHIER_LISTE))
    with st.spinner("L'agent travaille…"):
        session.avancer()
    poursuivre(session, question)


def poursuivre(session, question):
    if session.attente is not None:
        st.session_state.en_attente = {"session": session, "question": question}
    else:
        st.session_state.en_attente = None
        enregistrer(question, 2, session.sortie())


def decider(accepte):
    attente = st.session_state.en_attente
    with st.spinner("L'agent reprend…"):
        attente["session"].avancer(accepte)
    poursuivre(attente["session"], attente["question"])


# --- Page ---------------------------------------------------------------------------------

st.set_page_config(page_title="Assistant cinéphile", page_icon="🎬", layout="wide")
st.session_state.setdefault("historique", [])
st.session_state.setdefault("en_attente", None)

with st.sidebar:
    st.title("🎬 Assistant cinéphile")
    niveau = st.radio(
        "Niveau", list(NIVEAUX), format_func=lambda n: NIVEAUX[n][0], index=2,
        disabled=st.session_state.en_attente is not None,
    )
    st.caption(NIVEAUX[niveau][1])

    st.divider()
    liste = ListeAVoir(chemin=FICHIER_LISTE)
    st.subheader(f"Liste à voir ({len(liste.films)})")
    if liste.films:
        st.dataframe(
            [{"Titre": f["titre"], "Année": f.get("annee")} for f in liste.films],
            hide_index=True, use_container_width=True,
        )
    else:
        st.caption("La liste est vide. Demandez à l'agent (niveau 2) d'y ajouter un film.")

    st.divider()
    historique = st.session_state.historique
    st.subheader("Coût de la session")
    st.metric("Tokens consommés", f"{sum(e['sortie']['tokens'] for e in historique):,}".replace(",", " "))
    st.caption(f"{len(historique)} requête(s), traces dans traces/interface.jsonl")
    if historique and st.button("Effacer la conversation"):
        st.session_state.historique = []
        st.rerun()

for entree in st.session_state.historique:
    with st.chat_message("user"):
        st.markdown(entree["question"])
    with st.chat_message("assistant"):
        afficher_reponse(entree)

attente = st.session_state.en_attente
if attente is not None:
    action = attente["session"].attente["action"]
    with st.chat_message("user"):
        st.markdown(attente["question"])
    with st.chat_message("assistant"):
        st.warning(f"**Confirmation requise** · {action['texte']}", icon="🙋")
        gauche, droite, _ = st.columns([1, 1, 4])
        if gauche.button("Accepter", type="primary", use_container_width=True):
            decider(True)
            st.rerun()
        if droite.button("Refuser", use_container_width=True):
            decider(False)
            st.rerun()

if not st.session_state.historique and attente is None:
    st.markdown("### Posez une question sur un film ou une série")
    st.caption("Exemples :")
    for exemple in EXEMPLES:
        if st.button(exemple, key=exemple) and niveau != 3:
            lancer(exemple, niveau)
            st.rerun()

if niveau == 3:
    st.info("Le niveau 3 (extension) n'est pas encore construit.")
question = st.chat_input("Votre question…", disabled=attente is not None or niveau == 3)
if question:
    lancer(question, niveau)
    st.rerun()

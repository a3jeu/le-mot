#!/usr/bin/env python3
"""Classement des mots de Lexique 3.83 par fréquence, avec le filtre de la banque du jeu.

Reproduit (à quelques mots près) la façon dont les listes `answers` de words.js
ont été construites :
  - lemmes seulement (forme de base : nom, verbe à l'infinitif, adjectif) ;
  - lettres uniquement (pas de trait d'union ni d'apostrophe) ;
  - fréquence = moyenne de freqlemfilms2 et freqlemlivres ;
  - on retire les mots grammaticaux, les nombres, les participes utilisés
    comme adjectifs, les mots toujours au pluriel, les mots vulgaires, et les
    doublons une fois les accents enlevés (on garde le plus fréquent).

Exemples :
  python3 classement_mots.py                       # rangs 600, 1000, 1500, 2000, 3000
  python3 classement_mots.py --rangs 750 1200      # autres rangs
  python3 classement_mots.py --verifier            # compare avec words.js
  python3 classement_mots.py --exporter 1200       # écrit mots_5.csv et mots_6.csv

Aucune dépendance : seulement la bibliothèque standard de Python 3.
"""
import argparse
import collections
import csv
import json
import os
import re
import sys
import unicodedata
import urllib.request

ICI = os.path.dirname(os.path.abspath(__file__))
URL_LEXIQUE = "http://www.lexique.org/databases/Lexique383/Lexique383.tsv"

CATEGORIES_GARDEES = {"NOM", "VER", "ADJ"}
VULGAIRES = set("""
merde chier garce nègre foutre putain gueule baiser salaud bordel salope
pisser violer crétin abruti débile merder cinglé enculé bouffe
""".split())
LETTRES = re.compile(r"[a-zàâäçéèêëîïôöùûüÿœæ]+")


def sans_accents(mot):
    d = unicodedata.normalize("NFD", mot)
    return "".join(c for c in d if unicodedata.category(c) != "Mn").replace("œ", "oe").replace("æ", "ae")


def charger_lexique(chemin):
    if not os.path.exists(chemin):
        print("Téléchargement de Lexique 3.83 (~25 Mo)…", file=sys.stderr)
        urllib.request.urlretrieve(URL_LEXIQUE, chemin)
    with open(chemin, encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE))


def classement(lignes, longueur):
    """Liste [(mot, fréquence, catégories)] triée du plus fréquent au moins fréquent."""
    # Formes qui sont des participes (passés ou présents) d'un verbe.
    participes = {
        r["ortho"] for r in lignes
        if r["cgram"] in ("VER", "AUX") and ("par:pas" in r["infover"] or "par:pre" in r["infover"])
    }
    freq = collections.defaultdict(float)
    cats = collections.defaultdict(set)
    nombres = collections.defaultdict(set)
    for r in lignes:
        mot = r["ortho"]
        if mot != r["lemme"] or len(mot) != longueur or not LETTRES.fullmatch(mot):
            continue
        f = (float(r["freqlemfilms2"]) + float(r["freqlemlivres"])) / 2
        freq[mot] = max(freq[mot], f)
        cats[mot].add(r["cgram"])
        nombres[mot].add(r["nombre"])

    resultat, vus = [], set()
    for mot in sorted(freq, key=lambda m: (-freq[m], m)):
        c = cats[mot]
        if not c & CATEGORIES_GARDEES:
            continue                      # mot grammatical (adverbe, pronom…)
        if c <= {"ADJ"} and mot in participes:
            continue                      # participe utilisé comme adjectif (cassé, puant…)
        if nombres[mot] == {"p"}:
            continue                      # toujours au pluriel (cieux, moeurs…)
        if mot in VULGAIRES or "ADJ:num" in c:
            continue
        cle = sans_accents(mot)
        if cle in vus:
            continue                      # tache/tâche : on garde le plus fréquent
        vus.add(cle)
        resultat.append((mot, freq[mot], c))
    return resultat


def charger_banque(chemin):
    if not os.path.exists(chemin):
        return None
    src = open(chemin, encoding="utf-8").read()
    data = json.loads(src[src.index("{"):src.rindex("}") + 1])
    return {int(L): {m.lower() for m in v["answers"]} for L, v in data.items()}


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--lexique", default=os.path.join(ICI, "Lexique383.tsv"),
                   help="fichier Lexique383.tsv (téléchargé s'il est absent)")
    p.add_argument("--words", default=os.path.join(ICI, "..", "words.js"), help="words.js du jeu")
    p.add_argument("--longueurs", type=int, nargs="+", default=[5, 6])
    p.add_argument("--rangs", type=int, nargs="+", default=[600, 1000, 1500, 2000, 3000])
    p.add_argument("--verifier", action="store_true",
                   help="compare le classement avec la banque actuelle de words.js")
    p.add_argument("--exporter", type=int, metavar="N",
                   help="écrit les N premiers mots dans mots_<longueur>.csv")
    args = p.parse_args()

    lignes = charger_lexique(args.lexique)
    banque = charger_banque(args.words) or {}

    for L in args.longueurs:
        liste = classement(lignes, L)
        actuels = banque.get(L, set())
        print(f"\n== {L} lettres : {len(liste)} mots au total")

        for n in args.rangs:
            if n > len(liste):
                print(f"{n:>5}  (au-delà de la liste)")
                continue
            mot, f, c = liste[n - 1]
            autour = " · ".join(m for m, _, _ in liste[max(0, n - 4):n + 3])
            deja = "  [déjà dans le jeu]" if mot in actuels else ""
            print(f"{n:>5}  {mot.upper():<8} freq={f:<7.2f} {'/'.join(sorted(c))}{deja}")
            print(f"       autour : {autour}")

        if args.verifier and actuels:
            noms = {m for m, _, _ in liste}
            top = {m for m, _, _ in liste[:len(actuels)]}
            print(f"  Banque actuelle : {len(actuels)} mots")
            print("  Dans le jeu mais exclus par le filtre :", sorted(actuels - noms) or "aucun")
            print("  Dans le top", len(actuels), "mais pas dans le jeu :", sorted(top - actuels) or "aucun")
            print("  Dans le jeu mais hors du top", len(actuels), ":", sorted((actuels & noms) - top) or "aucun")

        if args.exporter:
            sortie = os.path.join(ICI, f"mots_{L}.csv")
            with open(sortie, "w", encoding="utf-8", newline="") as f:
                w = csv.writer(f)
                w.writerow(["rang", "mot", "frequence", "categories", "deja_dans_le_jeu"])
                for i, (mot, fr, c) in enumerate(liste[:args.exporter], 1):
                    w.writerow([i, mot, round(fr, 2), "/".join(sorted(c)), "oui" if mot in actuels else ""])
            print(f"  → {sortie}")


if __name__ == "__main__":
    main()

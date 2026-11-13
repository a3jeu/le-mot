#!/usr/bin/env python3
"""Refait la banque de solutions (`answers`) de words.js.

Prend les N mots de 5 et de 6 lettres les plus fréquents (même filtre que
classement_mots.py), les mélange et réécrit words.js. La liste des mots
acceptés (`valid`) est conservée ; les solutions qui n'y seraient pas y sont
ajoutées.

Les mots des jours déjà passés et d'aujourd'hui restent à leur place, pour ne
pas changer le mot du jour d'une partie en cours ni l'historique. Ils ne
reviennent pas plus loin dans la liste.

Exemples :
  python3 generer_banque.py                 # 1100 mots par longueur
  python3 generer_banque.py --nombre 1300
  python3 generer_banque.py --graine 42     # mélange reproductible
  python3 generer_banque.py --essai         # affiche le résultat sans écrire
  python3 generer_banque.py --tout          # mélange tout, même les jours passés
"""
import argparse
import datetime
import json
import os
import random
import sys

from classement_mots import ICI, charger_lexique, classement

# Jour n°1 du jeu (doit correspondre à EPOCH dans index.html).
DEBUT = datetime.date(2026, 11, 6)
ENTETE = (
    "// Généré à partir de Lexique 3.83 (lexique.org) et an-array-of-french-words.\n"
    "// answers : mots du jour (ordre fixe), valid : mots acceptés (sans accents).\n"
)


def sans_accents_maj(mot):
    # Même normalisation que strip() dans index.html.
    import unicodedata
    d = unicodedata.normalize("NFD", mot)
    d = "".join(c for c in d if unicodedata.category(c) != "Mn")
    return d.replace("Œ", "OE").replace("Æ", "AE").replace("œ", "oe").replace("æ", "ae").upper()


def lire_words(chemin):
    src = open(chemin, encoding="utf-8").read()
    return json.loads(src[src.index("{"):src.rindex("}") + 1])


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--nombre", type=int, default=1100, help="nombre de solutions par longueur (défaut 1100)")
    p.add_argument("--lexique", default=os.path.join(ICI, "Lexique383.tsv"))
    p.add_argument("--words", default=os.path.join(ICI, "..", "words.js"))
    p.add_argument("--graine", type=int, help="graine du mélange (aléatoire si absente)")
    p.add_argument("--date", type=lambda t: datetime.datetime.strptime(t, "%Y-%m-%d").date(), default=datetime.date.today(),
                   help="aujourd'hui, AAAA-MM-JJ (les jours jusqu'à cette date sont gardés)")
    p.add_argument("--essai", action="store_true", help="n'écrit rien, affiche seulement le résumé")
    p.add_argument("--tout", action="store_true",
                   help="mélange aussi les mots des jours passés et d'aujourd'hui (le mot du jour change)")
    args = p.parse_args()

    data = lire_words(args.words)
    lignes = charger_lexique(args.lexique)
    rng = random.Random(args.graine)
    # Index du jour dans la liste (0 = 6 novembre 2026) ; on garde 0..aujourd'hui.
    garder = 0 if args.tout else max(0, (args.date - DEBUT).days + 1)

    for L in ("5", "6"):
        anciens = data[L]["answers"]
        fixes = anciens[:garder]
        deja = {sans_accents_maj(m) for m in fixes}

        top = [m.upper() for m, _, _ in classement(lignes, int(L))[:args.nombre]]
        if len(top) < args.nombre:
            sys.exit(f"Seulement {len(top)} mots de {L} lettres disponibles.")
        reste = [m for m in top if sans_accents_maj(m) not in deja]
        rng.shuffle(reste)
        nouveaux = fixes + reste

        valid = data[L]["valid"].split(" ")
        connus = set(valid)
        ajouts = sorted({sans_accents_maj(m) for m in nouveaux} - connus)
        if ajouts:
            data[L]["valid"] = " ".join(sorted(connus | set(ajouts)))
        data[L]["answers"] = nouveaux

        hors_top = [m for m in fixes if m not in top]
        print(f"{L} lettres : {len(anciens)} → {len(nouveaux)} solutions "
              f"({len(fixes)} jours déjà joués gardés en tête"
              + (f", dont hors du top : {', '.join(hors_top)}" if hors_top else "") + ")")
        print(f"  ajoutés : {len(set(nouveaux) - set(anciens))}, retirés : {len(set(anciens) - set(nouveaux))}")
        if ajouts:
            print(f"  ajoutés aux mots acceptés : {', '.join(ajouts)}")
        print(f"  aperçu : {' '.join(reste[:12])} …")

    if args.essai:
        print("\n(essai : words.js n'a pas été modifié)")
        return
    with open(args.words, "w", encoding="utf-8") as f:
        f.write(ENTETE)
        f.write("window.LEMOT_WORDS=" + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";\n")
    print(f"\nwords.js réécrit : {os.path.abspath(args.words)}")

    # Change le numéro de version dans index.html pour que les navigateurs
    # (et Cloudflare) ne gardent pas l'ancien words.js en cache.
    import re
    index = os.path.join(os.path.dirname(os.path.abspath(args.words)), "index.html")
    if os.path.exists(index):
        html = open(index, encoding="utf-8").read()
        m = re.search(r'words\.js\?v=(\d+)', html)
        if m:
            v = int(m.group(1)) + 1
            html = html[:m.start()] + "words.js?v=%d" % v + html[m.end():]
            open(index, "w", encoding="utf-8").write(html)
            print("index.html : words.js?v=%d (cache des navigateurs contourné)" % v)


if __name__ == "__main__":
    main()

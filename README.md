# Le mot

Jeu de mots quotidien en français : deux mots à deviner chaque jour, un de 5 lettres et un de 6 lettres.

**Jouer :** https://mot.tommygagne.com

## Règles

- Trouvez le mot du jour en **6 essais**.
- Chaque essai doit être un mot français existant.
- Les accents ne comptent pas : tapez simplement les lettres.

## Fonctionnalités

- Deux grilles par jour (5 et 6 lettres), le même mot pour tout le monde.
- Clavier QWERTY ou AZERTY (dans les paramètres).
- Statistiques et séries de victoires, gardées dans le navigateur (`localStorage`).
- Bouton de partage du résultat.

## Structure

| Fichier | Rôle |
| --- | --- |
| `index.html` | Le jeu complet (HTML, CSS et JavaScript, sans dépendance) |
| `words.js` | Listes de mots : `answers` (mots du jour, dans un ordre fixe) et `valid` (mots acceptés, sans accents) |

Le mot du jour est choisi d'après le nombre de jours écoulés depuis le 6 novembre 2026 (jour n°1).

## Lancer en local

Aucune compilation n'est nécessaire : ouvrez `index.html` dans un navigateur, ou servez le dossier avec n'importe quel serveur statique, par exemple :

```sh
python3 -m http.server
```

## Crédits

Dictionnaire : [Lexique 3.83](http://www.lexique.org) et [an-array-of-french-words](https://github.com/words/an-array-of-french-words).

# Mes outils

Un tableau de bord personnel pour Windows : une petite bulle 🧰 flotte sur
l'écran et ouvre, d'un clic, vos outils, vos mails, vos notes, votre agenda,
vos mots de passe et vos serveurs.

Tout tourne sur votre PC : un petit serveur local (`127.0.0.1:8760`, inaccessible
depuis l'extérieur) et une page affichée dans une fenêtre Edge sans barre
d'adresse. Aucun compte, aucun service en ligne.

## Ce qu'il fait

- **Tuiles** : dossiers, fichiers, programmes, pages web ou applis locales,
  ouverts en un clic. Ajout et modification depuis la page.
- **Mails** : votre Gmail (lecture, réponse, envoi), avec un mot de passe
  d'application rangé dans le coffre de Windows.
- **Notes** : cartes colorées ou listes à cocher, épinglées, avec rappel.
- **Agenda** : vues semaine et mois, glisser-déposer, rappels par la bulle.
- **Mots de passe** : coffre chiffré (AES-256-GCM, clé tirée du mot de passe
  maître par scrypt), presse-papiers effacé après 30 secondes.
- **SSH** : une clé par serveur, déposée en un clic, puis `ssh <nom-court>`.
- **Serveurs Odoo** (facultatif) : démarrer, arrêter, ouvrir, voir le journal.

## Installation

Il faut Windows 10 ou 11 et Python 3.10 ou plus récent (avec tkinter, inclus
dans l'installateur de python.org).

```bat
git clone https://github.com/rarianaAina/mes-outils.git
cd mes-outils
pip install -r requirements.txt
"Mes outils.bat"
```

Au premier lancement, `outils.json` est créé à partir de
`outils.exemple.json`. Vos données (`outils.json`, `donnees\`) restent sur
votre PC et sont exclues du dépôt.

Pour lancer la bulle avec Windows : touche Windows + R, taper `shell:startup`,
puis y placer un raccourci vers `Mes outils.bat`.

Pour utiliser un autre Python que celui du PATH, définir la variable
d'environnement `MES_OUTILS_PYTHON` (chemin complet de `pythonw.exe`).

## Mode d'emploi

Tout est détaillé dans [LISEZMOI.txt](LISEZMOI.txt).

## Licence

[MIT](LICENSE)

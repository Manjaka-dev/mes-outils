# -*- coding: utf-8 -*-
"""Appelé par ssh (SSH_ASKPASS) pour la première connexion à un serveur : rend
le mot de passe que « Mes outils » a placé dans l'environnement de ce seul
processus ssh. Rien n'est écrit ailleurs."""
import os
import sys

sys.stdout.write(os.environ.get("MESOUTILS_SSH_SECRET", "") + "\n")

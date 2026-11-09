# -*- coding: utf-8 -*-
"""Installation de « Mes outils » : vérifications et raccourcis Windows.

Utilisé par installer.bat (python outil\\installation.py --installer) et par
l'onglet Réglages (démarrage avec Windows, raccourci sur le Bureau).
"""
import ctypes
import importlib.util
import os
import subprocess
import sys

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(ICI)
NOM_RACCOURCI = "Mes outils.lnk"
ICONE = os.path.join(ICI, "mes_outils.ico")
BULLE = os.path.join(ICI, "bulle.py")
CREATE_NO_WINDOW = 0x08000000
# Dossiers spéciaux de Windows (SHGetFolderPathW)
CSIDL = {"bureau": 0x0010, "demarrage": 0x0007}
BIBLIOTHEQUES = {"cryptography": "cryptography", "PIL": "Pillow"}


def dossier_special(genre):
    """Le vrai dossier du Bureau ou du Démarrage (le Bureau peut être dans
    OneDrive)."""
    tampon = ctypes.create_unicode_buffer(260)
    if ctypes.windll.shell32.SHGetFolderPathW(None, CSIDL[genre], None, 0, tampon) != 0:
        raise RuntimeError(f"Dossier Windows introuvable : {genre}")
    return tampon.value


def chemin_raccourci(genre):
    return os.path.join(dossier_special(genre), NOM_RACCOURCI)


def python_fenetre():
    """pythonw.exe (sans fenêtre noire) : celui de MES_OUTILS_PYTHON, sinon
    celui qui fait tourner ce programme."""
    choisi = os.environ.get("MES_OUTILS_PYTHON")
    if choisi and os.path.isfile(choisi):
        return choisi
    dossier = os.path.dirname(sys.executable)
    pythonw = os.path.join(dossier, "pythonw.exe")
    return pythonw if os.path.isfile(pythonw) else sys.executable


def creer_raccourci(genre):
    """Raccourci « Mes outils » qui lance la bulle. Les chemins passent par
    l'environnement de PowerShell, jamais dans le texte de la commande."""
    cible = chemin_raccourci(genre)
    env = dict(os.environ, MO_LNK=cible, MO_CIBLE=python_fenetre(), MO_ARGS=f'"{BULLE}"',
               MO_DOSSIER=RACINE, MO_ICONE=ICONE)
    script = ("$r = (New-Object -ComObject WScript.Shell).CreateShortcut($env:MO_LNK); "
              "$r.TargetPath = $env:MO_CIBLE; $r.Arguments = $env:MO_ARGS; "
              "$r.WorkingDirectory = $env:MO_DOSSIER; $r.IconLocation = $env:MO_ICONE; "
              "$r.Description = 'Mes outils'; $r.Save()")
    r = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", script], env=env,
                       capture_output=True, text=True, timeout=30, creationflags=CREATE_NO_WINDOW)
    if r.returncode != 0 or not os.path.isfile(cible):
        raise RuntimeError("Raccourci impossible à créer : " + (r.stderr or "").strip()[:200])
    return cible


def supprimer_raccourci(genre):
    cible = chemin_raccourci(genre)
    if os.path.isfile(cible):
        os.remove(cible)


def etat():
    resultat = {}
    for genre in CSIDL:
        try:
            resultat[genre] = os.path.isfile(chemin_raccourci(genre))
        except RuntimeError:
            resultat[genre] = False
    return resultat


def verifier():
    """Ce qui manque pour faire tourner « Mes outils » (liste vide = tout va bien)."""
    manque = []
    if sys.version_info < (3, 10):
        manque.append(f"Python 3.10 ou plus récent (ici {sys.version.split()[0]})")
    if importlib.util.find_spec("tkinter") is None:
        manque.append("tkinter (cocher « tcl/tk » dans l'installateur de python.org)")
    for module, paquet in BIBLIOTHEQUES.items():
        if importlib.util.find_spec(module) is None:
            manque.append(f"la bibliothèque {paquet} (pip install -r requirements.txt)")
    return manque


def installer():
    print("Mes outils : vérification…")
    manque = verifier()
    if manque:
        print("Il manque :")
        for m in manque:
            print("  -", m)
        return 1
    for genre, nom in (("bureau", "Bureau"), ("demarrage", "Démarrage de Windows")):
        try:
            creer_raccourci(genre)
            print(f"  Raccourci créé : {nom}")
        except RuntimeError as e:
            print(f"  {nom} : {e}")
    print("Installation terminée. La bulle 🧰 va apparaître.")
    return 0


def lancer():
    """Démarre la bulle, détachée de la fenêtre d'installation."""
    subprocess.Popen([python_fenetre(), BULLE], cwd=RACINE, close_fds=True,
                     creationflags=0x00000008 | 0x00000200)  # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP


if __name__ == "__main__":
    if "--lancer" in sys.argv:
        lancer()
        sys.exit(0)
    if "--verifier" in sys.argv:
        problemes = verifier()
        print("\n".join(problemes) if problemes else "ok")
        sys.exit(1 if problemes else 0)
    if "--installer" in sys.argv:
        sys.exit(installer())
    print("Usage : python outil\\installation.py --installer | --verifier")

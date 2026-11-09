# -*- coding: utf-8 -*-
"""Onglet Réglages : prénom, langue, onglets affichés, dossiers de projets,
raccourcis Windows, mise à jour. Routes POST /api/reglages/<action>.

Aussi : la fenêtre « Choisir un dossier » de Windows, utilisée par tous les
onglets (POST /api/reglages/choisir_dossier).
"""
import os
import subprocess

import config
import installation

CREATE_NO_WINDOW = 0x08000000


def _git(*args, delai=60):
    return subprocess.run(["git", "-C", config.RACINE, *args], capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=delai, creationflags=CREATE_NO_WINDOW)


def lire(_d=None):
    contenu = config.lire()
    return {
        "prenom": contenu.get("prenom") or "",
        "langue": config.langue(),
        "theme": config.theme(),
        "onglets_masques": contenu.get("onglets_masques") or [],
        "dossiers_projets": config.dossiers_projets(),
        "version": config.VERSION,
        "depot": config.DEPOT,
        "raccourcis": installation.etat(),
        "maj_possible": os.path.isdir(os.path.join(config.RACINE, ".git")),
    }


def enregistrer(d):
    valeurs = {}
    if "prenom" in d:
        valeurs["prenom"] = str(d["prenom"] or "").strip()[:40]
    if "langue" in d:
        if d["langue"] not in config.LANGUES:
            raise ValueError("Langue inconnue.")
        valeurs["langue"] = d["langue"]
    if "theme" in d:
        if d["theme"] not in config.THEMES:
            raise ValueError("Thème inconnu.")
        valeurs["theme"] = d["theme"]
    if "onglets_masques" in d:
        masques = d["onglets_masques"] or []
        if not isinstance(masques, list) or not all(isinstance(n, str) and n.isidentifier() for n in masques):
            raise ValueError("Liste d'onglets invalide.")
        valeurs["onglets_masques"] = [n for n in masques if n not in ("accueil", "reglages")]
    config.modifier(**valeurs)
    return lire()


def dossiers(d):
    config.enregistrer_dossiers_projets(d.get("dossiers"))
    return lire()


def raccourci(d):
    genre = d.get("genre")
    if genre not in installation.CSIDL:
        raise ValueError("Raccourci inconnu.")
    if d.get("actif"):
        installation.creer_raccourci(genre)
    else:
        installation.supprimer_raccourci(genre)
    return lire()


def mise_a_jour(_d=None):
    """git pull --ff-only : seulement si « Mes outils » a été installé avec
    git clone, et jamais par-dessus des modifications locales."""
    if not os.path.isdir(os.path.join(config.RACINE, ".git")):
        raise ValueError("Mise à jour automatique impossible : « Mes outils » n'a pas été installé avec git clone.")
    if _git("status", "--porcelain", "--untracked-files=no").stdout.strip():
        raise ValueError("Des fichiers de « Mes outils » ont été modifiés sur ce PC : mise à jour annulée.")
    avant = _git("rev-parse", "HEAD").stdout.strip()
    r = _git("pull", "--ff-only", delai=120)
    if r.returncode != 0:
        raise RuntimeError("La mise à jour a échoué : " + (r.stderr or r.stdout).strip()[:300])
    apres = _git("rev-parse", "HEAD").stdout.strip()
    return {"change": avant != apres, "message": (r.stdout or "").strip()[:500]}


SCRIPT_DOSSIER = r"""
Add-Type -AssemblyName System.Windows.Forms
$p = New-Object System.Windows.Forms.Form
$p.TopMost = $true
$d = New-Object System.Windows.Forms.FolderBrowserDialog
$d.Description = $env:MO_TITRE
$d.ShowNewFolderButton = $true
if ($env:MO_DEPART -and (Test-Path -LiteralPath $env:MO_DEPART)) { $d.SelectedPath = $env:MO_DEPART }
if ($d.ShowDialog($p) -eq [System.Windows.Forms.DialogResult]::OK) {
  [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
  Write-Output $d.SelectedPath
}
"""


def choisir_dossier(d):
    """Ouvre la fenêtre « Choisir un dossier » de Windows, au premier plan.
    Renvoie {"chemin": "..."} ou {"chemin": None} si annulé."""
    env = dict(os.environ, MO_TITRE=str(d.get("titre") or "Choisir un dossier")[:120],
               MO_DEPART=str(d.get("depart") or ""))
    r = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-STA", "-Command", SCRIPT_DOSSIER],
                       env=env, capture_output=True, text=True, encoding="utf-8", errors="replace",
                       timeout=600, creationflags=CREATE_NO_WINDOW)
    chemin = (r.stdout or "").strip().splitlines()
    return {"chemin": chemin[-1] if chemin and os.path.isdir(chemin[-1]) else None}


ROUTES = {
    "lire": lire,
    "enregistrer": enregistrer,
    "dossiers": dossiers,
    "raccourci": raccourci,
    "mise_a_jour": mise_a_jour,
    "choisir_dossier": choisir_dossier,
}

# -*- mode: python ; coding: utf-8 -*-
"""Construction de « Mes outils.exe » avec PyInstaller (Python et toutes les
bibliothèques inclus : rien d'autre à installer sur le PC).

    pyinstaller packaging/mes_outils.spec --noconfirm

Résultat : dist/Mes outils/ (le programme et son dossier _internal), que
l'installateur (packaging/installateur.iss) emballe dans Mes-outils-Setup.exe.
"""
import json
import os
import re

RACINE = os.path.abspath(os.path.join(SPECPATH, ".."))
OUTIL = os.path.join(RACINE, "outil")
TRAVAIL = os.path.join(RACINE, "build")
os.makedirs(TRAVAIL, exist_ok=True)

# Les modules de « Mes outils » : chargés par leur nom (routes /api/<nom>/…),
# PyInstaller ne peut pas les deviner. La liste sert aussi de liste blanche
# au serveur (hub.modules_connus).
MODULES = sorted(n[:-3] for n in os.listdir(OUTIL) if n.endswith(".py") and n not in ("hub.py", "bulle.py"))
LISTE = os.path.join(TRAVAIL, "modules.json")
with open(LISTE, "w", encoding="utf-8") as f:
    json.dump(MODULES, f)

# Version affichée dans les propriétés du programme (clic droit > Propriétés).
with open(os.path.join(OUTIL, "config.py"), encoding="utf-8") as f:
    VERSION = re.search(r'^VERSION = "([\d.]+)"', f.read(), re.M).group(1)
NUMEROS = tuple(int(x) for x in VERSION.split(".")) + (0,) * (4 - len(VERSION.split(".")))
FICHIER_VERSION = os.path.join(TRAVAIL, "version.txt")
with open(FICHIER_VERSION, "w", encoding="utf-8") as f:
    f.write(f"""VSVersionInfo(
  ffi=FixedFileInfo(filevers={NUMEROS}, prodvers={NUMEROS}),
  kids=[StringFileInfo([StringTable('040C04B0', [
    StringStruct('CompanyName', 'Mes outils'),
    StringStruct('FileDescription', 'Mes outils - tableau de bord'),
    StringStruct('FileVersion', '{VERSION}'),
    StringStruct('InternalName', 'Mes outils'),
    StringStruct('LegalCopyright', 'Licence MIT'),
    StringStruct('OriginalFilename', 'Mes outils.exe'),
    StringStruct('ProductName', 'Mes outils'),
    StringStruct('ProductVersion', '{VERSION}')])]),
    VarFileInfo([VarStruct('Translation', [1036, 1200])])])
""")

ICONE = os.path.join(OUTIL, "mes_outils.ico")

a = Analysis(
    [os.path.join(OUTIL, "bulle.py")],
    pathex=[OUTIL],
    datas=[
        (os.path.join(OUTIL, "hub.html"), "."),
        (os.path.join(OUTIL, "web"), "web"),
        (ICONE, "."),
        (os.path.join(RACINE, "outils.exemple.json"), "."),
        (LISTE, "."),
    ],
    hiddenimports=MODULES,
    # Rien de tout cela n'est utilisé : un programme plus léger.
    excludes=["unittest", "pydoc", "test", "lib2to3", "numpy", "IPython", "matplotlib"],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Mes outils",
    icon=ICONE,
    version=FICHIER_VERSION,
    console=False,      # pas de fenêtre noire
    upx=False,          # UPX déclenche souvent les antivirus
)
coll = COLLECT(exe, a.binaries, a.datas, name="Mes outils", upx=False)

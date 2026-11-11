# -*- coding: utf-8 -*-
"""Onglet « Ports » : quels programmes écoutent sur quels ports, et arrêt
d'un programme qui occupe un port.

Sans dépendance externe :
- netstat -ano : les ports en écoute (TCP LISTENING, UDP en option) et le PID ;
- tasklist /fo csv /nh : le nom du programme et sa mémoire ;
- PowerShell Get-CimInstance Win32_Process : la ligne de commande (en
  parallèle de tasklist, gardée en mémoire tant que le PID garde le même nom).

L'arrêt (taskkill) refuse les processus système, « Mes outils » lui-même et
un PID qui ne correspond plus au programme affiché dans la page.

Fonction utile aux autres modules : qui_ecoute(port) → dict ou None.
"""
import csv
import ctypes
import io
import json
import os
import re
import signal
import subprocess
import threading
import time
import webbrowser
from concurrent.futures import ThreadPoolExecutor
from ctypes import wintypes

import config

SANS_FENETRE = 0x08000000
DUREE_CACHE = 2.0  # secondes

# Ports de développement courants : surlignés dans la page.
PORTS_DEV = {
    80: "HTTP", 443: "HTTPS", 1433: "SQL Server", 3000: "Node / React", 3001: "Node", 3306: "MySQL",
    4200: "Angular", 5000: "Flask", 5173: "Vite", 5174: "Vite", 5432: "PostgreSQL", 5672: "RabbitMQ",
    6379: "Redis", 8000: "Django / Python", 8069: "Odoo", 8072: "Odoo (longpolling)", 8080: "HTTP",
    8081: "HTTP", 8443: "HTTPS", 8888: "Jupyter", 9000: "PHP / Portainer", 9200: "Elasticsearch",
    11434: "Ollama", 27017: "MongoDB",
}
# Ports qui ne servent pas de pages web (bases de données, files…).
PORTS_NON_WEB = {135, 139, 445, 1433, 1521, 3306, 3389, 5432, 5672, 6379, 9200, 11211, 27017}
PORTS_WEB = {80, 443, 3000, 3001, 4200, 5000, 5173, 5174, 8000, 8069, 8080, 8081, 8443, 8888, 9000}
PROGRAMMES_WEB = {"node", "python", "pythonw", "php", "java", "ruby", "nginx", "httpd", "deno", "bun",
                  "dotnet", "go", "uvicorn", "gunicorn", "caddy", "code", "ollama"}

# Processus que l'on n'arrête jamais (Windows en a besoin pour tenir debout).
PROTEGES = {
    "system", "system idle process", "idle", "registry", "memory compression", "secure system",
    "smss", "csrss", "wininit", "winlogon", "services", "lsass", "lsaiso", "svchost", "explorer",
    "dwm", "msmpeng", "nissrv", "securityhealthservice", "sgrmbroker", "fontdrvhost", "spoolsv",
    "sihost", "taskhostw", "searchindexer", "wudfhost", "audiodg", "ctfmon", "conhost",
}
PID_PROTEGES = {0, 4}

_verrou = threading.Lock()
_cache = {"udp": None, "instant": 0.0, "resultat": None}
_commandes = {}  # pid → (nom, ligne de commande)


def _executer(commande, delai=15):
    """Lance un programme sans fenêtre et rend sa sortie (texte)."""
    r = subprocess.run(commande, capture_output=True, timeout=delai, creationflags=SANS_FENETRE)
    sortie = r.stdout or b""
    if isinstance(sortie, str):
        return sortie
    return sortie.decode("oem", errors="replace")


def nom_court(nom):
    """« Python.EXE » → « python » (pour comparer et protéger)."""
    nom = (nom or "").strip().lower()
    return nom[:-4] if nom.endswith(".exe") else nom


# ---------------------------------------------------------------------------
# Lecture des sorties de netstat et tasklist
# ---------------------------------------------------------------------------
def separer_adresse(texte):
    """« 0.0.0.0:3000 » → ("0.0.0.0", 3000) ; « [::1]:5432 » → ("::1", 5432)."""
    texte = texte.strip()
    if ":" not in texte:
        return None, None
    hote, _, port = texte.rpartition(":")
    hote = hote.strip("[]")
    if "%" in hote:  # fe80::1%12 : l'indice d'interface n'intéresse personne
        hote = hote.split("%", 1)[0]
    try:
        return hote, int(port)
    except ValueError:
        return hote, None


def lire_netstat(sortie, udp=False):
    """Les ports en écoute d'une sortie « netstat -ano ».
    TCP : état LISTENING (ou adresse distante 0.0.0.0:0 / [::]:0, quelle que
    soit la langue de Windows). UDP : seulement si udp=True."""
    vus, resultat = set(), []
    for ligne in sortie.splitlines():
        morceaux = ligne.split()
        if len(morceaux) < 4:
            continue
        proto = morceaux[0].upper()
        if proto == "TCP" and len(morceaux) >= 5:
            distante, etat, pid = morceaux[2], morceaux[3], morceaux[4]
            if etat.upper() != "LISTENING" and distante not in ("0.0.0.0:0", "[::]:0"):
                continue
        elif proto == "UDP" and udp:
            pid = morceaux[-1]
        else:
            continue
        hote, port = separer_adresse(morceaux[1])
        if port is None or not pid.isdigit():
            continue
        cle = (proto, hote, port, int(pid))
        if cle in vus:
            continue
        vus.add(cle)
        resultat.append({"proto": proto, "adresse": hote, "port": port, "pid": int(pid)})
    return resultat


def lire_tasklist(sortie):
    """{pid: {"nom", "memoire_ko"}} depuis « tasklist /fo csv /nh »."""
    processus = {}
    for ligne in csv.reader(io.StringIO(sortie)):
        if len(ligne) < 5 or not ligne[1].strip().isdigit():
            continue
        chiffres = re.sub(r"\D", "", ligne[4])
        processus[int(ligne[1])] = {"nom": ligne[0].strip(), "memoire_ko": int(chiffres) if chiffres else None}
    return processus


def lire_commandes(sortie):
    """{pid: ligne de commande} depuis le JSON de Get-CimInstance."""
    try:
        donnees = json.loads(sortie or "null")
    except ValueError:
        return {}
    if isinstance(donnees, dict):
        donnees = [donnees]
    resultat = {}
    for p in donnees or []:
        if isinstance(p, dict) and isinstance(p.get("ProcessId"), int):
            resultat[p["ProcessId"]] = p.get("CommandLine") or ""
    return resultat


# ---------------------------------------------------------------------------
# Programmes externes
# ---------------------------------------------------------------------------
def processus():
    return lire_tasklist(_executer(["tasklist", "/fo", "csv", "/nh"]))


def processus_pid(pid):
    """Le processus « pid » tel qu'il est maintenant, ou None."""
    sortie = _executer(["tasklist", "/fo", "csv", "/nh", "/fi", f"PID eq {int(pid)}"], delai=10)
    return lire_tasklist(sortie).get(int(pid))


def commandes(pids):
    """Les lignes de commande des PID demandés (un seul appel à PowerShell)."""
    pids = sorted({int(p) for p in pids if int(p) not in PID_PROTEGES})
    if not pids:
        return {}
    filtre = " OR ".join(f"ProcessId={p}" for p in pids)
    script = ("[Console]::OutputEncoding=[Text.Encoding]::UTF8; "
              f"Get-CimInstance Win32_Process -Filter '{filtre}' | "
              "Select-Object ProcessId,CommandLine | ConvertTo-Json -Compress")
    try:
        r = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
                           capture_output=True, timeout=10, creationflags=SANS_FENETRE)
    except (OSError, subprocess.SubprocessError):
        return {}
    return lire_commandes((r.stdout or b"").decode("utf-8", errors="replace"))


# ---------------------------------------------------------------------------
# Liste
# ---------------------------------------------------------------------------
def est_web(port, nom):
    if port in PORTS_NON_WEB:
        return False
    return port in PORTS_WEB or (port >= 1024 and nom_court(nom) in PROGRAMMES_WEB)


def nos_pids():
    """Les PID de « Mes outils » : ce serveur et le programme qui l'a lancé."""
    return {os.getpid(), os.getppid()}


def lire_lsof(sortie, proto):
    resultat = {}
    pid, nom = None, ""
    for ligne in sortie.splitlines():
        champ, valeur = ligne[:1], ligne[1:]
        if champ == "p":
            pid, nom = (int(valeur) if valeur.isdecimal() else None), ""
        elif champ == "c":
            nom = valeur
        elif champ == "n" and pid is not None:
            adresse, port = separer_adresse(valeur.split("->", 1)[0])
            if port:
                resultat[(pid, adresse, port)] = {"pid": pid, "nom": nom, "proto": proto,
                                                 "adresse": adresse, "port": port}
    return list(resultat.values())


def _identite_mac(pid):
    from projets import chemin_processus_mac, processus_mac

    info = processus_mac(pid)
    if info is None:
        return None, True
    chemin = chemin_processus_mac(pid)
    systeme = ("/System/", "/usr/libexec/", "/usr/sbin/", "/Library/Apple/System/")
    protege = (info.identifiants[0] != os.getuid() or not chemin or chemin.startswith(systeme)
               or pid <= 4 or pid in ancetres_mac())
    return f"{info.secondes}:{info.microsecondes}", protege


def ancetres_mac():
    from projets import processus_mac

    courant, chaine = os.getpid(), set()
    while courant > 1 and courant not in chaine:
        chaine.add(courant)
        info = processus_mac(courant)
        if info is None:
            break
        courant = info.ppid
    return chaine


def _lister_mac(udp):
    lignes, identites = [], {}
    for proto in ("TCP", "UDP") if udp else ("TCP",):
        commande = ["/usr/sbin/lsof", "-nP", f"-i{proto}", "-Fpcfn"]
        if proto == "TCP":
            commande.append("-sTCP:LISTEN")
        try:
            r = subprocess.run(commande, capture_output=True, text=True, encoding="utf-8",
                               errors="replace", timeout=15)
        except (OSError, subprocess.SubprocessError):
            raise ValueError("Impossible de lire les ports en écoute.") from None
        if r.returncode not in (0, 1):
            raise ValueError("Impossible de lire les ports en écoute.")
        lignes.extend(lire_lsof(r.stdout, proto))
    for e in lignes:
        pid, port = e["pid"], e["port"]
        if pid not in identites:
            identites[pid] = _identite_mac(pid)
        cree, protege = identites[pid]
        e.update(cree=cree, protege=protege, soi=pid in nos_pids(), commande="", memoire_ko=None,
                 dev=PORTS_DEV.get(port, ""), web=e["proto"] == "TCP" and est_web(port, e["nom"]))
    return sorted(lignes, key=lambda e: (e["port"], e["proto"], e["adresse"]))


def lister_ports(udp=False, forcer=False):
    """Les ports en écoute, avec le programme qui les occupe (cache court)."""
    with _verrou:
        if (not forcer and _cache["resultat"] is not None and _cache["udp"] == udp
                and time.monotonic() - _cache["instant"] < DUREE_CACHE):
            return _cache["resultat"]
    if config.MACOS:
        resultat = _lister_mac(udp)
        with _verrou:
            _cache.update(udp=udp, instant=time.monotonic(), resultat=resultat)
        return resultat
    ecoutes = lire_netstat(_executer(["netstat", "-ano"]), udp=udp)
    pids = {e["pid"] for e in ecoutes}
    manquants = {p for p in pids if p not in _commandes}
    with ThreadPoolExecutor(max_workers=2) as pool:
        f_proc = pool.submit(processus)
        f_cmd = pool.submit(commandes, manquants) if manquants else None
        procs = f_proc.result()
        nouvelles = f_cmd.result() if f_cmd else {}
    nous = nos_pids()
    with _verrou:
        for pid, cmd in nouvelles.items():
            if pid in procs:
                _commandes[pid] = (procs[pid]["nom"], cmd)
        resultat = []
        for e in ecoutes:
            p = procs.get(e["pid"]) or {}
            nom = p.get("nom") or ("System" if e["pid"] == 4 else "?")
            memo = _commandes.get(e["pid"])
            commande = memo[1] if memo and memo[0] == nom else ""
            resultat.append({
                **e, "nom": nom, "memoire_ko": p.get("memoire_ko"), "commande": commande,
                "dev": PORTS_DEV.get(e["port"], ""), "web": e["proto"] == "TCP" and est_web(e["port"], nom),
                "protege": e["pid"] in PID_PROTEGES or nom_court(nom) in PROTEGES,
                "soi": e["pid"] in nous,
            })
        resultat.sort(key=lambda x: (x["port"], x["proto"], x["adresse"]))
        # Les PID disparus sont oubliés.
        for pid in [p for p in _commandes if p not in procs]:
            del _commandes[pid]
        _cache.update(udp=udp, instant=time.monotonic(), resultat=resultat)
        return resultat


def oublier_cache():
    with _verrou:
        _cache["resultat"] = None


def qui_ecoute(port):
    """Le programme qui écoute sur ce port TCP (dict), ou None.
    Ex. qui_ecoute(3000) → {"port": 3000, "pid": 1234, "nom": "node.exe", …}."""
    try:
        port = int(port)
    except (TypeError, ValueError):
        return None
    trouves = [e for e in lister_ports(udp=False) if e["port"] == port and e["proto"] == "TCP"]
    return dict(trouves[0]) if trouves else None


# ---------------------------------------------------------------------------
# Parenté des processus (pour ne pas arrêter l'arbre qui contient Mes outils)
# ---------------------------------------------------------------------------
class _Entree(ctypes.Structure):
    _fields_ = [("dwSize", wintypes.DWORD), ("cntUsage", wintypes.DWORD), ("th32ProcessID", wintypes.DWORD),
                ("th32DefaultHeapID", ctypes.c_size_t), ("th32ModuleID", wintypes.DWORD),
                ("cntThreads", wintypes.DWORD), ("th32ParentProcessID", wintypes.DWORD),
                ("pcPriClassBase", ctypes.c_long), ("dwFlags", wintypes.DWORD),
                ("szExeFile", ctypes.c_wchar * 260)]


def parents():
    """{pid: pid du parent} pour tous les processus (photo de Windows)."""
    k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    k32.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
    k32.Process32FirstW.argtypes = k32.Process32NextW.argtypes = [wintypes.HANDLE, ctypes.POINTER(_Entree)]
    k32.CloseHandle.argtypes = [wintypes.HANDLE]
    photo = k32.CreateToolhelp32Snapshot(0x2, 0)
    if not photo or photo == wintypes.HANDLE(-1).value:
        return {}
    resultat = {}
    try:
        entree = _Entree()
        entree.dwSize = ctypes.sizeof(_Entree)
        ok = k32.Process32FirstW(photo, ctypes.byref(entree))
        while ok:
            resultat[entree.th32ProcessID] = entree.th32ParentProcessID
            ok = k32.Process32NextW(photo, ctypes.byref(entree))
    finally:
        k32.CloseHandle(photo)
    return resultat


def ancetres(pid):
    """Les PID de « pid », de son parent, de son grand-parent…"""
    liens = parents()
    chaine, courant = [], pid
    while courant and courant not in chaine and len(chaine) < 64:
        chaine.append(courant)
        courant = liens.get(courant)
    return set(chaine)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
def _pid(d):
    try:
        pid = int(d.get("pid"))
    except (TypeError, ValueError):
        raise ValueError("Numéro de processus invalide.") from None
    if pid < 0:
        raise ValueError("Numéro de processus invalide.")
    return pid


def _port(d):
    try:
        port = int(d.get("port"))
    except (TypeError, ValueError):
        raise ValueError("Numéro de port invalide.") from None
    if not 1 <= port <= 65535:
        raise ValueError("Numéro de port invalide.")
    return port


def liste(d):
    udp = bool(d.get("udp"))
    return {"ports": lister_ports(udp=udp, forcer=bool(d.get("forcer"))), "udp": udp}


def chercher(d):
    """Qui occupe ce port ? (TCP)"""
    return {"port": _port(d), "resultat": qui_ecoute(_port(d))}


def verifier_arret(pid, nom_attendu, arbre=False):
    """Lève ValueError si le processus ne doit pas être arrêté. Rend son nom."""
    if pid in PID_PROTEGES:
        raise ValueError("Processus système : arrêt refusé.")
    nous = nos_pids()
    if pid in nous:
        raise ValueError("C'est « Mes outils » lui-même : arrêt refusé.")
    actuel = processus_pid(pid)
    if not actuel:
        raise ValueError("Ce processus n'existe plus.")
    if nom_court(actuel["nom"]) in PROTEGES:
        raise ValueError("Processus système : arrêt refusé.")
    if not nom_attendu or nom_court(actuel["nom"]) != nom_court(nom_attendu):
        raise ValueError("Ce numéro de processus correspond maintenant à un autre programme : actualisez la liste.")
    if arbre and pid in ancetres(os.getpid()):
        raise ValueError("Cet arbre de processus contient « Mes outils » : arrêt refusé.")
    return actuel["nom"]


def arreter(d):
    pid = _pid(d)
    arbre = bool(d.get("arbre"))
    if config.MACOS:
        port = _port(d)
        proto = d.get("proto")
        cree = d.get("cree")
        if arbre or proto not in ("TCP", "UDP") or not isinstance(cree, str):
            raise ValueError("Actualisez la liste des ports avant l’arrêt.")
        ligne = next((e for e in lister_ports(udp=proto == "UDP", forcer=True)
                      if (e["pid"], e["port"], e["proto"], e["cree"]) == (pid, port, proto, cree)), None)
        actuel, protege = _identite_mac(pid)
        if ligne is None or actuel != cree:
            raise ValueError("Le processus ou le port a changé : actualisez la liste.")
        if protege or ligne["protege"]:
            raise ValueError("Processus système : arrêt refusé.")
        try:
            os.kill(pid, signal.SIGTERM)
        except OSError:
            raise ValueError("Impossible d’arrêter ce processus.") from None
        oublier_cache()
        fin = time.monotonic() + 3
        while time.monotonic() < fin:
            if _identite_mac(pid)[0] != cree:
                return {"ok": True, "pid": pid, "nom": ligne["nom"]}
            time.sleep(0.1)
        raise ValueError("Le processus n’a pas répondu au signal d’arrêt.")
    nom = verifier_arret(pid, str(d.get("nom") or ""), arbre)
    commande = ["taskkill", "/PID", str(pid), "/F"] + (["/T"] if arbre else [])
    r = subprocess.run(commande, capture_output=True, timeout=20, creationflags=SANS_FENETRE)
    if r.returncode != 0:
        detail = (r.stderr or r.stdout or b"").decode("oem", errors="replace").strip().splitlines()
        raise ValueError("Arrêt impossible : " + (detail[0] if detail else f"code {r.returncode}"))
    oublier_cache()
    return {"ok": True, "pid": pid, "nom": nom}


def ouvrir(d):
    port = _port(d)
    webbrowser.open(f"http://localhost:{port}/")
    return {"ok": True}


ROUTES = {"liste": liste, "chercher": chercher, "arreter": arreter, "ouvrir": ouvrir}

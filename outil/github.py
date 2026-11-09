# -*- coding: utf-8 -*-
"""Onglet « GitHub » : vos dépôts, leur clonage et la création d'un dépôt.

- Connexion par le « Device Flow » de GitHub : l'outil affiche un code de
  8 caractères, que l'on valide sur github.com/login/device. Aucun mot de
  passe ne passe par l'outil. Le jeton obtenu est rangé dans le coffre de
  Windows (cible « MesOutils:github »), jamais dans un fichier.
- Pour git (clone, push), le jeton passe par des variables d'environnement
  du seul processus git (GIT_CONFIG_*) : il n'apparaît ni sur la ligne de
  commande, ni dans .git/config.
- Les dépôts déjà présents sur ce PC sont retrouvés dans les « dossiers de
  projets » choisis (outils.json, clé github > dossiers), d'après l'adresse
  de leur remote « origin ».
"""
import base64
import json
import os
import re
import shutil
import subprocess
import tempfile
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser

import coffre_windows

# Identifiant public de l'application GitHub « Mes outils » (OAuth App avec
# « Device Flow » activé). Ce n'est pas un secret. outils.json peut en donner
# un autre (clé github > client_id).
CLIENT_ID = "Ov23lixJbnztIOGA4hj6"
PORTEE = "repo"  # dépôts publics et privés : lire, créer, envoyer
CIBLE_COFFRE = "MesOutils:github"
API = "https://api.github.com"
URL_CODE = "https://github.com/login/device/code"
URL_JETON = "https://github.com/login/oauth/access_token"
TAILLE_MAX = 100 * 1024 * 1024  # GitHub refuse les fichiers de plus de 100 Mo
TAILLE_LOURDE = 50 * 1024 * 1024
CREATE_NO_WINDOW = 0x08000000
DETACHED = 0x00000008 | 0x00000200

NOM_VALIDE = re.compile(r"^[A-Za-z0-9._-]{1,100}$")
COMPLET_VALIDE = re.compile(r"^[A-Za-z0-9-]{1,39}/[A-Za-z0-9._-]{1,100}$")
MOTIF_GITHUB = re.compile(r"github\.com[:/]+([^/\s:]+)/([^/\s]+?)(?:\.git)?/?$", re.I)
SENSIBLES = re.compile(
    r"(^|/)(\.env(\.[^/]+)?|[^/]+\.(pem|key|pfx|p12|jks|keystore|kdbx|ppk)|id_(rsa|dsa|ecdsa|ed25519)"
    r"|credentials?(\.[^/]+)?|secrets?(\.[^/]+)?|key\.txt|\.npmrc|\.pypirc|\.netrc)$", re.I)
EXEMPLES = re.compile(r"\.(example|sample|template|dist)$", re.I)


class ErreurGitHub(Exception):
    pass


_verrou = threading.Lock()
_attente = {"code": None, "client_id": None, "intervalle": 5, "prochain": 0.0, "expire": 0.0}
_cache = {"profil": None}


# ---------------------------------------------------------------------------
# HTTP
# ---------------------------------------------------------------------------
def _requete(methode, url, jeton=None, donnees=None, formulaire=None, delai=20):
    """(statut, contenu JSON) ; une erreur HTTP est renvoyée, pas levée."""
    entetes = {"Accept": "application/vnd.github+json", "User-Agent": "mes-outils",
               "X-GitHub-Api-Version": "2022-11-28"}
    corps = None
    if formulaire is not None:
        corps = urllib.parse.urlencode(formulaire).encode()
        entetes.update({"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"})
    elif donnees is not None:
        corps = json.dumps(donnees).encode()
        entetes["Content-Type"] = "application/json"
    if jeton:
        entetes["Authorization"] = f"Bearer {jeton}"
    req = urllib.request.Request(url, data=corps, headers=entetes, method=methode)
    try:
        with urllib.request.urlopen(req, timeout=delai) as r:
            brut = r.read()
            return r.status, (json.loads(brut) if brut else None)
    except urllib.error.HTTPError as e:
        try:
            contenu = json.loads(e.read() or b"null")
        except ValueError:
            contenu = None
        return e.code, contenu
    except (urllib.error.URLError, TimeoutError, OSError):
        raise ErreurGitHub("GitHub ne répond pas : vérifiez la connexion internet.") from None


def jeton():
    return coffre_windows.lire(CIBLE_COFFRE)


def _appel(methode, chemin, donnees=None):
    """Appel à l'API avec le jeton du coffre ; lève ErreurGitHub en cas d'échec."""
    j = jeton()
    if not j:
        raise ErreurGitHub("GitHub n'est pas connecté.")
    statut, r = _requete(methode, API + chemin, jeton=j, donnees=donnees)
    if statut == 401:
        deconnecter()
        raise ErreurGitHub("L'accès à GitHub a été retiré : reconnectez GitHub.")
    if statut >= 400:
        message = (r or {}).get("message") if isinstance(r, dict) else None
        raise ErreurGitHub(f"GitHub a refusé la demande ({statut}){' : ' + message if message else ''}.")
    return r


def _profil_de(r):
    return {"login": r["login"], "nom": r.get("name") or r["login"], "avatar": r.get("avatar_url", ""),
            "id": r["id"]}


# ---------------------------------------------------------------------------
# Connexion (Device Flow)
# ---------------------------------------------------------------------------
def etat():
    if not jeton():
        _cache["profil"] = None
        return {"connecte": False}
    if not _cache["profil"]:
        _cache["profil"] = _profil_de(_appel("GET", "/user"))
    return {"connecte": True, **_cache["profil"]}


def _message_oauth(r):
    erreur = (r or {}).get("error") if isinstance(r, dict) else None
    if erreur == "device_flow_disabled":
        return ("Le « Device Flow » n'est pas activé dans l'application GitHub "
                "(github.com > Settings > Developer settings > OAuth Apps > Enable Device Flow).")
    if erreur in ("incorrect_client_credentials", "unauthorized_client", "Not Found"):
        return "L'identifiant de l'application GitHub (client_id) est invalide."
    return (r or {}).get("error_description") if isinstance(r, dict) and r.get("error_description") \
        else "Réponse inattendue de GitHub."


def connexion_debut(client_id):
    """Demande un code à GitHub et ouvre la page où le saisir."""
    if not client_id:
        raise ErreurGitHub("La connexion à GitHub n'est pas encore configurée : il manque "
                           "l'identifiant de l'application (client_id).")
    statut, r = _requete("POST", URL_CODE, formulaire={"client_id": client_id, "scope": PORTEE})
    if statut != 200 or not isinstance(r, dict) or "device_code" not in r:
        raise ErreurGitHub(_message_oauth(r))
    intervalle = int(r.get("interval") or 5)
    maintenant = time.time()
    with _verrou:
        _attente.update(code=r["device_code"], client_id=client_id, intervalle=intervalle,
                        prochain=maintenant + intervalle, expire=maintenant + int(r.get("expires_in") or 900))
    webbrowser.open(r["verification_uri"])
    return {"code": r["user_code"], "adresse": r["verification_uri"], "intervalle": intervalle,
            "expire_dans": int(r.get("expires_in") or 900)}


def connexion_suite():
    """Demande à GitHub si le code a été validé (au plus une fois par intervalle).
    État : attente, connecte, expire, refuse ou aucune."""
    with _verrou:
        if not _attente["code"]:
            return {"etat": "aucune"}
        maintenant = time.time()
        if maintenant > _attente["expire"]:
            _attente["code"] = None
            return {"etat": "expire"}
        if maintenant < _attente["prochain"]:
            return {"etat": "attente"}
        code, client_id = _attente["code"], _attente["client_id"]
        _attente["prochain"] = maintenant + _attente["intervalle"]
    _, r = _requete("POST", URL_JETON, formulaire={
        "client_id": client_id, "device_code": code,
        "grant_type": "urn:ietf:params:oauth:grant-type:device_code"})
    r = r if isinstance(r, dict) else {}
    if r.get("access_token"):
        statut, utilisateur = _requete("GET", API + "/user", jeton=r["access_token"])
        if statut != 200:
            raise ErreurGitHub("GitHub a donné un accès qui ne fonctionne pas : réessayez.")
        profil = _profil_de(utilisateur)
        if not coffre_windows.ecrire(CIBLE_COFFRE, profil["login"], r["access_token"]):
            raise ErreurGitHub("Impossible de ranger l'accès GitHub dans le coffre de Windows.")
        with _verrou:
            _attente["code"] = None
        _cache["profil"] = profil
        return {"etat": "connecte", **profil}
    erreur = r.get("error")
    if erreur == "authorization_pending":
        return {"etat": "attente"}
    if erreur == "slow_down":
        with _verrou:
            _attente["intervalle"] = int(r.get("interval") or _attente["intervalle"] + 5)
            _attente["prochain"] = time.time() + _attente["intervalle"]
        return {"etat": "attente"}
    with _verrou:
        _attente["code"] = None
    if erreur == "expired_token":
        return {"etat": "expire"}
    if erreur == "access_denied":
        return {"etat": "refuse"}
    raise ErreurGitHub(_message_oauth(r))


def deconnecter():
    """Retire le jeton de ce PC. Pour le révoquer aussi chez GitHub :
    github.com > Settings > Applications > Authorized OAuth Apps."""
    coffre_windows.supprimer(CIBLE_COFFRE)
    _cache["profil"] = None


# ---------------------------------------------------------------------------
# Dépôts
# ---------------------------------------------------------------------------
def depot_github(url):
    """« https://github.com/moi/projet.git » ou « git@github.com:moi/projet » →
    « moi/projet » (en minuscules) ; None pour une autre adresse."""
    m = MOTIF_GITHUB.search((url or "").strip())
    return f"{m.group(1)}/{m.group(2)}".lower() if m else None


def origine(dossier):
    """L'adresse du remote « origin » d'un dépôt git, lue dans .git/config."""
    config = os.path.join(dossier, ".git", "config")
    if not os.path.isfile(config):
        return None
    section = None
    try:
        with open(config, encoding="utf-8", errors="replace") as f:
            for ligne in f:
                ligne = ligne.strip()
                if ligne.startswith("["):
                    section = ligne
                elif section == '[remote "origin"]' and ligne.split("=")[0].strip() == "url":
                    return ligne.split("=", 1)[1].strip()
    except OSError:
        return None
    return None


def depots_locaux(dossiers):
    """{« moi/projet » : chemin} pour les dépôts GitHub trouvés dans les dossiers
    de projets (le dossier lui-même et ses sous-dossiers directs)."""
    trouves = {}
    for racine in dossiers or []:
        if not os.path.isdir(racine):
            continue
        candidats = [racine]
        try:
            with os.scandir(racine) as entrees:
                for e in entrees:
                    try:
                        if e.is_dir() and not e.name.startswith((".", "$")):
                            candidats.append(e.path)
                    except OSError:
                        pass
        except OSError:
            pass
        for chemin in candidats:
            cle = depot_github(origine(chemin))
            if cle and cle not in trouves:
                trouves[cle] = chemin
    return trouves


def lister_depots(dossiers):
    bruts = []
    for page in range(1, 31):
        r = _appel("GET", f"/user/repos?per_page=100&page={page}&sort=updated"
                          "&affiliation=owner,collaborator,organization_member")
        bruts += r
        if len(r) < 100:
            break
    locaux = depots_locaux(dossiers)
    depots = [{
        "nom": d["name"], "complet": d["full_name"], "description": d.get("description") or "",
        "prive": bool(d.get("private")), "langue": d.get("language") or "",
        "maj": d.get("pushed_at") or d.get("updated_at") or "", "url": d["html_url"],
        "archive": bool(d.get("archived")), "fork": bool(d.get("fork")),
        "etoiles": d.get("stargazers_count", 0), "local": locaux.get(d["full_name"].lower()),
    } for d in bruts]
    depots.sort(key=lambda d: d["maj"], reverse=True)
    return {"depots": depots, "dossiers": list(dossiers or [])}


# ---------------------------------------------------------------------------
# git
# ---------------------------------------------------------------------------
def _env_git(avec_acces):
    env = os.environ.copy()
    env.update(GIT_TERMINAL_PROMPT="0", GCM_INTERACTIVE="never")
    if avec_acces:
        j = jeton()
        if not j:
            raise ErreurGitHub("GitHub n'est pas connecté.")
        login = (_cache["profil"] or etat()).get("login") or "mes-outils"
        entete = base64.b64encode(f"{login}:{j}".encode()).decode()
        # L'accès ne vaut que pour github.com ; le gestionnaire d'identifiants
        # habituel est écarté pour ne pas ouvrir de fenêtre de connexion.
        env.update(GIT_CONFIG_COUNT="2",
                   GIT_CONFIG_KEY_0="http.https://github.com/.extraheader",
                   GIT_CONFIG_VALUE_0=f"AUTHORIZATION: basic {entete}",
                   GIT_CONFIG_KEY_1="credential.helper", GIT_CONFIG_VALUE_1="")
    return env


def _message_git(sortie):
    texte = (sortie or "").strip()
    bas = texte.lower()
    if "could not resolve host" in bas or "unable to access" in bas and "resolve" in bas:
        return "GitHub ne répond pas : vérifiez la connexion internet."
    if "authentication failed" in bas or "403" in bas or "permission" in bas and "denied" in bas:
        return "GitHub refuse l'accès : reconnectez GitHub."
    if "already exists and is not an empty directory" in bas:
        return "Le dossier de destination existe déjà."
    lignes = [l for l in texte.splitlines() if l.strip() and not l.lower().startswith(("warning:", "hint:"))]
    return lignes[-1] if lignes else "git a échoué."


def _git(args, dossier, acces=False, delai=120, verifier=True):
    try:
        p = subprocess.run(["git", *args], cwd=dossier, env=_env_git(acces), stdin=subprocess.DEVNULL,
                           capture_output=True, text=True, encoding="utf-8", errors="replace",
                           timeout=delai, creationflags=CREATE_NO_WINDOW)
    except FileNotFoundError:
        raise ErreurGitHub("Git n'est pas installé sur ce PC (https://git-scm.com).") from None
    except subprocess.TimeoutExpired:
        raise ErreurGitHub("Git met trop de temps à répondre.") from None
    if verifier and p.returncode != 0:
        raise ErreurGitHub(_message_git(p.stderr or p.stdout))
    return p if not verifier else p.stdout


def _a_des_commits(dossier):
    return _git(["rev-parse", "--verify", "-q", "HEAD"], dossier, verifier=False).returncode == 0


def _config_git(dossier, cle):
    return _git(["config", cle], dossier, verifier=False).stdout.strip()


def cloner(complet, dossier, dossiers):
    if not COMPLET_VALIDE.match(complet or ""):
        raise ErreurGitHub("Dépôt invalide.")
    if dossier not in (dossiers or []) or not os.path.isdir(dossier):
        raise ErreurGitHub("Choisissez un de vos dossiers de projets.")
    d = _appel("GET", f"/repos/{complet}")
    destination = os.path.join(dossier, d["name"])
    if os.path.exists(destination):
        raise ErreurGitHub(f"Le dossier {destination} existe déjà.")
    _git(["clone", "-q", d["clone_url"], destination], dossier, acces=True, delai=1800)
    return {"chemin": destination}


# ---------------------------------------------------------------------------
# Nouveau dépôt à partir d'un dossier
# ---------------------------------------------------------------------------
def _fichiers_a_envoyer(dossier, existant):
    """Les fichiers qui partiraient sur GitHub, en respectant .gitignore."""
    if existant and _a_des_commits(dossier):
        return _git(["ls-tree", "-r", "-z", "--name-only", "HEAD"], dossier).split("\0")
    if existant:
        return _git(["ls-files", "-z", "--cached", "--others", "--exclude-standard"], dossier).split("\0")
    # Pas encore de dépôt : un dépôt temporaire, hors du dossier, pour que git
    # applique les .gitignore sans rien créer dans le dossier.
    temporaire = tempfile.mkdtemp(prefix="mesoutils-git-")
    try:
        base = ["--git-dir", temporaire, "--work-tree", dossier]
        _git([*base, "init", "-q"], dossier)
        return _git([*base, "ls-files", "-z", "--others", "--exclude-standard"], dossier).split("\0")
    finally:
        shutil.rmtree(temporaire, ignore_errors=True)


def nom_suggere(dossier):
    nom = re.sub(r"[^A-Za-z0-9._-]+", "-", os.path.basename(dossier.rstrip("\\/"))).strip("-.")
    return nom.lower()[:100] or "mon-projet"


def apercu(dossier):
    """Ce qui partirait sur GitHub : nombre et taille des fichiers, fichiers
    sensibles (.env, clés…) et fichiers trop gros. Ne modifie rien."""
    dossier = os.path.abspath((dossier or "").strip().strip('"'))
    if not os.path.isdir(dossier):
        raise ErreurGitHub("Dossier introuvable.")
    existant = os.path.isdir(os.path.join(dossier, ".git"))
    relie = origine(dossier) if existant else None
    if relie:
        return {"dossier": dossier, "deja_relie": relie}
    fichiers = [f for f in _fichiers_a_envoyer(dossier, existant) if f]
    if not fichiers:
        raise ErreurGitHub("Aucun fichier à envoyer dans ce dossier.")
    taille, trop_gros, lourds, sensibles = 0, [], [], []
    for f in fichiers:
        try:
            t = os.path.getsize(os.path.join(dossier, f))
        except OSError:
            t = 0
        taille += t
        if t > TAILLE_MAX:
            trop_gros.append(f)
        elif t > TAILLE_LOURDE:
            lourds.append(f)
        if SENSIBLES.search(f) and not EXEMPLES.search(f):
            sensibles.append(f)
    modifs = existant and _a_des_commits(dossier) and bool(_git(["status", "--porcelain"], dossier).strip())
    return {"dossier": dossier, "nom_suggere": nom_suggere(dossier), "nombre": len(fichiers),
            "taille": taille, "exemples": sorted(fichiers)[:12], "sensibles": sensibles[:30],
            "trop_gros": trop_gros, "lourds": lourds, "existant": existant,
            "modifs_non_enregistrees": bool(modifs)}


def creer_et_envoyer(dossier, nom, description="", prive=True):
    nom = (nom or "").strip()
    if not NOM_VALIDE.match(nom) or nom in (".", ".."):
        raise ErreurGitHub("Nom de dépôt invalide : lettres, chiffres, tirets, points et soulignés seulement.")
    a = apercu(dossier)
    if a.get("deja_relie"):
        raise ErreurGitHub(f"Ce dossier est déjà relié à {a['deja_relie']}.")
    if a["trop_gros"]:
        raise ErreurGitHub("GitHub refuse les fichiers de plus de 100 Mo : " + ", ".join(a["trop_gros"][:3]))
    dossier = a["dossier"]
    profil = etat()
    if not profil.get("connecte"):
        raise ErreurGitHub("GitHub n'est pas connecté.")
    j = jeton()
    statut, d = _requete("POST", API + "/user/repos", jeton=j, donnees={
        "name": nom, "description": (description or "").strip()[:350], "private": bool(prive),
        "auto_init": False})
    if statut == 422:
        raise ErreurGitHub(f"Un dépôt « {nom} » existe déjà sur votre compte.")
    if statut >= 400 or not isinstance(d, dict):
        message = (d or {}).get("message") if isinstance(d, dict) else None
        raise ErreurGitHub(f"GitHub a refusé la création ({statut}){' : ' + message if message else ''}.")

    # Identité des commits : celle de git si elle existe, sinon l'adresse
    # « noreply » de GitHub (l'adresse e-mail réelle n'est jamais publiée).
    identite = []
    if not (_config_git(dossier, "user.name") and _config_git(dossier, "user.email")):
        identite = ["-c", f"user.name={profil['login']}",
                    "-c", f"user.email={profil['id']}+{profil['login']}@users.noreply.github.com"]
    if not a["existant"]:
        _git(["init", "-q", "-b", "main"], dossier)
    if not _a_des_commits(dossier):
        _git(["add", "-A"], dossier)
        _git([*identite, "commit", "-q", "-m", "Premier envoi"], dossier)
    branche = _git(["rev-parse", "--abbrev-ref", "HEAD"], dossier).strip()
    _git(["remote", "add", "origin", d["clone_url"]], dossier)
    try:
        _git(["push", "-q", "-u", "origin", branche], dossier, acces=True, delai=1800)
    except ErreurGitHub as e:
        raise ErreurGitHub(f"Le dépôt {d['html_url']} est créé, mais l'envoi a échoué ({e}). "
                           f"Relancez « git push -u origin {branche} » dans le dossier.") from None
    return {"url": d["html_url"], "complet": d["full_name"], "nombre": a["nombre"], "dossier": dossier}


# ---------------------------------------------------------------------------
# Ouvrir
# ---------------------------------------------------------------------------
def ouvrir_page(url):
    if not (url or "").startswith("https://github.com/"):
        raise ErreurGitHub("Adresse refusée.")
    webbrowser.open(url)


def ouvrir_dossier(chemin):
    if not os.path.isdir(chemin or ""):
        raise ErreurGitHub("Dossier introuvable.")
    os.startfile(chemin)


def _vscode():
    candidats = [os.path.expandvars(r"%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe"),
                 r"C:\Program Files\Microsoft VS Code\Code.exe",
                 r"C:\Program Files (x86)\Microsoft VS Code\Code.exe"]
    commande = shutil.which("code")
    if commande:  # …\Microsoft VS Code\bin\code.cmd → …\Microsoft VS Code\Code.exe
        candidats.append(os.path.join(os.path.dirname(os.path.dirname(commande)), "Code.exe"))
    return next((c for c in candidats if os.path.isfile(c)), None)


def ouvrir_vscode(chemin):
    if not os.path.isdir(chemin or ""):
        raise ErreurGitHub("Dossier introuvable.")
    code = _vscode()
    if not code:
        raise ErreurGitHub("VS Code est introuvable sur ce PC.")
    subprocess.Popen([code, chemin], creationflags=DETACHED, close_fds=True,
                     stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

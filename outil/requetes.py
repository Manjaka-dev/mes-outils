# -*- coding: utf-8 -*-
"""Onglet « Testeur d'API » : un petit Postman. Routes POST /api/requetes/<action>.

La requête part d'ici (urllib, sans dépendance) et non de la page : pas de
souci de CORS, et les en-têtes interdits au navigateur passent.

Données (donnees\\requetes.json) :
    {"historique": [...50 dernières...], "enregistrees": [...], "variables": {...}}

Secrets : rien de secret n'est écrit sur le disque. Avant d'enregistrer une
requête (historique ou requête nommée), les champs d'authentification, les
en-têtes sensibles (Authorization, Cookie, clés d'API…), les paramètres et
les champs du corps au nom sensible (password, token…) et le mot de passe
d'une URL sont remplacés par « •••• ». Une requête qui contient encore
« •••• » est refusée : il faut ressaisir la valeur.
"""
import base64
import copy
import gzip
import http.client
import json
import re
import secrets
import shlex
import socket
import ssl
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import zlib
from datetime import datetime

import config

NOM = "requetes"
METHODES = ("GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS")
TYPES_CORPS = ("aucun", "json", "texte", "formulaire")
TYPES_AUTH = ("aucune", "bearer", "basic")
MASQUE = "••••"
MAX_HISTORIQUE = 50
MAX_ENREGISTREES = 500
LIMITE_CORPS = 5 * 1024 * 1024          # réponse affichée : 5 Mo au plus
LIMITE_ENVOI = 10 * 1024 * 1024         # corps envoyé : 10 Mo au plus
TIMEOUT_DEFAUT = 30
NOM_SENSIBLE = re.compile(r"authori[sz]ation|cookie|api[-_]?key|token|secret|passw|pwd|mot[-_ ]?de[-_ ]?passe|session|signature|credential",
                          re.IGNORECASE)
NOM_ENTETE = re.compile(r"^[!#$%&'*+.^_`|~0-9A-Za-z-]+$")
VARIABLE = re.compile(r"\{\{\s*([A-Za-z_][A-Za-z0-9_.-]*)\s*\}\}")
AGENT = f"MesOutils/{config.VERSION}"

_verrou = threading.Lock()


class ErreurRequete(Exception):
    """Message pour l'utilisateur (réponse 400)."""


# ---------------------------------------------------------------------------
# Données
# ---------------------------------------------------------------------------
def _lire():
    d = config.lire_donnees(NOM, {})
    if not isinstance(d, dict):
        d = {}
    d.setdefault("historique", [])
    d.setdefault("enregistrees", [])
    d.setdefault("variables", {})
    return d


def _ecrire(d):
    config.ecrire_donnees(NOM, d)


def _nouvel_id():
    return secrets.token_hex(6)


# ---------------------------------------------------------------------------
# Lecture et contrôle de la requête envoyée par la page
# ---------------------------------------------------------------------------
def _texte(v, limite=LIMITE_ENVOI):
    v = "" if v is None else str(v)
    if len(v) > limite:
        raise ErreurRequete("Texte trop long.")
    return v


def _lignes(liste):
    """Lignes clé / valeur : [{"cle", "valeur", "actif"}] (100 au plus)."""
    if liste is None:
        return []
    if not isinstance(liste, list) or len(liste) > 100:
        raise ErreurRequete("Liste de lignes invalide.")
    sortie = []
    for ligne in liste:
        if not isinstance(ligne, dict):
            raise ErreurRequete("Liste de lignes invalide.")
        sortie.append({"cle": _texte(ligne.get("cle"), 2000), "valeur": _texte(ligne.get("valeur"), 100000),
                       "actif": ligne.get("actif", True) is not False})
    return sortie


def normaliser(r):
    """La requête de la page, contrôlée et ramenée à une forme connue."""
    if not isinstance(r, dict):
        raise ErreurRequete("Requête invalide.")
    methode = str(r.get("methode") or "GET").upper()
    if methode not in METHODES:
        raise ErreurRequete(f"Méthode non prise en charge : {methode}")
    corps = r.get("corps") if isinstance(r.get("corps"), dict) else {}
    type_corps = corps.get("type") or "aucun"
    if type_corps not in TYPES_CORPS:
        raise ErreurRequete("Type de corps inconnu.")
    auth = r.get("auth") if isinstance(r.get("auth"), dict) else {}
    type_auth = auth.get("type") or "aucune"
    if type_auth not in TYPES_AUTH:
        raise ErreurRequete("Type d'authentification inconnu.")
    options = r.get("options") if isinstance(r.get("options"), dict) else {}
    try:
        timeout = float(options.get("timeout") or TIMEOUT_DEFAUT)
    except (TypeError, ValueError):
        raise ErreurRequete("Délai d'attente invalide.") from None
    return {
        "methode": methode,
        "url": _texte(r.get("url"), 8000).strip(),
        "params": _lignes(r.get("params")),
        "entetes": _lignes(r.get("entetes")),
        "corps": {"type": type_corps, "texte": _texte(corps.get("texte")), "champs": _lignes(corps.get("champs"))},
        "auth": {"type": type_auth, "jeton": _texte(auth.get("jeton"), 20000),
                 "utilisateur": _texte(auth.get("utilisateur"), 2000), "mot_de_passe": _texte(auth.get("mot_de_passe"), 2000)},
        "options": {"timeout": min(max(timeout, 1.0), 600.0),
                    "redirections": options.get("redirections", True) is not False,
                    "ignorer_tls": options.get("ignorer_tls") is True},
    }


def verifier_url(url):
    """Seuls http:// et https:// sont acceptés, avec un nom d'hôte."""
    morceaux = urllib.parse.urlsplit(url)
    if morceaux.scheme.lower() not in ("http", "https"):
        raise ErreurRequete("Seules les adresses http:// et https:// sont acceptées.")
    if not morceaux.hostname:
        raise ErreurRequete("Adresse incomplète : il manque le nom du serveur.")
    return morceaux


# ---------------------------------------------------------------------------
# Variables {{nom}}
# ---------------------------------------------------------------------------
def remplacer_variables(texte, variables):
    def valeur(m):
        nom = m.group(1)
        if nom not in variables:
            raise ErreurRequete(f"Variable inconnue : {{{{{nom}}}}}")
        return str(variables[nom])
    return VARIABLE.sub(valeur, texte) if texte else texte


def resoudre(r, variables):
    """Une copie de la requête, variables remplacées partout."""
    r = copy.deepcopy(r)
    v = lambda s: remplacer_variables(s, variables)  # noqa: E731
    r["url"] = v(r["url"])
    for liste in (r["params"], r["entetes"], r["corps"]["champs"]):
        for ligne in liste:
            ligne["cle"], ligne["valeur"] = v(ligne["cle"]), v(ligne["valeur"])
    r["corps"]["texte"] = v(r["corps"]["texte"])
    for cle in ("jeton", "utilisateur", "mot_de_passe"):
        r["auth"][cle] = v(r["auth"][cle])
    return r


# ---------------------------------------------------------------------------
# Construction : URL finale, en-têtes, corps
# ---------------------------------------------------------------------------
def _refuser_masque(r):
    """Une valeur « •••• » vient de l'historique : elle doit être ressaisie."""
    morceaux = [r["url"], r["corps"]["texte"], r["auth"]["jeton"], r["auth"]["mot_de_passe"]]
    if r["auth"]["type"] == "basic":
        morceaux.append(r["auth"]["utilisateur"])
    for liste in (r["params"], r["entetes"], r["corps"]["champs"]):
        morceaux += [ligne["valeur"] for ligne in liste if ligne["actif"]]
    if any(MASQUE in m for m in morceaux):
        raise ErreurRequete("Une valeur masquée (••••) reste dans la requête : saisissez-la à nouveau.")


def url_complete(r):
    """L'URL avec les paramètres actifs ajoutés à ceux déjà présents."""
    url = r["url"]
    morceaux = verifier_url(url)
    params = [(p["cle"], p["valeur"]) for p in r["params"] if p["actif"] and p["cle"]]
    if not params:
        return url
    requete = morceaux.query
    ajout = urllib.parse.urlencode(params)
    requete = f"{requete}&{ajout}" if requete else ajout
    return urllib.parse.urlunsplit((morceaux.scheme, morceaux.netloc, morceaux.path or "/", requete, morceaux.fragment))


def construire(r):
    """(url, en-têtes [(nom, valeur)], corps en octets ou None)."""
    _refuser_masque(r)
    url = url_complete(r)
    entetes = []
    for e in r["entetes"]:
        if not (e["actif"] and e["cle"].strip()):
            continue
        nom = e["cle"].strip()
        if not NOM_ENTETE.match(nom):
            raise ErreurRequete(f"Nom d'en-tête invalide : {nom}")
        if "\r" in e["valeur"] or "\n" in e["valeur"]:
            raise ErreurRequete(f"Valeur d'en-tête invalide : {nom}")
        try:
            e["valeur"].encode("latin-1")
        except UnicodeEncodeError:
            raise ErreurRequete(f"Caractère non permis dans l'en-tête {nom} (accents, emojis…).") from None
        entetes.append((nom, e["valeur"]))

    def poser(nom, valeur, remplacer=False):
        nonlocal entetes
        if remplacer:
            entetes = [(n, v) for n, v in entetes if n.lower() != nom.lower()]
        elif any(n.lower() == nom.lower() for n, _ in entetes):
            return
        entetes.append((nom, valeur))

    auth = r["auth"]
    if auth["type"] == "bearer":
        jeton = auth["jeton"].strip()
        if not jeton:
            raise ErreurRequete("Jeton (Bearer) vide.")
        if "\r" in jeton or "\n" in jeton:
            raise ErreurRequete("Jeton invalide.")
        poser("Authorization", "Bearer " + jeton, remplacer=True)
    elif auth["type"] == "basic":
        brut = f"{auth['utilisateur']}:{auth['mot_de_passe']}".encode("utf-8")
        poser("Authorization", "Basic " + base64.b64encode(brut).decode("ascii"), remplacer=True)

    corps = None
    c = r["corps"]
    if c["type"] == "json":
        corps = c["texte"].encode("utf-8")
        poser("Content-Type", "application/json; charset=utf-8")
    elif c["type"] == "texte":
        corps = c["texte"].encode("utf-8")
        poser("Content-Type", "text/plain; charset=utf-8")
    elif c["type"] == "formulaire":
        corps = urllib.parse.urlencode([(f["cle"], f["valeur"]) for f in c["champs"] if f["actif"] and f["cle"]]).encode("utf-8")
        poser("Content-Type", "application/x-www-form-urlencoded")
    if corps is not None and len(corps) > LIMITE_ENVOI:
        raise ErreurRequete("Corps trop gros (10 Mo au plus).")
    poser("User-Agent", AGENT)
    poser("Accept", "*/*")
    return url, entetes, corps


# ---------------------------------------------------------------------------
# Envoi
# ---------------------------------------------------------------------------
ENTETES_A_RETIRER_AILLEURS = ("authorization", "cookie", "proxy-authorization")


class _Redirections(urllib.request.HTTPRedirectHandler):
    """Suit (ou non) les redirections ; jamais vers autre chose que http(s),
    et sans transmettre Authorization / Cookie à un autre serveur."""

    def __init__(self, suivre):
        super().__init__()
        self.suivre = suivre
        self.nombre = 0

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not self.suivre:
            return None  # la réponse 3xx est rendue telle quelle
        if urllib.parse.urlsplit(newurl).scheme.lower() not in ("http", "https"):
            return None
        nouvelle = super().redirect_request(req, fp, code, msg, headers, newurl)
        if nouvelle is None:
            return None
        if urllib.parse.urlsplit(newurl).netloc.lower() != urllib.parse.urlsplit(req.full_url).netloc.lower():
            for nom in list(nouvelle.headers):
                if nom.lower() in ENTETES_A_RETIRER_AILLEURS:
                    del nouvelle.headers[nom]
        self.nombre += 1
        return nouvelle


def _contexte_tls(ignorer):
    if not ignorer:
        return ssl.create_default_context()
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def _lire_corps(reponse):
    """(octets lus, tronqué ?) — 5 Mo au plus."""
    morceaux, total = [], 0
    while total <= LIMITE_CORPS:
        bloc = reponse.read(min(65536, LIMITE_CORPS + 1 - total))
        if not bloc:
            break
        morceaux.append(bloc)
        total += len(bloc)
    brut = b"".join(morceaux)
    if len(brut) > LIMITE_CORPS:
        return brut[:LIMITE_CORPS], True
    return brut, False


def _decompresser(brut, encodage, tronque):
    encodage = (encodage or "").lower().strip()
    if tronque or not brut or encodage not in ("gzip", "deflate"):
        return brut
    try:
        if encodage == "gzip":
            return gzip.decompress(brut)
        try:
            return zlib.decompress(brut)
        except zlib.error:
            return zlib.decompress(brut, -zlib.MAX_WBITS)
    except (OSError, zlib.error, EOFError):
        return brut


def _charset(type_contenu):
    m = re.search(r"charset=[\"']?([\w.:-]+)", type_contenu or "", re.IGNORECASE)
    return m.group(1) if m else None


TYPES_TEXTE = re.compile(r"^text/|json|xml|javascript|ecmascript|x-www-form-urlencoded|graphql|yaml|csv|html", re.IGNORECASE)


def interpreter(brut, type_contenu, tronque):
    """{"type": "json" | "texte" | "binaire" | "vide", "corps": texte affiché}."""
    if not brut:
        return {"type": "vide", "corps": ""}
    charset = _charset(type_contenu)
    texte = None
    if charset:
        try:
            texte = brut.decode(charset, errors="replace")
        except LookupError:
            texte = None
    if texte is None:
        try:
            texte = brut.decode("utf-8")
        except UnicodeDecodeError as e:
            # Tronqué au milieu d'un caractère : on garde ce qui précède.
            if tronque and e.start >= len(brut) - 4:
                texte = brut[:e.start].decode("utf-8")
            elif TYPES_TEXTE.search(type_contenu or ""):
                texte = brut.decode("utf-8", errors="replace")
            else:
                return {"type": "binaire", "corps": ""}
    if "\x00" in texte and not TYPES_TEXTE.search(type_contenu or ""):
        return {"type": "binaire", "corps": ""}
    est_json = "json" in (type_contenu or "").lower()
    if not tronque and (est_json or texte.lstrip()[:1] in ("{", "[")):
        try:
            valeur = json.loads(texte)
            return {"type": "json", "corps": json.dumps(valeur, ensure_ascii=False, indent=2)}
        except ValueError:
            pass
    return {"type": "texte", "corps": texte}


def executer(r):
    """Envoie la requête (déjà normalisée et résolue). Renvoie la réponse."""
    url, entetes, corps = construire(r)
    options = r["options"]
    redirections = _Redirections(options["redirections"])
    ouvreur = urllib.request.build_opener(
        redirections, urllib.request.HTTPSHandler(context=_contexte_tls(options["ignorer_tls"])))
    requete = urllib.request.Request(url, data=corps, method=r["methode"])
    for nom, valeur in entetes:
        requete.add_header(nom, valeur)
    debut = time.perf_counter()
    try:
        try:
            reponse = ouvreur.open(requete, timeout=options["timeout"])
        except urllib.error.HTTPError as e:
            reponse = e  # 4xx / 5xx / 3xx non suivie : c'est une réponse comme une autre
        with reponse:
            brut, tronque = (b"", False) if r["methode"] == "HEAD" else _lire_corps(reponse)
            statut = reponse.status if hasattr(reponse, "status") and reponse.status else reponse.code
            raison = getattr(reponse, "reason", "") or ""
            entetes_rep = list(reponse.headers.items())
            url_finale = reponse.geturl() if hasattr(reponse, "geturl") else url
    except urllib.error.URLError as e:
        raison = e.reason
        if isinstance(raison, (socket.timeout, TimeoutError)):
            raise ErreurRequete(f"Pas de réponse après {options['timeout']:g} s (délai dépassé).") from None
        if isinstance(raison, ssl.SSLCertVerificationError):
            raise ErreurRequete("Certificat refusé : " + (raison.verify_message or str(raison))
                                + ". Pour un serveur de développement, cochez « Ignorer les erreurs de certificat ».") from None
        if isinstance(raison, ssl.SSLError):
            raise ErreurRequete(f"Erreur TLS : {raison}") from None
        if isinstance(raison, socket.gaierror):
            raise ErreurRequete("Serveur introuvable (nom inconnu) : " + (urllib.parse.urlsplit(url).hostname or "")) from None
        if isinstance(raison, ConnectionRefusedError):
            raise ErreurRequete("Connexion refusée : rien n'écoute à cette adresse.") from None
        raise ErreurRequete(f"Échec de la connexion : {raison}") from None
    except (socket.timeout, TimeoutError):
        raise ErreurRequete(f"Pas de réponse après {options['timeout']:g} s (délai dépassé).") from None
    except (http.client.HTTPException, ConnectionError, OSError) as e:
        raise ErreurRequete(f"Échec de la connexion : {e}") from None
    duree = (time.perf_counter() - debut) * 1000

    entetes_dict = {k.lower(): v for k, v in entetes_rep}
    type_contenu = entetes_dict.get("content-type", "")
    taille = len(brut)
    if tronque:
        try:
            taille = int(entetes_dict.get("content-length"))
        except (TypeError, ValueError):
            taille = None
    brut = _decompresser(brut, entetes_dict.get("content-encoding"), tronque)
    sens = interpreter(brut, type_contenu, tronque)
    return {
        "statut": statut, "raison": raison, "duree_ms": round(duree, 1), "taille": taille,
        "tronque": tronque, "entetes": entetes_rep, "type_contenu": type_contenu,
        "type": sens["type"], "corps": sens["corps"], "octets": len(brut),
        "url_finale": url_finale, "redirections": redirections.nombre,
    }


# ---------------------------------------------------------------------------
# Secrets retirés avant toute écriture sur le disque
# ---------------------------------------------------------------------------
def _masquer_json(valeur):
    """(valeur, changé ?) : valeurs des clés sensibles remplacées."""
    if isinstance(valeur, dict):
        change = False
        sortie = {}
        for k, v in valeur.items():
            if NOM_SENSIBLE.search(str(k)) and v not in (None, ""):
                sortie[k], change = MASQUE, True
            else:
                sortie[k], c = _masquer_json(v)
                change = change or c
        return sortie, change
    if isinstance(valeur, list):
        sortie, change = [], False
        for v in valeur:
            v, c = _masquer_json(v)
            sortie.append(v)
            change = change or c
        return sortie, change
    return valeur, False


def _masquer_url(url):
    """Mot de passe (user:pass@) et paramètres sensibles de l'URL masqués."""
    try:
        m = urllib.parse.urlsplit(url)
    except ValueError:
        return url
    netloc = m.netloc
    if "@" in netloc:
        netloc = MASQUE + "@" + netloc.rsplit("@", 1)[1]
    requete = m.query
    if requete:
        morceaux = []
        for bout in requete.split("&"):
            cle = urllib.parse.unquote_plus(bout.split("=", 1)[0])
            morceaux.append(f"{bout.split('=', 1)[0]}={MASQUE}" if "=" in bout and NOM_SENSIBLE.search(cle) else bout)
        requete = "&".join(morceaux)
    return urllib.parse.urlunsplit((m.scheme, netloc, m.path, requete, m.fragment))


def sans_secret(r, garder_auth=True):
    """Copie de la requête bonne à écrire sur le disque.

    garder_auth=True (historique) : le type d'authentification reste, ses
    valeurs deviennent « •••• ». garder_auth=False (requêtes enregistrées) :
    les valeurs d'authentification sont vidées."""
    r = copy.deepcopy(r)
    remplacement = MASQUE if garder_auth else ""
    a = r["auth"]
    for cle in ("jeton", "utilisateur", "mot_de_passe"):
        if a.get(cle):
            a[cle] = remplacement
    r["url"] = _masquer_url(r["url"])
    for liste in (r["entetes"], r["params"], r["corps"]["champs"]):
        for ligne in liste:
            if ligne["valeur"] and NOM_SENSIBLE.search(ligne["cle"]):
                ligne["valeur"] = MASQUE
    if r["corps"]["type"] == "json" and r["corps"]["texte"].strip():
        try:
            valeur, change = _masquer_json(json.loads(r["corps"]["texte"]))
            if change:
                r["corps"]["texte"] = json.dumps(valeur, ensure_ascii=False, indent=2)
        except ValueError:
            pass
    if r["corps"]["type"] == "texte" and "=" in r["corps"]["texte"]:
        # corps « a=1&password=x » saisi en texte
        texte = r["corps"]["texte"]
        if "&" in texte or "\n" not in texte:
            r["corps"]["texte"] = re.sub(r"(^|&)([^=&]*)=([^&]*)",
                                         lambda m: m.group(0) if not NOM_SENSIBLE.search(m.group(2))
                                         else f"{m.group(1)}{m.group(2)}={MASQUE}", texte)
    return r


# ---------------------------------------------------------------------------
# cURL
# ---------------------------------------------------------------------------
def en_curl(r):
    """La commande cURL (syntaxe bash : Git Bash, Linux, macOS)."""
    url, entetes, corps = construire(r)
    morceaux = ["curl"]
    if r["methode"] == "HEAD":
        morceaux.append("-I")
    elif r["methode"] != ("POST" if corps is not None else "GET"):
        morceaux += ["-X", r["methode"]]
    morceaux.append(shlex.quote(url))
    for nom, valeur in entetes:
        if nom.lower() == "user-agent" and valeur == AGENT or nom.lower() == "accept" and valeur == "*/*":
            continue
        morceaux += ["-H", shlex.quote(f"{nom}: {valeur}")]
    if corps is not None:
        morceaux += ["--data-raw", shlex.quote(corps.decode("utf-8"))]
    if r["options"]["redirections"]:
        morceaux.append("-L")
    if r["options"]["ignorer_tls"]:
        morceaux.append("-k")
    morceaux += ["--max-time", f"{r['options']['timeout']:g}"]
    return " ".join(morceaux)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
def etat(_d=None):
    d = _lire()
    return {"historique": d["historique"], "enregistrees": d["enregistrees"], "variables": d["variables"]}


def envoyer(d):
    r = normaliser(d.get("requete"))
    with _verrou:
        variables = _lire()["variables"]
    reponse = executer(resoudre(r, variables))
    entree = {"id": _nouvel_id(), "date": datetime.now().isoformat(timespec="seconds"),
              "requete": sans_secret(r), "statut": reponse["statut"], "duree_ms": reponse["duree_ms"]}
    with _verrou:
        donnees = _lire()
        donnees["historique"] = [entree] + donnees["historique"][:MAX_HISTORIQUE - 1]
        _ecrire(donnees)
    return {"reponse": reponse, "historique": donnees["historique"]}


def curl(d):
    r = normaliser(d.get("requete"))
    with _verrou:
        variables = _lire()["variables"]
    return {"commande": en_curl(resoudre(r, variables))}


def vider_historique(_d=None):
    with _verrou:
        donnees = _lire()
        donnees["historique"] = []
        _ecrire(donnees)
    return etat()


def enregistrer(d):
    nom = _texte(d.get("nom"), 200).strip()
    if not nom:
        raise ErreurRequete("Donnez un nom à la requête.")
    collection = _texte(d.get("collection"), 200).strip()
    r = sans_secret(normaliser(d.get("requete")), garder_auth=False)
    with _verrou:
        donnees = _lire()
        liste = donnees["enregistrees"]
        ident = d.get("id")
        existante = next((e for e in liste if e.get("id") == ident), None) if ident else None
        if existante:
            existante.update(nom=nom, collection=collection, requete=r, date=datetime.now().isoformat(timespec="seconds"))
        else:
            if len(liste) >= MAX_ENREGISTREES:
                raise ErreurRequete("Trop de requêtes enregistrées : supprimez-en quelques-unes.")
            existante = {"id": _nouvel_id(), "nom": nom, "collection": collection, "requete": r,
                         "date": datetime.now().isoformat(timespec="seconds")}
            liste.append(existante)
        _ecrire(donnees)
    return {"enregistree": existante, **etat()}


def supprimer(d):
    ident = d.get("id")
    with _verrou:
        donnees = _lire()
        avant = len(donnees["enregistrees"])
        donnees["enregistrees"] = [e for e in donnees["enregistrees"] if e.get("id") != ident]
        if len(donnees["enregistrees"]) == avant:
            raise ErreurRequete("Requête introuvable.")
        _ecrire(donnees)
    return etat()


def enregistrer_variables(d):
    variables = d.get("variables")
    if not isinstance(variables, dict) or len(variables) > 200:
        raise ErreurRequete("Variables invalides.")
    propres = {}
    for nom, valeur in variables.items():
        nom = str(nom).strip()
        if not nom:
            continue
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_.-]{0,60}", nom):
            raise ErreurRequete(f"Nom de variable invalide : {nom}")
        propres[nom] = _texte(valeur, 20000)
    with _verrou:
        donnees = _lire()
        donnees["variables"] = propres
        _ecrire(donnees)
    return etat()


ROUTES = {
    "etat": etat,
    "envoyer": envoyer,
    "curl": curl,
    "historique/vider": vider_historique,
    "enregistrer": enregistrer,
    "supprimer": supprimer,
    "variables": enregistrer_variables,
}

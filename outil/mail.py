# -*- coding: utf-8 -*-
"""Boîte mail de « Mes outils » : Gmail par IMAP (lecture) et SMTP (envoi).

Le mot de passe d'application Google est rangé dans le Gestionnaire
d'identification de Windows (coffre chiffré par Windows, lié à votre session),
jamais dans un fichier. Il est saisi par l'utilisateur dans l'interface.
"""
import ctypes
import email
import email.policy
import email.utils
import imaplib
import re
import smtplib
import ssl
import threading
import time
from ctypes import wintypes
from email.header import decode_header, make_header
from email.message import EmailMessage

IMAP_HOTE, SMTP_HOTE = "imap.gmail.com", "smtp.gmail.com"
CIBLE_COFFRE = "MesOutils:mail:{adresse}"


class ErreurMail(Exception):
    pass


# ---------------------------------------------------------------------------
# Coffre Windows (Credential Manager)
# ---------------------------------------------------------------------------
class _CREDENTIAL(ctypes.Structure):
    _fields_ = [
        ("Flags", wintypes.DWORD), ("Type", wintypes.DWORD), ("TargetName", wintypes.LPWSTR),
        ("Comment", wintypes.LPWSTR), ("LastWritten", wintypes.FILETIME),
        ("CredentialBlobSize", wintypes.DWORD), ("CredentialBlob", ctypes.POINTER(ctypes.c_char)),
        ("Persist", wintypes.DWORD), ("AttributeCount", wintypes.DWORD), ("Attributes", ctypes.c_void_p),
        ("TargetAlias", wintypes.LPWSTR), ("UserName", wintypes.LPWSTR),
    ]


_advapi = ctypes.WinDLL("advapi32", use_last_error=True)
_advapi.CredReadW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.POINTER(ctypes.POINTER(_CREDENTIAL))]
_advapi.CredWriteW.argtypes = [ctypes.POINTER(_CREDENTIAL), wintypes.DWORD]
_advapi.CredDeleteW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD]
_advapi.CredFree.argtypes = [ctypes.c_void_p]
CRED_TYPE_GENERIC, CRED_PERSIST_LOCAL_MACHINE = 1, 2


def coffre_ecrire(adresse, secret):
    blob = secret.encode("utf-16-le")
    cred = _CREDENTIAL()
    cred.Type = CRED_TYPE_GENERIC
    cred.TargetName = CIBLE_COFFRE.format(adresse=adresse)
    cred.UserName = adresse
    cred.CredentialBlobSize = len(blob)
    cred.CredentialBlob = ctypes.cast(ctypes.create_string_buffer(blob, len(blob)), ctypes.POINTER(ctypes.c_char))
    cred.Persist = CRED_PERSIST_LOCAL_MACHINE
    if not _advapi.CredWriteW(ctypes.byref(cred), 0):
        raise ErreurMail("Impossible d'enregistrer le mot de passe dans le coffre Windows.")


def coffre_lire(adresse):
    pcred = ctypes.POINTER(_CREDENTIAL)()
    if not _advapi.CredReadW(CIBLE_COFFRE.format(adresse=adresse), CRED_TYPE_GENERIC, 0, ctypes.byref(pcred)):
        return None
    try:
        c = pcred.contents
        return ctypes.string_at(c.CredentialBlob, c.CredentialBlobSize).decode("utf-16-le")
    finally:
        _advapi.CredFree(pcred)


def coffre_supprimer(adresse):
    _advapi.CredDeleteW(CIBLE_COFFRE.format(adresse=adresse), CRED_TYPE_GENERIC, 0)


# ---------------------------------------------------------------------------
# Outils de décodage
# ---------------------------------------------------------------------------
def _entete(valeur):
    if not valeur:
        return ""
    try:
        return str(make_header(decode_header(valeur)))
    except Exception:
        return str(valeur)


def _personne(valeur):
    nom, adresse = email.utils.parseaddr(_entete(valeur))
    return {"nom": nom or adresse, "adresse": adresse}


def _date(valeur):
    try:
        d = email.utils.parsedate_to_datetime(valeur)
        return d.astimezone().strftime("%Y-%m-%dT%H:%M")
    except Exception:
        return ""


# ---------------------------------------------------------------------------
# La boîte
# ---------------------------------------------------------------------------
class Boite:
    def __init__(self, adresse):
        self.adresse = adresse
        self._verrou = threading.Lock()
        self._cache_liste = {}
        self._non_lus = (0, None)  # (heure, nombre)

    # -- connexion -----------------------------------------------------------
    def configuree(self):
        return bool(self.adresse) and coffre_lire(self.adresse) is not None

    def _imap(self):
        secret = coffre_lire(self.adresse)
        if not secret:
            raise ErreurMail("Boîte mail pas encore connectée.")
        try:
            c = imaplib.IMAP4_SSL(IMAP_HOTE, ssl_context=ssl.create_default_context(), timeout=20)
            c.login(self.adresse, secret)
            return c
        except imaplib.IMAP4.error as e:
            raise ErreurMail("Gmail refuse la connexion : vérifiez l'adresse et le mot de passe "
                             "d'application (16 lettres). " + _court(e))
        except OSError as e:
            raise ErreurMail("Pas de connexion à Gmail (Internet ?) : " + _court(e))

    def tester_et_enregistrer(self, adresse, secret):
        secret = re.sub(r"\s+", "", secret or "")
        if not adresse or not secret:
            raise ErreurMail("Indiquez l'adresse et le mot de passe d'application.")
        try:
            c = imaplib.IMAP4_SSL(IMAP_HOTE, ssl_context=ssl.create_default_context(), timeout=20)
            c.login(adresse, secret)
            c.logout()
        except imaplib.IMAP4.error as e:
            raise ErreurMail("Gmail refuse ce mot de passe. Il faut un mot de passe "
                             "d'application, pas votre mot de passe habituel. " + _court(e))
        except OSError as e:
            raise ErreurMail("Pas de connexion à Gmail (Internet ?) : " + _court(e))
        coffre_ecrire(adresse, secret)
        self.adresse = adresse
        self._cache_liste.clear()

    def deconnecter(self):
        if self.adresse:
            coffre_supprimer(self.adresse)
        self._cache_liste.clear()

    # -- lecture -----------------------------------------------------------
    # Le nom des dossiers dépend de la langue de Gmail (« Sent Mail »,
    # « Messages envoyés »…) : on les retrouve par leur marque officielle.
    MARQUES = {"envoyes": "\\Sent", "tous": "\\All"}

    def _choisir(self, c, dossier, lecture_seule=True):
        nom = "INBOX"
        if dossier in self.MARQUES:
            statut, lignes = c.list()
            for ligne in lignes or []:
                texte = ligne.decode("utf-8", "replace")
                if self.MARQUES[dossier] in texte.split(")")[0]:
                    nom = texte.rsplit(' "/" ', 1)[-1].strip()
                    break
            else:
                raise ErreurMail("Dossier introuvable dans la boîte.")
        statut, _ = c.select(nom, readonly=lecture_seule)
        if statut != "OK":
            raise ErreurMail("Dossier introuvable dans la boîte.")

    def lister(self, dossier="recus", recherche="", nombre=40):
        cle = (dossier, recherche, nombre)
        en_cache = self._cache_liste.get(cle)
        if en_cache and time.time() - en_cache[0] < 45:
            return en_cache[1]
        with self._verrou:
            c = self._imap()
            try:
                self._choisir(c, dossier)
                terme = recherche.replace("\\", " ").replace('"', " ").strip()
                if not terme:
                    statut, donnees = c.uid("SEARCH", None, "ALL")
                elif terme.isascii():
                    # Recherche façon Gmail (expéditeur, objet, texte…).
                    statut, donnees = c.uid("SEARCH", None, "X-GM-RAW", f'"{terme}"')
                else:
                    c.literal = terme.encode("utf-8")
                    statut, donnees = c.uid("SEARCH", "CHARSET", "UTF-8", "X-GM-RAW")
                uids = (donnees[0] or b"").split()[-nombre:]
                mails = []
                if uids:
                    statut, reponse = c.uid("FETCH", b",".join(uids),
                                            "(UID FLAGS BODY.PEEK[HEADER.FIELDS (FROM TO SUBJECT DATE)])")
                    for partie in reponse:
                        if not isinstance(partie, tuple):
                            continue
                        meta = partie[0].decode("utf-8", "replace")
                        uid = re.search(r"UID (\d+)", meta)
                        entetes = email.message_from_bytes(partie[1])
                        mails.append({
                            "uid": uid.group(1) if uid else "",
                            "de": _personne(entetes.get("From")),
                            "a": _personne(entetes.get("To")),
                            "sujet": _entete(entetes.get("Subject")) or "(sans objet)",
                            "date": _date(entetes.get("Date")),
                            "lu": "\\Seen" in meta,
                            "important": "\\Flagged" in meta,
                        })
                mails.sort(key=lambda m: int(m["uid"] or 0), reverse=True)
            finally:
                c.logout()
        self._cache_liste[cle] = (time.time(), mails)
        return mails

    def lire(self, uid, dossier="recus"):
        with self._verrou:
            c = self._imap()
            try:
                self._choisir(c, dossier, lecture_seule=False)
                statut, reponse = c.uid("FETCH", str(uid).encode(), "(BODY.PEEK[])")
                brut = next((p[1] for p in reponse if isinstance(p, tuple)), None)
                if not brut:
                    raise ErreurMail("Mail introuvable.")
                c.uid("STORE", str(uid).encode(), "+FLAGS", "(\\Seen)")
            finally:
                c.logout()
        self._cache_liste.clear()
        self._non_lus = (0, None)
        msg = email.message_from_bytes(brut, policy=email.policy.default)
        texte = html = None
        pieces = []
        for partie in msg.walk():
            if partie.is_multipart():
                continue
            nom = partie.get_filename()
            if nom or partie.get_content_disposition() == "attachment":
                pieces.append({"nom": _entete(nom) or "pièce jointe",
                               "taille": len(partie.get_payload(decode=True) or b"")})
                continue
            if partie.get_content_type() == "text/plain" and texte is None:
                texte = partie.get_content()
            elif partie.get_content_type() == "text/html" and html is None:
                html = partie.get_content()
        return {
            "uid": str(uid),
            "de": _personne(msg.get("From")),
            "a": _entete(msg.get("To")),
            "cc": _entete(msg.get("Cc")),
            "sujet": _entete(msg.get("Subject")) or "(sans objet)",
            "date": _date(msg.get("Date")),
            "texte": texte or "",
            "html": html or "",
            "pieces": pieces,
            "message_id": msg.get("Message-ID", ""),
            "references": msg.get("References", ""),
        }

    def non_lus(self):
        """Nombre de mails non lus dans la boîte de réception (relu au plus
        toutes les deux minutes)."""
        heure, nombre = self._non_lus
        if nombre is not None and time.time() - heure < 120:
            return nombre
        with self._verrou:
            c = self._imap()
            try:
                statut, donnees = c.status("INBOX", "(UNSEEN)")
                m = re.search(rb"UNSEEN (\d+)", donnees[0] or b"")
                nombre = int(m.group(1)) if m else 0
            finally:
                c.logout()
        self._non_lus = (time.time(), nombre)
        return nombre

    # -- envoi -------------------------------------------------------------
    def envoyer(self, a, sujet, corps, cc="", reponse_a=None, references=None):
        if not a.strip():
            raise ErreurMail("Indiquez au moins un destinataire.")
        secret = coffre_lire(self.adresse)
        if not secret:
            raise ErreurMail("Boîte mail pas encore connectée.")
        msg = EmailMessage()
        msg["From"] = self.adresse
        msg["To"] = a
        if cc.strip():
            msg["Cc"] = cc
        msg["Subject"] = sujet
        msg["Date"] = email.utils.formatdate(localtime=True)
        msg["Message-ID"] = email.utils.make_msgid(domain=self.adresse.split("@")[-1])
        if reponse_a:
            msg["In-Reply-To"] = reponse_a
            msg["References"] = f"{references or ''} {reponse_a}".strip()
        msg.set_content(corps)
        try:
            with smtplib.SMTP_SSL(SMTP_HOTE, 465, context=ssl.create_default_context(), timeout=30) as s:
                s.login(self.adresse, secret)
                s.send_message(msg)
        except smtplib.SMTPException as e:
            raise ErreurMail("Gmail a refusé l'envoi : " + _court(e))
        except OSError as e:
            raise ErreurMail("Pas de connexion à Gmail (Internet ?) : " + _court(e))
        self._cache_liste.clear()


def _court(e):
    texte = str(e)
    return texte if len(texte) < 160 else texte[:157] + "…"

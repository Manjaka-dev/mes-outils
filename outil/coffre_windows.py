# -*- coding: utf-8 -*-
"""Coffre de Windows (Gestionnaire d'identification) : un secret par « cible ».

Le secret n'est jamais écrit dans un fichier de l'outil ; on le retrouve dans
Panneau de configuration > Gestionnaire d'identification > Informations
d'identification Windows, sous le nom de sa cible (ex. « MesOutils:github »).
"""
import ctypes
from ctypes import wintypes


class _CREDENTIAL(ctypes.Structure):
    _fields_ = [
        ("Flags", wintypes.DWORD), ("Type", wintypes.DWORD), ("TargetName", wintypes.LPWSTR),
        ("Comment", wintypes.LPWSTR), ("LastWritten", wintypes.FILETIME),
        ("CredentialBlobSize", wintypes.DWORD), ("CredentialBlob", ctypes.POINTER(ctypes.c_char)),
        ("Persist", wintypes.DWORD), ("AttributeCount", wintypes.DWORD), ("Attributes", ctypes.c_void_p),
        ("TargetAlias", wintypes.LPWSTR), ("UserName", wintypes.LPWSTR),
    ]


_advapi = ctypes.WinDLL("advapi32", use_last_error=True)
_advapi.CredReadW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                              ctypes.POINTER(ctypes.POINTER(_CREDENTIAL))]
_advapi.CredWriteW.argtypes = [ctypes.POINTER(_CREDENTIAL), wintypes.DWORD]
_advapi.CredDeleteW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD]
_advapi.CredFree.argtypes = [ctypes.c_void_p]
CRED_TYPE_GENERIC, CRED_PERSIST_LOCAL_MACHINE = 1, 2


def ecrire(cible, utilisateur, secret):
    """Range (ou remplace) le secret de cette cible. Renvoie False en cas d'échec."""
    blob = secret.encode("utf-16-le")
    tampon = ctypes.create_string_buffer(blob, len(blob))
    cred = _CREDENTIAL()
    cred.Type = CRED_TYPE_GENERIC
    cred.TargetName = cible
    cred.UserName = utilisateur
    cred.CredentialBlobSize = len(blob)
    cred.CredentialBlob = ctypes.cast(tampon, ctypes.POINTER(ctypes.c_char))
    cred.Persist = CRED_PERSIST_LOCAL_MACHINE
    return bool(_advapi.CredWriteW(ctypes.byref(cred), 0))


def lire(cible):
    """Le secret de cette cible, ou None s'il n'y en a pas."""
    pcred = ctypes.POINTER(_CREDENTIAL)()
    if not _advapi.CredReadW(cible, CRED_TYPE_GENERIC, 0, ctypes.byref(pcred)):
        return None
    try:
        c = pcred.contents
        return ctypes.string_at(c.CredentialBlob, c.CredentialBlobSize).decode("utf-16-le")
    finally:
        _advapi.CredFree(pcred)


def supprimer(cible):
    _advapi.CredDeleteW(cible, CRED_TYPE_GENERIC, 0)

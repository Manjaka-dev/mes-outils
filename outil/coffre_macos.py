# -*- coding: utf-8 -*-
"""Secrets génériques de Mes outils dans le Trousseau macOS."""
import objc
import Security as sec


def _cible(cible):
    return {sec.kSecClass: sec.kSecClassGenericPassword,
            sec.kSecAttrService: "Mes outils", sec.kSecAttrAccount: cible}


def ecrire(cible, utilisateur, secret):
    with objc.autorelease_pool():
        recherche = _cible(cible)
        valeur = {sec.kSecValueData: secret.encode("utf-8")}
        statut, _ = sec.SecItemAdd({**recherche, **valeur}, None)
        if statut == sec.errSecDuplicateItem:
            statut = sec.SecItemUpdate(recherche, valeur)
        return statut == sec.errSecSuccess


def lire(cible):
    with objc.autorelease_pool():
        statut, valeur = sec.SecItemCopyMatching({**_cible(cible), sec.kSecReturnData: True}, None)
        if statut != sec.errSecSuccess:
            return None
        return bytes(valeur).decode("utf-8")


def supprimer(cible):
    with objc.autorelease_pool():
        statut = sec.SecItemDelete(_cible(cible))
        if statut not in (sec.errSecSuccess, sec.errSecItemNotFound):
            raise ValueError("Impossible de supprimer l’identifiant du Trousseau macOS.")

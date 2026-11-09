# -*- coding: utf-8 -*-
"""Onglet Temps : chronomètre de travail par projet et Pomodoro.

- Un seul chrono à la fois. Son état est gardé côté PC (donnees\\temps.json) :
  il survit à la fermeture de la page et au redémarrage de Mes outils.
- À l'arrêt, une session est créée : {id, projet, note, debut, fin, minutes},
  dates locales « YYYY-MM-DDTHH:MM ».
- Durées en minutes entières : minutes = fin − début, les deux heures étant
  prises à la minute (secondes ignorées). Ainsi la durée correspond toujours
  aux heures affichées (10:03 → 10:30 = 27 min). Un chrono arrêté avant la
  minute suivante ne crée pas de session.
- Pomodoro (facultatif, lié au chrono) : travail 25 min, pause courte 5 min,
  pause longue 15 min toutes les 4 périodes de travail (réglable :
  config.section("temps")). Chaque fin de période crée une alerte que la bulle
  affiche, comme les rappels. Les pauses restent comptées dans le chrono :
  l'arrêter pendant la pause si elles ne doivent pas être facturées.

Pour la bulle : alertes_dues(), marquer_alerte(id), etat().
"""
import csv
import datetime
import io
import re
import threading
import uuid

import config

NOM = "temps"
FORMAT = "%Y-%m-%dT%H:%M"
FORMAT_S = "%Y-%m-%dT%H:%M:%S"
DEFAUTS_POMODORO = {"travail": 25, "pause_courte": 5, "pause_longue": 15, "cycles": 4}
BORNES_POMODORO = {"travail": (1, 180), "pause_courte": (1, 60), "pause_longue": (1, 120), "cycles": (2, 12)}
PERIODES = ("jour", "semaine", "mois", "tout")
MAX_PROJET = 80
MAX_NOTE = 300
MAX_ALERTES = 20
ALERTE_PERIMEE = datetime.timedelta(hours=1)
MAX_SESSION = datetime.timedelta(hours=24)

_verrou = threading.RLock()

# Textes de la bulle et de l'export (la bulle n'a pas le dictionnaire de la page).
_ANGLAIS = {
    "Pause ! ☕": "Break time! ☕",
    "Grande pause ! 🌿": "Long break! 🌿",
    "Au travail ! 💪": "Back to work! 💪",
    "{projet} : {n} min de travail terminées. Pause de {p} min.": "{projet}: {n} min of work done. Take a {p} min break.",
    "{projet} : {c} périodes de travail d'affilée. Pause de {p} min.": "{projet}: {c} work periods in a row. Take a {p} min break.",
    "{projet} : période de travail n° {numero} ({n} min).": "{projet}: work period #{numero} ({n} min).",
    "Travail": "Work", "Pause courte": "Short break", "Pause longue": "Long break",
    "Date": "Date", "Début": "Start", "Fin": "End", "Projet": "Project", "Note": "Note",
    "Minutes": "Minutes", "Heures": "Hours", "Total": "Total", "Total par projet": "Total per project",
}
LIBELLES_PHASES = {"travail": "Travail", "pause_courte": "Pause courte", "pause_longue": "Pause longue"}


def _texte(fr, **valeurs):
    texte = _ANGLAIS.get(fr, fr) if config.langue() == "en" else fr
    return texte.format(**valeurs) if valeurs else texte


def maintenant():
    """L'heure locale (remplacée par une horloge simulée dans les tests)."""
    return datetime.datetime.now().replace(microsecond=0)


def _date(texte, nom="Date"):
    """« YYYY-MM-DDTHH:MM » (les secondes éventuelles sont ignorées)."""
    try:
        return datetime.datetime.strptime(str(texte or "")[:16], FORMAT)
    except ValueError:
        raise ValueError(f"{nom} invalide.") from None


def _a_la_minute(d):
    return d.replace(second=0, microsecond=0)


def _minutes(debut, fin):
    return int((_a_la_minute(fin) - _a_la_minute(debut)).total_seconds() // 60)


# ---------------------------------------------------------------------------
# Fichier et réglages
# ---------------------------------------------------------------------------
def _lire():
    d = config.lire_donnees(NOM, {})
    if not isinstance(d, dict):
        d = {}
    d.setdefault("sessions", [])
    d.setdefault("en_cours", None)
    d.setdefault("alertes", [])
    return d


def _ecrire(d):
    config.ecrire_donnees(NOM, d)


def reglages_pomodoro():
    sec = config.section("temps")
    r = {}
    for cle, defaut in DEFAUTS_POMODORO.items():
        try:
            valeur = int(sec.get(cle, defaut))
        except (TypeError, ValueError):
            valeur = defaut
        mini, maxi = BORNES_POMODORO[cle]
        r[cle] = min(max(valeur, mini), maxi)
    r["pomodoro_par_defaut"] = bool(sec.get("pomodoro_par_defaut", False))
    return r


def enregistrer_reglages(valeurs):
    propres = {}
    for cle, (mini, maxi) in BORNES_POMODORO.items():
        if cle in valeurs:
            try:
                n = int(valeurs[cle])
            except (TypeError, ValueError):
                raise ValueError("Durée invalide.") from None
            if not mini <= n <= maxi:
                raise ValueError(f"Valeur hors limites ({mini} à {maxi}).")
            propres[cle] = n
    if "pomodoro_par_defaut" in valeurs:
        propres["pomodoro_par_defaut"] = bool(valeurs["pomodoro_par_defaut"])
    config.modifier_section("temps", **propres)
    return reglages_pomodoro()


# ---------------------------------------------------------------------------
# Pomodoro
# ---------------------------------------------------------------------------
def _duree_phase(phase, r):
    return datetime.timedelta(minutes=r[phase])


def _fin_phase(pomo, r):
    return datetime.datetime.strptime(pomo["debut_phase"], FORMAT_S) + _duree_phase(pomo["phase"], r)


def _alerte_transition(projet, avant, apres, r):
    if avant["phase"] == "travail":
        if apres["phase"] == "pause_longue":
            titre = _texte("Grande pause ! 🌿")
            detail = _texte("{projet} : {c} périodes de travail d'affilée. Pause de {p} min.",
                            projet=projet, c=r["cycles"], p=r["pause_longue"])
        else:
            titre = _texte("Pause ! ☕")
            detail = _texte("{projet} : {n} min de travail terminées. Pause de {p} min.",
                            projet=projet, n=r["travail"], p=r["pause_courte"])
    else:
        titre = _texte("Au travail ! 💪")
        detail = _texte("{projet} : période de travail n° {numero} ({n} min).",
                        projet=projet, numero=apres["numero"], n=r["travail"])
    return {"id": uuid.uuid4().hex[:12], "titre": titre, "detail": detail,
            "quand": apres["debut_phase"], "vue": False}


def _avancer(d, a_l_heure):
    """Fait passer le Pomodoro aux périodes suivantes si l'heure est passée.
    Une seule alerte (la dernière) même si plusieurs périodes se sont
    écoulées (PC en veille). Renvoie True si quelque chose a changé."""
    en = d.get("en_cours")
    pomo = en and en.get("pomodoro")
    if not pomo:
        return False
    r = reglages_pomodoro()
    derniere = None
    for _ in range(500):
        fin = _fin_phase(pomo, r)
        if a_l_heure < fin:
            break
        avant = dict(pomo)
        if pomo["phase"] == "travail":
            pomo["phase"] = "pause_longue" if pomo["numero"] % r["cycles"] == 0 else "pause_courte"
        else:
            pomo["phase"] = "travail"
            pomo["numero"] += 1
        pomo["debut_phase"] = fin.strftime(FORMAT_S)
        derniere = (avant, dict(pomo))
    else:
        pomo["debut_phase"] = a_l_heure.strftime(FORMAT_S)
    if derniere is None:
        return False
    d["alertes"].append(_alerte_transition(en["projet"], *derniere, r))
    d["alertes"] = d["alertes"][-MAX_ALERTES:]
    return True


def _infos_pomodoro(pomo):
    if not pomo:
        return None
    r = reglages_pomodoro()
    return {"phase": pomo["phase"], "libelle": _texte(LIBELLES_PHASES[pomo["phase"]]),
            "numero": pomo["numero"], "debut_phase": pomo["debut_phase"],
            "fin_prevue": _fin_phase(pomo, r).strftime(FORMAT_S),
            "duree_minutes": r[pomo["phase"]], "cycles": r["cycles"]}


def _nouveau_pomodoro(a_l_heure):
    return {"phase": "travail", "numero": 1, "debut_phase": a_l_heure.strftime(FORMAT_S)}


# ---------------------------------------------------------------------------
# Pour la bulle
# ---------------------------------------------------------------------------
def alertes_dues():
    """Les alertes Pomodoro pas encore vues : [{id, titre, detail}].
    Une alerte de plus d'une heure est marquée vue sans être montrée."""
    with _verrou:
        d = _lire()
        a_l_heure = maintenant()
        change = _avancer(d, a_l_heure)
        dues = []
        for a in d["alertes"]:
            if a.get("vue"):
                continue
            try:
                quand = datetime.datetime.strptime(a.get("quand", ""), FORMAT_S)
            except ValueError:
                quand = a_l_heure
            if a_l_heure - quand > ALERTE_PERIMEE:
                a["vue"] = True
                change = True
                continue
            dues.append({"id": a["id"], "titre": a["titre"], "detail": a["detail"]})
        if change:
            _ecrire(d)
        return dues


def marquer_alerte(identifiant):
    """Alerte vue. Renvoie True si elle existait."""
    with _verrou:
        d = _lire()
        for a in d["alertes"]:
            if a["id"] == identifiant:
                a["vue"] = True
                _ecrire(d)
                return True
        return False


def etat():
    """Le chrono en cours : {en_cours: False} ou {en_cours: True, projet,
    note, depuis, secondes, pomodoro: None | {phase, libelle, numero,
    debut_phase, fin_prevue, duree_minutes, cycles}}."""
    with _verrou:
        d = _lire()
        a_l_heure = maintenant()
        if _avancer(d, a_l_heure):
            _ecrire(d)
        return _etat(d, a_l_heure)


def _etat(d, a_l_heure):
    en = d.get("en_cours")
    if not en:
        return {"en_cours": False}
    debut = datetime.datetime.strptime(en["debut"], FORMAT_S)
    return {"en_cours": True, "projet": en["projet"], "note": en.get("note", ""), "depuis": en["debut"],
            "secondes": max(0, int((a_l_heure - debut).total_seconds())),
            "pomodoro": _infos_pomodoro(en.get("pomodoro"))}


# ---------------------------------------------------------------------------
# Chrono
# ---------------------------------------------------------------------------
def _projet(valeur):
    projet = " ".join(str(valeur or "").split())[:MAX_PROJET]
    if not projet:
        raise ValueError("Indiquez un projet.")
    return projet


def _note(valeur):
    return str(valeur or "").strip()[:MAX_NOTE]


def demarrer(projet, note="", pomodoro=False):
    with _verrou:
        d = _lire()
        if d.get("en_cours"):
            raise ValueError(f"Un chrono tourne déjà sur « {d['en_cours']['projet']} » : arrêtez-le d'abord.")
        a_l_heure = maintenant()
        d["en_cours"] = {"projet": _projet(projet), "note": _note(note), "debut": a_l_heure.strftime(FORMAT_S),
                         "pomodoro": _nouveau_pomodoro(a_l_heure) if pomodoro else None}
        _ecrire(d)
        return _etat(d, a_l_heure)


def arreter(note=None):
    """Arrêter le chrono. Renvoie la session créée, ou None si elle a duré
    moins d'une minute."""
    with _verrou:
        d = _lire()
        en = d.get("en_cours")
        if not en:
            raise ValueError("Aucun chrono en cours.")
        a_l_heure = maintenant()
        _avancer(d, a_l_heure)
        debut = datetime.datetime.strptime(en["debut"], FORMAT_S)
        minutes = _minutes(debut, a_l_heure)
        session = None
        if minutes >= 1:
            session = {"id": uuid.uuid4().hex[:12], "projet": en["projet"],
                       "note": _note(en.get("note") if note is None else note),
                       "debut": debut.strftime(FORMAT), "fin": a_l_heure.strftime(FORMAT), "minutes": minutes}
            d["sessions"].append(session)
        d["en_cours"] = None
        _ecrire(d)
        return session


def modifier_en_cours(projet=None, note=None, pomodoro=None):
    """Changer le projet ou la note du chrono en cours, lancer ou arrêter son Pomodoro."""
    with _verrou:
        d = _lire()
        en = d.get("en_cours")
        if not en:
            raise ValueError("Aucun chrono en cours.")
        a_l_heure = maintenant()
        _avancer(d, a_l_heure)
        if projet is not None:
            en["projet"] = _projet(projet)
        if note is not None:
            en["note"] = _note(note)
        if pomodoro is not None:
            if pomodoro and not en.get("pomodoro"):
                en["pomodoro"] = _nouveau_pomodoro(a_l_heure)
            elif not pomodoro:
                en["pomodoro"] = None
        _ecrire(d)
        return _etat(d, a_l_heure)


# ---------------------------------------------------------------------------
# Sessions
# ---------------------------------------------------------------------------
def _valider_session(s):
    debut = _date(s.get("debut"), "Début")
    fin = _date(s.get("fin"), "Fin")
    if fin <= debut:
        raise ValueError("La fin doit être après le début.")
    if fin - debut > MAX_SESSION:
        raise ValueError("Une session ne peut pas dépasser 24 heures.")
    return {"projet": _projet(s.get("projet")), "note": _note(s.get("note")),
            "debut": debut.strftime(FORMAT), "fin": fin.strftime(FORMAT), "minutes": _minutes(debut, fin)}


def ajouter_session(session):
    """Ajout manuel d'une session oubliée."""
    propre = _valider_session(session or {})
    with _verrou:
        d = _lire()
        propre = {"id": uuid.uuid4().hex[:12], **propre}
        d["sessions"].append(propre)
        _ecrire(d)
        return propre


def modifier_session(session):
    propre = _valider_session(session or {})
    with _verrou:
        d = _lire()
        existante = next((s for s in d["sessions"] if s["id"] == (session or {}).get("id")), None)
        if existante is None:
            raise ValueError("Session introuvable.")
        existante.update(propre)
        _ecrire(d)
        return dict(existante)


def supprimer_session(identifiant):
    with _verrou:
        d = _lire()
        avant = len(d["sessions"])
        d["sessions"] = [s for s in d["sessions"] if s["id"] != identifiant]
        if len(d["sessions"]) != avant:
            _ecrire(d)
        return avant - len(d["sessions"])


def bornes(periode, reference=None):
    """(premier jour, jour suivant le dernier) de la période, ou (None, None)."""
    jour = reference or maintenant().date()
    if isinstance(jour, str):
        try:
            jour = datetime.date.fromisoformat(jour[:10])
        except ValueError:
            raise ValueError("Date invalide.") from None
    if periode == "jour":
        return jour, jour + datetime.timedelta(days=1)
    if periode == "semaine":
        lundi = jour - datetime.timedelta(days=jour.weekday())
        return lundi, lundi + datetime.timedelta(days=7)
    if periode == "mois":
        premier = jour.replace(day=1)
        suivant = (premier + datetime.timedelta(days=32)).replace(day=1)
        return premier, suivant
    if periode == "tout":
        return None, None
    raise ValueError("Période inconnue.")


def sessions(periode="semaine", reference=None):
    """Les sessions de la période (rangées par leur début), les plus récentes en tête."""
    debut, fin = bornes(periode, reference)
    with _verrou:
        toutes = _lire()["sessions"]
    choisies = [dict(s) for s in toutes
                if debut is None or debut.isoformat() <= s["debut"][:10] < fin.isoformat()]
    return sorted(choisies, key=lambda s: s["debut"], reverse=True)


def totaux(liste):
    """Minutes par projet, du plus long au plus court : [{projet, minutes}]."""
    par_projet = {}
    for s in liste:
        par_projet[s["projet"]] = par_projet.get(s["projet"], 0) + int(s.get("minutes") or 0)
    return [{"projet": p, "minutes": m} for p, m in sorted(par_projet.items(), key=lambda x: (-x[1], x[0].lower()))]


def projets_recents(limite=15):
    with _verrou:
        d = _lire()
    noms = []
    for s in sorted(d["sessions"], key=lambda s: s["debut"], reverse=True):
        if s["projet"] not in noms:
            noms.append(s["projet"])
    return noms[:limite]


# ---------------------------------------------------------------------------
# Export CSV (Excel en français : séparateur « ; », UTF-8 avec BOM)
# ---------------------------------------------------------------------------
_FORMULE = re.compile(r"^[=+@\t\r]|^-[^\s\-]")


def _cellule(valeur):
    """Un texte qu'Excel ne prendra pas pour une formule."""
    valeur = str(valeur or "")
    return "'" + valeur if _FORMULE.match(valeur) else valeur


def _heures(minutes):
    return f"{minutes / 60:.2f}".replace(".", ",")


def export_csv(periode="mois", reference=None):
    """{nom, csv} : le texte commence par le BOM UTF-8 (\\ufeff)."""
    liste = sorted(sessions(periode, reference), key=lambda s: s["debut"])
    sortie = io.StringIO()
    ecrivain = csv.writer(sortie, delimiter=";", lineterminator="\r\n")
    ecrivain.writerow([_texte(x) for x in ("Date", "Début", "Fin", "Projet", "Note", "Minutes", "Heures")])
    for s in liste:
        debut, fin = _date(s["debut"]), _date(s["fin"])
        ecrivain.writerow([debut.strftime("%d/%m/%Y"), debut.strftime("%H:%M"),
                           fin.strftime("%H:%M") if fin.date() == debut.date() else fin.strftime("%d/%m/%Y %H:%M"),
                           _cellule(s["projet"]), _cellule(s.get("note")), s["minutes"], _heures(s["minutes"])])
    total = sum(s["minutes"] for s in liste)
    ecrivain.writerow([])
    ecrivain.writerow([_texte("Total par projet")])
    for t in totaux(liste):
        ecrivain.writerow(["", "", "", _cellule(t["projet"]), "", t["minutes"], _heures(t["minutes"])])
    ecrivain.writerow([_texte("Total"), "", "", "", "", total, _heures(total)])
    debut, _ = bornes(periode, reference)
    suffixe = {"jour": "%Y-%m-%d", "semaine": "%Y-%m-%d", "mois": "%Y-%m"}.get(periode)
    nom = f"temps-{periode}-{debut.strftime(suffixe)}.csv" if debut else "temps-tout.csv"
    return {"nom": nom, "csv": "﻿" + sortie.getvalue()}


# ---------------------------------------------------------------------------
# Routes de la page
# ---------------------------------------------------------------------------
def _route_liste(d):
    periode = d.get("periode") or "semaine"
    debut, fin = bornes(periode, d.get("date"))
    liste = sessions(periode, d.get("date"))
    return {"etat": etat(), "sessions": liste, "totaux": totaux(liste),
            "total": sum(s["minutes"] for s in liste), "periode": periode,
            "debut": debut.isoformat() if debut else None,
            "fin": (fin - datetime.timedelta(days=1)).isoformat() if fin else None,
            "projets": projets_recents(), "reglages": reglages_pomodoro(),
            "maintenant": maintenant().strftime(FORMAT_S)}


ROUTES = {
    "liste": _route_liste,
    "etat": lambda d: etat(),
    "demarrer": lambda d: demarrer(d.get("projet"), d.get("note") or "", bool(d.get("pomodoro"))),
    "arreter": lambda d: {"session": arreter(d.get("note")), "etat": etat()},
    "en_cours": lambda d: modifier_en_cours(d.get("projet"), d.get("note"), d.get("pomodoro")),
    "ajouter": lambda d: ajouter_session(d.get("session")),
    "modifier": lambda d: modifier_session(d.get("session")),
    "supprimer": lambda d: {"supprimes": supprimer_session(d.get("id"))},
    "export": lambda d: export_csv(d.get("periode") or "mois", d.get("date")),
    "reglages": lambda d: enregistrer_reglages(d),
    "alertes": lambda d: {"alertes": alertes_dues()},
    "marquer_alerte": lambda d: {"ok": marquer_alerte(d.get("id"))},
}

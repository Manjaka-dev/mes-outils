"use strict";
/* Onglet « Projets » : les projets de développement de ce PC, leurs serveurs
   de dev (démarrer, arrêter, journal), leur état Git et leurs fichiers .env
   (sauvegardés dans le coffre chiffré). Voir projets.py. */
(() => {
  I18N.ajouter({
    "Impossible d’ouvrir le dossier du projet.": "Could not open the project folder.",
    "VS Code est introuvable.": "VS Code could not be found.",
    "Impossible d’identifier le processus lancé.": "Could not identify the process that was started.",
    "Impossible d’arrêter le serveur de développement.": "Could not stop the development server.",
    "Le groupe du serveur ne s’est pas arrêté.": "The server’s process group did not stop.",
    "Aucune commande de dev": "No dev command",
    "Local": "Local",
    "Pas de branche distante : rien à comparer": "No remote branch: nothing to compare",
    "Pas de dépôt Git": "No Git repository",
    "Lecture de l'état Git…": "Reading Git status…",
    "Projets": "Projects",
    "Rechercher un projet…": "Search a project…",
    "Tous": "All",
    "En marche": "Running",
    "À envoyer": "To push",
    "Modifiés": "Changed",
    "En retard": "Behind",
    "Masqués": "Hidden",
    "＋ Ajouter un projet": "＋ Add a project",
    "Ajouter un projet": "Add a project",
    "Choisir le dossier du projet": "Choose the project folder",
    "Projet ajouté": "Project added",
    "🔄 Tout vérifier": "🔄 Check all",
    "Vérification…": "Checking…",
    "Récupère les nouveautés de tous les dépôts (git fetch)": "Fetch news from all repositories (git fetch)",
    "Relire": "Reload",
    "Lecture des projets…": "Reading projects…",
    "Aucun projet trouvé pour l'instant.": "No project found yet.",
    "Indiquez vos dossiers de projets dans les Réglages : l'outil y cherche les dossiers qui contiennent un projet (.git, package.json, manage.py…).":
      "Set your project folders in Settings: the tool looks there for folders that contain a project (.git, package.json, manage.py…).",
    "Ouvrir les Réglages": "Open Settings",
    "Aucun projet ne correspond.": "No project matches.",
    "Dossier": "Folder",
    "VS Code": "VS Code",
    "Terminal": "Terminal",
    "Commandes": "Commands",
    "Ouvrir le dossier": "Open the folder",
    "Ouvrir dans VS Code": "Open in VS Code",
    "Ouvrir un terminal dans le dossier": "Open a terminal in the folder",
    "Serveurs de dev et autres commandes": "Dev servers and other commands",
    "Fichiers .env ↔ coffre": ".env files ↔ vault",
    "Récupérer (fetch)": "Fetch",
    "Masquer ce projet": "Hide this project",
    "Afficher ce projet": "Show this project",
    "Retirer de la liste": "Remove from the list",
    "Projet masqué": "Project hidden",
    "Projet de nouveau affiché": "Project shown again",
    "Retirer ce projet ?": "Remove this project?",
    "Il disparaît de la liste. Le dossier n'est pas touché.": "It disappears from the list. The folder is not touched.",
    "Retirer": "Remove",
    "📂 Dossier ouvert": "📂 Folder opened",
    "💻 VS Code s'ouvre…": "💻 VS Code is opening…",
    "⌨️ Terminal ouvert": "⌨️ Terminal opened",
    "Ajouté à la main": "Added manually",
    // Git
    "À jour": "Up to date",
    "{n} à envoyer": "{n} to push",
    "{n} à récupérer": "{n} to pull",
    "{n} modifié(s)": "{n} changed",
    "{n} non suivi(s)": "{n} untracked",
    "{n} conflit(s)": "{n} conflict(s)",
    "pas de branche distante": "no remote branch",
    "aucun commit": "no commit",
    "HEAD détachée": "detached HEAD",
    "Commits à envoyer (push)": "Commits to push",
    "Commits à récupérer (pull)": "Commits to pull",
    "Fichiers modifiés ou nouveaux": "Changed or new files",
    "Récupération…": "Fetching…",
    "✅ {nom} : à jour": "✅ {nom}: up to date",
    "⬇️ {nom} : {n} commit(s) à récupérer": "⬇️ {nom}: {n} commit(s) to pull",
    "✅ {n} dépôts vérifiés": "✅ {n} repositories checked",
    "{n} dépôts vérifiés, {e} en erreur": "{n} repositories checked, {e} with errors",
    "Vérifié à {h}": "Checked at {h}",
    // Commandes
    "Démarrer": "Start",
    "Arrêter": "Stop",
    "Redémarrer": "Restart",
    "Journal": "Logs",
    "Ouvrir le site": "Open the site",
    "en marche": "running",
    "démarrage…": "starting…",
    "arrêté": "stopped",
    "port occupé": "port in use",
    "Le port répond, mais le programme n'a pas été lancé par Mes outils.": "The port answers, but the program was not started by Mes outils.",
    "arrêté (code {c})": "stopped (code {c})",
    "▶ {nom} démarre…": "▶ {nom} is starting…",
    "⏹ {nom} arrêté": "⏹ {nom} stopped",
    "Arrêter « {nom} » ?": "Stop “{nom}”?",
    "Le processus lancé par Mes outils et tous ses sous-processus sont arrêtés.": "The process started by Mes outils and all its subprocesses are stopped.",
    "💡 {n} commande(s) proposée(s)": "💡 {n} suggested command(s)",
    "Configurer": "Set up",
    "Commandes de « {nom} »": "Commands of “{nom}”",
    "Chaque commande est lancée dans le dossier du projet, sans fenêtre. Sa sortie va dans le journal.":
      "Each command runs in the project folder, without a window. Its output goes to the logs.",
    "Nom": "Name",
    "Commande": "Command",
    "Port": "Port",
    "Adresse": "Address",
    "ex. npm run dev": "e.g. npm run dev",
    "ex. Front": "e.g. Front",
    "ex. 5173": "e.g. 5173",
    "ex. http://localhost:5173": "e.g. http://localhost:5173",
    "Supprimer": "Delete",
    "＋ Ajouter une commande": "＋ Add a command",
    "Proposées d'après le projet :": "Suggested from the project:",
    "Aucune commande pour l'instant.": "No command yet.",
    "Annuler": "Cancel",
    "Enregistrer": "Save",
    "Commandes enregistrées": "Commands saved",
    "Journal de {nom}": "Logs of {nom}",
    "300 dernières lignes, mises à jour toutes les 2 secondes": "Last 300 lines, refreshed every 2 seconds",
    "Journal vide.": "Empty log.",
    "Copier": "Copy",
    "Lecture…": "Reading…",
    "Fermer": "Close",
    // .env
    "Fichiers .env de « {nom} »": ".env files of “{nom}”",
    "Le contenu est rangé, chiffré, dans le coffre de l'onglet Mots de passe (catégorie « env »).":
      "The content is stored, encrypted, in the vault of the Passwords tab (category “env”).",
    "🔐 Sauvegarder dans le coffre": "🔐 Save to the vault",
    "Restaurer": "Restore",
    "Aucun fichier .env dans ce projet.": "No .env file in this project.",
    "absent du dossier": "missing from the folder",
    "sauvegardé le {d}": "saved on {d}",
    "pas encore sauvegardé": "not saved yet",
    "Le coffre est verrouillé.": "The vault is locked.",
    "Ouvrez d'abord le coffre dans l'onglet Mots de passe.": "First open the vault in the Passwords tab.",
    "Ouvrir l'onglet Mots de passe": "Open the Passwords tab",
    "🔐 {n} fichier(s) sauvegardé(s) dans le coffre": "🔐 {n} file(s) saved to the vault",
    "Restaurer {f} ?": "Restore {f}?",
    "Le fichier est réécrit avec la version du coffre. L'ancien est gardé en {f}.bak.":
      "The file is rewritten with the vault version. The old one is kept as {f}.bak.",
    "Le fichier est recréé avec la version du coffre.": "The file is recreated with the vault version.",
    "↩️ {f} restauré": "↩️ {f} restored",
    // Messages du serveur
    "Projet inconnu.": "Unknown project.",
    "Projet introuvable : le dossier a peut-être été déplacé.": "Project not found: the folder may have been moved.",
    "Dossier introuvable.": "Folder not found.",
    "Commande inconnue.": "Unknown command.",
    "Commande invalide.": "Invalid command.",
    "Donnez un nom à chaque commande.": "Give each command a name.",
    "Liste de commandes invalide.": "Invalid command list.",
    "Adresse invalide : elle doit commencer par http:// ou https://.": "Invalid address: it must start with http:// or https://.",
    "Aucune adresse pour cette commande.": "No address for this command.",
    "Arrêtez d'abord une commande en marche avant de la supprimer.": "Stop a running command before deleting it.",
    "Le dossier du projet est introuvable.": "The project folder was not found.",
    "Cette commande est déjà en marche.": "This command is already running.",
    "Cette commande n'est pas en marche (ou n'a pas été lancée par Mes outils).": "This command is not running (or was not started by Mes outils).",
    "Ce processus n'a pas été lancé par Mes outils : il n'est pas arrêté.": "This process was not started by Mes outils: it is not stopped.",
    "Action inconnue.": "Unknown action.",
    "Ce projet n'est pas un dépôt Git.": "This project is not a Git repository.",
    "Git n'est pas installé sur ce PC.": "Git is not installed on this PC.",
    "Git met trop de temps à répondre.": "Git takes too long to answer.",
    "git a échoué.": "git failed.",
    "git fetch a échoué.": "git fetch failed.",
    "Le serveur Git ne répond pas (délai dépassé).": "The Git server is not responding (timeout).",
    "Serveur Git injoignable ou accès refusé.": "Git server unreachable or access denied.",
    "Accès refusé : connectez-vous une fois avec git dans un terminal.": "Access denied: sign in once with git in a terminal.",
    "Fichier .env invalide.": "Invalid .env file.",
    "Le dossier de ce fichier n'existe plus.": "The folder of this file no longer exists.",
    "VS Code est introuvable sur ce PC.": "VS Code was not found on this PC.",
  });
  I18N.motifs([
    [/^Commande invalide : (.*)$/, "Invalid command: $1"],
    [/^Port invalide : (.*)$/, "Invalid port: $1"],
    [/^Le port (\d+) est déjà utilisé par un autre programme\.$/, "Port $1 is already used by another program."],
    [/^Impossible de lancer la commande : (.*)$/, "Unable to start the command: $1"],
    [/^Fichier introuvable : (.*)$/, "File not found: $1"],
    [/^Fichier trop gros pour le coffre : (.*)$/, "File too big for the vault: $1"],
    [/^Fichier illisible \(pas en UTF-8\) : (.*)$/, "Unreadable file (not UTF-8): $1"],
    [/^Aucune sauvegarde de (.*) dans le coffre\.$/, "No backup of $1 in the vault."],
  ]);

  const style = document.createElement("style");
  style.textContent = `
    /* Grille : cartes de même hauteur sur une rangée, chaque ligne à la même
       place d'une carte à l'autre, boutons toujours en bas. */
    .pj-liste { display: grid; grid-template-columns: repeat(auto-fill, minmax(430px, 1fr)); gap: 14px; align-items: stretch; }
    .pj-carte { background: var(--carte); border: 1px solid var(--bord); border-radius: var(--rayon); box-shadow: var(--ombre); padding: 16px 16px 14px; display: flex; flex-direction: column; gap: 9px; animation: apparait .3s both; min-width: 0; transition: box-shadow .2s, transform .2s; }
    .pj-carte:hover { box-shadow: var(--ombre-forte); }
    .pj-carte .pj-mini.masquer { opacity: 0; transition: opacity .15s; }
    .pj-carte:hover .pj-mini.masquer, .pj-carte.masque .pj-mini.masquer { opacity: 1; }
    .pj-milieu { display: flex; flex-direction: column; gap: 9px; flex: 1; }
    .pj-types { min-height: 20px; }
    .pj-aucune { font-size: 12.5px; color: var(--gris); }
    .pj-carte.masque { opacity: .6; }
    .pj-l1 { display: flex; align-items: center; gap: 10px; min-width: 0; }
    .pj-ic { width: 40px; height: 40px; border-radius: 13px; display: grid; place-items: center; font-size: 21px; background: var(--violet-clair); flex: none; }
    .pj-titre { flex: 1; min-width: 0; }
    .pj-nom { font-weight: 600; font-size: 15px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .pj-chemin { font-size: 12px; color: var(--doux); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; direction: rtl; text-align: left; }
    .pj-types { display: flex; gap: 4px; flex-wrap: wrap; }
    .pj-type { font-size: 11px; font-weight: 700; border-radius: 99px; padding: 1px 8px; background: var(--surface); color: var(--doux); }
    .pj-badges { display: flex; gap: 4px; flex: none; }
    .pj-badge { font-size: 12px; font-weight: 600; border-radius: 99px; padding: 3px 9px; white-space: nowrap; }
    .pj-badge.ok { background: var(--vert-clair); color: var(--vert-texte); }
    .pj-badge.envoi { background: var(--ambre-clair); color: var(--ambre-texte); }
    .pj-badge.retard { background: var(--bleu-clair); color: var(--bleu-texte); }
    .pj-badge.modif { background: var(--violet-clair); color: var(--violet); }
    .pj-badge.err { background: var(--rouge-clair); color: var(--rouge-texte); }
    .pj-git { font-size: 12.5px; color: var(--doux); display: flex; gap: 10px; flex-wrap: wrap; align-items: center; }
    .pj-git b { color: var(--encre); font-weight: 700; }
    .pj-git .err { color: var(--rouge-texte); }
    .pj-cmds { display: flex; flex-direction: column; gap: 4px; }
    .pj-cmd { display: flex; align-items: center; gap: 8px; background: var(--surface); border-radius: 12px; padding: 4px 6px 4px 10px; min-width: 0; }
    .pj-cmd .n { font-weight: 700; font-size: 13.5px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .pj-cmd .e { font-size: 12px; color: var(--doux); white-space: nowrap; flex: 1; }
    .pj-cmd .icone-btn { width: 30px; height: 30px; font-size: 13.5px; background: var(--carte); }
    .pj-propose { font-size: 12.5px; color: var(--doux); display: flex; align-items: center; gap: 8px; }
    .pj-actions { display: flex; gap: 6px; flex-wrap: nowrap; align-items: center; padding-top: 10px; border-top: 1px solid var(--ligne); }
    .pj-actions .btn { padding: 6px 10px; font-size: 12.5px; gap: 5px; box-shadow: none; background: var(--surface); }
    .pj-actions .btn:hover { background: var(--violet-clair); color: var(--violet); }
    .pj-icones { display: flex; gap: 4px; margin-left: auto; flex: none; }
    .pj-actions .icone-btn { width: 32px; height: 32px; font-size: 14px; background: var(--surface); }
    .pj-mini { border: 0; background: transparent; color: var(--gris); cursor: pointer; border-radius: 9px; width: 26px; height: 26px; font-size: 13px; display: grid; place-items: center; flex: none; }
    .pj-mini:hover { background: var(--violet-clair); color: var(--violet); }
    .pj-puces { flex-wrap: wrap; }
    .pj-puce-n { margin-left: 5px; opacity: .75; }
    .pj-edit { display: grid; grid-template-columns: 1.1fr 2fr .7fr 1.6fr auto; gap: 6px; align-items: center; margin-bottom: 6px; }
    .pj-edit input { border: 1.5px solid var(--ligne); border-radius: 10px; padding: 7px 9px; background: var(--champ); color: var(--encre); outline: none; font: inherit; font-size: 13px; min-width: 0; }
    .pj-edit input:focus { border-color: var(--violet); background: var(--champ-focus); }
    .pj-edit input.mono { font-family: var(--mono); font-size: 12.5px; }
    .pj-entetes { display: grid; grid-template-columns: 1.1fr 2fr .7fr 1.6fr 34px; gap: 6px; font-size: 11.5px; font-weight: 700; color: var(--doux); margin-bottom: 4px; }
    .pj-sugg { display: flex; gap: 6px; flex-wrap: wrap; margin: 8px 0 4px; }
    .pj-sugg button { border: 1.5px dashed var(--ligne); background: var(--surface); color: var(--encre); border-radius: 10px; padding: 5px 10px; cursor: pointer; font-size: 12.5px; font-family: var(--mono); }
    .pj-sugg button:hover { border-color: var(--violet); color: var(--violet); }
    .pj-journal { background: var(--code); color: var(--code-texte); font-family: var(--mono); font-size: 12px; line-height: 1.45; border-radius: 12px; padding: 10px 12px; height: min(58vh, 520px); overflow: auto; white-space: pre-wrap; word-break: break-all; margin: 0; text-align: left; }
    .pj-sous { font-size: 12.5px; color: var(--doux); margin: -4px 0 10px; display: flex; gap: 8px; align-items: center; }
    .pj-env { display: flex; flex-direction: column; gap: 6px; margin: 6px 0 4px; }
    .pj-env div { display: flex; align-items: center; gap: 10px; background: var(--surface); border-radius: 12px; padding: 8px 10px; font-size: 13.5px; }
    .pj-env code { font-family: var(--mono); font-weight: 700; color: var(--encre); }
    .pj-env small { flex: 1; color: var(--doux); }
    .pj-alerte { background: var(--ambre-clair); color: var(--ambre-texte); border-radius: 12px; padding: 10px 12px; font-size: 13.5px; display: flex; gap: 10px; align-items: center; flex-wrap: wrap; margin-bottom: 8px; }
  `;
  document.head.append(style);

  const P = { projets: null, git: {}, filtre: "tous", recherche: "", minuterie: null, verification: false };
  const racine = () => $("#vue-projets");
  const actif = () => racine()?.classList.contains("actif");
  const heure = iso => iso ? new Date(iso).toLocaleTimeString(I18N.locale(), { hour: "2-digit", minute: "2-digit" }) : "";
  const date = iso => iso ? new Date(iso).toLocaleString(I18N.locale(), { day: "numeric", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" }) : "";

  async function appel(action, donnees, message) {
    try {
      const r = await api("/api/projets/" + action, donnees || {});
      if (message) toast(message, "succes");
      return r;
    } catch (e) { toast("😕 " + e.message, "erreur", 7000); return null; }
  }

  // -- affichage ---------------------------------------------------------------
  async function afficher() {
    if (!P.projets) racine().replaceChildren(el("div", { class: "vide" }, el("span", { class: "attente" }, "⏳"), " ", "Lecture des projets…"));
    let r;
    try { r = await api("/api/projets/liste", {}); }
    catch (e) { racine().replaceChildren(el("div", { class: "vide" }, "😕 " + e.message)); return; }
    P.projets = r.projets;
    P.infos = r;
    dessiner();
    suivre();
    try { Object.assign(P.git, (await api("/api/projets/git/etats", {})).git); dessinerListe(); } catch {}
  }

  /** Tant que l'onglet est affiché : état des commandes toutes les 3 secondes. */
  function suivre() {
    clearInterval(P.minuterie);
    P.minuterie = setInterval(async () => {
      if (!actif()) { clearInterval(P.minuterie); return; }
      let r;
      try { r = await api("/api/projets/etats", {}); } catch { return; }
      let change = false;
      for (const s of r.serveurs) {
        const p = P.projets.find(x => x.id === s.projet_id);
        const c = p?.commandes.find(x => x.id === s.id);
        if (c && c.etat.etat !== s.etat) { c.etat = { etat: s.etat }; change = true; }
      }
      if (change) dessinerListe();
    }, 3000);
  }

  const gitDe = p => P.git[p.id] || null;
  const enMarche = p => p.commandes.some(c => ["marche", "demarrage"].includes(c.etat.etat));
  const FILTRES = [
    ["tous", "Tous", p => !p.masque],
    ["marche", "En marche", p => !p.masque && enMarche(p)],
    ["envoi", "À envoyer", p => !p.masque && (gitDe(p)?.avance > 0)],
    ["modifs", "Modifiés", p => !p.masque && ((gitDe(p)?.modifies || 0) + (gitDe(p)?.non_suivis || 0) + (gitDe(p)?.conflits || 0) > 0)],
    ["retard", "En retard", p => !p.masque && (gitDe(p)?.retard > 0)],
    ["masques", "Masqués", p => p.masque],
  ];

  function dessiner() {
    const recherche = el("input", { placeholder: "Rechercher un projet…", value: P.recherche,
      oninput: e => { P.recherche = e.target.value; dessinerListe(); } });
    const verifier = el("button", { class: "btn", id: "pj-verifier", title: "Récupère les nouveautés de tous les dépôts (git fetch)", onclick: toutVerifier },
      P.verification ? [el("span", { class: "attente" }, "⏳"), " ", t("Vérification…")] : "🔄 Tout vérifier");
    verifier.disabled = P.verification;
    racine().replaceChildren(
      el("div", { class: "barre-vue" },
        el("h2", {}, "📦 " + t("Projets"), " ", el("span", { class: "compte" }, String(P.projets.filter(p => !p.masque).length))),
        el("div", { class: "champ-recherche" }, el("span", {}, "🔍"), recherche),
        el("div", { class: "espace" }),
        verifier,
        el("button", { class: "btn principal", onclick: ajouterProjet }, "＋ Ajouter un projet"),
        el("button", { class: "icone-btn", title: "Relire", onclick: afficher }, "🔄")),
      el("div", { class: "puces pj-puces", id: "pj-puces", style: "margin:-6px 0 16px" }),
      el("div", { id: "pj-zone" }));
    dessinerListe();
  }

  function dessinerListe() {
    const puces = $("#pj-puces"), zone = $("#pj-zone");
    if (!puces || !zone) return;
    puces.replaceChildren(...FILTRES.filter(([v, , f]) => v !== "masques" || P.projets.some(f)).map(([v, libelle, f]) => {
      const n = P.projets.filter(f).length;
      return el("button", { class: "puce" + (P.filtre === v ? " actif" : ""), onclick: () => { P.filtre = v; dessinerListe(); } },
        libelle, v !== "tous" && n ? el("span", { class: "pj-puce-n" }, String(n)) : null);
    }));
    if (!P.projets.length) {
      zone.replaceChildren(el("div", { class: "vide" },
        el("p", { style: "margin-top:0" }, "📁 " + t("Aucun projet trouvé pour l'instant.")),
        el("p", {}, "Indiquez vos dossiers de projets dans les Réglages : l'outil y cherche les dossiers qui contiennent un projet (.git, package.json, manage.py…)."),
        el("button", { class: "btn principal", onclick: () => montrerVue("reglages") }, "Ouvrir les Réglages")));
      return;
    }
    const filtre = (FILTRES.find(f => f[0] === P.filtre) || FILTRES[0])[2];
    const q = P.recherche.trim().toLowerCase();
    const liste = P.projets.filter(filtre).filter(p => !q || `${p.nom} ${p.chemin} ${p.types.join(" ")} ${gitDe(p)?.branche || ""}`.toLowerCase().includes(q));
    zone.replaceChildren(liste.length ? el("div", { class: "pj-liste" }, liste.map(carte)) : el("div", { class: "vide" }, "Aucun projet ne correspond."));
  }

  // -- carte -------------------------------------------------------------------
  function badgesGit(g) {
    if (!g) return [];
    if (g.erreur) return [el("span", { class: "pj-badge err", title: g.erreur }, "⚠️ Git")];
    const b = [];
    const modifs = (g.modifies || 0) + (g.non_suivis || 0) + (g.conflits || 0);
    if (g.avance) b.push(el("span", { class: "pj-badge envoi", title: "Commits à envoyer (push)" }, `⬆️ ${g.avance}`));
    if (g.retard) b.push(el("span", { class: "pj-badge retard", title: "Commits à récupérer (pull)" }, `⬇️ ${g.retard}`));
    if (modifs) b.push(el("span", { class: "pj-badge modif", title: "Fichiers modifiés ou nouveaux" }, `✏️ ${modifs}`));
    // « À jour » seulement s'il y a une branche distante à comparer.
    if (!b.length && !g.erreur_fetch) b.push(g.amont && !g.sans_commit
      ? el("span", { class: "pj-badge ok" }, "✓ " + t("À jour"))
      : el("span", { class: "pj-badge", style: "background:var(--surface);color:var(--doux)", title: "Pas de branche distante : rien à comparer" }, "💾 " + t("Local")));
    if (g.erreur_fetch) b.push(el("span", { class: "pj-badge err", title: g.erreur_fetch }, "⚠️"));
    return b;
  }

  function ligneGit(p) {
    const g = gitDe(p);
    if (!p.git || !g) return null;
    if (g.erreur) return el("div", { class: "pj-git" }, el("span", { class: "err" }, "⚠️ " + I18N.traduire(g.erreur)));
    const morceaux = [el("span", {}, "🌿 ", el("b", {}, g.branche || t("HEAD détachée")))];
    if (g.sans_commit) morceaux.push(el("span", {}, t("aucun commit")));
    else if (!g.amont) morceaux.push(el("span", {}, t("pas de branche distante")));
    if (g.avance) morceaux.push(el("span", {}, t("{n} à envoyer", { n: g.avance })));
    if (g.retard) morceaux.push(el("span", {}, t("{n} à récupérer", { n: g.retard })));
    if (g.modifies) morceaux.push(el("span", {}, t("{n} modifié(s)", { n: g.modifies })));
    if (g.non_suivis) morceaux.push(el("span", {}, t("{n} non suivi(s)", { n: g.non_suivis })));
    if (g.conflits) morceaux.push(el("span", { class: "err" }, t("{n} conflit(s)", { n: g.conflits })));
    if (g.erreur_fetch) morceaux.push(el("span", { class: "err" }, "⚠️ " + I18N.traduire(g.erreur_fetch)));
    else if (g.verifie) morceaux.push(el("span", {}, t("Vérifié à {h}", { h: heure(g.verifie) })));
    return el("div", { class: "pj-git" }, morceaux);
  }

  const LIBELLES = { marche: "en marche", demarrage: "démarrage…", arrete: "arrêté", occupe: "port occupé" };

  function ligneCommande(p, c) {
    const e = c.etat.etat;
    const vivant = e === "marche" || e === "demarrage";
    const texte = e === "arrete" && c.etat.code_sortie ? t("arrêté (code {c})", { c: c.etat.code_sortie }) : t(LIBELLES[e] || e);
    return el("div", { class: "pj-cmd", title: c.commande },
      el("span", { class: "point " + (e === "arrete" ? "" : e) }),
      el("span", { class: "n" }, c.nom),
      el("span", { class: "e", ...(e === "occupe" ? { title: "Le port répond, mais le programme n'a pas été lancé par Mes outils." } : {}) },
        texte + (c.port ? ` · :${c.port}` : "")),
      vivant
        ? el("button", { class: "icone-btn stop", title: "Arrêter", onclick: () => arreter(p, c) }, "⏹")
        : el("button", { class: "icone-btn go", title: "Démarrer", disabled: e === "occupe", onclick: () => demarrer(p, c) }, "▶"),
      c.url ? el("button", { class: "icone-btn", title: "Ouvrir le site", disabled: !(e === "marche" || e === "occupe"),
        onclick: () => appel("ouvrir/site", { projet: p.id, commande: c.id }) }, "🌐") : null,
      el("button", { class: "icone-btn", title: "Journal", onclick: () => journal(p, c) }, "📜"));
  }

  function carte(p, i) {
    const cmds = p.commandes.length
      ? el("div", { class: "pj-cmds" }, p.commandes.map(c => ligneCommande(p, c)))
      : p.proposees.length
        ? el("div", { class: "pj-propose" }, t("💡 {n} commande(s) proposée(s)", { n: p.proposees.length }),
            el("button", { class: "btn discret", style: "padding:4px 10px", onclick: () => editerCommandes(p) }, "Configurer"))
        : el("div", { class: "pj-aucune" }, "Aucune commande de dev");
    const actions = [
      el("button", { class: "btn", title: "Ouvrir le dossier", onclick: () => appel("ouvrir/dossier", { projet: p.id }, "📂 Dossier ouvert") }, "📂 " + t("Dossier")),
      P.infos.vscode ? el("button", { class: "btn", title: "Ouvrir dans VS Code", onclick: () => appel("ouvrir/vscode", { projet: p.id }, "💻 VS Code s'ouvre…") }, "💻 VS Code") : null,
      el("button", { class: "btn", title: "Ouvrir un terminal dans le dossier", onclick: () => appel("ouvrir/terminal", { projet: p.id }, "⌨️ Terminal ouvert") }, "⌨️ " + t("Terminal")),
      el("div", { class: "pj-icones" },
        el("button", { class: "icone-btn", title: "Serveurs de dev et autres commandes", onclick: () => editerCommandes(p) }, "⚙️"),
        p.env ? el("button", { class: "icone-btn", title: "Fichiers .env ↔ coffre", onclick: () => fenetreEnv(p) }, "🔐") : null,
        p.git ? el("button", { class: "icone-btn", title: "Récupérer (fetch)", onclick: ev => fetch1(p, ev.currentTarget) }, "🔄") : null)];
    return el("div", { class: "pj-carte" + (p.masque ? " masque" : ""), style: `animation-delay:${Math.min(i, 20) * 20}ms` },
      el("div", { class: "pj-l1" },
        el("div", { class: "pj-ic" }, p.icone),
        el("div", { class: "pj-titre" },
          el("div", { class: "pj-nom", title: p.nom }, p.nom),
          el("div", { class: "pj-chemin", title: p.chemin }, el("bdi", {}, p.chemin))),
        el("div", { class: "pj-badges" }, badgesGit(gitDe(p))),
        el("button", { class: "pj-mini masquer", title: p.masque ? "Afficher ce projet" : "Masquer ce projet", onclick: () => masquer(p) }, p.masque ? "👁️" : "🙈"),
        p.manuel ? el("button", { class: "pj-mini", title: "Retirer de la liste", onclick: () => retirer(p) }, "✕") : null),
      el("div", { class: "pj-milieu" },
        el("div", { class: "pj-types" },
          p.types.slice(0, 4).map(ty => el("span", { class: "pj-type" }, ty)),
          p.manuel ? el("span", { class: "pj-type" }, "Ajouté à la main") : null),
        ligneGit(p) || el("div", { class: "pj-git" }, el("span", { class: "pj-aucune" }, p.git ? "Lecture de l'état Git…" : "Pas de dépôt Git")),
        cmds),
      el("div", { class: "pj-actions" }, actions));
  }

  // -- actions -----------------------------------------------------------------
  async function ajouterProjet() {
    const chemin = await choisirDossier("Choisir le dossier du projet");
    if (!chemin) return;
    if (await appel("ajouter", { chemin }, "Projet ajouté")) afficher();
  }

  async function masquer(p) {
    const r = await appel("masquer", { projet: p.id, masque: !p.masque });
    if (!r) return;
    p.masque = r.masque;
    toast(r.masque ? "🙈 " + t("Projet masqué") : "👁️ " + t("Projet de nouveau affiché"), "succes");
    dessiner();
  }

  async function retirer(p) {
    if (!(await confirmer("✕", "Retirer ce projet ?", "Il disparaît de la liste. Le dossier n'est pas touché.", "Retirer"))) return;
    if (await appel("retirer", { projet: p.id })) afficher();
  }

  async function fetch1(p, bouton) {
    bouton.disabled = true;
    bouton.replaceChildren(el("span", { class: "attente" }, "⏳"));
    const r = await appel("git/fetch", { projet: p.id });
    if (r) {
      P.git[p.id] = r.git;
      if (r.git.erreur_fetch) toast("😕 " + I18N.traduire(r.git.erreur_fetch), "erreur", 7000);
      else if (r.git.retard) toast(t("⬇️ {nom} : {n} commit(s) à récupérer", { nom: p.nom, n: r.git.retard }), "succes", 4000);
      else toast(t("✅ {nom} : à jour", { nom: p.nom }), "succes");
    }
    dessinerListe();
  }

  async function toutVerifier() {
    P.verification = true;
    dessiner();
    const r = await appel("git/tout_verifier", {});
    P.verification = false;
    if (r) {
      Object.assign(P.git, r.git);
      const n = Object.keys(r.git).length;
      if (r.erreurs) toast("⚠️ " + t("{n} dépôts vérifiés, {e} en erreur", { n, e: r.erreurs }), "erreur", 6000);
      else toast(t("✅ {n} dépôts vérifiés", { n }), "succes");
    }
    if (actif()) dessiner();
  }

  async function demarrer(p, c) {
    const r = await appel("commande", { projet: p.id, commande: c.id, action: "demarrer" });
    if (!r) return;
    c.etat = { etat: r.etat, code_sortie: r.code_sortie };
    toast(t("▶ {nom} démarre…", { nom: c.nom }), "succes");
    dessinerListe();
  }

  async function arreter(p, c, apres) {
    if (!(await confirmer("⏹", t("Arrêter « {nom} » ?", { nom: c.nom }),
      "Le processus lancé par Mes outils et tous ses sous-processus sont arrêtés.", "Arrêter"))) { if (apres) apres(); return; }
    const r = await appel("commande", { projet: p.id, commande: c.id, action: "arreter" });
    if (r) { c.etat = { etat: "arrete" }; toast(t("⏹ {nom} arrêté", { nom: c.nom }), "succes"); }
    dessinerListe();
    if (apres) apres();
  }

  // -- commandes ---------------------------------------------------------------
  function editerCommandes(p) {
    let lignes = p.commandes.map(c => ({ ...c }));
    if (!lignes.length && p.proposees.length) lignes = [{ ...p.proposees[0] }];
    const zone = el("div");
    const champ = (obj, cle, attrs) => el("input", { value: obj[cle] ?? "", spellcheck: "false", ...attrs,
      oninput: e => { obj[cle] = e.target.value; } });
    const redessiner = () => {
      zone.replaceChildren(...(lignes.length ? [
        el("div", { class: "pj-entetes" }, el("span", {}, "Nom"), el("span", {}, "Commande"), el("span", {}, "Port"), el("span", {}, "Adresse"), el("span")),
        ...lignes.map((c, i) => el("div", { class: "pj-edit" },
          champ(c, "nom", { placeholder: "ex. Front" }),
          champ(c, "commande", { placeholder: "ex. npm run dev", class: "mono" }),
          champ(c, "port", { placeholder: "ex. 5173", inputmode: "numeric" }),
          champ(c, "url", { placeholder: "ex. http://localhost:5173" }),
          el("button", { class: "icone-btn", title: "Supprimer", onclick: () => { lignes.splice(i, 1); redessiner(); } }, "✕")))]
        : [el("p", {}, "Aucune commande pour l'instant.")]));
    };
    redessiner();
    const enregistrer = el("button", { class: "btn principal", onclick: async () => {
      enregistrer.disabled = true;
      const r = await appel("commandes/enregistrer", { projet: p.id, commandes: lignes }, "Commandes enregistrées");
      enregistrer.disabled = false;
      if (!r) return;
      p.commandes = r.commandes;
      fermer();
      dessinerListe();
    } }, "Enregistrer");
    fenetre([
      el("h3", {}, "⚙️ " + t("Commandes de « {nom} »", { nom: p.nom })),
      el("p", {}, "Chaque commande est lancée dans le dossier du projet, sans fenêtre. Sa sortie va dans le journal."),
      zone,
      el("button", { class: "btn discret", onclick: () => { lignes.push({ nom: "", commande: "", port: "", url: "" }); redessiner(); } }, "＋ Ajouter une commande"),
      p.proposees.length ? el("div", {},
        el("div", { class: "pj-sous", style: "margin:12px 0 0" }, "Proposées d'après le projet :"),
        el("div", { class: "pj-sugg" }, p.proposees.map(s => el("button", { title: s.nom,
          onclick: () => { lignes.push({ ...s, id: lignes.some(l => l.id === s.id) ? "" : s.id }); redessiner(); } }, "＋ " + s.commande)))) : null,
      el("div", { class: "actions" }, el("button", { class: "btn", onclick: fermer }, "Annuler"), enregistrer)]);
    $("#fenetre").style.width = "min(860px, 96vw)";
  }

  // -- journal -----------------------------------------------------------------
  function journal(p, c) {
    const pre = el("pre", { class: "pj-journal" }, t("Lecture…"));
    const point = el("span", { class: "point" });
    const etat = el("span", {});
    const boutons = el("span", { style: "display:flex;gap:8px" });
    let lignes = [], ouvert = true;
    const fenetreActuelle = () => $("#voile").classList.contains("visible") && $("#fenetre").contains(pre);

    async function lire() {
      if (!ouvert || !fenetreActuelle()) { ouvert = false; return; }
      let r;
      try { r = await api("/api/projets/journal", { projet: p.id, commande: c.id }); }
      catch (e) { pre.textContent = "😕 " + e.message; return; }
      const enBas = pre.scrollHeight - pre.scrollTop - pre.clientHeight < 30;
      if (r.lignes.join("\n") !== lignes.join("\n")) {
        lignes = r.lignes;
        pre.textContent = lignes.length ? lignes.join("\n") : t("Journal vide.");
        if (enBas) pre.scrollTop = pre.scrollHeight;
      }
      c.etat = { etat: r.etat, code_sortie: r.code_sortie };
      point.className = "point " + (r.etat === "arrete" ? "" : r.etat);
      etat.textContent = r.etat === "arrete" && r.code_sortie ? t("arrêté (code {c})", { c: r.code_sortie }) : t(LIBELLES[r.etat] || r.etat);
      const vivant = r.etat === "marche" || r.etat === "demarrage";
      boutons.replaceChildren(
        vivant
          ? el("button", { class: "btn", onclick: () => arreter(p, c, () => journal(p, c)) }, "⏹ " + t("Arrêter"))
          : el("button", { class: "btn", disabled: r.etat === "occupe", onclick: async () => { await demarrer(p, c); lire(); } }, "▶ " + t("Démarrer")),
        el("button", { class: "btn", onclick: () => copier(lignes.join("\n")) }, "📋 " + t("Copier")),
        el("button", { class: "btn principal", onclick: () => { ouvert = false; fermer(); dessinerListe(); } }, "Fermer"));
      setTimeout(lire, 2000);
    }

    fenetre([
      el("h3", {}, "📜 " + t("Journal de {nom}", { nom: `${p.nom} · ${c.nom}` })),
      el("div", { class: "pj-sous" }, point, etat, "·", el("span", {}, "300 dernières lignes, mises à jour toutes les 2 secondes")),
      pre,
      el("div", { class: "actions" }, boutons)]);
    $("#fenetre").style.width = "min(980px, 96vw)";
    lire();
  }

  // -- .env --------------------------------------------------------------------
  async function fenetreEnv(p) {
    const r = await appel("env/liste", { projet: p.id });
    if (!r) return;
    const blocs = [];
    if (!r.coffre.ouvert) {
      blocs.push(el("div", { class: "pj-alerte" }, "🔒 " + t("Ouvrez d'abord le coffre dans l'onglet Mots de passe."),
        el("button", { class: "btn", onclick: () => { fermer(); montrerVue("motsdepasse"); } }, "Ouvrir l'onglet Mots de passe")));
    }
    blocs.push(r.fichiers.length
      ? el("div", { class: "pj-env" }, r.fichiers.map(f => el("div", {},
          el("code", {}, f.fichier),
          el("small", {}, [f.existe ? null : t("absent du dossier"),
            r.coffre.ouvert ? (f.sauvegarde ? t("sauvegardé le {d}", { d: date(f.sauvegarde) }) : t("pas encore sauvegardé")) : null]
            .filter(Boolean).join(" · ")),
          f.sauvegarde ? el("button", { class: "btn", style: "padding:5px 10px;font-size:12.5px", onclick: () => restaurer(p, f) }, "↩️ " + t("Restaurer")) : null)))
      : el("p", {}, "Aucun fichier .env dans ce projet."));
    const sauver = el("button", { class: "btn principal", disabled: !r.coffre.ouvert || !r.fichiers.some(f => f.existe), onclick: async () => {
      sauver.disabled = true;
      const s = await appel("env/sauvegarder", { projet: p.id });
      if (s) { toast(t("🔐 {n} fichier(s) sauvegardé(s) dans le coffre", { n: s.sauvegardes.length }), "succes"); fenetreEnv(p); }
      else sauver.disabled = false;
    } }, "🔐 Sauvegarder dans le coffre");
    fenetre([
      el("h3", {}, "🔐 " + t("Fichiers .env de « {nom} »", { nom: p.nom })),
      el("p", {}, "Le contenu est rangé, chiffré, dans le coffre de l'onglet Mots de passe (catégorie « env »)."),
      ...blocs,
      el("div", { class: "actions" }, el("button", { class: "btn", onclick: fermer }, "Fermer"), sauver)]);
  }

  async function restaurer(p, f) {
    const oui = await confirmer("↩️", t("Restaurer {f} ?", { f: f.fichier }),
      f.existe ? t("Le fichier est réécrit avec la version du coffre. L'ancien est gardé en {f}.bak.", { f: f.fichier })
               : t("Le fichier est recréé avec la version du coffre."), "Restaurer");
    if (!oui) { fenetreEnv(p); return; }
    const r = await appel("env/restaurer", { projet: p.id, fichier: f.fichier });
    if (r) toast(t("↩️ {f} restauré", { f: r.restaure }), "succes");
    fenetreEnv(p);
  }

  VUES.projets = { afficher, journal, titre: "Projets", icone: "📦", groupe: "dev", ordre: 10 };
})();

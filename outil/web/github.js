"use strict";
/* Onglet « GitHub » : tous vos dépôts, clonés ou ouverts en un clic, création
   d'un dépôt à partir d'un dossier, vos pull requests et issues, et l'état de
   GitHub Actions (voir github.py). Le jeton GitHub reste dans le coffre de
   Windows : il ne passe jamais par la page. */
(() => {
  I18N.ajouter({
    // Barre et sous-onglets
    "Dépôts": "Repositories", "Pull requests": "Pull requests", "Issues": "Issues", "Actions": "Actions",
    "Rechercher un dépôt…": "Search a repository…", "Filtrer…": "Filter…",
    "Tous": "All", "Privés": "Private", "Publics": "Public", "Sur ce PC": "On this PC", "Pas sur ce PC": "Not on this PC",
    "Nouveau dépôt": "New repository", "Dossiers de projets (où chercher et cloner)": "Project folders (where to look and clone)",
    "Relire": "Reload", "Relire depuis GitHub": "Reload from GitHub", "Déconnecter GitHub de ce PC": "Disconnect GitHub from this PC",
    "Lecture de vos dépôts…": "Reading your repositories…", "Lecture…": "Loading…",
    "Indiquez vos dossiers de projets pour voir quels dépôts sont déjà sur ce PC et pouvoir cloner : ":
      "Choose your project folders to see which repositories are already on this PC and to clone: ",
    "Choisir les dossiers": "Choose folders",
    // Dépôts
    "Aucun dépôt ne correspond.": "No repository matches.", "Aucun dépôt sur ce compte pour l'instant.": "No repository on this account yet.",
    "Ouvrir la page du dépôt": "Open the repository page", "Dossier": "Folder", "Ouvrir dans VS Code": "Open in VS Code",
    "Dossier ouvert": "Folder opened", "VS Code s'ouvre…": "VS Code is opening…",
    "Copier le dépôt sur ce PC": "Copy the repository to this PC", "Cloner": "Clone", "Clonage…": "Cloning…",
    "Archivé": "Archived", "Fork": "Fork", "Privé": "Private", "Public": "Public",
    "Mis à jour le {date}": "Updated {date}", "Sur ce PC : {chemin}": "On this PC: {chemin}",
    // Pull requests, issues
    "Revue demandée": "Review requested", "Mes pull requests ouvertes": "My open pull requests",
    "Aucune pull request ouverte.": "No open pull requests.", "Aucune revue en attente.": "No pending review.",
    "Aucune issue ne vous est assignée.": "No issue is assigned to you.", "Rien ne correspond.": "Nothing matches.",
    "Brouillon": "Draft", "Ouvrir": "Open", "Ouvrir sur GitHub": "Open on GitHub", "par {auteur}": "by {auteur}",
    "{n} affichées sur {total}": "{n} shown out of {total}",
    "Issues ouvertes qui vous sont assignées": "Open issues assigned to you",
    // Actions
    "Réussi": "Passed", "Échec": "Failed", "En cours": "In progress", "Annulé": "Cancelled",
    "Validation demandée": "Approval required", "Ignoré": "Skipped", "Illisible": "Unreadable", "Aucun workflow": "No workflow",
    "Voir le run": "View run", "Dépôt": "Repository",
    "{n} dépôt en échec : {depots}": "{n} repository failing: {depots}",
    "{n} dépôts en échec : {depots}": "{n} repositories failing: {depots}",
    "Tous les derniers runs ont réussi.": "All latest runs passed.",
    "{n} run en cours…": "{n} run in progress…", "{n} runs en cours…": "{n} runs in progress…",
    "Aucun run GitHub Actions sur vos dépôts récents.": "No GitHub Actions run on your recent repositories.",
    "Dernier run de la branche par défaut, pour vos 15 dépôts les plus récents et ceux de ce PC. Vérifié à {heure}.":
      "Latest run on the default branch, for your 15 most recent repositories and those on this PC. Checked at {heure}.",
    "Sans workflow : {depots}": "No workflow: {depots}",
    "Illisibles (Actions désactivé ou accès refusé) : {depots}": "Unreadable (Actions disabled or access denied): {depots}",
    "branche {branche}": "branch {branche}",
    // Connexion
    "Connecter GitHub": "Connect GitHub", "Connecter votre compte GitHub": "Connect your GitHub account",
    "Une seule fois. Aucun mot de passe à saisir ici : GitHub vous montre une page où valider un code.":
      "Only once. No password to type here: GitHub shows you a page where you confirm a code.",
    "Cliquez sur « Connecter GitHub » : un code de 8 caractères s'affiche et est copié.":
      "Click “Connect GitHub”: an 8-character code is shown and copied.",
    "La page github.com/login/device s'ouvre : collez le code, puis cliquez sur ":
      "The github.com/login/device page opens: paste the code, then click ",
    "Revenez ici : vos dépôts s'affichent tout seuls.": "Come back here: your repositories appear automatically.",
    "L'accès est rangé dans le coffre de Windows (Gestionnaire d'identification), jamais dans un fichier.":
      "Access is stored in the Windows vault (Credential Manager), never in a file.",
    "En attente de votre validation sur GitHub…": "Waiting for your confirmation on GitHub…",
    "Validez ce code sur GitHub": "Confirm this code on GitHub",
    "Il est déjà copié : collez-le sur la page github.com/login/device qui vient de s'ouvrir, puis cliquez sur Authorize.":
      "It is already copied: paste it on the github.com/login/device page that just opened, then click Authorize.",
    "Copier": "Copy", "Code copié": "Code copied", "Rouvrir la page": "Reopen the page", "Annuler": "Cancel",
    "GitHub connecté : {login}": "GitHub connected: {login}", "Accès refusé sur GitHub.": "Access denied on GitHub.",
    "Le code a expiré : fermez et recommencez.": "The code has expired: close and start again.",
    "Déconnecter GitHub ?": "Disconnect GitHub?", "Déconnecter": "Disconnect", "GitHub déconnecté": "GitHub disconnected",
    "L'accès est retiré de ce PC. Pour le révoquer aussi chez GitHub : Settings > Applications > Authorized OAuth Apps.":
      "Access is removed from this PC. To revoke it on GitHub too: Settings > Applications > Authorized OAuth Apps.",
    // Dossiers de projets
    "Dossiers de projets": "Project folders", "Retirer": "Remove", "Aucun dossier pour l'instant.": "No folder yet.",
    "ex. D:\\Projets": "e.g. D:\\Projects", "Enregistrer": "Save", "Dossiers enregistrés": "Folders saved", "Ajouter": "Add",
    "L'outil y cherche vos dépôts déjà présents sur ce PC (le dossier et ses sous-dossiers directs), et y clone les nouveaux.":
      "The tool looks there for repositories already on this PC (the folder and its direct subfolders), and clones new ones there.",
    // Cloner
    "Destination : {chemin}": "Destination: {chemin}", "Dans le dossier": "In folder",
    "{nom} cloné dans {chemin}": "{nom} cloned into {chemin}", "Cloner « {nom} »": "Clone “{nom}”",
    // Nouveau dépôt
    "ex. D:\\Projets\\mon-projet": "e.g. D:\\Projects\\my-project", "ex. mon-projet": "e.g. my-project",
    "Une phrase sur le projet (facultatif)": "One sentence about the project (optional)",
    "Créer et envoyer": "Create and upload", "Vérifier le contenu": "Check the content", "Lecture du dossier…": "Reading the folder…",
    "Ce dossier est déjà relié à {depot}.": "This folder is already linked to {depot}.",
    "{n} fichier · {taille}": "{n} file · {taille}", "{n} fichiers · {taille}": "{n} files · {taille}",
    " (les fichiers listés dans .gitignore sont exclus)": " (files listed in .gitignore are excluded)",
    "Ce dossier a des modifications non enregistrées (commit) : elles ne seront pas envoyées.":
      "This folder has uncommitted changes: they will not be uploaded.",
    "Fichiers lourds (plus de 50 Mo) :": "Large files (over 50 MB):",
    "GitHub refuse les fichiers de plus de 100 Mo. Ajoutez-les à .gitignore :": "GitHub refuses files over 100 MB. Add them to .gitignore:",
    "Fichiers qui contiennent souvent des mots de passe ou des clés :": "Files that often contain passwords or keys:",
    "Ajoutez-les à .gitignore puis vérifiez à nouveau, ou cochez ci-dessous si vous êtes sûr.":
      "Add them to .gitignore and check again, or tick below if you are sure.",
    "J'ai vérifié : ces fichiers peuvent être envoyés": "I checked: these files can be uploaded",
    "Envoi…": "Uploading…", "Dépôt créé et envoyé": "Repository created and uploaded",
    "{n} fichier envoyé sur {depot}.": "{n} file uploaded to {depot}.", "{n} fichiers envoyés sur {depot}.": "{n} files uploaded to {depot}.",
    "Voir sur GitHub": "View on GitHub", "Dépôt public ?": "Public repository?",
    "Tout le monde pourra voir ces fichiers sur GitHub.": "Everyone will be able to see these files on GitHub.", "Oui, public": "Yes, public",
    "Nouveau dépôt GitHub": "New GitHub repository",
    "Crée le dépôt sur votre compte et y envoie le contenu d'un dossier de ce PC.":
      "Creates the repository on your account and uploads the content of a folder from this PC.",
    "Dossier à envoyer": "Folder to upload", "Nom du dépôt": "Repository name", "Description": "Description",
    // Messages de github.py
    "GitHub ne répond pas : vérifiez la connexion internet.": "GitHub is not responding: check your internet connection.",
    "GitHub n'est pas connecté.": "GitHub is not connected.",
    "L'accès à GitHub a été retiré : reconnectez GitHub.": "Access to GitHub was revoked: reconnect GitHub.",
    "Limite d'appels à GitHub atteinte : réessayez dans quelques minutes.": "GitHub request limit reached: try again in a few minutes.",
    "Le « Device Flow » n'est pas activé dans l'application GitHub (github.com > Settings > Developer settings > OAuth Apps > Enable Device Flow).":
      "“Device Flow” is not enabled in the GitHub application (github.com > Settings > Developer settings > OAuth Apps > Enable Device Flow).",
    "L'identifiant de l'application GitHub (client_id) est invalide.": "The GitHub application ID (client_id) is invalid.",
    "Réponse inattendue de GitHub.": "Unexpected response from GitHub.",
    "La connexion à GitHub n'est pas encore configurée : il manque l'identifiant de l'application (client_id).":
      "The GitHub connection is not configured yet: the application ID (client_id) is missing.",
    "GitHub a donné un accès qui ne fonctionne pas : réessayez.": "GitHub granted an access that does not work: try again.",
    "Impossible de ranger l'accès GitHub dans le coffre de Windows.": "Could not store the GitHub access in the Windows vault.",
    "GitHub refuse l'accès : reconnectez GitHub.": "GitHub denies access: reconnect GitHub.",
    "Le dossier de destination existe déjà.": "The destination folder already exists.",
    "git a échoué.": "git failed.",
    "Git n'est pas installé sur ce PC (https://git-scm.com).": "Git is not installed on this PC (https://git-scm.com).",
    "Git met trop de temps à répondre.": "Git is taking too long to respond.",
    "Dépôt invalide.": "Invalid repository.", "Choisissez un de vos dossiers de projets.": "Choose one of your project folders.",
    "Dossier introuvable.": "Folder not found.", "Dossier introuvable": "Folder not found",
    "Aucun fichier à envoyer dans ce dossier.": "No file to upload in this folder.",
    "Nom de dépôt invalide : lettres, chiffres, tirets, points et soulignés seulement.":
      "Invalid repository name: letters, digits, hyphens, dots and underscores only.",
    "Adresse refusée.": "Address refused.", "VS Code est introuvable sur ce PC.": "VS Code was not found on this PC.",
  });
  I18N.motifs([
    [/^GitHub a refusé la demande \((\d+)\) : ([\s\S]*)\.$/, "GitHub refused the request ($1): $2."],
    [/^GitHub a refusé la demande \((\d+)\)\.$/, "GitHub refused the request ($1)."],
    [/^GitHub a refusé la création \((\d+)\) : ([\s\S]*)\.$/, "GitHub refused to create the repository ($1): $2."],
    [/^GitHub a refusé la création \((\d+)\)\.$/, "GitHub refused to create the repository ($1)."],
    [/^Le dossier (.+) existe déjà\.$/, "The folder $1 already exists."],
    [/^Ce dossier est déjà relié à (.+)\.$/, "This folder is already linked to $1."],
    [/^GitHub refuse les fichiers de plus de 100 Mo : (.+)$/, "GitHub refuses files over 100 MB: $1"],
    [/^Un dépôt « (.+) » existe déjà sur votre compte\.$/, "A repository “$1” already exists on your account."],
    [/^Le dépôt (\S+) est créé, mais l'envoi a échoué \(([\s\S]*)\)\. Relancez « (.+) » dans le dossier\.$/,
      "The repository $1 was created, but the upload failed ($2). Run “$3” again in the folder."],
  ]);

  const G = { etat: null, depots: null, dossiers: [], recherche: "", filtre: "tous", sous: "depots",
    prs: null, issues: null, actions: null };
  const COULEURS_LANGUES = { JavaScript: "#f1e05a", TypeScript: "#3178c6", Python: "#3572A5", Java: "#b07219", HTML: "#e34c26",
    CSS: "#663399", Vue: "#41b883", PHP: "#4F5D95", "C#": "#178600", Rust: "#dea584", Go: "#00ADD8", Dart: "#00B4AB",
    Kotlin: "#A97BFF", Shell: "#89e051", PowerShell: "#012456", "Jupyter Notebook": "#DA5B0B", PLpgSQL: "#336790" };
  const ETATS = {
    succes: { icone: "✅", libelle: "Réussi", badge: "vert" }, echec: { icone: "❌", libelle: "Échec", badge: "rouge" },
    en_cours: { icone: "⏳", libelle: "En cours", badge: "ambre" }, annule: { icone: "⛔", libelle: "Annulé", badge: "gris" },
    action: { icone: "✋", libelle: "Validation demandée", badge: "bleu" }, ignore: { icone: "⏭️", libelle: "Ignoré", badge: "gris" },
    inconnu: { icone: "❔", libelle: "Illisible", badge: "gris" }, aucun: { icone: "➖", libelle: "Aucun workflow", badge: "gris" },
  };
  const infoEtat = e => ETATS[e] || ETATS.inconnu;

  const style = document.createElement("style");
  style.textContent = `
    .liste-gh { display: grid; grid-template-columns: repeat(auto-fill, minmax(360px, 1fr)); gap: 12px; }
    .depot { background: var(--carte); border-radius: var(--rayon); box-shadow: var(--ombre); padding: 14px 16px; display: flex; flex-direction: column; gap: 6px; animation: apparait .3s both; min-width: 0; }
    .depot .l1 { display: flex; align-items: center; gap: 8px; min-width: 0; }
    .depot .t { font-weight: 800; font-size: 15px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; flex: 1; }
    .badge-gh { font-size: 11.5px; font-weight: 700; border-radius: 999px; padding: 2px 9px; white-space: nowrap; flex: none; }
    .badge-gh.prive, .badge-gh.rouge { background: var(--rouge-clair); color: var(--rouge-texte); }
    .badge-gh.public, .badge-gh.vert { background: var(--vert-clair); color: var(--vert-texte); }
    .badge-gh.ambre { background: var(--ambre-clair); color: var(--ambre-texte); }
    .badge-gh.bleu { background: var(--bleu-clair); color: var(--bleu-texte); }
    .badge-gh.gris { background: var(--surface); color: var(--doux); }
    .depot .d { font-size: 13px; color: var(--doux); display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; min-height: 1em; }
    .depot .meta, .meta-gh { font-size: 12.5px; color: var(--doux); display: flex; gap: 12px; align-items: center; flex-wrap: wrap; min-width: 0; }
    .depot .langue::before { content: ""; display: inline-block; width: 9px; height: 9px; border-radius: 50%; background: var(--c, var(--gris)); margin-right: 5px; }
    .depot .local { font-size: 12.5px; color: var(--vert-texte); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .actions-gh { display: flex; gap: 6px; margin-top: 4px; flex-wrap: wrap; }
    .depot .actions-gh .btn { padding: 6px 12px; font-size: 13px; }
    .profil-gh { display: flex; align-items: center; gap: 8px; font-weight: 700; color: var(--doux); font-size: 14px; }
    .profil-gh img { width: 30px; height: 30px; border-radius: 50%; }
    .outils-gh input, .outils-gh select { border: 1.5px solid var(--ligne); border-radius: 12px; padding: 8px 11px; outline: none; background: var(--champ); color: var(--encre); font: inherit; }
    .outils-gh input { width: 240px; }
    .outils-gh input:focus, .outils-gh select:focus { border-color: var(--violet); background: var(--champ-focus); }
    .code-gh { font-family: var(--mono); font-size: 34px; font-weight: 800; letter-spacing: 4px; background: var(--violet-clair); color: var(--violet); border-radius: 16px; padding: 14px; margin: 6px 0 14px; user-select: all; }
    .dossiers-gh { display: flex; flex-direction: column; gap: 6px; margin: 4px 0 12px; }
    .dossiers-gh div { display: flex; align-items: center; gap: 8px; background: var(--surface); border-radius: 12px; padding: 7px 10px; font-size: 14px; }
    .dossiers-gh div span { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    .ajout-gh { display: flex; gap: 8px; }
    .ajout-gh input { flex: 1; border: 1.5px solid var(--ligne); border-radius: 12px; padding: 9px 11px; outline: none; background: var(--champ); color: var(--encre); font: inherit; }
    .ajout-gh input:focus { border-color: var(--violet); background: var(--champ-focus); }
    .bilan-gh { background: var(--surface); border-radius: 14px; padding: 12px 14px; font-size: 13.5px; margin: 8px 0; text-align: left; }
    .bilan-gh ul { margin: 6px 0 0; padding-left: 18px; }
    .bilan-gh.danger { background: var(--rouge-clair); color: var(--rouge-texte); }
    .bilan-gh code { font-size: 12.5px; font-family: var(--mono); background: var(--code); color: var(--code-texte); border-radius: 6px; padding: 0 4px; }
    .choix-gh { display: flex; gap: 14px; margin: 4px 0 10px; font-size: 14px; }
    .choix-gh label { display: flex; gap: 6px; align-items: center; cursor: pointer; }

    .sous-gh { margin: 0 0 14px; flex-wrap: wrap; }
    .sous-gh .puce { display: inline-flex; align-items: center; gap: 6px; }
    .nb-gh { background: var(--violet-clair); color: var(--violet); border-radius: 99px; padding: 0 7px; font-size: 11.5px; min-width: 20px; text-align: center; }
    .puce.actif .nb-gh { background: color-mix(in srgb, var(--fond) 25%, transparent); color: inherit; }
    .nb-gh.echec-gh, .puce.actif .nb-gh.echec-gh { background: var(--rouge); color: var(--sur-violet); }
    .puce.alerte-gh:not(.actif) { box-shadow: 0 0 0 2px var(--rouge) inset; color: var(--rouge-texte); }

    .lignes-gh { display: flex; flex-direction: column; gap: 8px; margin-bottom: 18px; }
    .ligne-gh { background: var(--carte); border-radius: 16px; box-shadow: var(--ombre); padding: 11px 14px; display: flex; align-items: center; gap: 12px; animation: apparait .3s both; min-width: 0; }
    .ligne-gh .ic-gh { font-size: 20px; width: 26px; text-align: center; flex: none; }
    .ligne-gh .corps-gh { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 3px; }
    .ligne-gh .t-gh { display: flex; align-items: center; gap: 8px; min-width: 0; }
    .ligne-gh .titre-gh { font-weight: 700; font-size: 14.5px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .ligne-gh .num-gh { color: var(--doux); font-weight: 600; font-size: 13px; flex: none; }
    .ligne-gh.brouillon .titre-gh { color: var(--doux); }
    .ligne-gh img.av-gh { width: 18px; height: 18px; border-radius: 50%; vertical-align: -4px; margin-right: 4px; }
    .etiq-gh { font-size: 11px; font-weight: 700; border-radius: 99px; padding: 1px 8px; white-space: nowrap; flex: none; }
    .section-gh { font-size: 13px; font-weight: 800; color: var(--doux); text-transform: uppercase; letter-spacing: .6px; margin: 4px 2px 8px; display: flex; gap: 8px; align-items: center; }

    .run-gh { background: var(--carte); border-radius: var(--rayon); box-shadow: var(--ombre); padding: 13px 16px; display: flex; flex-direction: column; gap: 6px; border-left: 5px solid var(--ligne); animation: apparait .3s both; min-width: 0; }
    .run-gh.succes { border-left-color: var(--menthe); }
    .run-gh.echec { border-left-color: var(--rouge); background: linear-gradient(90deg, var(--rouge-clair), var(--carte) 75%); }
    .run-gh.en_cours { border-left-color: var(--ambre); }
    .run-gh.action { border-left-color: var(--bleu-texte); }
    .run-gh .l1 { display: flex; align-items: center; gap: 8px; min-width: 0; }
    .run-gh .ic-run { font-size: 18px; flex: none; }
    .run-gh .t { font-weight: 800; font-size: 15px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; flex: 1; }
    .run-gh .wf { font-size: 13.5px; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .run-gh .commit { font-size: 13px; color: var(--doux); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .run-gh .autres { display: flex; gap: 6px; flex-wrap: wrap; }
    .run-gh .autres button { border: 1px solid var(--ligne); background: var(--surface); color: var(--encre); border-radius: 99px; font-size: 11.5px; padding: 1px 8px; cursor: pointer; }
    .alerte-ci { border-radius: 16px; padding: 12px 16px; font-weight: 700; margin-bottom: 12px; }
    .alerte-ci.echec { background: var(--rouge-clair); color: var(--rouge-texte); box-shadow: 0 0 0 2px var(--rouge) inset; }
    .alerte-ci.en_cours { background: var(--ambre-clair); color: var(--ambre-texte); }
    .alerte-ci.succes { background: var(--vert-clair); color: var(--vert-texte); }
    .note-gh { font-size: 12.5px; color: var(--doux); margin: 14px 2px 0; }
    .attente-gh { color: var(--doux); padding: 18px; text-align: center; }
  `;
  document.head.append(style);
  const racine = () => $("#vue-github");
  /** Texte venu de GitHub ou déjà traduit : el() ne le retraduit pas. */
  const brut = s => document.createTextNode(s == null ? "" : String(s));

  // -- dates ---------------------------------------------------------------------
  const dateCourte = iso => iso ? new Date(iso).toLocaleDateString(I18N.locale(), { day: "numeric", month: "short", year: "numeric" }) : "";
  const dateLongue = iso => iso ? new Date(iso).toLocaleString(I18N.locale(), { dateStyle: "medium", timeStyle: "short" }) : "";
  function ilYa(iso) {
    if (!iso) return "";
    const s = (new Date(iso) - Date.now()) / 1000;
    const rtf = new Intl.RelativeTimeFormat(I18N.locale(), { numeric: "auto" });
    for (const [unite, duree] of [["year", 31536000], ["month", 2592000], ["week", 604800], ["day", 86400], ["hour", 3600], ["minute", 60]]) {
      if (Math.abs(s) >= duree) return rtf.format(Math.round(s / duree), unite);
    }
    return rtf.format(0, "minute");
  }
  const quand = iso => el("span", { title: dateLongue(iso) }, brut(ilYa(iso)));

  // -- affichage ---------------------------------------------------------------
  async function afficher(relire = true, forcer = false) {
    if (relire || !G.etat) {
      try { G.etat = await api("/api/github/etat", {}); }
      catch (e) { racine().replaceChildren(el("div", { class: "vide" }, "😕 " + e.message)); return; }
      G.dossiers = G.etat.dossiers || [];
    }
    if (!G.etat.connecte) return ecranConnexion();
    chargerSuivi(forcer);
    if (relire || !G.depots) {
      if (!G.depots) racine().replaceChildren(el("div", { class: "vide" }, el("span", { class: "attente" }, "⏳"), " ", t("Lecture de vos dépôts…")));
      try { const r = await api("/api/github/depots", {}); G.depots = r.depots; }
      catch (e) { racine().replaceChildren(el("div", { class: "vide" }, "😕 " + e.message)); return; }
    }
    dessiner();
  }

  /** Pull requests, issues et Actions : en parallèle, sans bloquer la liste
     des dépôts. Le serveur les garde quelques minutes (quota de GitHub). */
  function chargerSuivi(forcer) {
    for (const cle of ["prs", "issues", "actions"]) {
      if (forcer) G[cle] = null;
      api("/api/github/" + cle, { forcer })
        .then(r => { G[cle] = r; })
        .catch(e => { G[cle] = { erreur: e.message }; })
        .finally(() => { majPuces(); if (G.sous === cle) dessinerListe(); });
    }
  }

  function dessiner() {
    const surDepots = G.sous === "depots";
    const recherche = el("input", { placeholder: surDepots ? "Rechercher un dépôt…" : "Filtrer…", value: G.recherche,
      oninput: e => { G.recherche = e.target.value; dessinerListe(); } });
    const filtre = surDepots ? el("select", { onchange: e => { G.filtre = e.target.value; dessinerListe(); } },
      [["tous", "Tous"], ["prive", "Privés"], ["public", "Publics"], ["local", "Sur ce PC"], ["absent", "Pas sur ce PC"]]
        .map(([v, lib]) => el("option", { value: v, ...(G.filtre === v ? { selected: "" } : {}) }, lib))) : null;
    const barre = el("div", { class: "barre-vue" },
      el("h2", {}, "🐙 GitHub ", el("span", { class: "compte", id: "nb-depots" }, String(G.depots.length))),
      el("div", { class: "profil-gh" }, G.etat.avatar ? el("img", { src: G.etat.avatar, alt: "" }) : null, brut(G.etat.login)),
      el("div", { class: "espace" }),
      el("div", { class: "outils-gh", style: "display:flex;gap:8px;flex-wrap:wrap" }, recherche, filtre),
      el("button", { class: "btn principal", onclick: nouveauDepot }, "＋ " + t("Nouveau dépôt")),
      el("button", { class: "icone-btn", title: "Dossiers de projets (où chercher et cloner)", onclick: reglerDossiers }, "📁"),
      el("button", { class: "icone-btn", title: "Relire depuis GitHub", onclick: () => afficher(true, true) }, "🔄"),
      el("button", { class: "icone-btn", title: "Déconnecter GitHub de ce PC", onclick: deconnecter }, "🔌"));
    const conseil = G.dossiers.length || !surDepots ? null : el("div", { class: "vide", style: "margin-bottom:12px" },
      "📁 " + t("Indiquez vos dossiers de projets pour voir quels dépôts sont déjà sur ce PC et pouvoir cloner : "),
      el("button", { class: "btn", onclick: reglerDossiers }, "Choisir les dossiers"));
    racine().replaceChildren(...[barre, el("div", { class: "puces sous-gh", id: "sous-gh" }), conseil, el("div", { id: "liste-gh" })].filter(Boolean));
    majPuces();
    dessinerListe();
  }

  function compte(donnees) {
    if (!donnees) return el("span", { class: "nb-gh" }, "…");
    if (donnees.erreur) return el("span", { class: "nb-gh", title: donnees.erreur }, "!");
    return el("span", { class: "nb-gh" }, String(donnees.nombre ?? 0));
  }

  function majPuces() {
    const zone = $("#sous-gh");
    if (!zone) return;
    const a = G.actions;
    const echecs = a && !a.erreur ? a.nombre_echecs : 0;
    const badgeActions = !a ? el("span", { class: "nb-gh" }, "…")
      : a.erreur ? el("span", { class: "nb-gh", title: a.erreur }, "!")
      : echecs ? el("span", { class: "nb-gh echec-gh" }, "❌ " + echecs)
      : el("span", { class: "nb-gh" }, a.depots.some(d => d.etat === "en_cours") ? "⏳" : "✅");
    const puce = (cle, libelle, badge, alerte = false) => el("button", {
      class: "puce" + (G.sous === cle ? " actif" : "") + (alerte ? " alerte-gh" : ""),
      onclick: () => { if (G.sous !== cle) { G.sous = cle; G.recherche = ""; dessiner(); } } }, libelle, badge);
    zone.replaceChildren(
      puce("depots", "📦 " + t("Dépôts"), el("span", { class: "nb-gh" }, String(G.depots ? G.depots.length : "…"))),
      puce("prs", "🔀 " + t("Pull requests"), compte(G.prs)),
      puce("issues", "🐛 " + t("Issues"), compte(G.issues)),
      puce("actions", "⚙️ " + t("Actions"), badgeActions, echecs > 0));
  }

  function dessinerListe() {
    const zone = $("#liste-gh");
    if (!zone) return;
    if (G.sous === "prs") return zone.replaceChildren(...vuePRs());
    if (G.sous === "issues") return zone.replaceChildren(...vueIssues());
    if (G.sous === "actions") return zone.replaceChildren(...vueActions());
    const liste = visibles();
    zone.replaceChildren(liste.length
      ? el("div", { class: "liste-gh" }, liste.map(carte))
      : el("div", { class: "vide" }, G.depots.length ? "Aucun dépôt ne correspond." : "Aucun dépôt sur ce compte pour l'instant."));
  }

  const correspond = (...textes) => { const q = G.recherche.trim().toLowerCase(); return !q || textes.join(" ").toLowerCase().includes(q); };

  function visibles() {
    return G.depots.filter(d => correspond(d.complet, d.description, d.langue) &&
      (G.filtre === "tous" || (G.filtre === "prive" && d.prive) || (G.filtre === "public" && !d.prive) ||
       (G.filtre === "local" && d.local) || (G.filtre === "absent" && !d.local)));
  }

  /** En attente, ou l'erreur du serveur ; null quand les données sont là. */
  function etatChargement(donnees) {
    if (!donnees) return [el("div", { class: "attente-gh" }, el("span", { class: "attente" }, "⏳"), " ", t("Lecture…"))];
    if (donnees.erreur) return [el("div", { class: "vide" }, "😕 " + donnees.erreur)];
    return null;
  }

  // -- dépôts --------------------------------------------------------------------
  function carte(d, i) {
    const actions = [el("button", { class: "btn", title: "Ouvrir la page du dépôt", onclick: () => ouvrirPage(d.url) }, "🌐 GitHub")];
    if (d.local) {
      actions.push(el("button", { class: "btn", title: d.local, onclick: () => action("ouvrir_dossier", { chemin: d.local }, "📂 " + t("Dossier ouvert")) }, "📂 " + t("Dossier")),
        el("button", { class: "btn", title: "Ouvrir dans VS Code", onclick: () => action("vscode", { chemin: d.local }, "💻 " + t("VS Code s'ouvre…")) }, "💻 VS Code"));
    } else {
      actions.push(el("button", { class: "btn", title: "Copier le dépôt sur ce PC", onclick: () => cloner(d) }, "⬇️ " + t("Cloner")));
    }
    const proprietaire = d.complet.split("/")[0];
    return el("div", { class: "depot", style: `animation-delay:${Math.min(i, 20) * 25}ms` },
      el("div", { class: "l1" },
        el("div", { class: "t", title: d.complet }, brut(d.nom)),
        d.archive ? el("span", { class: "badge-gh gris" }, "Archivé") : null,
        d.fork ? el("span", { class: "badge-gh gris" }, "Fork") : null,
        el("span", { class: "badge-gh " + (d.prive ? "prive" : "public") }, d.prive ? "🔒 " + t("Privé") : t("Public"))),
      el("div", { class: "d" }, brut(d.description || "")),
      el("div", { class: "meta" },
        d.langue ? el("span", { class: "langue", style: `--c:${COULEURS_LANGUES[d.langue] || "var(--gris)"}` }, brut(d.langue)) : null,
        d.etoiles ? el("span", {}, `⭐ ${d.etoiles}`) : null,
        d.maj ? el("span", {}, brut(t("Mis à jour le {date}", { date: dateCourte(d.maj) }))) : null,
        proprietaire.toLowerCase() !== (G.etat.login || "").toLowerCase() ? el("span", {}, brut("👥 " + proprietaire)) : null),
      d.local ? el("div", { class: "local", title: d.local }, brut("✅ " + t("Sur ce PC : {chemin}", { chemin: d.local }))) : null,
      el("div", { class: "actions-gh" }, actions));
  }

  // -- pull requests et issues -------------------------------------------------------
  function etiquette(e) {
    const c = /^[0-9a-f]{6}$/i.test(e.couleur) ? e.couleur : "999999";
    const [r, v, b] = [0, 2, 4].map(i => parseInt(c.slice(i, i + 2), 16));
    const clair = (r * 299 + v * 587 + b * 114) / 1000 > 150;
    // Couleur choisie sur GitHub pour l'étiquette : texte noir ou blanc selon le fond.
    return el("span", { class: "etiq-gh", style: `background:#${c};color:${clair ? "#1f1a3a" : "#fff"}` }, brut(e.nom));
  }

  function ligne(x, icone, i) {
    return el("div", { class: "ligne-gh" + (x.brouillon ? " brouillon" : ""), style: `animation-delay:${Math.min(i, 20) * 20}ms` },
      el("div", { class: "ic-gh" }, icone),
      el("div", { class: "corps-gh" },
        el("div", { class: "t-gh" },
          el("span", { class: "titre-gh", title: x.titre }, brut(x.titre)),
          el("span", { class: "num-gh" }, brut("#" + x.numero)),
          x.brouillon ? el("span", { class: "badge-gh gris" }, "Brouillon") : null,
          (x.etiquettes || []).slice(0, 4).map(etiquette)),
        el("div", { class: "meta-gh" },
          el("span", {}, brut("📦 " + x.depot)),
          el("span", {}, x.avatar ? el("img", { class: "av-gh", src: x.avatar, alt: "" }) : null, brut(t("par {auteur}", { auteur: x.auteur }))),
          quand(x.date),
          x.commentaires ? el("span", {}, brut("💬 " + x.commentaires)) : null)),
      el("button", { class: "btn petit", title: "Ouvrir sur GitHub", onclick: () => ouvrirPage(x.url) }, "🌐 " + t("Ouvrir")));
  }

  function bloc(titre, liste, total, vide, icone) {
    const filtres = liste.filter(x => correspond(x.depot, x.titre, x.auteur, ...(x.etiquettes || []).map(e => e.nom)));
    return [
      el("div", { class: "section-gh" }, titre, el("span", { class: "nb-gh" }, String(total)),
        total > liste.length ? el("span", {}, brut(t("{n} affichées sur {total}", { n: liste.length, total }))) : null),
      el("div", { class: "lignes-gh" }, filtres.length ? filtres.map((x, i) => ligne(x, x.brouillon ? "📝" : icone, i))
        : el("div", { class: "vide" }, liste.length ? "Rien ne correspond." : vide))];
  }

  function vuePRs() {
    const p = G.prs;
    return etatChargement(p) || [
      ...bloc("👀 " + t("Revue demandée"), p.revues, p.nb_revues, "Aucune revue en attente.", "👀"),
      ...bloc("🙋 " + t("Mes pull requests ouvertes"), p.miennes, p.nb_miennes, "Aucune pull request ouverte.", "🔀")];
  }

  function vueIssues() {
    const r = G.issues;
    return etatChargement(r) || bloc("🐛 " + t("Issues ouvertes qui vous sont assignées"), r.issues, r.nombre, "Aucune issue ne vous est assignée.", "🐛");
  }

  // -- GitHub Actions ------------------------------------------------------------------
  function carteRun(d, i) {
    const e = infoEtat(d.etat);
    const autres = (d.workflows || []).filter(w => w.workflow !== d.workflow);
    return el("div", { class: "run-gh " + d.etat, style: `animation-delay:${Math.min(i, 20) * 25}ms` },
      el("div", { class: "l1" },
        el("span", { class: "ic-run", title: t(e.libelle) }, e.icone),
        el("div", { class: "t", title: d.complet }, brut(d.complet)),
        el("span", { class: "badge-gh " + e.badge }, e.libelle)),
      el("div", { class: "wf" }, brut(`${d.workflow}${d.numero ? " #" + d.numero : ""}`)),
      d.titre ? el("div", { class: "commit", title: d.titre }, brut(d.titre)) : null,
      el("div", { class: "meta-gh" }, el("span", {}, brut("🌿 " + t("branche {branche}", { branche: d.branche }))), quand(d.date),
        d.local ? el("span", { title: d.local }, "💻 " + t("Sur ce PC")) : null),
      autres.length ? el("div", { class: "autres" }, autres.map(w => el("button", {
        title: `${t(infoEtat(w.etat).libelle)} · ${dateLongue(w.date)}`, onclick: () => ouvrirPage(w.lien) },
        brut(`${infoEtat(w.etat).icone} ${w.workflow}`)))) : null,
      el("div", { class: "actions-gh" },
        el("button", { class: "btn petit" + (d.etat === "echec" ? " principal" : ""), onclick: () => ouvrirPage(d.lien) }, "🌐 " + t("Voir le run")),
        el("button", { class: "btn petit discret", onclick: () => ouvrirPage(d.url) }, "📦 " + t("Dépôt"))));
  }

  function vueActions() {
    const a = G.actions;
    const attente = etatChargement(a);
    if (attente) return attente;
    const filtres = a.depots.filter(d => correspond(d.complet, d.workflow, d.titre));
    const avecRuns = filtres.filter(d => !["aucun", "inconnu"].includes(d.etat));
    const sans = filtres.filter(d => d.etat === "aucun").map(d => d.complet);
    const illisibles = filtres.filter(d => d.etat === "inconnu").map(d => d.complet);
    const enCours = a.depots.filter(d => d.etat === "en_cours").length;
    const n = a.nombre_echecs;
    const alerte = n
      ? el("div", { class: "alerte-ci echec" }, brut("❌ " + t(n > 1 ? "{n} dépôts en échec : {depots}" : "{n} dépôt en échec : {depots}", { n, depots: a.echecs.join(", ") })))
      : enCours ? el("div", { class: "alerte-ci en_cours" }, brut("⏳ " + t(enCours > 1 ? "{n} runs en cours…" : "{n} run en cours…", { n: enCours })))
      : avecRuns.length ? el("div", { class: "alerte-ci succes" }, "✅ " + t("Tous les derniers runs ont réussi.")) : null;
    const heure = a.heure ? new Date(a.heure).toLocaleTimeString(I18N.locale(), { hour: "2-digit", minute: "2-digit" }) : "";
    return [
      alerte,
      avecRuns.length ? el("div", { class: "liste-gh" }, avecRuns.map(carteRun))
        : el("div", { class: "vide" }, a.depots.length && G.recherche.trim() ? "Rien ne correspond." : "Aucun run GitHub Actions sur vos dépôts récents."),
      sans.length ? el("div", { class: "note-gh" }, brut("➖ " + t("Sans workflow : {depots}", { depots: sans.join(", ") }))) : null,
      illisibles.length ? el("div", { class: "note-gh" }, brut("❔ " + t("Illisibles (Actions désactivé ou accès refusé) : {depots}", { depots: illisibles.join(", ") }))) : null,
      el("div", { class: "note-gh" }, brut("ℹ️ " + t("Dernier run de la branche par défaut, pour vos 15 dépôts les plus récents et ceux de ce PC. Vérifié à {heure}.", { heure })))]
      .filter(Boolean);
  }

  async function action(nom, donnees, message) {
    try { await api("/api/github/" + nom, donnees); if (message) toast(message, "succes"); }
    catch (e) { toast("😕 " + e.message, "erreur", 6000); }
  }
  const ouvrirPage = url => action("ouvrir_page", { url });

  // -- connexion ---------------------------------------------------------------
  function ecranConnexion() {
    G.depots = null; G.prs = G.issues = G.actions = null;
    const bouton = el("button", { class: "btn principal", onclick: () => connecter(bouton) }, "🐙 " + t("Connecter GitHub"));
    racine().replaceChildren(el("div", { class: "connexion" },
      el("div", { style: "font-size:48px" }, "🐙"),
      el("h3", {}, "Connecter votre compte GitHub"),
      el("p", { style: "color:var(--doux);margin-top:0" }, "Une seule fois. Aucun mot de passe à saisir ici : GitHub vous montre une page où valider un code."),
      el("ol", {},
        el("li", {}, "Cliquez sur « Connecter GitHub » : un code de 8 caractères s'affiche et est copié."),
        el("li", {}, "La page github.com/login/device s'ouvre : collez le code, puis cliquez sur ", el("b", {}, "Authorize"), "."),
        el("li", {}, "Revenez ici : vos dépôts s'affichent tout seuls.")),
      el("p", { style: "color:var(--doux);font-size:13px" }, "🔒 " + t("L'accès est rangé dans le coffre de Windows (Gestionnaire d'identification), jamais dans un fichier.")),
      el("div", { class: "actions" }, bouton)));
  }

  async function connecter(bouton) {
    bouton.disabled = true;
    let r;
    try { r = await api("/api/github/connexion/debut", {}); }
    catch (e) { toast("😕 " + e.message, "erreur", 9000); bouton.disabled = false; return; }
    finally { bouton.disabled = false; }
    try { await navigator.clipboard.writeText(r.code); } catch {}
    const etat = el("p", {}, el("span", { class: "attente" }, "⏳"), " ", t("En attente de votre validation sur GitHub…"));
    fenetre([
      el("div", { class: "gros" }, "🐙"),
      el("h3", {}, "Validez ce code sur GitHub"),
      el("div", { class: "code-gh" }, brut(r.code)),
      el("p", {}, "Il est déjà copié : collez-le sur la page github.com/login/device qui vient de s'ouvrir, puis cliquez sur Authorize."),
      etat,
      el("div", { class: "actions" },
        el("button", { class: "btn", onclick: async () => { try { await navigator.clipboard.writeText(r.code); toast("📋 " + t("Code copié"), "succes"); } catch {} } }, "📋 " + t("Copier")),
        el("button", { class: "btn", onclick: () => ouvrirPage(r.adresse) }, "🌐 " + t("Rouvrir la page")),
        el("button", { class: "btn", onclick: fermer }, "Annuler"))], true);
    const fin = Date.now() + r.expire_dans * 1000;
    while (Date.now() < fin && $("#voile").classList.contains("visible")) {
      await new Promise(ok => setTimeout(ok, 2000));
      if (!$("#voile").classList.contains("visible")) return;
      let s;
      try { s = await api("/api/github/connexion/suite", {}); }
      catch (e) { etat.textContent = "❌ " + e.message; return; }
      if (s.etat === "connecte") { fermer(); toast("🎉 " + t("GitHub connecté : {login}", { login: s.login }), "succes"); afficher(true); return; }
      if (s.etat === "refuse") { etat.textContent = "❌ " + t("Accès refusé sur GitHub."); return; }
      if (s.etat === "expire" || s.etat === "aucune") { etat.textContent = "⌛ " + t("Le code a expiré : fermez et recommencez."); return; }
    }
  }

  async function deconnecter() {
    const oui = await confirmer("🔌", "Déconnecter GitHub ?",
      "L'accès est retiré de ce PC. Pour le révoquer aussi chez GitHub : Settings > Applications > Authorized OAuth Apps.", "Déconnecter");
    if (!oui) return;
    await action("deconnexion", {}, "🔌 " + t("GitHub déconnecté"));
    afficher(true);
  }

  // -- dossiers de projets -----------------------------------------------------
  function reglerDossiers() {
    let dossiers = [...G.dossiers];
    const liste = el("div", { class: "dossiers-gh" });
    const dessinerDossiers = () => liste.replaceChildren(...(dossiers.length
      ? dossiers.map((c, i) => el("div", {}, "📁", el("span", { title: c }, brut(c)),
          el("button", { class: "icone-btn", title: "Retirer", onclick: () => { dossiers.splice(i, 1); dessinerDossiers(); } }, "✕")))
      : [el("p", {}, "Aucun dossier pour l'instant.")]));
    const champ = el("input", { placeholder: "ex. D:\\Projets", spellcheck: "false" });
    const ajouter = () => {
      const v = champ.value.trim().replace(/^"|"$/g, "");
      if (v && !dossiers.includes(v)) dossiers.push(v);
      champ.value = ""; dessinerDossiers(); champ.focus();
    };
    champ.addEventListener("keydown", e => { if (e.key === "Enter") ajouter(); });
    const enregistrer = el("button", { class: "btn principal", onclick: async () => {
      if (champ.value.trim()) ajouter();
      try {
        const r = await api("/api/github/dossiers", { dossiers });
        G.dossiers = r.dossiers; fermer(); toast("📁 " + t("Dossiers enregistrés"), "succes"); afficher(true);
      } catch (e) { toast("😕 " + e.message, "erreur", 6000); }
    } }, "Enregistrer");
    dessinerDossiers();
    fenetre([
      el("h3", {}, "📁 " + t("Dossiers de projets")),
      el("p", {}, "L'outil y cherche vos dépôts déjà présents sur ce PC (le dossier et ses sous-dossiers directs), et y clone les nouveaux."),
      liste,
      el("div", { class: "ajout-gh" }, champ, el("button", { class: "btn", onclick: ajouter }, "Ajouter")),
      el("div", { class: "actions" }, el("button", { class: "btn", onclick: fermer }, "Annuler"), enregistrer)]);
    champ.focus();
  }

  // -- cloner ------------------------------------------------------------------
  function cloner(d) {
    if (!G.dossiers.length) { reglerDossiers(); return; }
    const choix = el("select", {}, G.dossiers.map(c => el("option", { value: c }, brut(c))));
    const destination = el("small", {});
    const maj = () => { destination.textContent = t("Destination : {chemin}", { chemin: `${choix.value.replace(/[\\/]+$/, "")}\\${d.nom}` }); };
    choix.addEventListener("change", maj); maj();
    const libelle = "⬇️ " + t("Cloner");
    const bouton = el("button", { class: "btn principal", onclick: async () => {
      bouton.disabled = true;
      bouton.replaceChildren(el("span", { class: "attente" }, "⏳"), " ", t("Clonage…"));
      try {
        const r = await api("/api/github/cloner", { complet: d.complet, dossier: choix.value });
        fermer(); toast("⬇️ " + t("{nom} cloné dans {chemin}", { nom: d.nom, chemin: r.chemin }), "succes", 5000); afficher(true);
      } catch (e) { toast("😕 " + e.message, "erreur", 8000); bouton.disabled = false; bouton.textContent = libelle; }
    } }, libelle);
    fenetre([
      el("h3", {}, brut("⬇️ " + t("Cloner « {nom} »", { nom: d.nom }))),
      el("label", { class: "champ" }, "Dans le dossier", choix, destination),
      el("div", { class: "actions" }, el("button", { class: "btn", onclick: fermer }, "Annuler"), bouton)]);
  }

  // -- nouveau dépôt -----------------------------------------------------------
  function taille(o) {
    const [u0, u1, u2] = I18N.langue === "en" ? ["B", "KB", "MB"] : ["o", "Ko", "Mo"];
    const nombre = (x, chiffres) => x.toLocaleString(I18N.locale(), { maximumFractionDigits: chiffres });
    return o < 1024 ? `${o} ${u0}` : o < 1048576 ? `${nombre(o / 1024, 0)} ${u1}` : `${nombre(o / 1048576, 1)} ${u2}`;
  }

  function nouveauDepot() {
    const dossier = el("input", { placeholder: "ex. D:\\Projets\\mon-projet", spellcheck: "false" });
    const nom = el("input", { placeholder: "ex. mon-projet", spellcheck: "false" });
    const description = el("input", { placeholder: "Une phrase sur le projet (facultatif)" });
    const prive = el("input", { type: "radio", name: "visibilite-gh", checked: "" });
    const public_ = el("input", { type: "radio", name: "visibilite-gh" });
    const bilan = el("div");
    let apercu = null;
    const accord = el("input", { type: "checkbox" });
    const libelleEnvoyer = "🚀 " + t("Créer et envoyer");
    const envoyer = el("button", { class: "btn principal", disabled: "", onclick: creer }, libelleEnvoyer);
    const verifier = el("button", { class: "btn", onclick: lireApercu }, "🔍 " + t("Vérifier le contenu"));
    dossier.addEventListener("input", () => { apercu = null; envoyer.disabled = true; bilan.replaceChildren(); });
    accord.addEventListener("change", () => { envoyer.disabled = !apercu || !accord.checked; });
    const listeFichiers = fichiers => el("ul", {}, fichiers.map(f => el("li", {}, el("code", {}, brut(f)))));

    async function lireApercu() {
      verifier.disabled = true; envoyer.disabled = true;
      bilan.replaceChildren(el("p", {}, el("span", { class: "attente" }, "⏳"), " ", t("Lecture du dossier…")));
      try {
        const a = await api("/api/github/apercu", { dossier: dossier.value });
        if (a.deja_relie) {
          apercu = null;
          bilan.replaceChildren(el("div", { class: "bilan-gh danger" }, brut(t("Ce dossier est déjà relié à {depot}.", { depot: a.deja_relie }))));
          return;
        }
        apercu = a;
        dossier.value = a.dossier;
        if (!nom.value.trim()) nom.value = a.nom_suggere;
        const blocs = [el("div", { class: "bilan-gh" },
          el("b", {}, brut(t(a.nombre > 1 ? "{n} fichiers · {taille}" : "{n} fichier · {taille}", { n: a.nombre, taille: taille(a.taille) }))),
          " (les fichiers listés dans .gitignore sont exclus)",
          el("ul", {}, a.exemples.map(f => el("li", {}, el("code", {}, brut(f)))), a.nombre > a.exemples.length ? el("li", {}, "…") : null))];
        if (a.modifs_non_enregistrees) blocs.push(el("div", { class: "bilan-gh" }, "ℹ️ " + t("Ce dossier a des modifications non enregistrées (commit) : elles ne seront pas envoyées.")));
        if (a.lourds.length) blocs.push(el("div", { class: "bilan-gh" }, "⚠️ " + t("Fichiers lourds (plus de 50 Mo) :"), listeFichiers(a.lourds)));
        if (a.trop_gros.length) blocs.push(el("div", { class: "bilan-gh danger" }, "⛔ " + t("GitHub refuse les fichiers de plus de 100 Mo. Ajoutez-les à .gitignore :"), listeFichiers(a.trop_gros)));
        const risque = a.sensibles.length > 0;
        if (risque) blocs.push(el("div", { class: "bilan-gh danger" }, "🔐 " + t("Fichiers qui contiennent souvent des mots de passe ou des clés :"),
          listeFichiers(a.sensibles),
          "Ajoutez-les à .gitignore puis vérifiez à nouveau, ou cochez ci-dessous si vous êtes sûr."));
        if (risque) blocs.push(el("label", { class: "choix-gh" }, accord, "J'ai vérifié : ces fichiers peuvent être envoyés"));
        bilan.replaceChildren(...blocs);
        accord.checked = false;
        envoyer.disabled = a.trop_gros.length > 0 || risque;
      } catch (e) {
        apercu = null;
        bilan.replaceChildren(el("div", { class: "bilan-gh danger" }, "❌ " + e.message));
      } finally { verifier.disabled = false; }
    }

    async function creer() {
      if (!apercu) return;
      if (public_.checked && !(await confirmerPublic())) return;
      envoyer.disabled = true; verifier.disabled = true;
      envoyer.replaceChildren(el("span", { class: "attente" }, "⏳"), " ", t("Envoi…"));
      try {
        const r = await api("/api/github/creer", { dossier: dossier.value, nom: nom.value, description: description.value, prive: prive.checked });
        fenetre([
          el("div", { class: "gros" }, "🎉"),
          el("h3", {}, "Dépôt créé et envoyé"),
          el("p", {}, brut(t(r.nombre > 1 ? "{n} fichiers envoyés sur {depot}." : "{n} fichier envoyé sur {depot}.", { n: r.nombre, depot: r.complet }))),
          el("div", { class: "actions" },
            el("button", { class: "btn", onclick: () => ouvrirPage(r.url) }, "🌐 " + t("Voir sur GitHub")),
            el("button", { class: "btn principal", onclick: () => { fermer(); afficher(true); } }, "OK"))], true);
      } catch (e) {
        toast("😕 " + e.message, "erreur", 12000);
        envoyer.disabled = false; verifier.disabled = false; envoyer.textContent = libelleEnvoyer;
      }
    }

    // La fenêtre de confirmation remplace celle du formulaire : on garde ses
    // éléments pour la réafficher ensuite.
    let formulaire;
    async function confirmerPublic() {
      const oui = await confirmer("🌍", "Dépôt public ?", "Tout le monde pourra voir ces fichiers sur GitHub.", "Oui, public");
      fenetre(formulaire);
      return oui;
    }

    formulaire = [
      el("h3", {}, "＋ " + t("Nouveau dépôt GitHub")),
      el("p", {}, "Crée le dépôt sur votre compte et y envoie le contenu d'un dossier de ce PC."),
      el("label", { class: "champ" }, "Dossier à envoyer", dossier),
      el("label", { class: "champ" }, "Nom du dépôt", nom),
      el("label", { class: "champ" }, "Description", description),
      el("div", { class: "choix-gh" },
        el("label", {}, prive, "🔒 " + t("Privé")),
        el("label", {}, public_, "🌍 " + t("Public"))),
      bilan,
      el("div", { class: "actions" }, el("button", { class: "btn", onclick: fermer }, "Annuler"), verifier, envoyer)];
    fenetre(formulaire);
    dossier.focus();
  }

  VUES.github = { afficher, titre: "GitHub", icone: "🐙", groupe: "dev", ordre: 20 };
})();

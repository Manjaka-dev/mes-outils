"use strict";
/* Onglet « GitHub » : tous vos dépôts, clonés ou ouverts en un clic, et
   création d'un dépôt à partir d'un dossier (voir github.py). Le jeton
   GitHub reste dans le coffre de Windows : il ne passe jamais par la page. */
(() => {
  const G = { etat: null, depots: null, dossiers: [], recherche: "", filtre: "tous" };
  const COULEURS_LANGUES = { JavaScript: "#f1e05a", TypeScript: "#3178c6", Python: "#3572A5", Java: "#b07219", HTML: "#e34c26",
    CSS: "#663399", Vue: "#41b883", PHP: "#4F5D95", "C#": "#178600", Rust: "#dea584", Go: "#00ADD8", Dart: "#00B4AB",
    Kotlin: "#A97BFF", Shell: "#89e051", PowerShell: "#012456", "Jupyter Notebook": "#DA5B0B", PLpgSQL: "#336790" };

  const style = document.createElement("style");
  style.textContent = `
    .liste-gh { display: grid; grid-template-columns: repeat(auto-fill, minmax(360px, 1fr)); gap: 12px; }
    .depot { background: var(--carte); border-radius: 18px; box-shadow: var(--ombre); padding: 14px 16px; display: flex; flex-direction: column; gap: 6px; animation: apparait .3s both; min-width: 0; }
    .depot .l1 { display: flex; align-items: center; gap: 8px; min-width: 0; }
    .depot .t { font-weight: 800; font-size: 15px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; flex: 1; }
    .badge-gh { font-size: 11.5px; font-weight: 700; border-radius: 999px; padding: 2px 9px; white-space: nowrap; }
    .badge-gh.prive { background: #fdecef; color: #c2185b; }
    .badge-gh.public { background: #e7f7f1; color: #12795f; }
    .badge-gh.gris { background: #f1f0f5; color: var(--doux); }
    .depot .d { font-size: 13px; color: var(--doux); display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; min-height: 1em; }
    .depot .meta { font-size: 12.5px; color: var(--doux); display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }
    .depot .langue::before { content: ""; display: inline-block; width: 9px; height: 9px; border-radius: 50%; background: var(--c, #aaa); margin-right: 5px; }
    .depot .local { font-size: 12.5px; color: #12795f; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .depot .actions-gh { display: flex; gap: 6px; margin-top: 4px; flex-wrap: wrap; }
    .depot .actions-gh .btn { padding: 6px 12px; font-size: 13px; }
    .profil-gh { display: flex; align-items: center; gap: 8px; font-weight: 700; color: var(--doux); font-size: 14px; }
    .profil-gh img { width: 30px; height: 30px; border-radius: 50%; }
    .outils-gh input, .outils-gh select { border: 1.5px solid var(--ligne); border-radius: 12px; padding: 8px 11px; outline: none; background: #fbfaff; font: inherit; }
    .outils-gh input { width: 240px; }
    .outils-gh input:focus, .outils-gh select:focus { border-color: var(--violet); background: #fff; }
    .code-gh { font-family: Consolas, monospace; font-size: 34px; font-weight: 800; letter-spacing: 4px; background: var(--violet-clair); color: var(--violet); border-radius: 16px; padding: 14px; margin: 6px 0 14px; user-select: all; }
    .dossiers-gh { display: flex; flex-direction: column; gap: 6px; margin: 4px 0 12px; }
    .dossiers-gh div { display: flex; align-items: center; gap: 8px; background: #f7f5fe; border-radius: 12px; padding: 7px 10px; font-size: 14px; }
    .dossiers-gh div span { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    .ajout-gh { display: flex; gap: 8px; }
    .ajout-gh input { flex: 1; border: 1.5px solid var(--ligne); border-radius: 12px; padding: 9px 11px; outline: none; background: #fbfaff; font: inherit; }
    .bilan-gh { background: #f7f5fe; border-radius: 14px; padding: 12px 14px; font-size: 13.5px; margin: 8px 0; text-align: left; }
    .bilan-gh ul { margin: 6px 0 0; padding-left: 18px; }
    .bilan-gh.danger { background: #fdecef; color: #8a1538; }
    .bilan-gh code { font-size: 12.5px; }
    .choix-gh { display: flex; gap: 14px; margin: 4px 0 10px; font-size: 14px; }
    .choix-gh label { display: flex; gap: 6px; align-items: center; cursor: pointer; }
  `;
  document.head.append(style);
  const racine = () => $("#vue-github");

  // -- affichage ---------------------------------------------------------------
  async function afficher(relire = true) {
    if (relire || !G.etat) {
      try { G.etat = await api("/api/github/etat", {}); }
      catch (e) { racine().replaceChildren(el("div", { class: "vide" }, "😕 " + e.message)); return; }
      G.dossiers = G.etat.dossiers || [];
    }
    if (!G.etat.connecte) return ecranConnexion();
    if (relire || !G.depots) {
      if (!G.depots) racine().replaceChildren(el("div", { class: "vide" }, el("span", { class: "attente" }, "⏳"), " Lecture de vos dépôts…"));
      try { const r = await api("/api/github/depots", {}); G.depots = r.depots; }
      catch (e) { racine().replaceChildren(el("div", { class: "vide" }, "😕 " + e.message)); return; }
    }
    dessiner();
  }

  function dessiner() {
    const recherche = el("input", { placeholder: "Rechercher un dépôt…", value: G.recherche,
      oninput: e => { G.recherche = e.target.value; dessinerListe(); } });
    const filtre = el("select", { onchange: e => { G.filtre = e.target.value; dessinerListe(); } },
      [["tous", "Tous"], ["prive", "Privés"], ["public", "Publics"], ["local", "Sur ce PC"], ["absent", "Pas sur ce PC"]]
        .map(([v, t]) => el("option", { value: v, ...(G.filtre === v ? { selected: "" } : {}) }, t)));
    const barre = el("div", { class: "barre-vue" },
      el("h2", {}, "🐙 GitHub ", el("span", { class: "compte", id: "nb-depots" }, String(G.depots.length))),
      el("div", { class: "profil-gh" }, G.etat.avatar ? el("img", { src: G.etat.avatar, alt: "" }) : null, G.etat.login),
      el("div", { class: "espace" }),
      el("div", { class: "outils-gh", style: "display:flex;gap:8px;flex-wrap:wrap" }, recherche, filtre),
      el("button", { class: "btn principal", onclick: nouveauDepot }, "＋ Nouveau dépôt"),
      el("button", { class: "icone-btn", title: "Dossiers de projets (où chercher et cloner)", onclick: reglerDossiers }, "📁"),
      el("button", { class: "icone-btn", title: "Relire", onclick: () => afficher(true) }, "🔄"),
      el("button", { class: "icone-btn", title: "Déconnecter GitHub de ce PC", onclick: deconnecter }, "🔌"));
    const conseil = G.dossiers.length ? null : el("div", { class: "vide", style: "margin-bottom:12px" },
      "📁 Indiquez vos dossiers de projets pour voir quels dépôts sont déjà sur ce PC et pouvoir cloner : ",
      el("button", { class: "btn", onclick: reglerDossiers }, "Choisir les dossiers"));
    racine().replaceChildren(...[barre, conseil, el("div", { id: "liste-gh" })].filter(Boolean));
    dessinerListe();
  }

  function visibles() {
    const q = G.recherche.trim().toLowerCase();
    return G.depots.filter(d =>
      (!q || `${d.complet} ${d.description} ${d.langue}`.toLowerCase().includes(q)) &&
      (G.filtre === "tous" || (G.filtre === "prive" && d.prive) || (G.filtre === "public" && !d.prive) ||
       (G.filtre === "local" && d.local) || (G.filtre === "absent" && !d.local)));
  }

  function dessinerListe() {
    const liste = visibles();
    const zone = $("#liste-gh");
    if (!zone) return;
    zone.replaceChildren(liste.length
      ? el("div", { class: "liste-gh" }, liste.map(carte))
      : el("div", { class: "vide" }, G.depots.length ? "Aucun dépôt ne correspond." : "Aucun dépôt sur ce compte pour l'instant."));
  }

  const dateFr = iso => iso ? new Date(iso).toLocaleDateString("fr-FR", { day: "numeric", month: "short", year: "numeric" }) : "";

  function carte(d, i) {
    const actions = [el("button", { class: "btn", title: "Ouvrir la page du dépôt", onclick: () => ouvrirPage(d.url) }, "🌐 GitHub")];
    if (d.local) {
      actions.push(el("button", { class: "btn", title: d.local, onclick: () => action("ouvrir_dossier", { chemin: d.local }, "📂 Dossier ouvert") }, "📂 Dossier"),
        el("button", { class: "btn", title: "Ouvrir dans VS Code", onclick: () => action("vscode", { chemin: d.local }, "💻 VS Code s'ouvre…") }, "💻 VS Code"));
    } else {
      actions.push(el("button", { class: "btn", title: "Copier le dépôt sur ce PC", onclick: () => cloner(d) }, "⬇️ Cloner"));
    }
    return el("div", { class: "depot", style: `animation-delay:${Math.min(i, 20) * 25}ms` },
      el("div", { class: "l1" },
        el("div", { class: "t", title: d.complet }, d.nom),
        d.archive ? el("span", { class: "badge-gh gris" }, "Archivé") : null,
        d.fork ? el("span", { class: "badge-gh gris" }, "Fork") : null,
        el("span", { class: "badge-gh " + (d.prive ? "prive" : "public") }, d.prive ? "🔒 Privé" : "Public")),
      el("div", { class: "d" }, d.description || ""),
      el("div", { class: "meta" },
        d.langue ? el("span", { class: "langue", style: `--c:${COULEURS_LANGUES[d.langue] || "#a3a0b5"}` }, d.langue) : null,
        d.etoiles ? el("span", {}, `⭐ ${d.etoiles}`) : null,
        d.maj ? el("span", {}, `Mis à jour le ${dateFr(d.maj)}`) : null,
        d.complet.split("/")[0].toLowerCase() !== (G.etat.login || "").toLowerCase() ? el("span", {}, "👥 " + d.complet.split("/")[0]) : null),
      d.local ? el("div", { class: "local", title: d.local }, "✅ Sur ce PC : " + d.local) : null,
      el("div", { class: "actions-gh" }, actions));
  }

  async function action(nom, donnees, message) {
    try { await api("/api/github/" + nom, donnees); if (message) toast(message, "succes"); }
    catch (e) { toast("😕 " + e.message, "erreur", 6000); }
  }
  const ouvrirPage = url => action("ouvrir_page", { url });

  // -- connexion ---------------------------------------------------------------
  function ecranConnexion() {
    G.depots = null;
    const bouton = el("button", { class: "btn principal", onclick: () => connecter(bouton) }, "🐙 Connecter GitHub");
    racine().replaceChildren(el("div", { class: "connexion" },
      el("div", { style: "font-size:48px" }, "🐙"),
      el("h3", {}, "Connecter votre compte GitHub"),
      el("p", { style: "color:var(--doux);margin-top:0" }, "Une seule fois. Aucun mot de passe à saisir ici : GitHub vous montre une page où valider un code."),
      el("ol", {},
        el("li", {}, "Cliquez sur « Connecter GitHub » : un code de 8 caractères s'affiche et est copié."),
        el("li", {}, "La page github.com/login/device s'ouvre : collez le code, puis cliquez sur ", el("b", {}, "Authorize"), "."),
        el("li", {}, "Revenez ici : vos dépôts s'affichent tout seuls.")),
      el("p", { style: "color:var(--doux);font-size:13px" }, "🔒 L'accès est rangé dans le coffre de Windows (Gestionnaire d'identification), jamais dans un fichier."),
      el("div", { class: "actions" }, bouton)));
  }

  async function connecter(bouton) {
    bouton.disabled = true;
    let r;
    try { r = await api("/api/github/connexion/debut", {}); }
    catch (e) { toast("😕 " + e.message, "erreur", 9000); bouton.disabled = false; return; }
    finally { bouton.disabled = false; }
    try { await navigator.clipboard.writeText(r.code); } catch {}
    const etat = el("p", {}, el("span", { class: "attente" }, "⏳"), " En attente de votre validation sur GitHub…");
    fenetre([
      el("div", { class: "gros" }, "🐙"),
      el("h3", {}, "Validez ce code sur GitHub"),
      el("div", { class: "code-gh" }, r.code),
      el("p", {}, "Il est déjà copié : collez-le sur la page github.com/login/device qui vient de s'ouvrir, puis cliquez sur Authorize."),
      etat,
      el("div", { class: "actions" },
        el("button", { class: "btn", onclick: async () => { try { await navigator.clipboard.writeText(r.code); toast("📋 Code copié", "succes"); } catch {} } }, "📋 Copier"),
        el("button", { class: "btn", onclick: () => ouvrirPage(r.adresse) }, "🌐 Rouvrir la page"),
        el("button", { class: "btn", onclick: fermer }, "Annuler"))], true);
    const fin = Date.now() + r.expire_dans * 1000;
    while (Date.now() < fin && $("#voile").classList.contains("visible")) {
      await new Promise(ok => setTimeout(ok, 2000));
      if (!$("#voile").classList.contains("visible")) return;
      let s;
      try { s = await api("/api/github/connexion/suite", {}); }
      catch (e) { etat.textContent = "❌ " + e.message; return; }
      if (s.etat === "connecte") { fermer(); toast(`🎉 GitHub connecté : ${s.login}`, "succes"); afficher(true); return; }
      if (s.etat === "refuse") { etat.textContent = "❌ Accès refusé sur GitHub."; return; }
      if (s.etat === "expire" || s.etat === "aucune") { etat.textContent = "⌛ Le code a expiré : fermez et recommencez."; return; }
    }
  }

  async function deconnecter() {
    const oui = await confirmer("🔌", "Déconnecter GitHub ?",
      "L'accès est retiré de ce PC. Pour le révoquer aussi chez GitHub : Settings > Applications > Authorized OAuth Apps.", "Déconnecter");
    if (!oui) return;
    await action("deconnexion", {}, "🔌 GitHub déconnecté");
    afficher(true);
  }

  // -- dossiers de projets -----------------------------------------------------
  function reglerDossiers() {
    let dossiers = [...G.dossiers];
    const liste = el("div", { class: "dossiers-gh" });
    const dessinerDossiers = () => liste.replaceChildren(...(dossiers.length
      ? dossiers.map((c, i) => el("div", {}, "📁", el("span", { title: c }, c),
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
        G.dossiers = r.dossiers; fermer(); toast("📁 Dossiers enregistrés", "succes"); afficher(true);
      } catch (e) { toast("😕 " + e.message, "erreur", 6000); }
    } }, "Enregistrer");
    dessinerDossiers();
    fenetre([
      el("h3", {}, "📁 Dossiers de projets"),
      el("p", {}, "L'outil y cherche vos dépôts déjà présents sur ce PC (le dossier et ses sous-dossiers directs), et y clone les nouveaux."),
      liste,
      el("div", { class: "ajout-gh" }, champ, el("button", { class: "btn", onclick: ajouter }, "Ajouter")),
      el("div", { class: "actions" }, el("button", { class: "btn", onclick: fermer }, "Annuler"), enregistrer)]);
    champ.focus();
  }

  // -- cloner ------------------------------------------------------------------
  function cloner(d) {
    if (!G.dossiers.length) { reglerDossiers(); return; }
    const choix = el("select", {}, G.dossiers.map(c => el("option", { value: c }, c)));
    const destination = el("small", {});
    const maj = () => { destination.textContent = `Destination : ${choix.value.replace(/[\\/]+$/, "")}\\${d.nom}`; };
    choix.addEventListener("change", maj); maj();
    const bouton = el("button", { class: "btn principal", onclick: async () => {
      bouton.disabled = true;
      bouton.replaceChildren(el("span", { class: "attente" }, "⏳"), " Clonage…");
      try {
        const r = await api("/api/github/cloner", { complet: d.complet, dossier: choix.value });
        fermer(); toast(`⬇️ ${d.nom} cloné dans ${r.chemin}`, "succes", 5000); afficher(true);
      } catch (e) { toast("😕 " + e.message, "erreur", 8000); bouton.disabled = false; bouton.textContent = "⬇️ Cloner"; }
    } }, "⬇️ Cloner");
    fenetre([
      el("h3", {}, `⬇️ Cloner « ${d.nom} »`),
      el("label", { class: "champ" }, "Dans le dossier", choix, destination),
      el("div", { class: "actions" }, el("button", { class: "btn", onclick: fermer }, "Annuler"), bouton)]);
  }

  // -- nouveau dépôt -----------------------------------------------------------
  const taille = o => o < 1024 ? `${o} o` : o < 1048576 ? `${(o / 1024).toFixed(0)} Ko` : `${(o / 1048576).toFixed(1)} Mo`;

  function nouveauDepot() {
    const dossier = el("input", { placeholder: "ex. D:\\Projets\\mon-projet", spellcheck: "false" });
    const nom = el("input", { placeholder: "ex. mon-projet", spellcheck: "false" });
    const description = el("input", { placeholder: "Une phrase sur le projet (facultatif)" });
    const prive = el("input", { type: "radio", name: "visibilite-gh", checked: "" });
    const public_ = el("input", { type: "radio", name: "visibilite-gh" });
    const bilan = el("div");
    let apercu = null;
    const accord = el("input", { type: "checkbox" });
    const envoyer = el("button", { class: "btn principal", disabled: "", onclick: creer }, "🚀 Créer et envoyer");
    const verifier = el("button", { class: "btn", onclick: lireApercu }, "🔍 Vérifier le contenu");
    dossier.addEventListener("input", () => { apercu = null; envoyer.disabled = true; bilan.replaceChildren(); });
    accord.addEventListener("change", () => { envoyer.disabled = !apercu || !accord.checked; });

    async function lireApercu() {
      verifier.disabled = true; envoyer.disabled = true;
      bilan.replaceChildren(el("p", {}, el("span", { class: "attente" }, "⏳"), " Lecture du dossier…"));
      try {
        const a = await api("/api/github/apercu", { dossier: dossier.value });
        if (a.deja_relie) {
          apercu = null;
          bilan.replaceChildren(el("div", { class: "bilan-gh danger" }, `Ce dossier est déjà relié à ${a.deja_relie}.`));
          return;
        }
        apercu = a;
        dossier.value = a.dossier;
        if (!nom.value.trim()) nom.value = a.nom_suggere;
        const blocs = [el("div", { class: "bilan-gh" },
          el("b", {}, `${a.nombre} fichier${a.nombre > 1 ? "s" : ""} · ${taille(a.taille)}`), " (les fichiers listés dans .gitignore sont exclus)",
          el("ul", {}, a.exemples.map(f => el("li", {}, el("code", {}, f))), a.nombre > a.exemples.length ? el("li", {}, "…") : null))];
        if (a.modifs_non_enregistrees) blocs.push(el("div", { class: "bilan-gh" }, "ℹ️ Ce dossier a des modifications non enregistrées (commit) : elles ne seront pas envoyées."));
        if (a.lourds.length) blocs.push(el("div", { class: "bilan-gh" }, "⚠️ Fichiers lourds (plus de 50 Mo) :", el("ul", {}, a.lourds.map(f => el("li", {}, el("code", {}, f))))));
        if (a.trop_gros.length) blocs.push(el("div", { class: "bilan-gh danger" }, "⛔ GitHub refuse les fichiers de plus de 100 Mo. Ajoutez-les à .gitignore :", el("ul", {}, a.trop_gros.map(f => el("li", {}, el("code", {}, f))))));
        const risque = a.sensibles.length > 0;
        if (risque) blocs.push(el("div", { class: "bilan-gh danger" }, "🔐 Fichiers qui contiennent souvent des mots de passe ou des clés :",
          el("ul", {}, a.sensibles.map(f => el("li", {}, el("code", {}, f)))),
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
      envoyer.replaceChildren(el("span", { class: "attente" }, "⏳"), " Envoi…");
      try {
        const r = await api("/api/github/creer", { dossier: dossier.value, nom: nom.value, description: description.value, prive: prive.checked });
        fenetre([
          el("div", { class: "gros" }, "🎉"),
          el("h3", {}, "Dépôt créé et envoyé"),
          el("p", {}, `${r.nombre} fichier${r.nombre > 1 ? "s" : ""} envoyé${r.nombre > 1 ? "s" : ""} sur ${r.complet}.`),
          el("div", { class: "actions" },
            el("button", { class: "btn", onclick: () => ouvrirPage(r.url) }, "🌐 Voir sur GitHub"),
            el("button", { class: "btn principal", onclick: () => { fermer(); afficher(true); } }, "OK"))], true);
      } catch (e) {
        toast("😕 " + e.message, "erreur", 12000);
        envoyer.disabled = false; verifier.disabled = false; envoyer.textContent = "🚀 Créer et envoyer";
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
      el("h3", {}, "＋ Nouveau dépôt GitHub"),
      el("p", {}, "Crée le dépôt sur votre compte et y envoie le contenu d'un dossier de ce PC."),
      el("label", { class: "champ" }, "Dossier à envoyer", dossier),
      el("label", { class: "champ" }, "Nom du dépôt", nom),
      el("label", { class: "champ" }, "Description", description),
      el("div", { class: "choix-gh" },
        el("label", {}, prive, "🔒 Privé"),
        el("label", {}, public_, "🌍 Public")),
      bilan,
      el("div", { class: "actions" }, el("button", { class: "btn", onclick: fermer }, "Annuler"), verifier, envoyer)];
    fenetre(formulaire);
    dossier.focus();
  }

  VUES.github = { afficher };
})();

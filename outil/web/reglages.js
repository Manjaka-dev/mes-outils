"use strict";
/* Onglet « Réglages » : prénom, langue, onglets affichés, dossiers de projets,
   raccourcis Windows, mise à jour (voir reglages.py). */
(() => {
  const R = { infos: null };

  I18N.ajouter({
    "Réglages": "Settings",
    "Profil": "Profile",
    "Prénom (pour la salutation)": "First name (for the greeting)",
    "ex. Marie": "e.g. Mary",
    "Langue": "Language",
    "Thème": "Theme",
    "🌗 Automatique": "🌗 Automatic",
    "☀️ Clair": "☀️ Light",
    "🌙 Sombre": "🌙 Dark",
    "Onglets affichés": "Visible tabs",
    "Décochez les onglets dont vous ne vous servez pas : ils disparaissent du menu (rien n'est effacé).":
      "Untick the tabs you don't use: they disappear from the menu (nothing is deleted).",
    "Dossiers de projets": "Project folders",
    "Les onglets GitHub, Projets et État Git y cherchent vos projets (le dossier et ses sous-dossiers directs).":
      "The GitHub, Projects and Git status tabs look for your projects there (the folder and its direct subfolders).",
    "＋ Ajouter un dossier": "＋ Add a folder",
    "Aucun dossier pour l'instant.": "No folder yet.",
    "Retirer": "Remove",
    "Windows": "Windows",
    "Lancer la bulle au démarrage de Windows": "Start the bubble with Windows",
    "Raccourci « Mes outils » sur le Bureau": "“Mes outils” shortcut on the Desktop",
    "Boîte mail": "Mailbox",
    "La boîte mail se connecte dans l'onglet Mails.": "The mailbox is connected in the Mails tab.",
    "Ouvrir l'onglet Mails": "Open the Mails tab",
    "À propos": "About",
    "Version {v}": "Version {v}",
    "🌐 Code source sur GitHub": "🌐 Source code on GitHub",
    "🔄 Rechercher une mise à jour": "🔄 Check for updates",
    "Recherche…": "Checking…",
    "✅ Mis à jour : la page va se recharger": "✅ Updated: the page will reload",
    "Déjà à jour 👍": "Already up to date 👍",
    "Enregistré": "Saved",
    "Choisir un dossier de projets": "Choose a projects folder",
    "Installé sans git clone : téléchargez la nouvelle version sur GitHub.": "Installed without git clone: download the new version from GitHub.",
    "Relancez la bulle (clic droit › Quitter, puis le raccourci) pour finir la mise à jour.":
      "Restart the bubble (right-click › Quit, then the shortcut) to finish the update.",
  });

  const style = document.createElement("style");
  style.textContent = `
    .reglages { display: grid; grid-template-columns: repeat(auto-fill, minmax(380px, 1fr)); gap: 16px; align-items: start; }
    .carte-reg { background: var(--carte); border: 1px solid var(--bord); border-radius: var(--rayon); box-shadow: var(--ombre); padding: 18px 20px; animation: apparait .35s both; }
    .carte-reg h3 { margin: 0 0 12px; font-size: 16px; display: flex; gap: 8px; align-items: center; }
    .carte-reg p.aide { color: var(--doux); font-size: 13px; margin: -4px 0 12px; }
    .cases-reg { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 4px 12px; }
    .case-reg { display: flex; align-items: center; gap: 8px; padding: 5px 4px; border-radius: 10px; cursor: pointer; font-weight: 600; font-size: 14px; }
    .case-reg:hover { background: var(--surface); }
    .case-reg input { width: 17px; height: 17px; accent-color: var(--violet); flex: none; }
    .liste-reg { display: flex; flex-direction: column; gap: 6px; margin-bottom: 10px; }
    .liste-reg div { display: flex; align-items: center; gap: 8px; background: var(--surface); border-radius: 12px; padding: 7px 10px; font-size: 14px; }
    .liste-reg div span { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    .langues-reg { display: flex; gap: 8px; flex-wrap: wrap; }
  `;
  document.head.append(style);

  async function charger() {
    R.infos = await api("/api/reglages/lire", {});
    dessiner();
  }

  async function enregistrer(valeurs, recharger = false) {
    try {
      R.infos = await api("/api/reglages/enregistrer", valeurs);
      toast("✅ " + t("Enregistré"), "succes", 1400);
      if (recharger) setTimeout(() => location.reload(), 500);
      else {
        S.masques = R.infos.onglets_masques;
        if (S.config && "prenom" in valeurs) { S.config.prenom = R.infos.prenom; horloge(); }
        construireMenu();
      }
    } catch (e) { toast("😕 " + e.message, "erreur"); }
  }

  function carte(icone, titre, ...contenu) {
    return el("div", { class: "carte-reg" }, el("h3", {}, icone + " " + t(titre)), ...contenu);
  }

  function dessiner() {
    const i = R.infos;
    const prenom = el("input", { value: i.prenom, placeholder: "ex. Marie", maxlength: 40 });
    let minuterie;
    prenom.addEventListener("input", () => { clearTimeout(minuterie); minuterie = setTimeout(() => enregistrer({ prenom: prenom.value }), 700); });

    const langues = el("div", { class: "langues-reg" }, [["fr", "Français"], ["en", "English"]].map(([code, nom]) =>
      el("button", { class: "btn" + (i.langue === code ? " actif" : ""), onclick: () => { if (code !== i.langue) enregistrer({ langue: code }, true); } }, nom)));

    const themes = el("div", { class: "langues-reg" }, [["auto", "🌗 Automatique"], ["clair", "☀️ Clair"], ["sombre", "🌙 Sombre"]].map(([code, nom]) =>
      el("button", { class: "btn" + (S.theme === code ? " actif" : ""), onclick: async () => { await changerTheme(code); dessiner(); } }, nom)));

    const masques = new Set(i.onglets_masques);
    const onglets = listeOnglets().filter(o => o.nom !== "accueil" && o.nom !== "reglages")
      .sort((a, b) => (Object.keys(GROUPES).indexOf(a.groupe) - Object.keys(GROUPES).indexOf(b.groupe)) || ((a.ordre ?? 99) - (b.ordre ?? 99)));
    const cases = el("div", { class: "cases-reg" }, onglets.map(o =>
      el("label", { class: "case-reg" },
        el("input", { type: "checkbox", checked: masques.has(o.nom) ? null : "", onchange: e => {
          if (e.target.checked) masques.delete(o.nom); else masques.add(o.nom);
          enregistrer({ onglets_masques: [...masques] });
        } }), (o.icone || "🧩") + " " + I18N.traduire(o.titre))));

    const listeDossiers = el("div", { class: "liste-reg" },
      i.dossiers_projets.length ? i.dossiers_projets.map(d => el("div", {}, "📁", el("span", { title: d }, d),
        el("button", { class: "icone-btn", title: "Retirer", onclick: () => majDossiers(i.dossiers_projets.filter(x => x !== d)) }, "✕")))
        : el("div", { style: "color:var(--doux)" }, "Aucun dossier pour l'instant."));
    const ajoutDossier = el("button", { class: "btn", onclick: async () => {
      const chemin = await choisirDossier("Choisir un dossier de projets");
      if (chemin) majDossiers([...i.dossiers_projets, chemin]);
    } }, "＋ Ajouter un dossier");

    const interrupteur = (genre, texte) => el("label", { class: "case-reg" },
      el("input", { type: "checkbox", checked: i.raccourcis[genre] ? "" : null, onchange: async e => {
        try { R.infos = await api("/api/reglages/raccourci", { genre, actif: e.target.checked }); toast("✅ " + t("Enregistré"), "succes", 1400); }
        catch (err) { e.target.checked = !e.target.checked; toast("😕 " + err.message, "erreur"); }
      } }), texte);

    const majBtn = el("button", { class: "btn", onclick: async () => {
      if (!i.maj_possible) { toast(t("Installé sans git clone : téléchargez la nouvelle version sur GitHub."), "", 5000); return; }
      majBtn.disabled = true; majBtn.textContent = t("Recherche…");
      try {
        const r = await api("/api/reglages/mise_a_jour", {});
        if (r.change) { toast(t("✅ Mis à jour : la page va se recharger"), "succes", 3000); toast(t("Relancez la bulle (clic droit › Quitter, puis le raccourci) pour finir la mise à jour."), "", 9000); setTimeout(() => location.reload(), 2500); }
        else toast(t("Déjà à jour 👍"), "succes");
      } catch (e) { toast("😕 " + e.message, "erreur", 7000); }
      finally { majBtn.disabled = false; majBtn.textContent = t("🔄 Rechercher une mise à jour"); }
    } }, "🔄 Rechercher une mise à jour");

    $("#vue-reglages").replaceChildren(
      el("div", { class: "barre-vue" }, el("h2", {}, "⚙️ " + t("Réglages"))),
      el("div", { class: "reglages" },
        carte("👤", "Profil",
          el("label", { class: "champ" }, "Prénom (pour la salutation)", prenom),
          el("label", { class: "champ" }, "Langue", langues),
          el("label", { class: "champ" }, "Thème", themes)),
        carte("🗂️", "Onglets affichés", el("p", { class: "aide" }, "Décochez les onglets dont vous ne vous servez pas : ils disparaissent du menu (rien n'est effacé)."), cases),
        carte("📁", "Dossiers de projets", el("p", { class: "aide" }, "Les onglets GitHub, Projets et État Git y cherchent vos projets (le dossier et ses sous-dossiers directs)."),
          listeDossiers, ajoutDossier),
        carte("💻", "Windows", interrupteur("demarrage", "Lancer la bulle au démarrage de Windows"),
          interrupteur("bureau", "Raccourci « Mes outils » sur le Bureau")),
        carte("✉️", "Boîte mail", el("p", { class: "aide" }, "La boîte mail se connecte dans l'onglet Mails."),
          el("button", { class: "btn", onclick: () => montrerVue("mails") }, "Ouvrir l'onglet Mails")),
        carte("🧰", "À propos", el("p", { class: "aide" }, t("Version {v}", { v: i.version })),
          el("div", { style: "display:flex;gap:8px;flex-wrap:wrap" },
            el("button", { class: "btn", onclick: () => api("/api/github/ouvrir_page", { url: i.depot }).catch(e => toast("😕 " + e.message, "erreur")) }, "🌐 Code source sur GitHub"),
            majBtn))));
  }

  async function majDossiers(liste) {
    try { R.infos = await api("/api/reglages/dossiers", { dossiers: liste }); dessiner(); toast("✅ " + t("Enregistré"), "succes", 1400); }
    catch (e) { toast("😕 " + e.message, "erreur"); }
  }

  VUES.reglages = { afficher: () => charger().catch(e => toast("😕 " + e.message, "erreur")),
    titre: "Réglages", icone: "⚙️", groupe: "systeme", ordre: 90 };
})();

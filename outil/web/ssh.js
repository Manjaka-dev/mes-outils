"use strict";
/* Onglet « Serveurs SSH » : une clé par serveur, posée en un clic (voir
   ssh_cles.py). Le mot de passe saisi part une seule fois au serveur local,
   pour la première connexion ; il n'est ni gardé ni réaffiché. */
(() => {
  const X = { serveurs: [] };
  const COULEURS_SSH = ["#2f8cff", "#6c4cf5", "#18b597", "#ff7a59", "#e5488d", "#ffb020", "#0ea5a4"];

  const style = document.createElement("style");
  style.textContent = `
    .liste-ssh { display: grid; grid-template-columns: repeat(auto-fill, minmax(380px, 1fr)); gap: 12px; }
    .srv { background: var(--carte); border-radius: 18px; box-shadow: var(--ombre); padding: 14px 16px; display: flex; gap: 12px; align-items: center; animation: apparait .3s both; }
    .srv .av { width: 46px; height: 46px; border-radius: 15px; display: grid; place-items: center; font-size: 22px; flex: none; color: #fff; }
    .srv .infos { flex: 1; min-width: 0; }
    .srv .t { font-weight: 800; font-size: 15px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .srv .u { font-size: 13px; color: var(--doux); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .srv .cmd { font-family: Consolas, monospace; font-size: 13px; background: #f4f2fc; border-radius: 8px; padding: 2px 8px; margin-top: 5px; display: inline-block; cursor: pointer; }
    .srv .cmd:hover { background: var(--violet-clair); color: var(--violet); }
    .srv .etat-test { font-size: 12px; margin-top: 4px; color: var(--doux); }
    .srv .etat-test.ok { color: #12a386; }
    .srv .etat-test.ko { color: var(--rouge); }
    .srv .actions-srv { display: flex; gap: 4px; }
    .note-ssh { background: #eef6ff; border-radius: 14px; padding: 12px 14px; font-size: 13.5px; color: #24507a; margin: 4px 0 14px; text-align: left; }
    .ligne-champs { display: grid; grid-template-columns: 1fr 110px; gap: 10px; }
    .attente { display: inline-block; animation: tourne 1s linear infinite; }
    @keyframes tourne { to { transform: rotate(360deg); } }
  `;
  document.head.append(style);
  const racine = () => $("#vue-ssh");

  async function charger() {
    const { serveurs } = await api("/api/ssh/liste", {});
    X.serveurs = serveurs;
  }

  async function afficher() {
    try { await charger(); } catch (e) { toast(e.message, "erreur"); }
    const r = racine();
    const barre = el("div", { class: "barre-vue" },
      el("h2", {}, "🔑 Serveurs SSH ", el("span", { class: "compte" }, String(X.serveurs.length))),
      el("div", { class: "espace" }),
      el("button", { class: "btn principal", onclick: nouveau }, "＋ Nouveau serveur"));
    const liste = X.serveurs.length
      ? el("div", { class: "liste-ssh" }, X.serveurs.map(carte))
      : el("div", { class: "vide" }, "Aucun serveur pour l'instant. « ＋ Nouveau serveur » : saisissez l'adresse, l'utilisateur et le mot de passe, la clé est créée et installée pour vous.");
    r.replaceChildren(barre, liste);
  }

  // « 2026-11-06 19:23 » → « 06/11/2026 à 19:23 »
  function dateFr(texte) {
    const m = /^(\d{4})-(\d{2})-(\d{2}) (\d{2}:\d{2})/.exec(texte || "");
    return m ? `${m[3]}/${m[2]}/${m[1]} à ${m[4]}` : texte;
  }

  function carte(s, i) {
    const etat = el("div", { class: "etat-test" + (s.dernier_resultat === "ok" ? " ok" : "") },
      !s.cle_presente ? "⚠️ Clé absente de ce PC" : s.dernier_test ? `✅ Connexion vérifiée le ${dateFr(s.dernier_test)}` : "Pas encore testé");
    const boutons = el("div", { class: "actions-srv" },
      el("button", { class: "icone-btn", title: "Tester la connexion", onclick: e => tester(s, etat, e.currentTarget) }, "🧪"),
      el("button", { class: "icone-btn", title: "Ouvrir un terminal sur ce serveur", onclick: () => terminal(s) }, "💻"),
      el("button", { class: "icone-btn", title: "Retirer la clé du serveur et de ce PC", onclick: () => retirer(s) }, "🗑️"));
    return el("div", { class: "srv", style: `animation-delay:${i * 40}ms` },
      el("div", { class: "av", style: `background:${COULEURS_SSH[i % COULEURS_SSH.length]}` }, "🖥️"),
      el("div", { class: "infos" },
        el("div", { class: "t", title: s.nom }, s.nom),
        el("div", { class: "u" }, `${s.utilisateur}@${s.hote} · port ${s.port}`),
        el("span", { class: "cmd", title: "Copier la commande", onclick: () => copier(`ssh ${s.alias}`) }, `ssh ${s.alias}`),
        etat),
      boutons);
  }

  async function copier(texte) {
    try { await navigator.clipboard.writeText(texte); toast(`📋 « ${texte} » copié`, "succes"); }
    catch { toast("Copie impossible", "erreur"); }
  }

  async function tester(s, etat, bouton) {
    bouton.disabled = true;
    etat.className = "etat-test";
    etat.replaceChildren(el("span", { class: "attente" }, "⏳"), " Connexion…");
    try {
      const r = await api("/api/ssh/tester", { alias: s.alias });
      toast(`✅ Connexion réussie${r.machine ? " à " + r.machine : ""}, sans mot de passe`, "succes");
      await afficher();
    } catch (e) {
      etat.className = "etat-test ko";
      etat.textContent = "❌ " + e.message;
    } finally { bouton.disabled = false; }
  }

  async function terminal(s) {
    try { await api("/api/ssh/terminal", { alias: s.alias }); toast("💻 Terminal ouvert", "succes"); }
    catch (e) { toast(e.message, "erreur"); }
  }

  async function retirer(s) {
    const oui = await confirmer("🗑️", `Retirer « ${s.nom} » ?`,
      "La clé est retirée du serveur, puis supprimée de ce PC. Pour y revenir sans mot de passe, il faudra recréer une clé.",
      "Retirer");
    if (!oui) return;
    try {
      const r = await api("/api/ssh/retirer", { alias: s.alias });
      if (r.avertissement) toast("⚠️ " + r.avertissement, "erreur", 9000);
      else toast("🗑️ Clé retirée du serveur et de ce PC", "succes");
      afficher();
    } catch (e) { toast(e.message, "erreur"); }
  }

  function nouveau() {
    const champ = (attrs) => el("input", { autocomplete: "off", spellcheck: "false", ...attrs });
    const nom = champ({ placeholder: "ex. Serveur web" });
    const hote = champ({ placeholder: "ex. 213.136.92.160" });
    const port = champ({ value: "22", inputmode: "numeric" });
    const utilisateur = champ({ value: "root" });
    const mdp = champ({ type: "password", autocomplete: "new-password" });
    const oeil = el("button", { class: "icone-btn", type: "button", title: "Afficher", onclick: () => { mdp.type = mdp.type === "password" ? "text" : "password"; } }, "👁️");
    const message = el("div");
    const bouton = el("button", { class: "btn principal", onclick: async () => {
      bouton.disabled = true;
      bouton.replaceChildren(el("span", { class: "attente" }, "⏳"), " Installation…");
      message.replaceChildren();
      try {
        const r = await api("/api/ssh/creer", { nom: nom.value, hote: hote.value, port: port.value, utilisateur: utilisateur.value, mot_de_passe: mdp.value });
        mdp.value = "";
        fenetre([
          el("div", { class: "gros" }, "✅"),
          el("h3", {}, "Clé installée"),
          el("p", {}, `Connexion vérifiée${r.machine ? " sur « " + r.machine + " »" : ""}, sans mot de passe. Désormais, dans un terminal :`),
          el("div", { class: "genere", style: "font-size:17px" }, `ssh ${r.serveur.alias}`),
          el("div", { class: "actions" },
            el("button", { class: "btn", onclick: () => copier(`ssh ${r.serveur.alias}`) }, "📋 Copier"),
            el("button", { class: "btn principal", onclick: () => { fermer(); afficher(); } }, "OK"))], true);
      } catch (e) {
        message.replaceChildren(el("div", { class: "alerte" }, "❌ " + e.message));
        bouton.disabled = false;
        bouton.textContent = "🔑 Créer et installer la clé";
      }
    } }, "🔑 Créer et installer la clé");
    mdp.addEventListener("keydown", e => { if (e.key === "Enter") bouton.click(); });
    fenetre([
      el("h3", {}, "🔑 Nouveau serveur SSH"),
      el("div", { class: "note-ssh" }, "Une clé est créée pour ce serveur et déposée avec le mot de passe. Le mot de passe ne sert qu'à cette première connexion : il n'est pas enregistré."),
      el("label", { class: "champ" }, "Nom du serveur", nom),
      el("div", { class: "ligne-champs" },
        el("label", { class: "champ" }, "Adresse IP ou nom", hote),
        el("label", { class: "champ" }, "Port SSH", port)),
      el("label", { class: "champ" }, "Utilisateur", utilisateur),
      el("label", { class: "champ" }, "Mot de passe du serveur", el("div", { class: "avec-oeil" }, mdp, oeil)),
      message,
      el("div", { class: "actions" },
        el("button", { class: "btn", onclick: fermer }, "Annuler"),
        bouton)]);
    nom.focus();
  }

  VUES.ssh = { afficher };
})();

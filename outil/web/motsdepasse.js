"use strict";
/* Onglet « Mots de passe » : coffre chiffré (voir coffre.py).
   Les secrets ne viennent jamais dans la liste : ils ne sont demandés au
   serveur qu'au moment de les copier ou de les afficher, un par un. */
(() => {
  const CATEGORIES = ["Clients Odoo", "Serveurs", "Mails", "Banque", "Travail", "Personnel"];
  const COULEURS_CAT = { "Clients Odoo": "#6c4cf5", "Serveurs": "#2f8cff", "Mails": "#ff7a59", "Banque": "#18b597", "Travail": "#ffb020", "Personnel": "#e5488d" };
  const C = { etat: null, entrees: [], recherche: "", categorie: "toutes", fin: 0, minuterie: null };

  const style = document.createElement("style");
  style.textContent = `
    .coffre-ecran { max-width: 520px; margin: 20px auto; background: var(--carte); border-radius: 26px; box-shadow: var(--ombre); padding: 30px; text-align: center; animation: apparait .35s both; }
    .coffre-ecran .cadenas { font-size: 64px; animation: balance 2.6s ease-in-out infinite; display: inline-block; }
    @keyframes balance { 25% { transform: rotate(-8deg); } 75% { transform: rotate(8deg); } }
    .coffre-ecran h3 { margin: 8px 0 6px; font-size: 22px; }
    .coffre-ecran p { color: var(--doux); }
    .coffre-ecran .champ { text-align: left; }
    .alerte { background: #fff4dc; border-radius: 14px; padding: 12px 14px; text-align: left; font-size: 13.5px; color: #6b4a00; margin: 12px 0; }
    .jauge { height: 7px; border-radius: 9px; background: #eceaf6; overflow: hidden; margin-top: 6px; }
    .jauge div { height: 100%; border-radius: 9px; transition: width .3s, background .3s; }
    .jauge-texte { font-size: 12px; font-weight: 700; margin-top: 4px; }
    .liste-mdp { display: grid; grid-template-columns: repeat(auto-fill, minmax(360px, 1fr)); gap: 12px; }
    .mdp { background: var(--carte); border-radius: 18px; box-shadow: var(--ombre); padding: 12px 14px; display: flex; gap: 12px; align-items: center; animation: apparait .3s both; }
    .mdp .av { width: 42px; height: 42px; border-radius: 14px; display: grid; place-items: center; color: #fff; font-weight: 800; font-size: 17px; flex: none; }
    .mdp .infos { flex: 1; min-width: 0; }
    .mdp .t { font-weight: 800; font-size: 15px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .mdp .u { font-size: 13px; color: var(--doux); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .mdp .secret { font-family: Consolas, monospace; font-size: 13.5px; background: #f4f2fc; border-radius: 8px; padding: 2px 7px; margin-top: 4px; display: inline-block; max-width: 100%; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    .mdp .actions-mdp { display: flex; gap: 4px; }
    .minuterie { font-size: 12.5px; color: var(--doux); font-variant-numeric: tabular-nums; }
    .genere { font-family: Consolas, monospace; font-size: 20px; background: #f4f2fc; border-radius: 14px; padding: 14px; word-break: break-all; text-align: center; margin: 10px 0; letter-spacing: .5px; }
    .options-gen { display: flex; flex-wrap: wrap; gap: 8px 18px; margin: 8px 0 4px; font-size: 14px; }
    .options-gen label { display: flex; gap: 6px; align-items: center; cursor: pointer; }
    .avec-oeil { display: flex; gap: 6px; }
    .avec-oeil input { flex: 1; min-width: 0; font-family: Consolas, monospace; }
  `;
  document.head.append(style);
  const racine = () => $("#vue-motsdepasse");

  // -- solidité d'un mot de passe ---------------------------------------------
  function solidite(mdp) {
    if (!mdp) return { score: 0, texte: "", couleur: "#eceaf6" };
    let jeu = 0;
    if (/[a-z]/.test(mdp)) jeu += 26;
    if (/[A-Z]/.test(mdp)) jeu += 26;
    if (/\d/.test(mdp)) jeu += 10;
    if (/[^a-zA-Z0-9]/.test(mdp)) jeu += 32;
    let bits = mdp.length * Math.log2(Math.max(jeu, 2));
    if (/(.)\1\1/.test(mdp) || /^(?:123|abc|azerty|qwerty|password|motdepasse)/i.test(mdp)) bits *= 0.6;
    if (bits < 40) return { score: 20, texte: "Faible 😟", couleur: "#e5484d" };
    if (bits < 60) return { score: 50, texte: "Moyen 😐", couleur: "#ffb020" };
    if (bits < 80) return { score: 78, texte: "Bon 🙂", couleur: "#2f8cff" };
    return { score: 100, texte: "Excellent 💪", couleur: "#18b597" };
  }
  function jauge(champ) {
    const barre = el("div", { style: "width:0" }), texte = el("div", { class: "jauge-texte" });
    const maj = () => { const s = solidite(champ.value); barre.style.width = s.score + "%"; barre.style.background = s.couleur; texte.textContent = s.texte; texte.style.color = s.couleur; };
    champ.addEventListener("input", maj); maj();
    return [el("div", { class: "jauge" }, barre), texte];
  }

  // -- générateur --------------------------------------------------------------
  function generer({ longueur = 20, majuscules = true, chiffres = true, symboles = true, ambigus = false } = {}) {
    let jeux = ["abcdefghijkmnopqrstuvwxyz"];
    if (majuscules) jeux.push("ABCDEFGHJKLMNPQRSTUVWXYZ");
    if (chiffres) jeux.push("23456789");
    if (symboles) jeux.push("!@#$%&*+-=?_.:");
    if (ambigus) jeux = jeux.map((j, i) => j + ["lo", "IO", "01", "()[]{}"][i]);
    const tout = jeux.join("");
    const hasard = n => { const t = new Uint32Array(1); let x; do { crypto.getRandomValues(t); x = t[0]; } while (x >= Math.floor(2 ** 32 / n) * n); return x % n; };
    // Au moins un caractère de chaque famille choisie, puis on mélange.
    const car = jeux.map(j => j[hasard(j.length)]);
    while (car.length < longueur) car.push(tout[hasard(tout.length)]);
    for (let i = car.length - 1; i > 0; i--) { const j = hasard(i + 1); [car[i], car[j]] = [car[j], car[i]]; }
    return car.join("");
  }
  function fenetreGenerateur(versChamp) {
    const opts = { longueur: 20, majuscules: true, chiffres: true, symboles: true };
    const sortie = el("div", { class: "genere" });
    const valeur = el("span");
    const longueur = el("input", { type: "range", min: "8", max: "48", value: "20", style: "width:100%;accent-color:var(--violet)" });
    const etiquette = el("b", {}, "20 caractères");
    const s = el("div", { class: "jauge-texte", style: "text-align:center" });
    const relancer = () => { const v = generer(opts); valeur.textContent = v; sortie.replaceChildren(valeur); const x = solidite(v); s.textContent = x.texte; s.style.color = x.couleur; };
    longueur.addEventListener("input", () => { opts.longueur = Number(longueur.value); etiquette.textContent = `${opts.longueur} caractères`; relancer(); });
    const coche = (cle, texte) => el("label", {}, el("input", { type: "checkbox", checked: opts[cle] ? "" : null, style: "accent-color:var(--violet)", onchange: e => { opts[cle] = e.target.checked; relancer(); } }), texte);
    fenetre([
      el("h3", {}, "🎲 Générateur de mot de passe"),
      sortie, s,
      el("label", { class: "champ" }, etiquette, longueur),
      el("div", { class: "options-gen" }, coche("majuscules", "Majuscules"), coche("chiffres", "Chiffres"), coche("symboles", "Symboles")),
      el("div", { class: "actions" },
        el("button", { class: "btn", onclick: relancer }, "🔄 Un autre"),
        versChamp ? el("button", { class: "btn principal", onclick: () => { versChamp(valeur.textContent); } }, "✅ Utiliser")
          : el("button", { class: "btn principal", onclick: async () => {
            await api("/api/coffre/presse_papiers", { texte: valeur.textContent });
            toast("📋 Copié — effacé du presse-papiers dans 30 s", "succes");
          } }, "📋 Copier"))]);
    relancer();
  }

  // -- verrouillage ------------------------------------------------------------
  function suivreEtat(etat) {
    C.etat = { ...C.etat, ...etat };
    C.fin = Date.now() + (etat.restant || 0) * 1000;
    if (!C.minuterie) C.minuterie = setInterval(tictac, 1000);
  }
  function tictac() {
    const m = $("#minuterie-coffre");
    if (!C.etat?.ouvert) return;
    const reste = Math.max(0, Math.round((C.fin - Date.now()) / 1000));
    if (m) m.textContent = `🔒 se verrouille dans ${Math.floor(reste / 60)}:${String(reste % 60).padStart(2, "0")}`;
    if (reste <= 0) { C.etat.ouvert = false; C.entrees = []; if (S.vue === "motsdepasse") ecranVerrouille(); }
  }
  async function appel(chemin, corps) {
    try {
      const r = await api(chemin, corps);
      if ("ouvert" in r) suivreEtat(r);
      return r;
    } catch (e) {
      if (/verrouillé/.test(e.message)) { C.etat.ouvert = false; ecranVerrouille(); }
      throw e;
    }
  }

  async function afficher() {
    try { suivreEtat(await api("/api/coffre/etat", {})); } catch (e) { toast("😕 " + e.message, "erreur"); return; }
    if (!C.etat.existe) return ecranCreation();
    if (!C.etat.ouvert) return ecranVerrouille();
    await chargerListe();
  }

  function ecranCreation() {
    const m1 = el("input", { type: "password", autocomplete: "new-password", placeholder: "ex. une phrase de 4 ou 5 mots" });
    const m2 = el("input", { type: "password", autocomplete: "new-password" });
    const compris = el("input", { type: "checkbox", style: "accent-color:var(--violet);width:17px;height:17px" });
    const bouton = el("button", { class: "btn principal", onclick: async () => {
      if (m1.value !== m2.value) { toast("Les deux mots de passe ne sont pas identiques", "erreur"); return; }
      if (!compris.checked) { toast("Cochez la case : c'est important 🙏", "erreur"); return; }
      bouton.disabled = true; bouton.textContent = "Création…";
      try { await appel("/api/coffre/creer", { maitre: m1.value }); m1.value = m2.value = ""; toast("🎉 Coffre créé et ouvert !", "succes"); await chargerListe(); }
      catch (e) { toast("😕 " + e.message, "erreur", 6000); bouton.disabled = false; bouton.textContent = "Créer le coffre"; }
    } }, "Créer le coffre");
    racine().replaceChildren(el("div", { class: "coffre-ecran" },
      el("div", { class: "cadenas" }, "🔐"),
      el("h3", {}, "Créer votre coffre"),
      el("p", {}, "Choisissez un mot de passe maître : c'est le seul que vous aurez à retenir. Il ouvre le coffre, et il n'est enregistré nulle part."),
      el("label", { class: "champ" }, "Mot de passe maître", m1, ...jauge(m1)),
      el("label", { class: "champ" }, "Le retaper", m2),
      el("div", { class: "alerte" }, "⚠️ ", el("b", {}, "Si vous l'oubliez, personne ne pourra ouvrir le coffre"), " — ni vous, ni moi : c'est ce qui le rend sûr. Notez-le sur papier, rangé en lieu sûr."),
      el("label", { class: "champ", style: "flex-direction:row;align-items:center;gap:8px" }, compris, "J'ai compris et noté mon mot de passe maître"),
      el("div", { class: "actions", style: "justify-content:center" }, bouton)));
    setTimeout(() => m1.focus(), 50);
  }

  function ecranVerrouille() {
    const m = el("input", { type: "password", autocomplete: "current-password", placeholder: "Mot de passe maître",
      onkeydown: e => { if (e.key === "Enter") ouvrir(); } });
    const bouton = el("button", { class: "btn principal", onclick: () => ouvrir() }, "🔓 Déverrouiller");
    async function ouvrir() {
      bouton.disabled = true; bouton.textContent = "Ouverture…";
      try { await appel("/api/coffre/ouvrir", { maitre: m.value }); m.value = ""; await chargerListe(); }
      catch (e) { toast("😕 " + e.message, "erreur", 5000); m.select(); bouton.disabled = false; bouton.textContent = "🔓 Déverrouiller"; }
    }
    racine().replaceChildren(el("div", { class: "coffre-ecran" },
      el("div", { class: "cadenas" }, "🔒"),
      el("h3", {}, "Coffre verrouillé"),
      el("p", {}, "Il se referme tout seul après 5 minutes sans utilisation."),
      el("label", { class: "champ" }, m),
      el("div", { class: "actions", style: "justify-content:center" }, bouton)));
    setTimeout(() => m.focus(), 50);
  }

  // -- liste ---------------------------------------------------------------------
  async function chargerListe() {
    const r = await appel("/api/coffre/liste", {});
    C.entrees = r.entrees;
    dessiner();
  }
  function dessiner() {
    const cats = [...new Set(C.entrees.map(e => e.categorie).filter(Boolean))].sort();
    const recherche = el("input", { placeholder: "Chercher (nom, identifiant, site)…", value: C.recherche,
      oninput: e => { C.recherche = e.target.value; dessinerListe(); } });
    racine().replaceChildren(...[
      el("div", { class: "barre-vue" },
        el("h2", {}, "🔐 Mots de passe ", el("span", { class: "compte" }, String(C.entrees.length))),
        el("span", { class: "minuterie", id: "minuterie-coffre" }),
        el("div", { class: "espace" }),
        el("div", { class: "champ-recherche" }, el("span", {}, "🔎"), recherche),
        el("button", { class: "btn principal", onclick: () => editer({}) }, "＋ Nouveau"),
        el("button", { class: "btn", onclick: () => fenetreGenerateur() }, "🎲 Générateur"),
        el("button", { class: "btn", title: "Verrouiller maintenant", onclick: async () => { await appel("/api/coffre/fermer", {}); C.entrees = []; ecranVerrouille(); } }, "🔒")),
      cats.length ? el("div", { class: "puces", style: "margin:-6px 0 16px;flex-wrap:wrap" },
        [["toutes", "Toutes"], ...cats.map(c => [c, c])].map(([v, t]) =>
          el("button", { class: "puce" + (C.categorie === v ? " actif" : ""), onclick: () => { C.categorie = v; dessiner(); } }, t))) : null,
      el("div", { id: "liste-mdp" })].filter(Boolean));  // sans catégorie : rien à la place des puces
    dessinerListe(); tictac();
  }
  function dessinerListe() {
    const q = C.recherche.toLowerCase();
    const liste = C.entrees
      .filter(e => C.categorie === "toutes" || e.categorie === C.categorie)
      .filter(e => !q || [e.titre, e.identifiant, e.site, e.categorie].join(" ").toLowerCase().includes(q))
      .sort((a, b) => (a.titre || "").localeCompare(b.titre || "", "fr"));
    const box = $("#liste-mdp");
    if (!box) return;
    if (!liste.length) {
      box.replaceChildren(el("div", { class: "notes-vide", style: "text-align:center;padding:40px;color:var(--doux)" },
        el("div", { style: "font-size:56px" }, C.entrees.length ? "🔍" : "🗝️"),
        C.entrees.length ? "Aucune entrée ne correspond." : "Le coffre est vide. Ajoutez votre premier mot de passe ! ✨"));
      return;
    }
    box.replaceChildren(el("div", { class: "liste-mdp" }, liste.map((e, i) => {
      const secret = el("div", { class: "secret", hidden: "" });
      const couleur = COULEURS_CAT[e.categorie] || "#475569";
      return el("div", { class: "mdp", style: `animation-delay:${i * 25}ms` },
        el("div", { class: "av", style: `background:${couleur}` }, (e.titre || "?").charAt(0).toUpperCase()),
        el("div", { class: "infos" },
          el("div", { class: "t", title: e.titre }, e.titre),
          el("div", { class: "u" }, [e.identifiant, e.categorie].filter(Boolean).join(" · ") || "—"),
          secret),
        el("div", { class: "actions-mdp" },
          e.identifiant ? el("button", { class: "icone-btn", title: "Copier l'identifiant", onclick: () => copier(e, "identifiant") }, "👤") : null,
          el("button", { class: "icone-btn", title: "Copier le mot de passe (effacé du presse-papiers après 30 s)", onclick: () => copier(e, "mot_de_passe") }, "🔑"),
          el("button", { class: "icone-btn", title: "Afficher 15 secondes", onclick: async () => {
            const { valeur } = await appel("/api/coffre/reveler", { id: e.id, champ: "mot_de_passe" });
            secret.textContent = valeur || "(vide)"; secret.hidden = false;
            setTimeout(() => { secret.textContent = ""; secret.hidden = true; }, 15000);
          } }, "👁"),
          e.site ? el("button", { class: "icone-btn", title: "Ouvrir le site", onclick: () => window.open(/^https?:\/\//.test(e.site) ? e.site : "https://" + e.site, "_blank", "noopener") }, "↗") : null,
          el("button", { class: "icone-btn", title: "Modifier", onclick: () => editer(e) }, "✎")));
    })));
  }
  async function copier(e, champ) {
    try {
      await appel("/api/coffre/copier", { id: e.id, champ });
      toast(champ === "mot_de_passe" ? "🔑 Mot de passe copié — effacé dans 30 s" : "👤 Identifiant copié", "succes");
    } catch (err) { toast("😕 " + err.message, "erreur"); }
  }

  // -- formulaire -----------------------------------------------------------------
  function editer(entree) {
    const e = { ...entree };
    const titre = el("input", { value: e.titre || "", placeholder: "ex. Odoo (production)" });
    const site = el("input", { value: e.site || "", placeholder: "ex. monentreprise.odoo.com" });
    const identifiant = el("input", { value: e.identifiant || "", autocomplete: "off" });
    const mdp = el("input", { type: "password", autocomplete: "new-password", placeholder: e.id ? "(inchangé — 👁 pour l'afficher)" : "" });
    let mdpModifie = !e.id;
    mdp.addEventListener("input", () => { mdpModifie = true; });
    const oeil = el("button", { class: "btn", title: "Afficher", onclick: async () => {
      if (e.id && !mdpModifie && !mdp.value) { mdp.value = (await appel("/api/coffre/reveler", { id: e.id, champ: "mot_de_passe" })).valeur; mdp.dispatchEvent(new Event("input")); mdpModifie = false; }
      mdp.type = mdp.type === "password" ? "text" : "password";
    } }, "👁");
    const de = el("button", { class: "btn", title: "Générer un mot de passe solide", onclick: () => {
      const v = generer({ longueur: 20 }); mdp.value = v; mdp.type = "text"; mdpModifie = true; mdp.dispatchEvent(new Event("input"));
    } }, "🎲");
    const categorie = el("input", { value: e.categorie || "", list: "cat-mdp", placeholder: "ex. Clients Odoo" });
    const note = el("textarea", { rows: 3, style: "width:100%", placeholder: "Infos utiles (base, port, question secrète…)" });
    let noteChargee = !e.id || !e.a_note;
    const zoneNote = el("div");
    if (noteChargee) zoneNote.append(note);
    else zoneNote.append(el("button", { class: "btn discret", onclick: async () => {
      note.value = (await appel("/api/coffre/reveler", { id: e.id, champ: "note" })).valeur; noteChargee = true; zoneNote.replaceChildren(note);
    } }, "🔓 Afficher la note"));

    fenetre([
      el("h3", {}, e.id ? "✏️ Modifier" : "🗝️ Nouvelle entrée"),
      el("label", { class: "champ" }, "Nom", titre),
      el("label", { class: "champ" }, "Site ou adresse", site),
      el("label", { class: "champ" }, "Identifiant", identifiant),
      el("label", { class: "champ" }, "Mot de passe", el("div", { class: "avec-oeil" }, mdp, oeil, de), ...jauge(mdp)),
      el("label", { class: "champ" }, "Catégorie", categorie),
      el("datalist", { id: "cat-mdp" }, [...new Set([...CATEGORIES, ...C.entrees.map(x => x.categorie).filter(Boolean)])].map(c => el("option", { value: c }))),
      el("label", { class: "champ" }, "Note (chiffrée)", zoneNote),
      el("div", { class: "actions" },
        e.id ? el("button", { class: "btn discret", style: "margin-right:auto;color:var(--rouge)", onclick: async () => {
          if (!(await confirmer("🗑️", `Supprimer « ${e.titre} » ?`, "L'entrée disparaît du coffre. Rien ne pourra la récupérer.", "Supprimer"))) { editer(entree); return; }
          await appel("/api/coffre/supprimer", { id: e.id }); await chargerListe(); toast("🗑️ Entrée supprimée");
        } }, "🗑 Supprimer") : null,
        el("button", { class: "btn", onclick: fermer }, "Annuler"),
        el("button", { class: "btn principal", onclick: async () => {
          const x = { id: e.id, titre: titre.value, site: site.value, identifiant: identifiant.value, categorie: categorie.value };
          if (mdpModifie) x.mot_de_passe = mdp.value;
          if (noteChargee) x.note = note.value;
          try { await appel("/api/coffre/enregistrer", { entree: x }); fermer(); await chargerListe(); toast(e.id ? "✏️ Entrée modifiée" : "🎉 Ajouté au coffre !", "succes"); }
          catch (err) { toast("😕 " + err.message, "erreur"); }
        } }, e.id ? "Enregistrer" : "Ajouter"))]);
    setTimeout(() => titre.focus(), 60);
  }

  VUES.motsdepasse = { afficher };
})();

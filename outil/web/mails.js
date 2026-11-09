"use strict";
/* Onglet « Mails » : boîte Gmail (IMAP / SMTP) avec mot de passe
   d'application rangé dans le coffre Windows. */
(() => {
  const M = { etat: null, dossier: "recus", recherche: "", liste: [], ouvert: null, images: false, charge: false };

  const style = document.createElement("style");
  style.textContent = `
    .boite { display: grid; grid-template-columns: 380px 1fr; gap: 16px; height: 640px; }
    .boite .colonne-liste, .boite .lecture { background: var(--carte); border-radius: 22px; box-shadow: var(--ombre); overflow: hidden; display: flex; flex-direction: column; animation: apparait .35s both; }
    .liste-mails { overflow-y: auto; flex: 1; }
    .mail { padding: 11px 16px; border-bottom: 1px solid #f1eefb; cursor: pointer; display: flex; gap: 11px; transition: background .15s; }
    .mail:hover { background: #faf8ff; }
    .mail.actif { background: var(--violet-clair); }
    .mail .av { width: 38px; height: 38px; border-radius: 13px; display: grid; place-items: center; color: #fff; font-weight: 800; flex: none; font-size: 14px; }
    .mail .contenu { min-width: 0; flex: 1; }
    .mail .l1 { display: flex; gap: 8px; align-items: baseline; }
    .mail .qui { font-size: 14px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; flex: 1; }
    .mail .quand { font-size: 12px; color: var(--doux); white-space: nowrap; }
    .mail .objet { font-size: 13.5px; color: var(--doux); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .mail.non-lu .qui, .mail.non-lu .objet { font-weight: 800; color: var(--encre); }
    .mail.non-lu .av::after { content: ""; }
    .point-nonlu { width: 8px; height: 8px; border-radius: 50%; background: var(--corail); flex: none; margin-top: 6px; }
    .entete-liste { padding: 12px; display: flex; gap: 8px; align-items: center; border-bottom: 1px solid var(--ligne); flex-wrap: wrap; }
    .entete-liste input { flex: 1; min-width: 120px; border: 1.5px solid var(--ligne); border-radius: 12px; padding: 8px 11px; outline: none; background: #fbfaff; }
    .entete-liste input:focus { border-color: var(--violet); background: #fff; }
    .lecture .tete { padding: 18px 22px 12px; border-bottom: 1px solid var(--ligne); }
    .lecture .tete h3 { margin: 0 0 10px; font-size: 19px; }
    .lecture .meta { font-size: 13px; color: var(--doux); display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }
    .lecture .actions-mail { display: flex; gap: 6px; margin-top: 12px; flex-wrap: wrap; }
    .lecture iframe { flex: 1; border: 0; width: 100%; background: #fff; }
    .lecture .texte-brut { flex: 1; overflow: auto; padding: 18px 22px; white-space: pre-wrap; font-size: 14.5px; line-height: 1.5; }
    .lecture .vide-lecture { flex: 1; display: grid; place-items: center; color: var(--doux); text-align: center; }
    .lecture .vide-lecture div div { font-size: 58px; }
    .pieces { padding: 8px 22px; font-size: 12.5px; color: var(--doux); border-top: 1px solid var(--ligne); }
    .connexion { max-width: 620px; margin: 10px auto; background: var(--carte); border-radius: 24px; box-shadow: var(--ombre); padding: 28px; animation: apparait .35s both; }
    .connexion h3 { margin: 0 0 6px; font-size: 22px; }
    .connexion ol { padding-left: 20px; line-height: 1.7; color: #3b3657; }
    .connexion a { color: var(--violet); font-weight: 700; }
    .chargement-mails { padding: 30px; text-align: center; color: var(--doux); }
  `;
  document.head.append(style);

  const racine = () => $("#vue-mails");
  const COULEURS_AV = ["#6c4cf5", "#ff7a59", "#18b597", "#ffb020", "#e5488d", "#2f8cff"];
  const couleur = t => { let h = 0; for (const c of t || "?") h = (h * 31 + c.charCodeAt(0)) >>> 0; return COULEURS_AV[h % COULEURS_AV.length]; };
  const initiale = t => (t || "?").replace(/[^\p{L}\p{N}]/gu, "").charAt(0).toUpperCase() || "?";
  function quand(iso) {
    if (!iso) return "";
    const d = new Date(iso), auj = new Date();
    if (d.toDateString() === auj.toDateString()) return d.toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" });
    if (d.getFullYear() === auj.getFullYear()) return d.toLocaleDateString("fr-FR", { day: "numeric", month: "short" });
    return d.toLocaleDateString("fr-FR");
  }

  async function afficher() {
    try { M.etat = await api("/api/mail/etat"); }
    catch (e) { racine().replaceChildren(el("div", { class: "vide" }, "😕 " + e.message)); return; }
    if (!M.etat.configuree) return ecranConnexion();
    if (!M.charge) dessinerBoite();
    rafraichir();
  }

  // -- première connexion ------------------------------------------------------
  function ecranConnexion() {
    M.charge = false;
    const adresse = el("input", { type: "email", value: M.etat.adresse || "", autocomplete: "username" });
    const secret = el("input", { type: "password", placeholder: "16 lettres, ex. abcd efgh ijkl mnop", autocomplete: "new-password" });
    const bouton = el("button", { class: "btn principal", onclick: async () => {
      bouton.disabled = true; bouton.textContent = "Connexion…";
      try {
        await api("/api/mail/connexion", { adresse: adresse.value, secret: secret.value });
        secret.value = "";
        toast("🎉 Boîte mail connectée !", "succes");
        M.etat = await api("/api/mail/etat");
        dessinerBoite(); rafraichir(); compterMails();
      } catch (e) { toast("😕 " + e.message, "erreur", 7000); }
      finally { bouton.disabled = false; bouton.textContent = "Connecter"; }
    } }, "Connecter");
    racine().replaceChildren(el("div", { class: "connexion" },
      el("div", { style: "font-size:48px" }, "✉️"),
      el("h3", {}, "Connecter votre Gmail"),
      el("p", { style: "color:var(--doux);margin-top:0" }, "Une seule fois. Google demande un « mot de passe d'application » : un code de 16 lettres réservé à cet outil, que vous pouvez révoquer à tout moment."),
      el("ol", {},
        el("li", {}, "La ", el("b", {}, "validation en deux étapes"), " doit être activée sur votre compte Google (Sécurité)."),
        el("li", {}, "Ouvrez ", el("a", { href: "https://myaccount.google.com/apppasswords", target: "_blank", rel: "noopener" }, "myaccount.google.com/apppasswords"), ", donnez un nom (ex. « Mes outils ») et cliquez sur Créer."),
        el("li", {}, "Copiez le code affiché et collez-le ci-dessous.")),
      el("label", { class: "champ" }, "Adresse Gmail", adresse),
      el("label", { class: "champ" }, "Mot de passe d'application", secret,
        el("small", {}, "🔒 Il est rangé dans le coffre de Windows (Gestionnaire d'identification), jamais dans un fichier.")),
      el("div", { class: "actions" }, bouton)));
  }

  // -- la boîte --------------------------------------------------------------
  function dessinerBoite() {
    M.charge = true;
    const recherche = el("input", { placeholder: "Rechercher (expéditeur, objet, texte…)", value: M.recherche,
      onkeydown: e => { if (e.key === "Enter") { M.recherche = e.target.value; rafraichir(true); } } });
    racine().replaceChildren(
      el("div", { class: "barre-vue" },
        el("h2", {}, "✉️ Mails"),
        el("span", { style: "color:var(--doux);font-size:13px" }, M.etat.adresse),
        el("div", { class: "espace" }),
        el("button", { class: "btn principal", onclick: () => composer({}) }, "✏️ Nouveau mail"),
        el("button", { class: "btn discret", title: "Déconnecter la boîte (le mot de passe est retiré du coffre)", onclick: async () => {
          if (!(await confirmer("🔌", "Déconnecter Gmail ?", "Le mot de passe d'application est retiré du coffre Windows. Vos mails ne sont pas touchés.", "Déconnecter"))) return;
          await api("/api/mail/deconnexion", {}); M.etat.configuree = false; ecranConnexion(); compterMails();
        } }, "🔌")),
      el("div", { class: "boite" },
        el("div", { class: "colonne-liste" },
          el("div", { class: "entete-liste" },
            el("div", { class: "puces" }, [["recus", "📥 Reçus"], ["envoyes", "📤 Envoyés"]].map(([d, t]) =>
              el("button", { class: "puce" + (M.dossier === d ? " actif" : ""), onclick: ev => {
                M.dossier = d; ev.currentTarget.parentNode.querySelectorAll(".puce").forEach(p => p.classList.toggle("actif", p === ev.currentTarget)); rafraichir(true);
              } }, t))),
            el("button", { class: "btn discret", title: "Actualiser", onclick: () => rafraichir(true) }, "⟳"),
            recherche),
          el("div", { class: "liste-mails", id: "liste-mails" }, el("div", { class: "chargement-mails" }, "Chargement…"))),
        el("div", { class: "lecture", id: "lecture" },
          el("div", { class: "vide-lecture" }, el("div", {}, el("div", {}, "📬"), "Choisissez un mail à lire")))));
  }

  async function rafraichir(montrerChargement = false) {
    const box = $("#liste-mails");
    if (!box) return;
    if (montrerChargement) box.replaceChildren(el("div", { class: "chargement-mails" }, "Chargement…"));
    try {
      M.liste = await api("/api/mail/liste", { dossier: M.dossier, recherche: M.recherche });
    } catch (e) { box.replaceChildren(el("div", { class: "chargement-mails" }, "😕 " + e.message)); return; }
    if (!M.liste.length) { box.replaceChildren(el("div", { class: "chargement-mails" }, "Aucun mail 🎈")); return; }
    box.replaceChildren(...M.liste.map(m => {
      const qui = M.dossier === "envoyes" ? m.a : m.de;
      return el("div", { class: "mail" + (m.lu ? "" : " non-lu") + (M.ouvert?.uid === m.uid ? " actif" : ""), onclick: () => ouvrir(m) },
        el("div", { class: "av", style: `background:${couleur(qui.adresse)}` }, initiale(qui.nom)),
        el("div", { class: "contenu" },
          el("div", { class: "l1" }, el("span", { class: "qui" }, (M.dossier === "envoyes" ? "À : " : "") + (qui.nom || qui.adresse)), el("span", { class: "quand" }, quand(m.date))),
          el("div", { class: "objet" }, m.sujet)),
        m.lu ? null : el("span", { class: "point-nonlu" }));
    }));
  }

  async function ouvrir(m) {
    M.images = false;
    const zone = $("#lecture");
    zone.replaceChildren(el("div", { class: "vide-lecture" }, "Ouverture…"));
    try {
      M.ouvert = await api("/api/mail/lire", { uid: m.uid, dossier: M.dossier });
      m.lu = true;
      dessinerLecture();
      rafraichir(); compterMails();
    } catch (e) { zone.replaceChildren(el("div", { class: "vide-lecture" }, "😕 " + e.message)); }
  }

  function srcdoc(html, images) {
    // Pas de script, et pas d'image distante sans votre accord : une image
    // distante dit à l'expéditeur que vous avez ouvert son mail.
    const csp = `default-src 'none'; style-src 'unsafe-inline' data:; font-src data:; img-src ${images ? "* data: blob:" : "data: cid:"};`;
    return `<!doctype html><html><head><meta charset="utf-8"><meta http-equiv="Content-Security-Policy" content="${csp}"><base target="_blank">
      <style>body{font-family:Segoe UI,sans-serif;font-size:14.5px;color:#1f1a3a;margin:18px 22px;word-wrap:break-word}img{max-width:100%;height:auto}</style></head><body>${html}</body></html>`;
  }

  function dessinerLecture() {
    const m = M.ouvert;
    const zone = $("#lecture");
    const contenu = m.html
      ? el("iframe", { sandbox: "allow-popups allow-popups-to-escape-sandbox", title: "Contenu du mail" })
      : el("div", { class: "texte-brut" }, m.texte || "(mail vide)");
    if (m.html) contenu.srcdoc = srcdoc(m.html, M.images);
    zone.replaceChildren(
      el("div", { class: "tete" },
        el("h3", {}, m.sujet),
        el("div", { class: "meta" },
          el("span", { class: "av", style: `background:${couleur(m.de.adresse)};width:30px;height:30px;border-radius:10px;display:grid;place-items:center;color:#fff;font-weight:800` }, initiale(m.de.nom)),
          el("b", { style: "color:var(--encre)" }, m.de.nom), el("span", {}, `<${m.de.adresse}>`),
          el("span", {}, "· " + (m.date ? new Date(m.date).toLocaleString("fr-FR", { dateStyle: "medium", timeStyle: "short" }) : ""))),
        el("div", { class: "meta", style: "margin-top:4px" }, "À : " + (m.a || "") + (m.cc ? " · Cc : " + m.cc : "")),
        el("div", { class: "actions-mail" },
          el("button", { class: "btn principal", onclick: () => repondre(false) }, "↩️ Répondre"),
          m.cc || (m.a || "").includes(",") ? el("button", { class: "btn", onclick: () => repondre(true) }, "↩️ Répondre à tous") : null,
          el("button", { class: "btn", onclick: transferer }, "➡️ Transférer"),
          m.html && !M.images ? el("button", { class: "btn discret", onclick: () => { M.images = true; dessinerLecture(); } }, "🖼️ Afficher les images") : null)),
      contenu,
      m.pieces.length ? el("div", { class: "pieces" }, "📎 " + m.pieces.map(p => `${p.nom} (${Math.max(1, Math.round(p.taille / 1024))} Ko)`).join(" · ") + " — à ouvrir depuis Gmail") : null);
  }

  // -- écrire --------------------------------------------------------------------
  function citation(m) {
    const texte = m.texte || (m.html ? new DOMParser().parseFromString(m.html, "text/html").body.innerText : "");
    const date = m.date ? new Date(m.date).toLocaleString("fr-FR", { dateStyle: "long", timeStyle: "short" }) : "";
    return `\n\n\nLe ${date}, ${m.de.nom} <${m.de.adresse}> a écrit :\n` + texte.split("\n").map(l => "> " + l).join("\n");
  }
  function repondre(tous) {
    const m = M.ouvert;
    const moi = (M.etat.adresse || "").toLowerCase();
    const autres = tous ? [m.a, m.cc].join(",").split(",").map(x => x.trim()).filter(x => x && !x.toLowerCase().includes(moi)) : [];
    composer({ a: m.de.adresse, cc: autres.join(", "), sujet: /^re\s*:/i.test(m.sujet) ? m.sujet : "Re: " + m.sujet,
      corps: citation(m), reponse_a: m.message_id, references: m.references });
  }
  function transferer() {
    const m = M.ouvert;
    composer({ sujet: /^(tr|fwd?)\s*:/i.test(m.sujet) ? m.sujet : "Tr: " + m.sujet,
      corps: `\n\n\n---------- Message transféré ----------\nDe : ${m.de.nom} <${m.de.adresse}>\nDate : ${m.date ? new Date(m.date).toLocaleString("fr-FR") : ""}\nObjet : ${m.sujet}\nÀ : ${m.a}\n\n${m.texte || (m.html ? new DOMParser().parseFromString(m.html, "text/html").body.innerText : "")}` });
  }
  function composer(v) {
    const a = el("input", { value: v.a || "", placeholder: "adresse@exemple.com, autre@exemple.com" });
    const cc = el("input", { value: v.cc || "" });
    const sujet = el("input", { value: v.sujet || "" });
    const corps = el("textarea", { rows: 12, value: v.corps || "", style: "font-family:inherit" });
    const envoyer = el("button", { class: "btn principal", onclick: async () => {
      envoyer.disabled = true; envoyer.textContent = "Envoi…";
      try {
        await api("/api/mail/envoyer", { a: a.value, cc: cc.value, sujet: sujet.value, corps: corps.value, reponse_a: v.reponse_a, references: v.references });
        fermer(); toast("🚀 Mail envoyé !", "succes");
        if (M.dossier === "envoyes") rafraichir();
      } catch (e) { toast("😕 " + e.message, "erreur", 7000); envoyer.disabled = false; envoyer.textContent = "📨 Envoyer"; }
    } }, "📨 Envoyer");
    fenetre([
      el("h3", {}, v.reponse_a ? "↩️ Répondre" : "✏️ Nouveau mail"),
      el("label", { class: "champ" }, "À", a),
      el("label", { class: "champ" }, "Cc", cc),
      el("label", { class: "champ" }, "Objet", sujet),
      el("label", { class: "champ" }, "Message", corps),
      el("div", { class: "actions" }, el("button", { class: "btn", onclick: fermer }, "Annuler"), envoyer)]);
    $("#fenetre").style.width = "min(720px, 94vw)";
    setTimeout(() => { (v.a ? corps : a).focus(); if (v.a) corps.setSelectionRange(0, 0); }, 60);
  }

  VUES.mails = { afficher };
})();

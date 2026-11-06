// Reiter, Schalter, Filter und Knoepfe der Uebersicht.
//
// Reiter, Schalter und Sender-Filter merkt sich der Browser (localStorage) -
// jedes Geraet fuer sich, wie beim Hell/Dunkel-Umschalter. Das Haekchen und
// "Gehört nicht dazu" speichert dagegen die App, damit es auf PC und Handy
// gleich aussieht.
//
// Ohne JavaScript funktioniert die Seite weiter: alle Bereiche stehen
// untereinander, und die Knoepfe sind normale Formulare.
(function () {
  var SCHALTER = {
    "filter-wiederholungen": { klasse: "ohne-wiederholungen", speicher: "rtv-ohne-wiederholungen" },
    "filter-gesehen": { klasse: "ohne-gesehene", speicher: "rtv-ohne-gesehene" }
  };
  // Anker, mit denen die App nach "Hinzufuegen"/"Ausblenden" zurueckkommt
  var ANKER_REITER = { "#entdeckungen": "neu", "#demnaechst": "demnaechst", "#woche2": "woche2" };
  var WOCHEN = ["woche1", "woche2"];

  function lesen(name) {
    try { return localStorage.getItem(name); } catch (e) { return null; }
  }

  function schreiben(name, wert) {
    try { localStorage.setItem(name, wert); } catch (e) {}
  }

  function alle(selektor, wurzel) {
    return Array.prototype.slice.call((wurzel || document).querySelectorAll(selektor));
  }

  // --- Kurze Meldung unten, optional mit Knopf ("Rückgängig") ------------
  var meldung = document.getElementById("meldung");
  var meldungUhr = null;

  function zeigeMeldung(text, knopfText, knopfAktion) {
    if (!meldung) return;
    meldung.textContent = text;
    if (knopfText) {
      var knopf = document.createElement("button");
      knopf.type = "button";
      knopf.textContent = knopfText;
      knopf.addEventListener("click", function () {
        meldung.hidden = true;
        knopfAktion();
      });
      meldung.appendChild(knopf);
    }
    meldung.hidden = false;
    clearTimeout(meldungUhr);
    meldungUhr = setTimeout(function () { meldung.hidden = true; }, knopfText ? 10000 : 6000);
  }

  // Formular per fetch abschicken; die App antwortet dann mit JSON statt mit
  // einer Weiterleitung (webapp/app.py: _will_json)
  function abschicken(form) {
    return fetch(form.action, {
      method: "POST",
      headers: { "Accept": "application/json" },
      body: new FormData(form)
    }).then(function (antwort) {
      if (!antwort.ok) throw new Error("HTTP " + antwort.status);
      return antwort.json();
    });
  }

  function titelSenden(url, titel) {
    var daten = new FormData();
    daten.append("titel", titel);
    return fetch(url, { method: "POST", headers: { "Accept": "application/json" }, body: daten })
      .then(function (antwort) { if (!antwort.ok) throw new Error("HTTP " + antwort.status); });
  }

  // --- Reiter -------------------------------------------------------------
  var reiterKnoepfe = alle("[data-reiter]");
  // Nach "Hinzufügen" unter "Neu entdeckt" stehen neue Termine in der
  // Datenbank - beim naechsten Wechsel in eine Woche einmal neu laden
  var wochenVeraltet = false;

  function zeigeReiter(name) {
    if (!document.querySelector('[data-panel="' + name + '"]')) name = "woche1";
    alle("[data-panel]").forEach(function (panel) {
      panel.classList.toggle("aktiv", panel.getAttribute("data-panel") === name);
    });
    reiterKnoepfe.forEach(function (knopf) {
      var aktiv = knopf.getAttribute("data-reiter") === name;
      knopf.classList.toggle("aktiv", aktiv);
      knopf.setAttribute("aria-current", aktiv ? "page" : "false");
    });
    schreiben("rtv-reiter", name);
  }

  if (reiterKnoepfe.length) {
    // Erst jetzt verstecken - ohne JavaScript bleiben alle Bereiche sichtbar
    document.body.classList.add("mit-reitern");
    reiterKnoepfe.forEach(function (knopf) {
      knopf.addEventListener("click", function () {
        var name = knopf.getAttribute("data-reiter");
        setzeTitelFilter(null);
        if (wochenVeraltet && WOCHEN.indexOf(name) >= 0) {
          schreiben("rtv-reiter", name);
          location.replace(location.pathname);
          return;
        }
        zeigeReiter(name);
      });
    });
    zeigeReiter(ANKER_REITER[location.hash] || lesen("rtv-reiter") || "woche1");
  }

  // --- Was ist ausgeblendet? ----------------------------------------------
  function istAusgeblendet(li) {
    var body = document.body.classList;
    return (body.contains("ohne-wiederholungen") && li.hasAttribute("data-wiederholung")) ||
      (body.contains("ohne-gesehene") && li.classList.contains("ist-gesehen")) ||
      li.classList.contains("sender-aus") ||
      li.classList.contains("titel-aus");
  }

  // Tage, an denen nichts mehr zu sehen ist, sagen das, statt kommentarlos
  // nur eine Ueberschrift zu zeigen. Bewusst aus den Schaltern berechnet,
  // nicht aus der Sichtbarkeit: die Tage in einem gerade nicht gezeigten
  // Reiter sind ohnehin unsichtbar.
  function leereTageMarkieren() {
    alle(".tag").forEach(function (tag) {
      if (!tag.querySelector(".sendungen")) return;
      var sendungen = alle(".sendung", tag);
      var alleWeg = sendungen.every(istAusgeblendet);
      tag.classList.toggle("alles-ausgeblendet", alleWeg);
    });
    // Beim Titel-Filter: Wochen ganz ohne Treffer verschwinden
    WOCHEN.forEach(function (name) {
      var panel = document.querySelector('[data-panel="' + name + '"]');
      if (!panel) return;
      var sichtbar = alle(".sendung", panel).some(function (li) { return !istAusgeblendet(li); });
      panel.classList.toggle("panel-ohne-treffer", !sichtbar);
    });
  }

  // --- Schalter (Wiederholungen / Gesehenes) ------------------------------
  Object.keys(SCHALTER).forEach(function (id) {
    var box = document.getElementById(id);
    if (!box) return;
    var info = SCHALTER[id];
    box.checked = lesen(info.speicher) === "1";
    document.body.classList.toggle(info.klasse, box.checked);
    box.addEventListener("change", function () {
      document.body.classList.toggle(info.klasse, box.checked);
      schreiben(info.speicher, box.checked ? "1" : "0");
      leereTageMarkieren();
    });
  });

  // --- Sender-Filter ------------------------------------------------------
  var senderKnopf = document.getElementById("sender-knopf");
  var senderAuswahl = document.getElementById("sender-auswahl");
  var senderAus = [];
  try { senderAus = JSON.parse(lesen("rtv-sender-aus") || "[]") || []; } catch (e) { senderAus = []; }

  function senderAnwenden() {
    alle(".sendung[data-sender]").forEach(function (li) {
      li.classList.toggle("sender-aus", senderAus.indexOf(li.getAttribute("data-sender")) >= 0);
    });
    alle("[data-sender-chip]").forEach(function (chip) {
      chip.setAttribute("aria-pressed", senderAus.indexOf(chip.getAttribute("data-sender-chip")) >= 0 ? "false" : "true");
    });
    // Nur Sender zaehlen, die gerade ueberhaupt vorkommen
    var vorhanden = alle("[data-sender-chip]").map(function (c) { return c.getAttribute("data-sender-chip"); });
    var anzahlAus = senderAus.filter(function (s) { return vorhanden.indexOf(s) >= 0; }).length;
    var zahl = document.getElementById("sender-aus-zahl");
    if (zahl) zahl.textContent = anzahlAus ? "(" + anzahlAus + " aus)" : "";
    if (senderKnopf) senderKnopf.classList.toggle("aktiv", anzahlAus > 0);
    schreiben("rtv-sender-aus", JSON.stringify(senderAus));
    leereTageMarkieren();
  }

  if (senderKnopf && senderAuswahl) {
    senderKnopf.hidden = false;
    senderKnopf.addEventListener("click", function () {
      var offen = senderAuswahl.hidden;
      senderAuswahl.hidden = !offen;
      senderKnopf.setAttribute("aria-expanded", offen ? "true" : "false");
    });
    alle("[data-sender-chip]").forEach(function (chip) {
      chip.addEventListener("click", function () {
        var name = chip.getAttribute("data-sender-chip");
        var stelle = senderAus.indexOf(name);
        if (stelle >= 0) senderAus.splice(stelle, 1); else senderAus.push(name);
        senderAnwenden();
      });
    });
    var alleKnopf = document.getElementById("sender-alle");
    if (alleKnopf) alleKnopf.addEventListener("click", function () { senderAus = []; senderAnwenden(); });
  }

  // --- Titel-Filter: Klick auf einen Titel zeigt nur diese Sendung -------
  var titelLeiste = document.getElementById("titel-filter-leiste");
  var titelFilter = null;

  function setzeTitelFilter(show) {
    if (titelFilter === show) return;
    titelFilter = show;
    alle(".sendung[data-show]").forEach(function (li) {
      li.classList.toggle("titel-aus", show !== null && li.getAttribute("data-show") !== show);
    });
    document.body.classList.toggle("titel-filter-aktiv", show !== null);
    if (titelLeiste) {
      titelLeiste.hidden = show === null;
      if (show !== null) {
        var anzahl = alle(".sendung[data-show]").filter(function (li) { return !istAusgeblendet(li); }).length;
        document.getElementById("titel-filter-name").textContent = "„" + show + "“";
        document.getElementById("titel-filter-zahl").textContent =
          anzahl + (anzahl === 1 ? " Termin" : " Termine") + " in den zwei Wochen";
      }
    }
    leereTageMarkieren();
    if (show !== null && titelLeiste) titelLeiste.scrollIntoView({ block: "start", behavior: "smooth" });
  }

  document.addEventListener("click", function (ereignis) {
    var titel = ereignis.target.closest(".titel-knopf");
    if (!titel) return;
    var li = titel.closest(".sendung");
    setzeTitelFilter(titelFilter === li.getAttribute("data-show") ? null : li.getAttribute("data-show"));
  });

  var titelAus = document.getElementById("titel-filter-aus");
  if (titelAus) titelAus.addEventListener("click", function () { setzeTitelFilter(null); });
  document.addEventListener("keydown", function (ereignis) {
    if (ereignis.key === "Escape" && titelFilter !== null) setzeTitelFilter(null);
  });

  // --- Gesehen-Haekchen ---------------------------------------------------
  document.addEventListener("click", function (ereignis) {
    var knopf = ereignis.target.closest(".gesehen-knopf");
    if (!knopf) return;
    var li = knopf.closest(".sendung");
    var schluessel = li.getAttribute("data-schluessel");
    var neu = !li.classList.contains("ist-gesehen");
    knopf.disabled = true;
    fetch(window.RTV_GESEHEN_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ schluessel: schluessel, gesehen: neu })
    })
      .then(function (antwort) {
        if (!antwort.ok) throw new Error("HTTP " + antwort.status);
        // Dieselbe Folge kann mehrfach in der Liste stehen (Wiederholungen) -
        // das Haekchen gilt fuer alle.
        alle(".sendung").forEach(function (andere) {
          if (andere.getAttribute("data-schluessel") !== schluessel) return;
          andere.classList.toggle("ist-gesehen", neu);
          andere.querySelector(".gesehen-knopf").setAttribute("aria-pressed", neu ? "true" : "false");
        });
        leereTageMarkieren();
      })
      .catch(function () {
        alert("Konnte nicht gespeichert werden - läuft die App noch?");
      })
      .finally(function () {
        knopf.disabled = false;
      });
  });

  // --- "Gehört nicht dazu" ------------------------------------------------
  document.addEventListener("submit", function (ereignis) {
    var form = ereignis.target.closest(".ausschliessen-form");
    if (!form) return;
    ereignis.preventDefault();
    var titel = form.querySelector('input[name="titel"]').value;
    if (!confirm("„" + titel + "“ gehört nicht dazu?\n\nDer Titel verschwindet aus der Übersicht " +
      "(alle Termine). Rückgängig auch später unter „Sendungen verwalten“.")) return;

    abschicken(form)
      .then(function () {
        // Zeilen merken statt wegwerfen - fuer "Rückgängig"
        var entfernt = alle(".sendung").filter(function (li) {
          return li.getAttribute("data-titel") === titel;
        }).map(function (li) {
          var stelle = { li: li, eltern: li.parentNode, danach: li.nextSibling };
          li.remove();
          return stelle;
        });
        leereTageMarkieren();
        zeigeMeldung("„" + titel + "“ ausgeblendet.", "Rückgängig", function () {
          titelSenden(window.RTV_ZULASSEN_URL, titel)
            .then(function () {
              entfernt.reverse().forEach(function (s) { s.eltern.insertBefore(s.li, s.danach); });
              leereTageMarkieren();
              zeigeMeldung("„" + titel + "“ ist wieder da.");
            })
            .catch(function () { alert("Konnte nicht rückgängig gemacht werden - läuft die App noch?"); });
        });
      })
      .catch(function () { form.submit(); });
  });

  // --- "Neu entdeckt": Hinzufügen / Ausblenden ohne Neuladen --------------
  function entdecktZaehlen() {
    var kasten = document.querySelector("#entdeckungen > div.tag");
    var zahl = document.querySelector('[data-reiter="neu"] .zahl');
    if (!kasten || !zahl) return;
    var anzahl = alle(".entdeckt-eintrag", kasten).length;
    zahl.textContent = anzahl;
    zahl.hidden = anzahl === 0;
  }

  document.addEventListener("submit", function (ereignis) {
    var form = ereignis.target.closest("form[data-aktion]");
    if (!form) return;
    ereignis.preventDefault();
    var eintrag = form.closest(".entdeckt-eintrag");
    var aktion = form.getAttribute("data-aktion");
    alle("button", eintrag).forEach(function (k) { k.disabled = true; });

    abschicken(form)
      .then(function (daten) {
        var titel = form.querySelector('input[name="titel"]').value;
        if (aktion === "hinzufuegen") {
          wochenVeraltet = true;
          zeigeMeldung("„" + daten.titel + "“ steht jetzt in deiner Liste" +
            (daten.termine ? " – " + daten.termine + " Termin(e) kommen in die Übersicht." : "."));
        } else {
          zeigeMeldung("„" + titel + "“ wird nicht mehr vorgeschlagen (rückgängig unter „Sendungen verwalten“).");
        }
        eintrag.classList.add("verschwindet");
        setTimeout(function () { eintrag.remove(); entdecktZaehlen(); }, 250);
      })
      .catch(function () { form.submit(); });
  });

  // --- Heute schon Gelaufenes ausgrauen -----------------------------------
  // Nach der Uhr des Browsers, jede Minute neu - so stimmt es auch, wenn die
  // Seite den ganzen Abend offen bleibt. Eine Sendung gilt ab ihrer
  // Startzeit plus 30 Minuten als gelaufen (die Endzeit kennen die Quellen
  // nicht); TMDB-Termine ohne Uhrzeit tragen kein data-zeit.
  function zweistellig(n) { return (n < 10 ? "0" : "") + n; }

  function vorbeiMarkieren() {
    var grenze = new Date(Date.now() - 30 * 60 * 1000);
    var jetzt = grenze.getFullYear() + "-" + zweistellig(grenze.getMonth() + 1) + "-" +
      zweistellig(grenze.getDate()) + "T" + zweistellig(grenze.getHours()) + ":" + zweistellig(grenze.getMinutes());
    alle(".sendung[data-zeit]").forEach(function (li) {
      li.classList.toggle("vorbei", li.getAttribute("data-zeit") < jetzt);
    });
  }

  vorbeiMarkieren();
  setInterval(vorbeiMarkieren, 60 * 1000);
  senderAnwenden();
})();

// Reiter, Schalter "Wiederholungen ausblenden" / "Gesehenes ausblenden" und
// das Gesehen-Haekchen in der Uebersicht.
//
// Reiter und Schalter merkt sich der Browser (localStorage) - jedes Geraet
// fuer sich, wie beim Hell/Dunkel-Umschalter. Das Haekchen dagegen speichert
// die App (Tabelle "gesehen"), damit es auf PC und Handy gleich aussieht.
(function () {
  var SCHALTER = {
    "filter-wiederholungen": { klasse: "ohne-wiederholungen", speicher: "rtv-ohne-wiederholungen" },
    "filter-gesehen": { klasse: "ohne-gesehene", speicher: "rtv-ohne-gesehene" }
  };
  // Anker, mit denen die App nach "Hinzufuegen"/"Ausblenden" zurueckkommt
  var ANKER_REITER = { "#entdeckungen": "neu", "#demnaechst": "demnaechst", "#woche2": "woche2" };

  function lesen(name) {
    try { return localStorage.getItem(name); } catch (e) { return null; }
  }

  function schreiben(name, wert) {
    try { localStorage.setItem(name, wert); } catch (e) {}
  }

  // --- Reiter -------------------------------------------------------------
  var reiterKnoepfe = document.querySelectorAll("[data-reiter]");

  function zeigeReiter(name) {
    if (!document.querySelector('[data-panel="' + name + '"]')) name = "woche1";
    document.querySelectorAll("[data-panel]").forEach(function (panel) {
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
        zeigeReiter(knopf.getAttribute("data-reiter"));
      });
    });
    zeigeReiter(ANKER_REITER[location.hash] || lesen("rtv-reiter") || "woche1");
  }

  // --- Schalter -----------------------------------------------------------
  function istAusgeblendet(li) {
    var body = document.body.classList;
    return (body.contains("ohne-wiederholungen") && li.hasAttribute("data-wiederholung")) ||
      (body.contains("ohne-gesehene") && li.classList.contains("ist-gesehen"));
  }

  // Tage, an denen durch die Schalter nichts mehr zu sehen ist, sagen das,
  // statt kommentarlos nur eine Ueberschrift zu zeigen. Bewusst aus den
  // Schaltern berechnet, nicht aus der Sichtbarkeit: die Tage in einem
  // gerade nicht gezeigten Reiter sind ohnehin unsichtbar.
  function leereTageMarkieren() {
    document.querySelectorAll(".tag").forEach(function (tag) {
      var sendungen = tag.querySelectorAll(".sendung");
      if (!sendungen.length) return;
      var alleWeg = Array.prototype.every.call(sendungen, istAusgeblendet);
      tag.classList.toggle("alles-ausgeblendet", alleWeg);
    });
  }

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
        document.querySelectorAll(".sendung").forEach(function (andere) {
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

  leereTageMarkieren();
})();

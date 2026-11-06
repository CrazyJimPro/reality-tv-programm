// Seite "Sendungen verwalten": eigene Sendung hinzufuegen, Suche und Zaehler
// ueber der Liste, Speichern-Leiste bei ungespeicherten Aenderungen.
//
// Ohne JavaScript bleibt die Seite benutzbar: Liste anhaken, unten
// "Speichern" - nur das Hinzufuegen eigener Sendungen braucht das Skript.
(function () {
  var form = document.getElementById("einstellungen-form");
  var liste = document.getElementById("show-liste");
  if (!form || !liste) return;

  var nameFeld = document.getElementById("neuer-name");
  var aliasFeld = document.getElementById("neue-aliases");
  var suche = document.getElementById("liste-suche");
  var nurAusgewaehlte = document.getElementById("nur-ausgewaehlte");
  var zaehler = document.getElementById("liste-zaehler");
  var leer = document.getElementById("liste-leer");
  var leiste = document.getElementById("speichern-leiste");
  var leisteText = document.getElementById("speichern-text");
  var wirdGespeichert = false;

  function kaestchen() {
    return Array.prototype.slice.call(liste.querySelectorAll('input[name="shows"]'));
  }

  // Ausgangszustand: welche Namen beim Laden angehakt waren und welche
  // Eintraege es gab - daran misst sich "ungespeichert"
  var anfangsHaken = {};
  var anfangsNamen = {};
  kaestchen().forEach(function (cb) {
    anfangsNamen[cb.value] = true;
    if (cb.checked) anfangsHaken[cb.value] = true;
  });

  // --- Aenderungen zaehlen, Leiste und Zaehler ----------------------------
  function aenderungen() {
    var anzahl = 0;
    kaestchen().forEach(function (cb) {
      if (!!anfangsHaken[cb.value] !== cb.checked) anzahl++;
    });
    return anzahl;
  }

  function aktualisieren() {
    var alle = kaestchen();
    var angehakt = alle.filter(function (cb) { return cb.checked; }).length;
    var begriff = (suche.value || "").trim().toLowerCase();
    var nurHaken = nurAusgewaehlte.checked;
    var sichtbar = 0;

    alle.forEach(function (cb) {
      var label = cb.closest(".show-checkbox");
      var passt = (!begriff || label.textContent.toLowerCase().indexOf(begriff) >= 0) && (!nurHaken || cb.checked);
      label.hidden = !passt;
      if (passt) sichtbar++;
    });

    leer.hidden = sichtbar > 0;
    zaehler.textContent = angehakt + " von " + alle.length + " ausgewählt" +
      (sichtbar < alle.length ? " · " + sichtbar + " angezeigt" : "");

    var offen = aenderungen();
    leiste.hidden = offen === 0;
    document.body.classList.toggle("mit-speichern-leiste", offen > 0);
    leisteText.textContent = offen === 1 ? "1 Änderung nicht gespeichert" : offen + " Änderungen nicht gespeichert";
  }

  // --- Eigene Sendung hinzufuegen -----------------------------------------
  function hinzufuegen() {
    var name = nameFeld.value.trim();
    if (!name) { nameFeld.focus(); return; }
    var aliases = aliasFeld.value.trim();

    var treffer = kaestchen().find(function (cb) { return cb.value.toLowerCase() === name.toLowerCase(); });

    if (treffer) {
      treffer.checked = true;
    } else {
      var label = document.createElement("label");
      label.className = "show-checkbox neu-hinzugefuegt";

      var checkbox = document.createElement("input");
      checkbox.type = "checkbox";
      checkbox.name = "shows";
      checkbox.value = name;
      checkbox.checked = true;

      var hiddenAliases = document.createElement("input");
      hiddenAliases.type = "hidden";
      hiddenAliases.name = "aliases__" + name;
      hiddenAliases.value = aliases;

      label.appendChild(checkbox);
      label.appendChild(hiddenAliases);
      label.appendChild(document.createTextNode(" " + name + " "));

      if (aliases) {
        var span = document.createElement("span");
        span.className = "show-aliases";
        span.textContent = "(" + aliases + ")";
        label.appendChild(span);
      }

      liste.appendChild(label);

      var labels = Array.prototype.slice.call(liste.querySelectorAll(".show-checkbox"));
      labels.sort(function (a, b) {
        var an = a.querySelector('input[type="checkbox"]').value;
        var bn = b.querySelector('input[type="checkbox"]').value;
        return an.localeCompare(bn, "de", { sensitivity: "base" });
      });
      labels.forEach(function (l) { liste.appendChild(l); });
      treffer = checkbox;
    }

    // Suche zuruecksetzen, damit die neue Sendung auch zu sehen ist
    suche.value = "";
    aktualisieren();
    treffer.closest(".show-checkbox").scrollIntoView({ block: "nearest", behavior: "smooth" });

    nameFeld.value = "";
    aliasFeld.value = "";
    nameFeld.focus();
  }

  document.getElementById("hinzufuegen-button").addEventListener("click", hinzufuegen);

  // Enter in den beiden Feldern heisst "Hinzufuegen" - frueher schickte es das
  // ganze Formular ab, und der getippte Name ging verloren
  [nameFeld, aliasFeld].forEach(function (feld) {
    feld.addEventListener("keydown", function (ereignis) {
      if (ereignis.key === "Enter") {
        ereignis.preventDefault();
        hinzufuegen();
      }
    });
  });

  // Enter im Suchfeld soll ebenfalls nicht speichern
  suche.addEventListener("keydown", function (ereignis) {
    if (ereignis.key === "Enter") ereignis.preventDefault();
    if (ereignis.key === "Escape") { suche.value = ""; aktualisieren(); }
  });
  suche.addEventListener("input", aktualisieren);
  nurAusgewaehlte.addEventListener("change", aktualisieren);
  liste.addEventListener("change", aktualisieren);

  // --- Verwerfen ----------------------------------------------------------
  document.getElementById("verwerfen-knopf").addEventListener("click", function () {
    kaestchen().forEach(function (cb) {
      if (!anfangsNamen[cb.value]) {
        cb.closest(".show-checkbox").remove();
      } else {
        cb.checked = !!anfangsHaken[cb.value];
      }
    });
    aktualisieren();
  });

  // --- Speichern / Seite verlassen ----------------------------------------
  form.addEventListener("submit", function () {
    wirdGespeichert = true;
    ["speichern-unten", "speichern-leiste-knopf"].forEach(function (id) {
      var knopf = document.getElementById(id);
      knopf.disabled = true;
      knopf.textContent = "Wird gespeichert …";
    });
  });

  window.addEventListener("beforeunload", function (ereignis) {
    if (wirdGespeichert || aenderungen() === 0) return;
    ereignis.preventDefault();
    ereignis.returnValue = "";
  });

  document.getElementById("liste-werkzeuge").hidden = false;
  aktualisieren();
})();

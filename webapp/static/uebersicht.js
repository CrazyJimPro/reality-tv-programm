// Schalter "Wiederholungen ausblenden" / "Gesehenes ausblenden" und das
// Gesehen-Haekchen in der Uebersicht.
//
// Die Schalter merkt sich der Browser (localStorage) - jedes Geraet fuer
// sich, wie beim Hell/Dunkel-Umschalter. Das Haekchen dagegen speichert die
// App (Tabelle "gesehen"), damit es auf PC und Handy gleich aussieht.
(function () {
  var SCHALTER = {
    "filter-wiederholungen": { klasse: "ohne-wiederholungen", speicher: "rtv-ohne-wiederholungen" },
    "filter-gesehen": { klasse: "ohne-gesehene", speicher: "rtv-ohne-gesehene" }
  };

  function lesen(name) {
    try { return localStorage.getItem(name) === "1"; } catch (e) { return false; }
  }

  function schreiben(name, wert) {
    try { localStorage.setItem(name, wert ? "1" : "0"); } catch (e) {}
  }

  // Tage, an denen durch die Schalter nichts mehr zu sehen ist, sagen das,
  // statt kommentarlos nur eine Ueberschrift zu zeigen.
  function leereTageMarkieren() {
    document.querySelectorAll(".tag").forEach(function (tag) {
      var sendungen = tag.querySelectorAll(".sendung");
      if (!sendungen.length) return;
      var sichtbar = Array.prototype.some.call(sendungen, function (li) {
        return li.offsetParent !== null;
      });
      tag.classList.toggle("alles-ausgeblendet", !sichtbar);
    });
  }

  Object.keys(SCHALTER).forEach(function (id) {
    var box = document.getElementById(id);
    if (!box) return;
    var info = SCHALTER[id];
    box.checked = lesen(info.speicher);
    document.body.classList.toggle(info.klasse, box.checked);
    box.addEventListener("change", function () {
      document.body.classList.toggle(info.klasse, box.checked);
      schreiben(info.speicher, box.checked);
      leereTageMarkieren();
    });
  });

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

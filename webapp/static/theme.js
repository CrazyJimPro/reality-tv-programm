// Manueller Hell/Dunkel-Umschalter. Die eigentliche Farbwahl passiert per
// CSS ueber :root[data-theme="..."] (siehe style.css) - hier wird nur der
// Knopf verdrahtet und die Wahl in localStorage gemerkt. Das sofortige
// Setzen von data-theme beim Laden (gegen Farbflackern) passiert bereits
// per Inline-Script im <head>, noch vor diesem Skript.
(function () {
  function effektivesTheme() {
    var explizit = document.documentElement.getAttribute("data-theme");
    if (explizit === "dark" || explizit === "light") return explizit;
    return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  }

  // Strichsymbole statt Emoji, damit der Knopf zu den anderen Symbolen passt
  // (Emoji sehen je nach Betriebssystem anders aus)
  var SONNE = '<svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="4"/>' +
    '<path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>';
  var MOND = '<svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5z"/></svg>';

  function beschrifte(button) {
    var aktuell = effektivesTheme();
    button.innerHTML = aktuell === "dark" ? SONNE : MOND;
    button.setAttribute(
      "aria-label",
      aktuell === "dark" ? "Helles Design aktivieren" : "Dunkles Design aktivieren"
    );
  }

  function init() {
    var button = document.getElementById("theme-toggle");
    if (!button) return;
    beschrifte(button);

    button.addEventListener("click", function () {
      var neu = effektivesTheme() === "dark" ? "light" : "dark";
      document.documentElement.setAttribute("data-theme", neu);
      try {
        localStorage.setItem("rtv-theme", neu);
      } catch (e) {
        // localStorage kann z.B. im privaten Modus fehlschlagen - dann
        // wirkt der Umschalter nur fuer die aktuelle Seitenansicht.
      }
      beschrifte(button);
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();

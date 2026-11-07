// Theme switcher. Colors are defined with light-dark(), so the effective
// theme is whatever color-scheme resolves to: the OS preference by default,
// or the data-theme override set here. Loaded blocking in <head> so a stored
// choice applies before first paint. An override matching the OS preference
// is dropped, returning the visitor to auto-following. It also fetches the
// feedback overlay, for enrolled readers only.
(function() {
  const root = document.documentElement;

  function stored(key) {
    try {
      return localStorage.getItem(key);
    } catch (e) {
      return null;
    }
  }

  function store(value) {
    try {
      if (value === null) localStorage.removeItem("theme");
      else localStorage.setItem("theme", value);
    } catch (e) {
      /* storage blocked: the override still applies for this page view */
    }
  }

  const choice = stored("theme");
  if (choice === "light" || choice === "dark") root.dataset.theme = choice;

  // What reveals the toggle, which CSS keeps hidden otherwise. Set here rather
  // than once the button exists, because this runs before the first paint and
  // DOMContentLoaded does not: revealing it later shifted the page.
  root.dataset.js = "";

  // Public visitors never download signals.js. Enrolled readers start the
  // download here, before the body parses. The key and the fragment match
  // signals.js.
  const signals = document.querySelector("meta[name=\"signals\"]");
  if (
    signals
    && (location.hash.startsWith("#signals-token=") || stored("signals-token"))
  ) {
    const script = document.createElement("script");
    script.src = signals.dataset.src;
    script.dataset.endpoint = signals.content;
    document.head.append(script);
  }

  document.addEventListener("DOMContentLoaded", function() {
    const button = document.getElementById("theme-toggle");
    if (!button) return;
    button.addEventListener("click", function() {
      const system = matchMedia("(prefers-color-scheme: dark)").matches
        ? "dark"
        : "light";
      const current = root.dataset.theme || system;
      const next = current === "dark" ? "light" : "dark";
      if (next === system) {
        delete root.dataset.theme;
        store(null);
      } else {
        root.dataset.theme = next;
        store(next);
      }
    });
  });
})();

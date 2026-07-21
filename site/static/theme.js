// Theme switcher. Colors are defined with light-dark(), so the effective
// theme is whatever color-scheme resolves to: the OS preference by default,
// or the data-theme override set here. Loaded blocking in <head> so a stored
// choice applies before first paint. An override matching the OS preference
// is dropped, returning the visitor to auto-following.
(function() {
  const root = document.documentElement;

  function stored() {
    try {
      return localStorage.getItem("theme");
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

  const choice = stored();
  if (choice === "light" || choice === "dark") root.dataset.theme = choice;

  document.addEventListener("DOMContentLoaded", function() {
    const button = document.getElementById("theme-toggle");
    if (!button) return;
    button.hidden = false;
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

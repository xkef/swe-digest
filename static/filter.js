// Data-driven story filter for the home index. Progressive enhancement:
// without JS every story is already rendered and visible.
(function () {
  const index = document.querySelector(".story-index");
  if (!index) return;

  const rows = Array.from(index.querySelectorAll(".story-row"));
  const groups = Array.from(index.querySelectorAll(".digest-group"));
  const facets = Array.from(index.querySelectorAll(".facet[data-facet]"));
  const search = document.getElementById("story-search");
  const count = document.getElementById("story-count");
  const empty = document.getElementById("story-empty");
  const reset = document.getElementById("filter-reset");

  const active = { category: new Set(), status: new Set() };
  let query = "";

  function apply() {
    let shown = 0;
    for (const row of rows) {
      const okCat = active.category.size === 0 || active.category.has(row.dataset.category);
      const okStatus = active.status.size === 0 || active.status.has(row.dataset.status);
      const okText = !query || row.dataset.text.includes(query);
      const visible = okCat && okStatus && okText;
      row.hidden = !visible;
      if (visible) shown++;
    }
    for (const group of groups) {
      group.hidden = !group.querySelector(".story-row:not([hidden])");
    }
    count.textContent = shown === 1 ? "1 story" : shown + " stories";
    empty.hidden = shown !== 0;
    reset.hidden = active.category.size === 0 && active.status.size === 0 && !query;
  }

  for (const button of facets) {
    button.addEventListener("click", function () {
      const set = active[button.dataset.facet];
      const value = button.dataset.value;
      if (set.has(value)) {
        set.delete(value);
        button.setAttribute("aria-pressed", "false");
      } else {
        set.add(value);
        button.setAttribute("aria-pressed", "true");
      }
      apply();
    });
  }

  if (search) {
    search.addEventListener("input", function () {
      query = search.value.trim().toLowerCase();
      apply();
    });
  }

  reset.addEventListener("click", function () {
    active.category.clear();
    active.status.clear();
    query = "";
    if (search) search.value = "";
    for (const button of facets) button.setAttribute("aria-pressed", "false");
    apply();
  });

  apply();
})();

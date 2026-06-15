// Story search for the home index. Without JS every story on the current
// page is rendered and visible. With JS, any query searches the full archive
// index fetched from /stories.json; clearing it restores the server-rendered
// page.
(function () {
  const index = document.querySelector(".story-index");
  if (!index) return;

  const rows = Array.from(index.querySelectorAll(".story-row"));
  const groups = Array.from(index.querySelectorAll(".digest-group"));
  const search = document.getElementById("story-search");
  const count = document.getElementById("story-count");
  const empty = document.getElementById("story-empty");
  const results = document.getElementById("archive-results");
  const pagination = index.querySelector(".pagination");
  const base = index.dataset.base || "";
  const defaultCount = count.textContent;

  const MAX_RESULTS = 100;
  let query = "";
  let needleSets = [];
  let archive = null;

  fetch(base + "/stories.json")
    .then(function (response) { return response.ok ? response.json() : null; })
    .then(function (data) { archive = data; setQuery(query); apply(); })
    .catch(function () {});

  // Each query term expands through the alias groups in stories.json, so
  // "anthropic" also matches claude/opus/sonnet stories. A story matches
  // when every term matches via at least one of its alternatives.
  function expand(term) {
    const needles = [term];
    for (const group of (archive && archive.aliases) || []) {
      const hit = group.some(function (word) {
        return word === term || (term.length >= 3 && word.startsWith(term));
      });
      if (!hit) continue;
      for (const word of group) {
        if (!needles.includes(word)) needles.push(word);
      }
    }
    return needles;
  }

  function setQuery(value) {
    query = value;
    needleSets = query ? query.split(/\s+/).map(expand) : [];
  }

  function matchesText(text) {
    return needleSets.every(function (needles) {
      return needles.some(function (needle) { return text.includes(needle); });
    });
  }

  function matches(story) {
    const text = (story.title + " " + story.summary + " " + story.category).toLowerCase();
    return matchesText(text);
  }

  function badge(cls, text) {
    const span = document.createElement("span");
    span.className = cls;
    span.textContent = text;
    return span;
  }

  function renderRow(story) {
    const li = document.createElement("li");
    li.className = "story-row";
    const link = document.createElement("a");
    link.className = "story-link";
    link.href = base + story.url;
    const meta = document.createElement("span");
    meta.className = "story-meta";
    meta.appendChild(badge("badge", story.date));
    if (story.category) meta.appendChild(badge("badge badge-cat", story.category));
    if (story.status) meta.appendChild(badge("badge badge-status status-" + story.status, story.status));
    link.appendChild(meta);
    const title = document.createElement("span");
    title.className = "story-title";
    title.textContent = story.title;
    link.appendChild(title);
    if (story.summary) {
      const summary = document.createElement("span");
      summary.className = "story-summary";
      summary.textContent = story.summary;
      link.appendChild(summary);
    }
    li.appendChild(link);
    return li;
  }

  function showPage() {
    for (const row of rows) row.hidden = false;
    for (const group of groups) group.hidden = false;
    if (pagination) pagination.hidden = false;
    results.hidden = true;
    results.textContent = "";
    empty.hidden = true;
    count.textContent = defaultCount;
  }

  function showArchive() {
    const found = archive.stories.filter(matches);
    results.textContent = "";
    for (const story of found.slice(0, MAX_RESULTS)) results.appendChild(renderRow(story));
    for (const group of groups) group.hidden = true;
    if (pagination) pagination.hidden = true;
    results.hidden = found.length === 0;
    empty.hidden = found.length !== 0;
    count.textContent = found.length > MAX_RESULTS
      ? "first " + MAX_RESULTS + " of " + found.length + " matching stories"
      : found.length + " of " + archive.total_stories + " stories";
  }

  function filterPageRows() {
    let shown = 0;
    for (const row of rows) {
      const visible = matchesText(row.dataset.text);
      row.hidden = !visible;
      if (visible) shown++;
    }
    for (const group of groups) {
      group.hidden = !group.querySelector(".story-row:not([hidden])");
    }
    count.textContent = shown === 1 ? "1 story on this page" : shown + " stories on this page";
    empty.hidden = shown !== 0;
  }

  function apply() {
    if (!query) {
      showPage();
    } else if (archive) {
      showArchive();
    } else {
      filterPageRows();
    }
  }

  if (search) {
    search.addEventListener("input", function () {
      setQuery(search.value.trim().toLowerCase());
      apply();
    });
  }
})();

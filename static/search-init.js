// Story search for the home index. Without JS every story on the current page
// is rendered and visible. With JS, a query runs against the Pagefind index
// (built from the rendered story pages); clearing it restores the
// server-rendered page. Pagefind shards its index, so only the chunks a query
// touches are fetched, and the module itself loads lazily on first use.
(function () {
  const index = document.querySelector(".story-index");
  if (!index) return;

  const search = document.getElementById("story-search");
  const count = document.getElementById("story-count");
  const empty = document.getElementById("story-empty");
  const results = document.getElementById("archive-results");
  const more = document.getElementById("search-more");
  const groups = Array.from(index.querySelectorAll(".digest-group"));
  const pagination = index.querySelector(".pagination");
  // The site is served under a base path (GitHub Pages /swe-digest/). Pagefind
  // records result URLs and loads its chunks relative to the site root, so
  // derive that prefix from the page's data-base attribute.
  const basePath = new URL(index.dataset.base).pathname.replace(/\/$/, "");
  const defaultCount = count.textContent;
  const BATCH = 20;

  let pagefind = null;
  let unavailable = false;
  let current = null;
  let shown = 0;
  let token = 0; // guards against out-of-order async renders
  let timer = null;

  async function loadPagefind() {
    if (unavailable) throw new Error("pagefind unavailable");
    if (!pagefind) {
      try {
        pagefind = await import(basePath + "/pagefind/pagefind.js");
        await pagefind.init();
      } catch (err) {
        // The index is built after `zola build` (Pagefind), so it is absent
        // under `zola serve`. Disable search rather than retry every keystroke.
        unavailable = true;
        throw err;
      }
    }
    return pagefind;
  }

  function badge(cls, text) {
    const span = document.createElement("span");
    span.className = cls;
    span.textContent = text;
    return span;
  }

  function renderRow(data) {
    const meta = data.meta || {};
    const li = document.createElement("li");
    li.className = "story-row";
    const link = document.createElement("a");
    link.className = "story-link";
    link.href = basePath + data.url;
    const row = document.createElement("span");
    row.className = "story-meta";
    if (meta.date) row.appendChild(badge("badge", meta.date));
    if (meta.category) row.appendChild(badge("badge badge-cat", meta.category));
    if (meta.status) row.appendChild(badge("badge badge-status status-" + meta.status, meta.status));
    link.appendChild(row);
    const title = document.createElement("span");
    title.className = "story-title";
    title.textContent = meta.title || "";
    link.appendChild(title);
    if (data.excerpt) {
      const summary = document.createElement("span");
      summary.className = "story-summary";
      summary.innerHTML = data.excerpt;
      link.appendChild(summary);
    }
    li.appendChild(link);
    return li;
  }

  // Fetch and build a batch of rows into a detached fragment. Building off-DOM
  // and swapping in one step keeps the visible list stable while the next batch
  // loads, so typing does not flash an empty list or shift the page.
  async function buildRows(start) {
    const slice = current.results.slice(start, start + BATCH);
    const datas = await Promise.all(slice.map((result) => result.data()));
    const fragment = document.createDocumentFragment();
    for (const data of datas) fragment.appendChild(renderRow(data));
    return { fragment, length: datas.length };
  }

  function hideBrowse() {
    for (const group of groups) group.hidden = true;
    if (pagination) pagination.hidden = true;
  }

  function showBrowse() {
    for (const group of groups) group.hidden = false;
    if (pagination) pagination.hidden = false;
    results.replaceChildren();
    results.hidden = true;
    empty.hidden = true;
    more.hidden = true;
    count.textContent = defaultCount;
  }

  async function run(query) {
    const mine = ++token;
    let pf, found;
    try {
      pf = await loadPagefind();
      found = await pf.search(query);
    } catch (err) {
      return; // search index unavailable (e.g. `zola serve`); keep the browse
    }
    if (mine !== token) return; // a newer query superseded this one
    current = found;
    const total = found.results.length;
    if (total === 0) {
      hideBrowse();
      results.replaceChildren();
      results.hidden = true;
      empty.hidden = false;
      more.hidden = true;
      count.textContent = "No stories match " + query;
      return;
    }
    const { fragment, length } = await buildRows(0);
    if (mine !== token) return; // re-check: data() awaited above
    shown = length;
    results.replaceChildren(fragment);
    results.hidden = false;
    empty.hidden = true;
    hideBrowse();
    count.textContent = total + (total === 1 ? " result" : " results");
    more.hidden = shown >= total;
  }

  async function loadMore() {
    if (!current) return;
    const mine = token;
    const { fragment, length } = await buildRows(shown);
    if (mine !== token) return; // query changed while this batch loaded
    results.appendChild(fragment);
    shown += length;
    more.hidden = shown >= current.results.length;
  }

  search.addEventListener("input", function () {
    const query = search.value.trim();
    clearTimeout(timer);
    if (!query) {
      ++token;
      showBrowse();
      return;
    }
    timer = setTimeout(() => run(query), 150);
  });

  more.addEventListener("click", loadMore);
})();

(() => {
  const input = document.querySelector("#search-input");
  const results = document.querySelector("#search-results");
  const status = document.querySelector("#search-status");
  const script = document.currentScript || document.querySelector('script[src$="search.js"]');
  const indexUrl = new URL("search_index.en.json", script ? script.src : window.location.href);
  let docs = [];

  const text = (value) => (value || "").toString();

  const normalizeDoc = (doc) => {
    const body = text(doc.body || doc.content || doc.description || doc.summary);
    const title = text(doc.title || doc.name || "Untitled");
    const description = text(doc.description || doc.summary || "");
    const url = text(doc.url || doc.permalink || doc.path || doc.id || "#");
    return {
      title,
      description,
      body,
      url,
      haystack: `${title} ${description} ${body}`.toLowerCase(),
    };
  };

  const extractDocs = (data) => {
    if (Array.isArray(data)) return data.map(normalizeDoc);
    if (Array.isArray(data.documents)) return data.documents.map(normalizeDoc);
    if (data && data.documentStore && data.documentStore.docs) {
      return Object.values(data.documentStore.docs).map(normalizeDoc);
    }
    if (data && data.docs && typeof data.docs === "object") {
      return Object.values(data.docs).map(normalizeDoc);
    }
    return [];
  };

  const escapeHtml = (value) => text(value).replace(/[&<>"]/g, (char) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    "\"": "&quot;",
  }[char]));

  const snippet = (doc, terms) => {
    const source = doc.description || doc.body || "";
    const lower = source.toLowerCase();
    const hit = terms.map((term) => lower.indexOf(term)).filter((idx) => idx >= 0).sort((a, b) => a - b)[0] || 0;
    const start = Math.max(0, hit - 80);
    const end = Math.min(source.length, hit + 180);
    const prefix = start > 0 ? "..." : "";
    const suffix = end < source.length ? "..." : "";
    return `${prefix}${source.slice(start, end).trim()}${suffix}`;
  };

  const score = (doc, terms, query) => {
    const title = doc.title.toLowerCase();
    let total = 0;
    for (const term of terms) {
      if (title.includes(term)) total += 8;
      if (doc.haystack.includes(term)) total += 2;
    }
    if (title.includes(query)) total += 12;
    if (doc.haystack.includes(query)) total += 4;
    return total;
  };

  const render = () => {
    const query = input.value.trim().toLowerCase();
    const terms = query.split(/\s+/).filter(Boolean);

    results.innerHTML = "";
    if (terms.length === 0) {
      status.textContent = "Type to search.";
      return;
    }

    const matches = docs
      .map((doc) => ({ doc, score: score(doc, terms, query) }))
      .filter((item) => item.score > 0 && terms.every((term) => item.doc.haystack.includes(term)))
      .sort((a, b) => b.score - a.score)
      .slice(0, 25);

    status.textContent = matches.length === 1 ? "1 result." : `${matches.length} results.`;

    results.innerHTML = matches.map(({ doc }) => `
      <li>
        <a href="${escapeHtml(doc.url)}">${escapeHtml(doc.title)}</a>
        <p>${escapeHtml(snippet(doc, terms))}</p>
      </li>
    `).join("");
  };

  fetch(indexUrl)
    .then((response) => {
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return response.json();
    })
    .then((data) => {
      docs = extractDocs(data);
      status.textContent = docs.length ? "Type to search." : "Search index is empty.";
      render();
    })
    .catch(() => {
      status.textContent = "Search index failed to load.";
    });

  input.addEventListener("input", render);
})();

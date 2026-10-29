// Feedback overlay for enrolled readers. /enroll on the signals Worker
// redirects here with a device token in the URL fragment, which this script
// moves into localStorage. Without a token the script stops before any
// network request, so public visitors send nothing.
(function() {
  const KEY = "signals-token";
  const FRAGMENT = "#signals-token=";
  const endpoint = document.currentScript
    && document.currentScript.dataset.endpoint;
  if (!endpoint) {
    return;
  }

  const token = captureToken() || stored();
  if (!token) {
    return;
  }

  const TOGGLES = [
    { label: "more", field: "vote", on: "more", off: null },
    { label: "less", field: "vote", on: "less", off: null },
    { label: "knew it", field: "knew", on: true, off: false },
    { label: "follow", field: "follow", on: true, off: false },
  ];

  start().catch(report);

  async function start() {
    const me = await api("GET", "/me");
    const stories = Array.from(document.querySelectorAll("[data-story]"));
    const days = new Set(stories.map((el) => el.dataset.story.slice(0, 10)));
    const saved = new Map();
    for (const day of days) {
      for (const feedback of await api("GET", "/feedback?day=" + day)) {
        saved.set(feedback.story, feedback);
      }
    }

    // The bar takes the place of the issue link on a story page.
    for (const el of stories) {
      const bar = controls(el.dataset.story, saved.get(el.dataset.story), me);
      const link = el.querySelector(".story-feedback");
      if (link) {
        link.replaceWith(bar);
      } else {
        el.append(bar);
      }
    }
    const suggest = document.querySelector("[data-signals-suggest]");
    if (suggest) {
      dropdown(suggest, panel(me));
    }
  }

  // One row of toggles under a story. Every click saves the whole state, so
  // the server always holds what the buttons show.
  function controls(story, saved, me) {
    const state = Object.assign(
      { vote: null, knew: false, follow: false, note: "" },
      saved,
    );
    const bar = element("div", "signals-bar");
    const status = element("span", "signals-status");
    const buttons = TOGGLES.map((toggle) => {
      const button = element("button", "signals-toggle", toggle.label);
      button.type = "button";
      button.addEventListener("click", () => {
        state[toggle.field] = state[toggle.field] === toggle.on
          ? toggle.off
          : toggle.on;
        save();
      });
      bar.append(button);
      return { button, toggle };
    });

    if (me.role === "owner") {
      const note = element("input", "signals-note");
      note.type = "text";
      note.placeholder = "note";
      note.maxLength = 500;
      note.value = state.note;
      note.setAttribute("aria-label", "Note on this story");
      note.addEventListener("change", () => {
        state.note = note.value.trim();
        save();
      });
      bar.append(note);
    }
    bar.append(status);

    function render() {
      for (const { button, toggle } of buttons) {
        button.setAttribute(
          "aria-pressed",
          String(state[toggle.field] === toggle.on),
        );
      }
    }

    async function save() {
      render();
      status.textContent = "";
      try {
        await api("PUT", "/feedback/" + story, state);
      } catch (error) {
        status.textContent = "not saved";
        report(error);
      }
    }

    render();
    return bar;
  }

  // For enrolled readers the header's suggest link, which otherwise opens
  // the GitHub issue form, toggles the panel under the header instead.
  function dropdown(link, content) {
    content.id = "signals-panel";
    content.hidden = true;
    link.closest("header").after(content);
    link.setAttribute("aria-controls", content.id);
    link.setAttribute("aria-expanded", "false");

    function toggle(open) {
      content.hidden = !open;
      link.setAttribute("aria-expanded", String(open));
      if (open) {
        content.querySelector("input").focus();
      }
    }

    link.addEventListener("click", (event) => {
      event.preventDefault();
      toggle(content.hidden);
    });
    content.addEventListener("keydown", (event) => {
      if (event.key === "Escape") {
        toggle(false);
        link.focus();
      }
    });
  }

  // The suggest form and the request list. The owner approves or rejects
  // friends' requests here.
  function panel(me) {
    const aside = element("aside", "signals-panel");
    aside.setAttribute("aria-label", "Feedback");
    const form = element("form", "signals-form");
    const url = element("input", "signals-url");
    url.type = "url";
    url.required = true;
    url.placeholder = "suggest a story URL";
    url.setAttribute("aria-label", "Story URL");
    const note = element("input", "signals-note");
    note.type = "text";
    note.placeholder = "why (optional)";
    note.maxLength = 500;
    note.setAttribute("aria-label", "Why this story");
    const send = element("button", "signals-toggle", "suggest");
    send.type = "submit";
    const status = element("span", "signals-status");
    const list = element("ul", "signals-requests");
    form.append(url, note, send, status);
    aside.append(form, list);

    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      try {
        const added = await api("POST", "/requests", {
          url: url.value,
          note: note.value,
        });
        url.value = "";
        note.value = "";
        status.textContent = added.status === "pending"
          ? "sent, waiting for approval"
          : "added";
        await refresh();
      } catch (error) {
        status.textContent = "not sent";
        report(error);
      }
    });

    async function refresh() {
      const requests = await api("GET", "/requests");
      list.replaceChildren(...requests.map((request) => row(request)));
    }

    function row(request) {
      const item = element("li", "signals-request");
      const link = element("a", "", request.url);
      link.href = request.url;
      link.rel = "noopener noreferrer nofollow";
      item.append(link, element("span", "signals-status", request.status));
      if (request.note) {
        item.append(element("span", "signals-status", request.note));
      }
      if (me.role === "owner" && request.status === "pending") {
        item.append(element("span", "signals-status", request.from));
        for (const decision of ["approved", "rejected"]) {
          const button = element(
            "button",
            "signals-toggle",
            decision === "approved" ? "approve" : "reject",
          );
          button.type = "button";
          button.addEventListener("click", () => {
            api("PUT", "/requests/" + request.id, { status: decision })
              .then(refresh)
              .catch(report);
          });
          item.append(button);
        }
      }
      return item;
    }

    refresh().catch(report);
    return aside;
  }

  async function api(method, path, body) {
    const headers = { Authorization: "Bearer " + token };
    if (body !== undefined) {
      headers["Content-Type"] = "application/json";
    }
    const response = await fetch(endpoint + path, {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
    });
    if (response.status === 401) {
      store(null);
    }
    if (!response.ok) {
      throw new Error(method + " " + path + ": " + response.status);
    }
    return response.status === 204 ? null : response.json();
  }

  function captureToken() {
    if (!location.hash.startsWith(FRAGMENT)) {
      return null;
    }
    const value = location.hash.slice(FRAGMENT.length);
    store(value);
    history.replaceState(null, "", location.pathname + location.search);
    return value;
  }

  function stored() {
    try {
      return localStorage.getItem(KEY);
    } catch (e) {
      return null;
    }
  }

  function store(value) {
    try {
      if (value === null) {
        localStorage.removeItem(KEY);
      } else {
        localStorage.setItem(KEY, value);
      }
    } catch (e) {
      // Storage can be blocked. The overlay then lasts for this page only.
    }
  }

  function element(tag, className, text) {
    const el = document.createElement(tag);
    if (className) {
      el.className = className;
    }
    if (text !== undefined) {
      el.textContent = text;
    }
    return el;
  }

  function report(error) {
    console.warn("signals:", error);
  }
})();

// Rewrite UTC timestamps to the visitor's local timezone. Each timestamp is
// server-rendered as <time class="js-localtime" datetime="<ISO>">UTC label</time>,
// so without JS the UTC label stands; with JS the text becomes local time.
(function() {
  function pad(n) {
    return String(n).padStart(2, "0");
  }

  function zoneName(date) {
    try {
      const part = new Intl.DateTimeFormat(undefined, { timeZoneName: "short" })
        .formatToParts(date)
        .find(function(p) {
          return p.type === "timeZoneName";
        });
      return part ? part.value : "";
    } catch (e) {
      return "";
    }
  }

  function format(date) {
    const zone = zoneName(date);
    return date.getFullYear() + "-" + pad(date.getMonth() + 1) + "-"
      + pad(date.getDate())
      + " " + pad(date.getHours()) + ":" + pad(date.getMinutes())
      + (zone ? " " + zone : "");
  }

  const nodes = document.querySelectorAll("time.js-localtime[datetime]");
  for (const node of nodes) {
    const date = new Date(node.getAttribute("datetime"));
    if (!isNaN(date.getTime())) node.textContent = format(date);
  }
})();

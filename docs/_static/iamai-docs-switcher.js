(function() {
  function escapeHtml(value) {
    return String(value || "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;");
  }

  function itemList(title, items) {
    const links = items
      .map((item) => {
        const current = item.current ? ' aria-current="page"' : "";
        const badge = item.current
          ? '<span class="iamai-docs-switcher__current">current</span>'
          : "";
        return `
        <a href="${escapeHtml(item.url)}"${current}>
          <span>${escapeHtml(item.label)}</span>
          ${badge}
        </a>
      `;
      })
      .join("");
    return `
      <section>
        <div class="iamai-docs-switcher__section-title">${escapeHtml(title)}</div>
        <div class="iamai-docs-switcher__items">${links}</div>
      </section>
    `;
  }

  function switcherIcon() {
    return `
      <span class="iamai-docs-switcher__icon" aria-hidden="true">
        <span></span>
      </span>
    `;
  }

  function mountTarget() {
    return document.querySelector(".sidebar-sticky") || document.body;
  }

  function renderSwitcher(config) {
    const currentVersion =
      (config.versions || []).find((item) => item.current) || {};
    const currentLanguage =
      (config.languages || []).find((item) => item.current) || {};
    const target = mountTarget();
    const inSidebar = target !== document.body;
    const root = document.createElement("div");
    root.className = inSidebar
      ? "iamai-docs-switcher iamai-docs-switcher--sidebar"
      : "iamai-docs-switcher iamai-docs-switcher--floating";
    root.innerHTML = `
      <button class="iamai-docs-switcher__button" type="button" aria-expanded="false" aria-label="Switch documentation version and language">
        ${switcherIcon()}
      </button>
      <div class="iamai-docs-switcher__panel" hidden>
        <div class="iamai-docs-switcher__summary">
          <span class="iamai-docs-switcher__project">${escapeHtml(config.project || "iamai")}</span>
          <strong>${escapeHtml(currentVersion.label || config.current_version)} · ${escapeHtml(currentLanguage.label || config.current_language)}</strong>
        </div>
        ${itemList("Versions", config.versions || [])}
        ${itemList("Languages", config.languages || [])}
      </div>
    `;
    const button = root.querySelector(".iamai-docs-switcher__button");
    const panel = root.querySelector(".iamai-docs-switcher__panel");
    button.addEventListener("click", () => {
      const expanded = button.getAttribute("aria-expanded") === "true";
      button.setAttribute("aria-expanded", String(!expanded));
      panel.hidden = expanded;
    });
    document.addEventListener("click", (event) => {
      if (!root.contains(event.target)) {
        button.setAttribute("aria-expanded", "false");
        panel.hidden = true;
      }
    });
    target.appendChild(root);
  }

  function init() {
    if (!window.iamai_DOCS_SWITCHER) {
      return;
    }
    renderSwitcher(window.iamai_DOCS_SWITCHER);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();

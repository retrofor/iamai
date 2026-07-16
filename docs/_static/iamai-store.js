(function() {
  const scriptUrl = document.currentScript ? document.currentScript.src : "";
  const INDEX_URL = scriptUrl
    ? scriptUrl.replace(/iamai-store\.js(?:\?.*)?$/, "iamai-store-index.json")
    : "_static/iamai-store-index.json";
  const STORE_TYPES = [
    "plugin",
    "adapter",
    "ruleset",
    "permission",
    "state_backend",
    "agent_tool",
    "agent_skill",
    "middleware",
    "template",
    "example",
    "provider",
    "theme",
  ];
  const STORE_PAGE_SIZE = 8;
  const BADGE_DESCRIPTIONS = {
    community: "社区提交，基础 schema 通过。",
    package_verified: "包名、安装命令和 entry point 信息完整。",
    author_verified: "作者、仓库或维护者身份经过人工审核。",
    official: "iamai 官方维护或推荐。",
    security_reviewed: "经过额外安全检查。",
    deprecated: "已弃用，保留展示但会降权。",
  };
  const STORE_I18N = {
    zh: {
      searchPlaceholder: "搜索包名、标签、作者、平台...",
      searchAria: "搜索社区扩展",
      allTypes: "全部类型",
      allPlatforms: "全部平台",
      allVerification: "全部认证",
      filterType: "按类型筛选",
      filterPlatform: "按平台筛选",
      filterVerification: "按认证筛选",
      entries: "条目",
      page: "第",
      noMatches: "没有符合当前筛选条件的社区扩展。",
      notFound: "未找到商店条目。",
      previous: "上一页",
      next: "下一页",
      submitOpen: "提交扩展",
      submitTitle: "提交社区扩展",
      submitSubtitle: "生成 GitHub issue，等待维护者审核。",
      closeSubmit: "关闭提交表单",
      type: "类型",
      entryId: "条目 ID",
      displayName: "展示名称",
      license: "许可证",
      summary: "简介",
      summaryPlaceholder: "180 字以内的一句话。",
      summaryHelp: "保持简短；这段文本会直接显示在社区商店卡片上。",
      package: "Python 包名",
      repository: "仓库 URL",
      iamaiRequires: "iamai 兼容范围",
      iamaiRequiresHelp: "填写包元数据中的 Requires-Dist 值，例如 iamai>=0.4,<0.5。",
      conformanceEvidence: "Conformance evidence",
      conformanceEvidenceHelp: "每行一个可复核的 CI、测试报告或命令输出 URL。",
      sourceUrl: "源码 URL",
      docsUrl: "文档 URL",
      homepageUrl: "主页 URL",
      tags: "标签",
      platforms: "平台",
      requires: "依赖能力",
      runtimeCapabilities: "运行时能力",
      entryPoints: "Entry points",
      entryPointsHelp: "每行一个：plugin:name=module:Class 或 adapter:name=module:Class。",
      configExample: "配置示例",
      securityStatement: "安全声明",
      permissionNotes: "权限说明",
      confirm: "此提交不包含密钥、私有端点或误导性的认证声明。",
      openIssue: "打开 GitHub Issue",
      submitDirect: "直接提交",
      previewTitle: "Registry JSON",
      configureRepo: "维护者需要先配置 iamai_store_github_repo，才能打开 GitHub 提交链接。",
      submitting: "正在提交...",
      submitted: "已提交。请在 GitHub 等待维护者审核。",
      invalidId: "条目 ID 只能使用小写字母、数字、点、下划线或连字符。",
      nameRequired: "展示名称为必填项。",
      summaryRequired: "简介为必填项，且不能超过 180 字。",
      packageOrRepoRequired: "请至少填写 Python 包名或仓库 URL。",
      iamaiRequiresRequired: "plugin 和 adapter 条目必须填写 iamai 兼容范围。",
      conformanceEvidenceRequired: "plugin 和 adapter 条目必须提供至少一条 conformance evidence URL。",
      securityRequired: "plugin、adapter 和 agent_tool 条目必须填写安全声明。",
      permissionRequired: "agent_tool 条目必须填写权限说明。",
      absoluteUrlRequired: "必须是绝对 http(s) URL。",
      loadFailed: "社区扩展加载失败。请通过 HTTP 服务访问文档，或重新构建文档。",
      safety: "安全",
    },
    en: {
      searchPlaceholder: "Search packages, tags, authors, platforms...",
      searchAria: "Search ecosystem entries",
      allTypes: "All types",
      allPlatforms: "All platforms",
      allVerification: "All verification",
      filterType: "Filter by type",
      filterPlatform: "Filter by platform",
      filterVerification: "Filter by verification",
      entries: "entries",
      page: "page",
      noMatches: "No ecosystem entries match the current filters.",
      notFound: "Store entry not found.",
      previous: "Previous",
      next: "Next",
      submitOpen: "Submit extension",
      submitTitle: "Submit a community extension",
      submitSubtitle: "Generate a GitHub issue for maintainer review.",
      closeSubmit: "Close submission form",
      type: "Type",
      entryId: "Entry id",
      displayName: "Display name",
      license: "License",
      summary: "Summary",
      summaryPlaceholder: "One sentence under 180 characters.",
      summaryHelp: "Keep this short; it appears directly on the ecosystem card.",
      package: "Python package",
      repository: "Repository URL",
      iamaiRequires: "iamai compatibility range",
      iamaiRequiresHelp: "Use the package metadata Requires-Dist value, for example iamai>=0.4,<0.5.",
      conformanceEvidence: "Conformance evidence",
      conformanceEvidenceHelp: "Use one reviewable CI, test report, or command-output URL per line.",
      sourceUrl: "Source URL",
      docsUrl: "Docs URL",
      homepageUrl: "Homepage URL",
      tags: "Tags",
      platforms: "Platforms",
      requires: "Requires",
      runtimeCapabilities: "Runtime capabilities",
      entryPoints: "Entry points",
      entryPointsHelp: "Use one entry per line: plugin:name=module:Class or adapter:name=module:Class.",
      configExample: "Config example",
      securityStatement: "Security statement",
      permissionNotes: "Permission notes",
      confirm: "This submission contains no secrets, private endpoints, or misleading verification claims.",
      openIssue: "Open GitHub issue",
      submitDirect: "Submit directly",
      previewTitle: "Registry JSON",
      configureRepo: "Maintainers must configure iamai_store_github_repo before submissions can open GitHub.",
      submitting: "Submitting...",
      submitted: "Submission sent. Watch GitHub for maintainer review.",
      invalidId: "Entry id must use lowercase letters, numbers, dots, underscores, or hyphens.",
      nameRequired: "Display name is required.",
      summaryRequired: "Summary is required and must be 180 characters or fewer.",
      packageOrRepoRequired: "Provide at least a Python package or a repository URL.",
      iamaiRequiresRequired: "plugin and adapter entries must provide an iamai compatibility range.",
      conformanceEvidenceRequired: "plugin and adapter entries must provide at least one conformance evidence URL.",
      securityRequired: "Security statement is required for plugin, adapter, and agent_tool entries.",
      permissionRequired: "Permission notes are required for agent_tool entries.",
      absoluteUrlRequired: "must be an absolute http(s) URL.",
      loadFailed: "Failed to load ecosystem entries. Serve the docs over HTTP or rebuild the docs.",
      safety: "Safety",
    },
  };
  const I18N_LANG = (document.documentElement.lang || "zh").toLowerCase().startsWith("en") ? "en" : "zh";

  function t(key) {
    return STORE_I18N[I18N_LANG][key] || STORE_I18N.zh[key] || key;
  }

  function normalize(value) {
    return String(value || "").toLowerCase();
  }

  function option(label, value) {
    return `<option value="${escapeAttr(value)}">${escapeHtml(label)}</option>`;
  }

  function escapeHtml(value) {
    return String(value || "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;");
  }

  function escapeAttr(value) {
    return escapeHtml(value).replaceAll("'", "&#x27;");
  }

  function unique(items) {
    return Array.from(new Set(items.filter(Boolean))).sort((a, b) => a.localeCompare(b));
  }

  function splitList(value) {
    return String(value || "")
      .split(/[\n,]/)
      .map((item) => item.trim())
      .filter(Boolean);
  }

  function splitLines(value) {
    return String(value || "")
      .split(/\r?\n/)
      .map((item) => item.trim())
      .filter(Boolean);
  }

  function isPublicHttpUrl(value) {
    if (!value || /\s/.test(value)) {
      return false;
    }
    let parsed;
    try {
      parsed = new URL(value);
    } catch (_error) {
      return false;
    }
    if (!["http:", "https:"].includes(parsed.protocol) || parsed.username || parsed.password) {
      return false;
    }
    const hostname = parsed.hostname.replace(/^\[|\]$/g, "").replace(/\.$/, "").toLowerCase();
    if (!hostname) {
      return false;
    }
    if ([".local", ".localhost", ".invalid", ".test", ".example"].some(
      (suffix) => hostname.endsWith(suffix),
    )) {
      return false;
    }
    const ipv4 = hostname.match(/^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$/);
    if (ipv4) {
      return false;
    }
    if (hostname.includes(":")) {
      return false;
    }
    if (hostname.length > 253) {
      return false;
    }
    const labels = hostname.split(".");
    return labels.length >= 2 && labels.every(
      (label) => /^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$/.test(label),
    );
  }

  function parseEntryPoints(value) {
    return splitList(value).map((item) => {
      const parts = item.split("=");
      const left = (parts[0] || "").trim();
      const target = parts.slice(1).join("=").trim();
      const group = left.startsWith("adapter:")
        ? "iamai.adapters"
        : left.startsWith("plugin:")
          ? "iamai.plugins"
          : "";
      const name = left.replace(/^(adapter|plugin):/, "").trim();
      return { group, name, value: target };
    }).filter((entry) => entry.group && entry.name && entry.value);
  }

  function removeEmpty(value) {
    if (Array.isArray(value)) {
      return value.map(removeEmpty).filter((item) => {
        if (Array.isArray(item)) {
          return item.length;
        }
        if (item && typeof item === "object") {
          return Object.keys(item).length;
        }
        return item !== "" && item !== null && item !== undefined;
      });
    }
    if (value && typeof value === "object") {
      const result = {};
      Object.entries(value).forEach(([key, item]) => {
        const cleaned = removeEmpty(item);
        if (cleaned !== "" && cleaned !== null && cleaned !== undefined) {
          if (!Array.isArray(cleaned) || cleaned.length) {
            result[key] = cleaned;
          }
        }
      });
      return result;
    }
    return value;
  }

  function badgeLabel(value) {
    return String(value || "").replaceAll("_", " ");
  }

  function badgeDescription(value) {
    return BADGE_DESCRIPTIONS[value] || "社区商店认证徽章。";
  }

  function highlightJson(value) {
    return escapeHtml(value).replace(
      /("(?:\\u[\da-fA-F]{4}|\\[^u]|[^\\"])*"(?:\s*:)?|\b(?:true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+-]?\d+)?)/g,
      (match) => {
        let className = "iamai-store-json__number";
        if (match.endsWith(":")) {
          className = "iamai-store-json__key";
        } else if (match.startsWith('"')) {
          className = "iamai-store-json__string";
        } else if (match === "true" || match === "false") {
          className = "iamai-store-json__boolean";
        } else if (match === "null") {
          className = "iamai-store-json__null";
        }
        return `<span class="${className}">${match}</span>`;
      },
    );
  }

  function field(name, label, attrs) {
    const required = attrs.required ? " required" : "";
    const placeholder = attrs.placeholder ? ` placeholder="${escapeAttr(attrs.placeholder)}"` : "";
    const help = attrs.help ? `<small>${escapeHtml(attrs.help)}</small>` : "";
    const value = attrs.value ? ` value="${escapeAttr(attrs.value)}"` : "";
    return `
      <label class="iamai-store-submit__field">
        <span>${escapeHtml(label)}</span>
        <input name="${escapeAttr(name)}"${required}${placeholder}${value}>
        ${help}
      </label>
    `;
  }

  function textarea(name, label, attrs) {
    const required = attrs.required ? " required" : "";
    const placeholder = attrs.placeholder ? ` placeholder="${escapeAttr(attrs.placeholder)}"` : "";
    const help = attrs.help ? `<small>${escapeHtml(attrs.help)}</small>` : "";
    return `
      <label class="iamai-store-submit__field iamai-store-submit__field--textarea">
        <span>${escapeHtml(label)}</span>
        <textarea name="${escapeAttr(name)}"${required}${placeholder}>${escapeHtml(attrs.value || "")}</textarea>
        ${help}
      </label>
    `;
  }

  function selectField(name, label, values) {
    return `
      <label class="iamai-store-submit__field">
        <span>${escapeHtml(label)}</span>
        <select name="${escapeAttr(name)}" required>
          ${values.map((value) => option(value, value)).join("")}
        </select>
      </label>
    `;
  }

  function renderCard(entry) {
    const tags = (entry.tags || []).map((tag) => `<span class="iamai-store-pill">#${escapeHtml(tag)}</span>`).join("");
    const platforms = (entry.platforms || []).map((platform) => `<span class="iamai-store-pill">${escapeHtml(platform)}</span>`).join("");
    const badges = (entry.verification || [])
      .map((badge) => `
        <span
          class="iamai-store-pill iamai-store-pill--verified"
          title="${escapeAttr(badgeDescription(badge))}"
          aria-label="${escapeAttr(`${badgeLabel(badge)}: ${badgeDescription(badge)}`)}"
        >${escapeHtml(badgeLabel(badge))}</span>
      `)
      .join("");
    const links = [
      entry.docs_url ? `<a href="${escapeAttr(entry.docs_url)}">Docs</a>` : "",
      entry.source_url ? `<a href="${escapeAttr(entry.source_url)}">Source</a>` : "",
      entry.homepage_url ? `<a href="${escapeAttr(entry.homepage_url)}">Home</a>` : "",
    ].filter(Boolean).join(" · ");
    const install = entry.install_command ? `<code>${escapeHtml(entry.install_command)}</code>` : "";
    const entryPoints = (entry.entry_points || [])
      .map((item) => `<code>${escapeHtml(item.group)}:${escapeHtml(item.name)}</code>`)
      .join(" ");
    const capabilities = (entry.runtime_capabilities || [])
      .map((item) => `<span class="iamai-store-pill">${escapeHtml(item)}</span>`)
      .join("");
    const safety = entry.security_notes
      ? `<div class="iamai-store-card__safety"><strong>${escapeHtml(t("safety"))}:</strong> ${escapeHtml(entry.security_notes)}</div>`
      : "";
    const deprecated = entry.status === "deprecated" ? " iamai-store-card--deprecated" : "";
    return `
      <article class="iamai-store-card${deprecated}">
        <div class="iamai-store-card__topline">
          <span class="iamai-store-card__type">${escapeHtml(entry.type)}</span>
          <span class="iamai-store-card__status">${escapeHtml(entry.status)}</span>
        </div>
        <h3>${escapeHtml(entry.name)}</h3>
        <p>${escapeHtml(entry.summary)}</p>
        <div class="iamai-store-card__badges">${badges}</div>
        <div class="iamai-store-card__meta">${platforms}</div>
        <div class="iamai-store-card__tags">${tags}</div>
        ${capabilities ? `<div class="iamai-store-card__capabilities">${capabilities}</div>` : ""}
        ${entryPoints ? `<div class="iamai-store-card__entrypoints">${entryPoints}</div>` : ""}
        ${safety}
        ${install ? `<div class="iamai-store-card__install">${install}</div>` : ""}
        ${links ? `<div class="iamai-store-card__links">${links}</div>` : ""}
      </article>
    `;
  }

  function buildFilters(entries, defaultType) {
    const types = unique(entries.map((entry) => entry.type));
    const platforms = unique(entries.flatMap((entry) => entry.platforms || []));
    const badges = unique(entries.flatMap((entry) => entry.verification || []));
    return `
      <div class="iamai-store__controls">
        <input data-store-search type="search" placeholder="${escapeAttr(t("searchPlaceholder"))}" aria-label="${escapeAttr(t("searchAria"))}">
        <select data-store-type aria-label="${escapeAttr(t("filterType"))}">
          ${option(t("allTypes"), "")}
          ${types.map((type) => option(type, type)).join("")}
        </select>
        <select data-store-platform aria-label="${escapeAttr(t("filterPlatform"))}">
          ${option(t("allPlatforms"), "")}
          ${platforms.map((platform) => option(platform, platform)).join("")}
        </select>
        <select data-store-verification aria-label="${escapeAttr(t("filterVerification"))}">
          ${option(t("allVerification"), "")}
          ${badges.map((badge) => option(badgeLabel(badge), badge)).join("")}
        </select>
      </div>
      <div class="iamai-store__summary" data-store-summary></div>
      <div class="iamai-store__grid" data-store-grid></div>
      <div class="iamai-store__pagination" data-store-pagination></div>
    `;
  }

  function applyFilters(container, entries) {
    const search = normalize(container.querySelector("[data-store-search]").value);
    const type = container.querySelector("[data-store-type]").value;
    const platform = container.querySelector("[data-store-platform]").value;
    const verification = container.querySelector("[data-store-verification]").value;
    const filtered = entries
      .filter((entry) => !type || entry.type === type)
      .filter((entry) => !platform || (entry.platforms || []).includes(platform))
      .filter((entry) => !verification || (entry.verification || []).includes(verification))
      .filter((entry) => !search || normalize(entry.search_text).includes(search))
      .sort((left, right) => (left.sort_rank - right.sort_rank) || left.name.localeCompare(right.name));
    const pageCount = Math.max(1, Math.ceil(filtered.length / STORE_PAGE_SIZE));
    const currentPage = Math.min(Math.max(Number(container.dataset.storePage || "1"), 1), pageCount);
    container.dataset.storePage = String(currentPage);
    const start = (currentPage - 1) * STORE_PAGE_SIZE;
    const pageItems = filtered.slice(start, start + STORE_PAGE_SIZE);
    const grid = container.querySelector("[data-store-grid]");
    const summary = container.querySelector("[data-store-summary]");
    summary.textContent = filtered.length
      ? `${filtered.length} / ${entries.length} ${t("entries")} · ${t("page")} ${currentPage} / ${pageCount}`
      : `0 / ${entries.length} ${t("entries")}`;
    grid.innerHTML = pageItems.length
      ? pageItems.map(renderCard).join("")
      : `<div class="iamai-store__empty">${escapeHtml(t("noMatches"))}</div>`;
    renderPagination(container, entries, pageCount, currentPage);
  }

  function renderPagination(container, entries, pageCount, currentPage) {
    const pagination = container.querySelector("[data-store-pagination]");
    if (pageCount <= 1) {
      pagination.innerHTML = "";
      return;
    }
    const pages = Array.from({ length: pageCount }, (_, index) => index + 1)
      .map((page) => `
        <button type="button" data-store-page="${page}" aria-current="${page === currentPage ? "page" : "false"}">
          ${page}
        </button>
      `)
      .join("");
    pagination.innerHTML = `
      <button type="button" data-store-page="${currentPage - 1}" ${currentPage <= 1 ? "disabled" : ""}>${escapeHtml(t("previous"))}</button>
      ${pages}
      <button type="button" data-store-page="${currentPage + 1}" ${currentPage >= pageCount ? "disabled" : ""}>${escapeHtml(t("next"))}</button>
    `;
    pagination.querySelectorAll("[data-store-page]").forEach((button) => {
      button.addEventListener("click", () => {
        container.dataset.storePage = button.dataset.storePage;
        applyFilters(container, entries);
      });
    });
  }

  function renderStore(container, entries) {
    const defaultType = container.dataset.defaultType || "";
    container.querySelector(".iamai-store__loading")?.remove();
    container.insertAdjacentHTML("beforeend", buildFilters(entries, defaultType));
    if (container.querySelector(".iamai-store-submit__mount")) {
      renderSubmissionForm(container);
    }
    if (defaultType) {
      container.querySelector("[data-store-type]").value = defaultType;
    }
    container.dataset.storePage = "1";
    container.querySelectorAll(".iamai-store__controls input, .iamai-store__controls select").forEach((input) => {
      const onChange = () => {
        container.dataset.storePage = "1";
        applyFilters(container, entries);
      };
      input.addEventListener("input", onChange);
      input.addEventListener("change", onChange);
    });
    applyFilters(container, entries);
  }

  function renderCardSlots(entries) {
    const byId = new Map(entries.map((entry) => [entry.id, entry]));
    document.querySelectorAll("[data-iamai-store-card]").forEach((slot) => {
      const entry = byId.get(slot.dataset.iamaiStoreCard);
      slot.innerHTML = entry ? renderCard(entry) : `<div class="iamai-store__empty">${escapeHtml(t("notFound"))}</div>`;
    });
  }

  function buildSubmissionForm(repoConfigured) {
    return `
      <button type="button" class="iamai-store-submit__open" data-store-submit-open>${escapeHtml(t("submitOpen"))}</button>
      <dialog class="iamai-store-submit__dialog" data-store-submit-dialog>
      <form class="iamai-store-submit__form" method="dialog">
        <div class="iamai-store-submit__dialog-header">
          <div>
            <h3>${escapeHtml(t("submitTitle"))}</h3>
            <p>${escapeHtml(t("submitSubtitle"))}</p>
          </div>
          <button type="button" class="iamai-store-submit__close" data-store-submit-close aria-label="${escapeAttr(t("closeSubmit"))}">&times;</button>
        </div>
        <div class="iamai-store-submit__body">
          <div class="iamai-store-submit__fields">
            <div class="iamai-store-submit__grid iamai-store-submit__grid--compact">
              ${selectField("type", t("type"), STORE_TYPES)}
              ${field("id", t("entryId"), { required: true, placeholder: "plugin.echo" })}
              ${field("name", t("displayName"), { required: true, placeholder: "Echo Plugin" })}
              ${field("license", t("license"), { required: true, value: "MIT" })}
            </div>
            ${textarea("summary", t("summary"), {
      required: true,
      placeholder: t("summaryPlaceholder"),
      help: t("summaryHelp"),
    })}
            <div class="iamai-store-submit__grid">
              ${field("package", t("package"), { placeholder: "iamai-plugin-echo" })}
              ${field("repository", t("repository"), { placeholder: "https://github.com/you/iamai-plugin-echo" })}
              ${field("iamai_requires", t("iamaiRequires"), {
      placeholder: "iamai>=0.4,<0.5",
      help: t("iamaiRequiresHelp"),
    })}
              ${field("source_url", t("sourceUrl"), { placeholder: "https://github.com/you/iamai-plugin-echo" })}
              ${field("docs_url", t("docsUrl"), { placeholder: "https://example.com/docs" })}
              ${field("homepage_url", t("homepageUrl"), { placeholder: "https://example.com" })}
            </div>
            <div class="iamai-store-submit__grid">
              ${textarea("tags", t("tags"), { placeholder: "echo, demo, commands" })}
              ${textarea("platforms", t("platforms"), { placeholder: "terminal, onebot11" })}
              ${textarea("requires", t("requires"), { placeholder: "plugin.auth, state_backend.sqlite" })}
              ${textarea("runtime_capabilities", t("runtimeCapabilities"), {
      placeholder: "network:http, storage:sqlite, agent:tool, approval:required",
    })}
              ${textarea("entry_points", t("entryPoints"), {
      placeholder: "plugin:echo=iamai_plugin_echo:EchoPlugin\nadapter:acme=iamai_adapter_acme:AcmeAdapter",
      help: t("entryPointsHelp"),
    })}
              ${textarea("conformance_evidence", t("conformanceEvidence"), {
      placeholder: "https://github.com/you/project/actions/runs/123",
      help: t("conformanceEvidenceHelp"),
    })}
            </div>
            ${textarea("config_example", t("configExample"), { placeholder: "[plugin.echo]\nenabled = true" })}
            ${textarea("security_notes", t("securityStatement"), { placeholder: "Network access, credentials, dangerous actions, optional dependencies, or review notes." })}
            ${textarea("permission_notes", t("permissionNotes"), { placeholder: "Agent tool permission name, input schema, audit fields, and approval requirement." })}
            <label class="iamai-store-submit__check">
              <input name="confirm" type="checkbox" required>
              <span>${escapeHtml(t("confirm"))}</span>
            </label>
            <div class="iamai-store-submit__actions">
              <button type="submit"${repoConfigured ? "" : " disabled"}>${escapeHtml(t("openIssue"))}</button>
              <button type="button" data-store-direct-submit hidden>${escapeHtml(t("submitDirect"))}</button>
            </div>
            <div class="iamai-store-submit__status" data-store-submit-status>
              ${repoConfigured ? "" : escapeHtml(t("configureRepo"))}
            </div>
          </div>
          <aside class="iamai-store-submit__preview">
            <div class="iamai-store-submit__preview-title">${escapeHtml(t("previewTitle"))}</div>
            <pre><code data-store-submit-preview>{}</code></pre>
          </aside>
        </div>
      </form>
      </dialog>
    `;
  }

  function readSubmission(form) {
    const data = new FormData(form);
    return removeEmpty({
      id: data.get("id"),
      name: data.get("name"),
      type: data.get("type"),
      summary: data.get("summary"),
      package: data.get("package"),
      repository: data.get("repository"),
      license: data.get("license"),
      status: "active",
      verification: ["community"],
      entry_points: parseEntryPoints(data.get("entry_points")),
      tags: splitList(data.get("tags")),
      platforms: splitList(data.get("platforms")),
      requires: splitList(data.get("requires")),
      iamai_requires: data.get("iamai_requires"),
      conformance_evidence: splitLines(data.get("conformance_evidence")),
      runtime_capabilities: splitList(data.get("runtime_capabilities")),
      docs_url: data.get("docs_url"),
      source_url: data.get("source_url"),
      homepage_url: data.get("homepage_url"),
      config_example: data.get("config_example"),
      security_notes: data.get("security_notes"),
      permission_notes: data.get("permission_notes"),
    });
  }

  function validateSubmission(entry) {
    const errors = [];
    if (!/^[a-z0-9][a-z0-9_.-]*$/.test(entry.id || "")) {
      errors.push(t("invalidId"));
    }
    if (!entry.name) {
      errors.push(t("nameRequired"));
    }
    if (!entry.summary || entry.summary.length > 180) {
      errors.push(t("summaryRequired"));
    }
    if (!entry.package && !entry.repository) {
      errors.push(t("packageOrRepoRequired"));
    }
    if (["plugin", "adapter"].includes(entry.type) && !entry.iamai_requires) {
      errors.push(t("iamaiRequiresRequired"));
    }
    if (["plugin", "adapter"].includes(entry.type) && !(entry.conformance_evidence || []).length) {
      errors.push(t("conformanceEvidenceRequired"));
    }
    if (["plugin", "adapter", "agent_tool"].includes(entry.type) && !entry.security_notes) {
      errors.push(t("securityRequired"));
    }
    if (entry.type === "agent_tool" && !entry.permission_notes) {
      errors.push(t("permissionRequired"));
    }
    ["repository", "source_url", "docs_url", "homepage_url"].forEach((key) => {
      if (entry[key] && !/^https?:\/\/[^/]+\S*$/.test(entry[key])) {
        errors.push(`${key} ${t("absoluteUrlRequired")}`);
      }
    });
    (entry.conformance_evidence || []).forEach((url) => {
      if (!isPublicHttpUrl(url)) {
        errors.push(`conformance_evidence ${t("absoluteUrlRequired")}`);
      }
    });
    return errors;
  }

  function buildIssueBody(entry) {
    return [
      "## Ecosystem submission",
      "",
      "Please review this iamai ecosystem entry.",
      "",
      "```json",
      JSON.stringify(entry, null, 2),
      "```",
      "",
      "## Review checklist",
      "",
      "- [ ] Package or repository is reachable.",
      "- [ ] Entry points match published package metadata when applicable.",
      "- [ ] iamai_requires matches the package's published Requires-Dist metadata.",
      "- [ ] Conformance evidence is public and reproducible when required.",
      "- [ ] No secrets, private endpoints, or unsafe install steps are included.",
      "- [ ] Verification badges are assigned by maintainers only.",
    ].join("\n");
  }

  function buildIssueUrl(container, entry) {
    const repo = container.dataset.githubRepo;
    const template = container.dataset.issueTemplate || "ecosystem-submission.yml";
    const requiresConformance = ["plugin", "adapter"].includes(entry.type);
    const notApplicable = "Not applicable";
    const params = new URLSearchParams({
      template,
      title: `[Ecosystem] ${entry.name}`,
      extension_type: entry.type || "",
      entry_id: entry.id || "",
      display_name: entry.name || "",
      summary: entry.summary || "",
      package_name: entry.package || "",
      repository_url: entry.repository || "",
      iamai_requires: entry.iamai_requires || (requiresConformance ? "" : notApplicable),
      conformance_evidence: (entry.conformance_evidence || []).join("\n") ||
        (requiresConformance ? "" : notApplicable),
      runtime_capabilities: (entry.runtime_capabilities || []).join(", "),
      security_notes: entry.security_notes || "",
      permission_notes: entry.permission_notes || "",
      registry_json: JSON.stringify(entry, null, 2),
      body: buildIssueBody(entry),
    });
    return `https://github.com/${repo}/issues/new?${params.toString()}`;
  }

  function updateSubmissionPreview(container, form) {
    const entry = readSubmission(form);
    const errors = validateSubmission(entry);
    const preview = container.querySelector("[data-store-submit-preview]");
    const status = container.querySelector("[data-store-submit-status]");
    preview.innerHTML = highlightJson(JSON.stringify(entry, null, 2));
    status.textContent = errors.join(" ");
    status.classList.toggle("iamai-store-submit__status--error", errors.length > 0);
    return { entry, errors };
  }

  async function submitDirect(container, entry, status) {
    const url = container.dataset.submitApiUrl;
    if (!url) {
      return;
    }
    status.textContent = t("submitting");
    const response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ entry }),
    });
    if (!response.ok) {
      throw new Error(`Direct submission failed: ${response.status}`);
    }
    status.textContent = t("submitted");
  }

  function renderSubmissionForm(container) {
    const repoConfigured = Boolean(container.dataset.githubRepo);
    const mount = container.querySelector(".iamai-store-submit__mount");
    if (!mount) {
      return;
    }
    mount.innerHTML = buildSubmissionForm(repoConfigured);
    const form = container.querySelector("form");
    const dialog = container.querySelector("[data-store-submit-dialog]");
    const openButton = container.querySelector("[data-store-submit-open]");
    const closeButton = container.querySelector("[data-store-submit-close]");
    const directButton = container.querySelector("[data-store-direct-submit]");
    if (container.dataset.submitApiUrl) {
      directButton.hidden = false;
    }
    openButton.addEventListener("click", () => {
      if (typeof dialog.showModal === "function") {
        dialog.showModal();
      } else {
        dialog.setAttribute("open", "");
      }
    });
    closeButton.addEventListener("click", () => dialog.close());
    dialog.addEventListener("click", (event) => {
      if (event.target === dialog) {
        dialog.close();
      }
    });
    form.addEventListener("input", () => updateSubmissionPreview(container, form));
    form.addEventListener("submit", (event) => {
      event.preventDefault();
      const status = container.querySelector("[data-store-submit-status]");
      const { entry, errors } = updateSubmissionPreview(container, form);
      if (errors.length) {
        return;
      }
      window.location.href = buildIssueUrl(container, entry);
    });
    directButton.addEventListener("click", async () => {
      const status = container.querySelector("[data-store-submit-status]");
      const { entry, errors } = updateSubmissionPreview(container, form);
      if (errors.length) {
        return;
      }
      try {
        await submitDirect(container, entry, status);
      } catch (error) {
        status.textContent = String(error.message || error);
        status.classList.add("iamai-store-submit__status--error");
      }
    });
    updateSubmissionPreview(container, form);
  }

  async function loadIndex() {
    if (window.iamai_STORE_INDEX) {
      return window.iamai_STORE_INDEX;
    }
    const response = await fetch(INDEX_URL);
    return response.json();
  }

  async function initStore() {
    const stores = Array.from(document.querySelectorAll("[data-iamai-store]"));
    const cards = Array.from(document.querySelectorAll("[data-iamai-store-card]"));
    const submissionForms = Array.from(document.querySelectorAll("[data-iamai-store-submit]"));
    submissionForms.forEach(renderSubmissionForm);
    if (!stores.length && !cards.length) {
      return;
    }
    try {
      const index = await loadIndex();
      const entries = index.entries || [];
      stores.forEach((container) => renderStore(container, entries));
      renderCardSlots(entries);
    } catch (error) {
      stores.forEach((container) => {
        const loading = container.querySelector(".iamai-store__loading");
        if (loading) {
          loading.textContent = t("loadFailed");
        }
      });
      console.error("Failed to load iamai store index", error);
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initStore);
  } else {
    initStore();
  }
})();

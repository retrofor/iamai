(function () {
  const blocks = document.querySelectorAll("pre.mermaid");
  if (!blocks.length) {
    return;
  }

  function initialize() {
    window.mermaid.initialize({
      startOnLoad: false,
      securityLevel: "strict",
      theme: document.documentElement.dataset.theme === "dark" ? "dark" : "default",
      flowchart: {
        htmlLabels: false,
      },
    });
    window.mermaid.run({ nodes: blocks });
  }

  if (window.mermaid) {
    initialize();
    return;
  }

  const script = document.createElement("script");
  script.src = "https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js";
  script.defer = true;
  script.addEventListener("load", initialize);
  document.head.appendChild(script);
})();

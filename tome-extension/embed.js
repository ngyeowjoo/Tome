<!--
  ╔══════════════════════════════════════════════════════════════════╗
  ║  Tome — Floating Side Panel Embed                               ║
  ║  Drop this snippet just before </body> on any internal page.   ║
  ║  Replace TOME_URL with your Streamlit Cloud URL.               ║
  ╚══════════════════════════════════════════════════════════════════╝
-->

<script>
(function () {
  // ── CONFIG ────────────────────────────────────────────────────────
  const TOME_URL = "https://YOUR-APP.streamlit.app"; // 🔁 Replace this
  const PANEL_WIDTH = "420px";
  const TRIGGER_LABEL = "📚 Tome";
  // ─────────────────────────────────────────────────────────────────

  // Don't inject twice
  if (document.getElementById("tome-embed-panel")) return;

  // ── Context extractor (mirrors Chrome extension logic) ────────────
  function extractContext() {
    const title = document.title.replace(/[-|–—].*$/, "").trim();

    const prioritySelectors = [
      "[data-test-id='ticket-subject']", ".ticket-subject",
      "#ticket_description", ".slds-page-header__title",
      ".ticket-title", ".ticket-body", "[data-test='conversation-subject']",
      "article", "main", "[role='main']", ".content", "#content",
    ];

    let text = "";
    for (const sel of prioritySelectors) {
      const el = document.querySelector(sel);
      if (el) {
        text = el.innerText?.trim();
        if (text && text.length > 30) break;
      }
    }

    if (!text || text.length < 30) {
      const els = document.querySelectorAll("h1, h2, p, .subject, .description");
      const parts = [];
      for (const el of els) {
        const t = el.innerText?.trim();
        if (t && t.length > 10 && t.length < 400) parts.push(t);
        if (parts.join(" ").length > 600) break;
      }
      text = parts.join(" ");
    }

    text = text.replace(/\s+/g, " ").trim().slice(0, 500);

    const firstSentence = text.split(/[.!?]/)[0]?.trim() || "";
    const titleOk = title.length > 10 && title.length < 100
      && !/(dashboard|home|inbox|login)/i.test(title);

    return titleOk
      ? `${title} ${firstSentence}`.trim().slice(0, 200)
      : (firstSentence || title).slice(0, 200);
  }

  function buildUrl(query) {
    const base = TOME_URL.replace(/\/$/, "");
    return query ? `${base}?q=${encodeURIComponent(query)}` : base;
  }

  // ── Build panel DOM ────────────────────────────────────────────────
  const style = document.createElement("style");
  style.textContent = `
    #tome-embed-panel {
      position: fixed;
      top: 0;
      right: -${PANEL_WIDTH};
      width: ${PANEL_WIDTH};
      height: 100vh;
      z-index: 2147483647;
      display: flex;
      flex-direction: column;
      background: #FAFAF7;
      box-shadow: -4px 0 24px rgba(0,0,0,0.12);
      transition: right 0.28s cubic-bezier(0.4,0,0.2,1);
      border-left: 1px solid #E0DAD0;
      font-family: system-ui, sans-serif;
    }
    #tome-embed-panel.open { right: 0; }

    #tome-embed-topbar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 12px;
      height: 44px;
      background: #F5F2EB;
      border-bottom: 1px solid #E0DAD0;
      flex-shrink: 0;
    }
    #tome-embed-logo {
      font-family: 'Courier New', monospace;
      font-weight: 700;
      font-size: 0.95rem;
      color: #C4992A;
    }
    .tome-btn {
      background: none;
      border: 1px solid #DDD8CE;
      border-radius: 5px;
      padding: 4px 8px;
      font-size: 0.72rem;
      color: #666;
      cursor: pointer;
      transition: background 0.15s;
    }
    .tome-btn:hover { background: #EDE9E0; }

    #tome-embed-context {
      display: none;
      align-items: center;
      gap: 8px;
      padding: 6px 12px;
      background: #FFF9EC;
      border-bottom: 1px solid #F0E4C0;
      font-size: 0.7rem;
      color: #7A6020;
      flex-shrink: 0;
    }
    #tome-embed-context.show { display: flex; }
    #tome-context-label { flex: 1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

    #tome-embed-frame {
      flex: 1;
      width: 100%;
      border: none;
    }

    #tome-trigger {
      position: fixed;
      bottom: 80px;
      right: 0;
      z-index: 2147483646;
      background: #C4992A;
      color: white;
      border: none;
      border-radius: 8px 0 0 8px;
      padding: 10px 14px;
      font-size: 0.82rem;
      font-weight: 600;
      cursor: pointer;
      box-shadow: -2px 2px 10px rgba(0,0,0,0.15);
      writing-mode: vertical-rl;
      text-orientation: mixed;
      letter-spacing: 0.05em;
      transition: background 0.15s, right 0.28s cubic-bezier(0.4,0,0.2,1);
    }
    #tome-trigger.hidden { right: -60px; }
    #tome-trigger:hover { background: #A87E20; }
  `;
  document.head.appendChild(style);

  // Panel
  const panel = document.createElement("div");
  panel.id = "tome-embed-panel";
  panel.innerHTML = `
    <div id="tome-embed-topbar">
      <span id="tome-embed-logo">📚 Tome</span>
      <div style="display:flex;gap:6px">
        <button class="tome-btn" id="tome-btn-recapture">⊙ Recapture</button>
        <button class="tome-btn" id="tome-btn-close">✕ Close</button>
      </div>
    </div>
    <div id="tome-embed-context">
      <span style="width:7px;height:7px;border-radius:50%;background:#C4992A;flex-shrink:0;"></span>
      <span id="tome-context-label"></span>
      <button class="tome-btn" id="tome-ctx-dismiss" style="border:none;background:none;color:#AAA;font-size:0.9rem;cursor:pointer">✕</button>
    </div>
    <iframe id="tome-embed-frame" allow="clipboard-write"
      sandbox="allow-scripts allow-same-origin allow-forms allow-popups">
    </iframe>
  `;
  document.body.appendChild(panel);

  // Trigger tab
  const trigger = document.createElement("button");
  trigger.id = "tome-trigger";
  trigger.textContent = TRIGGER_LABEL;
  document.body.appendChild(trigger);

  // ── State ─────────────────────────────────────────────────────────
  let isOpen = false;
  let currentQuery = "";

  const frame = document.getElementById("tome-embed-frame");
  const contextBar = document.getElementById("tome-embed-context");
  const contextLabel = document.getElementById("tome-context-label");

  function openPanel() {
    currentQuery = extractContext();
    const url = buildUrl(currentQuery);
    frame.src = url;

    if (currentQuery) {
      contextLabel.textContent = `Auto-captured: "${currentQuery.slice(0, 55)}${currentQuery.length > 55 ? "…" : ""}"`;
      contextBar.classList.add("show");
    }

    panel.classList.add("open");
    trigger.classList.add("hidden");
    isOpen = true;
  }

  function closePanel() {
    panel.classList.remove("open");
    trigger.classList.remove("hidden");
    isOpen = false;
  }

  trigger.addEventListener("click", openPanel);
  document.getElementById("tome-btn-close").addEventListener("click", closePanel);
  document.getElementById("tome-ctx-dismiss").addEventListener("click", () => {
    contextBar.classList.remove("show");
  });
  document.getElementById("tome-btn-recapture").addEventListener("click", () => {
    currentQuery = extractContext();
    if (currentQuery) {
      frame.src = buildUrl(currentQuery);
      contextLabel.textContent = `Auto-captured: "${currentQuery.slice(0, 55)}…"`;
      contextBar.classList.add("show");
    }
  });

  // Close on Escape
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && isOpen) closePanel();
  });

  // SPA navigation — re-capture on route change
  let lastUrl = location.href;
  new MutationObserver(() => {
    if (location.href !== lastUrl) {
      lastUrl = location.href;
      if (isOpen) {
        setTimeout(() => {
          currentQuery = extractContext();
          if (currentQuery) {
            frame.src = buildUrl(currentQuery);
            contextLabel.textContent = `Page changed — "${currentQuery.slice(0, 50)}…"`;
            contextBar.classList.add("show");
          }
        }, 800);
      }
    }
  }).observe(document.body, { subtree: true, childList: true });

})();
</script>

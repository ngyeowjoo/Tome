// content.js — Tome Context Extractor
// Runs on every page. Extracts meaningful text and sends it to the background worker.

(function () {
  // Don't run inside iframes
  if (window !== window.top) return;

  function extractContext() {
    const url = window.location.href;
    const title = document.title;

    // Priority selectors — common CRM/helpdesk patterns first, then fallback
    const prioritySelectors = [
      // Zendesk
      "[data-test-id='ticket-subject']",
      ".ticket-subject",
      "#ticket_description",
      // Salesforce
      ".slds-page-header__title",
      "[data-aura-class='forceRecordLayout']",
      // Freshdesk
      ".ticket-title",
      ".ticket-body",
      // Intercom
      "[data-test='conversation-subject']",
      // HubSpot
      ".ticket-header",
      // Generic meaningful containers
      "article",
      "main",
      "[role='main']",
      ".content",
      "#content",
      ".ticket",
      ".case",
      ".conversation",
      ".email-body",
      ".message-body",
    ];

    let extractedText = "";

    // Try priority selectors first
    for (const selector of prioritySelectors) {
      const el = document.querySelector(selector);
      if (el) {
        extractedText = el.innerText?.trim();
        if (extractedText && extractedText.length > 30) break;
      }
    }

    // Fallback: grab all visible paragraph/heading text from body
    if (!extractedText || extractedText.length < 30) {
      const elements = document.querySelectorAll("h1, h2, h3, p, li, td, .subject, .description");
      const lines = [];
      for (const el of elements) {
        const text = el.innerText?.trim();
        if (text && text.length > 10 && text.length < 500) {
          lines.push(text);
        }
        if (lines.join(" ").length > 800) break;
      }
      extractedText = lines.join(" ");
    }

    // Clean up whitespace
    extractedText = extractedText
      .replace(/\s+/g, " ")
      .replace(/\n+/g, " ")
      .trim()
      .slice(0, 600); // Cap at 600 chars for URL safety

    // Build a search-friendly query from the context
    const query = buildQuery(extractedText, title, url);

    return { query, url, title, rawText: extractedText };
  }

  function buildQuery(text, title, url) {
    // Use page title as primary signal if it's meaningful
    const cleanTitle = title
      .replace(/[-|–—].*$/, "") // strip site name suffix
      .replace(/\s+/g, " ")
      .trim();

    // If title looks like a ticket/issue/query, use it directly
    const titleIsQuery =
      cleanTitle.length > 10 &&
      cleanTitle.length < 120 &&
      !cleanTitle.toLowerCase().includes("dashboard") &&
      !cleanTitle.toLowerCase().includes("home") &&
      !cleanTitle.toLowerCase().includes("inbox");

    if (titleIsQuery && text.length < 50) {
      return cleanTitle;
    }

    // Otherwise combine title + first meaningful sentence from text
    const firstSentence = text.split(/[.!?]/)[0]?.trim() || "";
    const combined = titleIsQuery
      ? `${cleanTitle} ${firstSentence}`.trim()
      : firstSentence || cleanTitle;

    return combined.slice(0, 200);
  }

  // Run extraction and send to background
  function sendContext() {
    try {
      const context = extractContext();
      if (context.query) {
        chrome.runtime.sendMessage({ type: "PAGE_CONTEXT", ...context });
      }
    } catch (e) {
      // Silently fail — content scripts can be blocked on some pages
    }
  }

  // Run on load
  sendContext();

  // Re-run on SPA navigation (for tools like Salesforce, Zendesk that use pushState)
  let lastUrl = location.href;
  const observer = new MutationObserver(() => {
    if (location.href !== lastUrl) {
      lastUrl = location.href;
      setTimeout(sendContext, 800); // slight delay for SPA content to render
    }
  });
  observer.observe(document.body, { subtree: true, childList: true });
})();

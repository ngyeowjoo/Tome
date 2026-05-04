// background.js — Tome Chrome Extension Service Worker

const TOME_URL = "https://YOUR-APP.streamlit.app"; // 🔁 Replace with your Streamlit Cloud URL

// Open side panel when toolbar icon is clicked
chrome.action.onClicked.addListener((tab) => {
  chrome.sidePanel.open({ tabId: tab.id });
});

// Enable side panel for all URLs
chrome.runtime.onInstalled.addListener(() => {
  chrome.sidePanel.setPanelBehavior({ openPanelOnActionClick: true });
});

// Listen for context messages from content.js
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === "PAGE_CONTEXT") {
    // Store the extracted context so panel.html can read it
    chrome.storage.session.set({
      pageContext: {
        query: message.query,
        url: message.url,
        title: message.title,
        timestamp: Date.now(),
      }
    });
    sendResponse({ ok: true });
  }

  if (message.type === "GET_TOME_URL") {
    sendResponse({ url: TOME_URL });
  }
});

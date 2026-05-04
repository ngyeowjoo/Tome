# 📚 Tome — Chrome Extension & Embed Panel

Gives call center agents instant access to Tome from any webpage.
Auto-captures page context (ticket text, subject line, CRM content) to pre-fill the search query.

---

## 🗂 Files

```
tome-extension/
  manifest.json     Chrome extension config
  background.js     Service worker — opens side panel, stores context
  content.js        Runs on every page — extracts context
  panel.html        Side panel UI — loads Tome in an iframe
  embed.js          Drop-in snippet for your own internal website
```

---

## 🔁 Step 1 — Set your Streamlit URL

Open `background.js` and replace the placeholder:

```js
const TOME_URL = "https://YOUR-APP.streamlit.app";
```

Do the same in `embed.js`:

```js
const TOME_URL = "https://YOUR-APP.streamlit.app";
```

---

## 🧩 Chrome Extension Setup

### Install (Developer Mode)

1. Open Chrome → go to `chrome://extensions`
2. Enable **Developer mode** (top right toggle)
3. Click **Load unpacked**
4. Select the `tome-extension/` folder
5. The Tome icon appears in your toolbar

### Usage

- Click the **📚 toolbar icon** → Tome opens as a side panel
- As you navigate pages, Tome auto-captures context and pre-fills search
- Click **⊙ Capture** in the panel to manually re-capture the current page
- Click **↗ Expand** to open Tome in a full tab

### Icons

The extension expects icon files at:
```
tome-extension/icons/icon16.png
tome-extension/icons/icon48.png
tome-extension/icons/icon128.png
```
Add your own icons, or use any 16×16, 48×48, 128×128 PNG files.
If you skip this, Chrome will show a default icon — the extension still works.

---

## 🌐 Embed on Your Internal Website

Drop this single line just before `</body>` on any internal page:

```html
<script src="/path/to/embed.js"></script>
```

Or paste the contents of `embed.js` directly into a `<script>` tag.

### What it adds

- A **"📚 Tome" tab** fixed to the right edge of the screen
- Click it → a slide-in panel opens with Tome pre-loaded
- Context is auto-captured from the current page on open
- Click **⊙ Recapture** to refresh context after page changes
- Press **Escape** to close

### Works with SPAs (Zendesk, Salesforce, Freshdesk, etc.)

The embed watches for URL changes and re-captures context automatically
when agents navigate between tickets/records.

---

## ⚠️ Iframe Embedding Requirement

Streamlit blocks iframes by default. The `config.toml` in the Tome app
already includes the necessary settings:

```toml
[server]
enableCORS = false
enableXsrfProtection = false
```

These are set in `tome/.streamlit/config.toml` — no extra steps needed.

> **Note:** For production, consider self-hosting Tome (Railway, Render, or VPS)
> for full control over CORS and security headers.

---

## 🔍 How Context Extraction Works

1. **Content script** (`content.js`) runs on every page after load
2. It scans for CRM-specific selectors first (Zendesk ticket subject, Salesforce header, etc.)
3. Falls back to headings and paragraph text if no specific selector matches
4. Extracts up to 600 characters, builds a clean search query
5. Passes it to the side panel via `chrome.storage.session`
6. Panel appends `?q=<query>` to the Tome URL — Streamlit reads it and pre-fills search

---

## 🛠 Supported CRM Selectors (auto-detected)

| Platform    | Elements targeted                              |
|-------------|------------------------------------------------|
| Zendesk     | Ticket subject, description                   |
| Salesforce  | Page header title, record layout              |
| Freshdesk   | Ticket title, body                            |
| Intercom    | Conversation subject                          |
| HubSpot     | Ticket header                                 |
| Generic     | `<article>`, `<main>`, `.content`, `.ticket`  |

To add support for another tool, add its CSS selectors to the
`prioritySelectors` array in `content.js` and `embed.js`.

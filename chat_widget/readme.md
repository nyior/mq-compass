# chat_widget

A minimal browser chat widget demo for a Retrieval-Augmented Generation (RAG) API.

## Files

- `index.html` – chat widget UI shell
- `styles.css` – small custom styles + loading animation
- `app.js` – message handling + API calls + rendering answer/sources

## Run locally

You can serve this folder with any static file server.

### Option 1: Python (no dependencies)

```bash
cd chat_widget
python3 -m http.server 8301
```

Open: `http://127.0.0.1:8301`

### Option 2: Node (already included in this folder)

```bash
cd chat_widget
npm run dev
```

Open: `http://127.0.0.1:8301`

## Configure backend API URL

Edit this constant in `app.js`:

```js
const API_BASE_URL = "http://127.0.0.1:8203";
```

If your retrieval backend runs somewhere else, update the URL and refresh the page.

## Backend contract expected by the widget

- `POST /ask`
- request JSON:

```json
{ "question": "Why are messages piling up?" }
```

- response JSON:

```json
{
  "answer": "I am not sure based on available docs.",
  "sources": [
    {
      "title": "Delayed message exchange - LavinMQ",
      "url": "https://lavinmq.com/documentation/delayed-message",
      "source_type": "docs",
      "section": null
    }
  ]
}
```

## Notes

- Chat history is in-memory only (current page session).
- Refreshing the page clears all messages.

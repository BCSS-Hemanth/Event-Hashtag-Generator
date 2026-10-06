# Event Keyword & Hashtag Search — API Documentation

**Base URL:** `http://127.0.0.1:8000`

**Interactive docs (OpenAPI / Swagger):** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)  
**OpenAPI schema:** [http://127.0.0.1:8000/openapi.json](http://127.0.0.1:8000/openapi.json)

Content type for JSON endpoints: `application/json`

---

## Overview

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Serves the web UI |
| `GET` | `/health` | Health / liveness check |
| `GET` | `/static/*` | Static frontend assets (CSS, JS) |
| `POST` | `/generate` | Generate hashtags and keywords |
| `POST` | `/event-hashtags` | Generate event hashtags (dedicated API) |
| `POST` | `/create-event` | Reset state and clear Wigolo search cache |

---

## `GET /`

Serves the single-page web interface (`index.html`).

**Response:** HTML page (or JSON message if the static UI is missing)

---

## `GET /health`

Liveness check for the API process (use this for load balancers / nginx / monitors).

### Example request

```bash
curl -s http://127.0.0.1:8000/health
```

### Success response — `200 OK`

```json
{
  "status": "ok",
  "service": "event-keyword-hashtag-search",
  "version": "1.0.0"
}
```

---

## `POST /generate`

Generates event-related **hashtags** and **keywords** by:

1. Building a search query from event, location, and description  
2. Retrieving web results via Wigolo  
3. Extracting hashtags/keywords with deterministic text processing (no LLM)

Supports two modes:

- **JSON** (default) — returns a single JSON body  
- **SSE** — streams status updates, then the final result (when `Accept: text/event-stream`)

### Request body

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `event` | string | yes | — | Event name or topic |
| `location` | string | yes | — | Event location |
| `description` | string | yes | — | Event description |
| `include_social` | boolean | no | `false` | Also search Reddit, YouTube, X |
| `search_engine` | string | no | `"all"` | `all`, `bing`, `duckduckgo`, `wikipedia`, `marginalia` |
| `max_keywords` | integer \| null | no | `null` | Cap keyword count (`null` = all) |
| `max_hashtags` | integer \| null | no | `null` | Cap hashtag count (`null` = all) |

### Example request (JSON)

```bash
curl -s -X POST http://127.0.0.1:8000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "event": "Technology Conference",
    "location": "Hyderabad",
    "description": "AI and cloud computing conference in Hyderabad.",
    "include_social": false,
    "search_engine": "all"
  }'
```

### Success response — `200 OK`

```json
{
  "hashtags": ["#TechnologyConference", "#Hyderabad", "#ArtificialIntelligence"],
  "keywords": ["technology conference hyderabad", "cloud computing", "AI"],
  "sources": [
    {
      "title": "IT Conferences in Hyderabad",
      "url": "https://example.com/article",
      "snippet": "Short excerpt from the page...",
      "engine": ""
    }
  ],
  "engines_used": ["Bing", "DuckDuckGo", "Wikipedia"],
  "primary_engine": ""
}
```

| Field | Type | Description |
|-------|------|-------------|
| `hashtags` | string[] | CamelCase tags starting with `#` (listed first) |
| `keywords` | string[] | Plain-text topic phrases (listed second) |
| `sources` | object[] | Web results used for extraction |
| `sources[].title` | string | Result title |
| `sources[].url` | string | Result URL |
| `sources[].snippet` | string | Short excerpt |
| `sources[].engine` | string | Engine label when available |
| `engines_used` | string[] | Search engines that ran |
| `primary_engine` | string | Reserved; often empty |

### SSE streaming mode

Send header `Accept: text/event-stream`.

```bash
curl -N -X POST http://127.0.0.1:8000/generate \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{
    "event": "Music Festival",
    "location": "Mumbai",
    "description": "Live music festival in Mumbai."
  }'
```

Each SSE `data:` payload is JSON with a `type` field:

**Status update**

```json
{ "type": "status", "message": "Searching DuckDuckGo..." }
```

**Final result**

```json
{
  "type": "result",
  "hashtags": ["#MusicFestival", "#Mumbai"],
  "keywords": ["music festival mumbai"],
  "sources": [],
  "engines_used": ["DuckDuckGo", "Bing"]
}
```

**Error**

```json
{ "type": "error", "detail": "Please enter an event." }
```

### Error responses

| Status | When |
|--------|------|
| `400` | Missing or blank `event`, `location`, or `description` |
| `502` | Wigolo web search failed |
| `500` | Text processing failed |

Example:

```json
{ "detail": "Please enter an event." }
```

Combined missing fields:

```json
{ "detail": "Please enter an event and a location." }
```

---

## `POST /event-hashtags`

Dedicated event-hashtag API. Same request body as `POST /generate`, but the response contains **only hashtags**.

### Example request

```bash
curl -s -X POST http://127.0.0.1:8000/event-hashtags \
  -H "Content-Type: application/json" \
  -d '{
    "event": "Technology Conference",
    "location": "Hyderabad",
    "description": "AI conference"
  }'
```

### Success response — `200 OK`

```json
{
  "hashtags": ["#TechnologyConference", "#Hyderabad", "#ArtificialIntelligence"]
}
```

Validation and error codes match `POST /generate` (`400`, `502`, `500`).

---

## `POST /create-event`

Resets server-side event state and clears Wigolo’s search/content cache.

No request body.

### Example request

```bash
curl -s -X POST http://127.0.0.1:8000/create-event
```

### Success response — `200 OK`

```json
{
  "success": true,
  "message": "New event created and Wigolo cache cleared (8 entries removed)."
}
```

| Field | Type | Description |
|-------|------|-------------|
| `success` | boolean | `true` when cache clear succeeds |
| `message` | string | Human-readable status |

### Error responses

| Status | When |
|--------|------|
| `500` | Wigolo cache clear failed |

```json
{ "detail": "Failed to clear Wigolo cache: ..." }
```

---

## Validation rules (`/generate`)

All of `event`, `location`, and `description` must be non-empty after trimming whitespace.

| Missing field(s) | Message |
|------------------|---------|
| event only | `Please enter an event.` |
| location only | `Please enter a location.` |
| description only | `Please enter a description.` |
| two fields | `Please enter {a} and {b}.` |
| all three | `Please enter an event, location, and description.` |

---

## Running the server

```bash
source .venv/bin/activate
keyword-generator-main
```

Server listens on `http://127.0.0.1:8000` with auto-reload enabled.

---

## Notes

- Hashtags are always returned **before** keywords in the response model.
- Extraction is deterministic Python processing over search snippets — not LLM-generated text.
- Generate calls can take ~20–90 seconds depending on search engines and network.
- CORS is enabled for all origins (`*`) for local development.

# Deploy — Event Keyword & Hashtag Generator

Nginx fronts the FastAPI app on **port 2001** (no Docker).

## Start

```bash
# requires nginx: brew install nginx
cd deploy
chmod +x start.sh
./start.sh
```

Then open:

- App: http://127.0.0.1:2001  
- Health: http://127.0.0.1:2001/health  
- API docs: http://127.0.0.1:2001/docs  

Stop with `Ctrl+C`.

## Architecture

```
Browser → nginx (:2001) → uvicorn / FastAPI (:8000)
```

| File | Purpose |
|------|---------|
| `nginx/nginx.conf` | nginx listen 2001 → proxy to `127.0.0.1:8000` |
| `start.sh` | Starts uvicorn (if needed) + nginx |

Requires project `.venv` with dependencies installed.

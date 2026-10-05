"""
FastAPI Application for Event Keyword & Hashtag Search System.

Endpoints:
- POST /generate: Validates Event, Location, Description; searches web via Wigolo;
  extracts hashtags and keywords using deterministic Python processing.
- POST /create-event: Clears Wigolo's search cache and resets server-side state.
- GET /: Serves the frontend web interface.
"""

import asyncio
import json
import logging
import os
import re
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from keyword_generator_main.text_processor import process_content
from keyword_generator_main.wigolo_client import clear_cache, search_web

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("event_keyword_search")

app = FastAPI(
    title="Event Keyword & Hashtag Search System",
    description="Web retrieval via Wigolo and deterministic Python keyword/hashtag processing.",
    version="1.0.0",
)

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files directory
STATIC_DIR = Path(__file__).parent / "static"


class GenerateRequest(BaseModel):
    event: str = Field(..., description="Name or topic of the event")
    location: str = Field(..., description="Location of the event")
    description: str = Field(..., description="Detailed description of the event")
    include_social: bool = Field(False, description="Whether to include public social discussions from Reddit, YouTube, X")
    search_engine: Optional[str] = Field("all", description="Search engine to query: all, bing, duckduckgo, wikipedia, marginalia")
    max_keywords: Optional[int] = Field(None, description="Optional cap on keywords (None = provide all)")
    max_hashtags: Optional[int] = Field(None, description="Optional cap on hashtags (None = provide all)")


class SearchSource(BaseModel):
    title: str
    url: str
    snippet: str = ""
    engine: str = ""


class GenerateResponse(BaseModel):
    # IMPORTANT: Hashtags must appear first, Keywords second
    hashtags: List[str]
    keywords: List[str]
    sources: List[SearchSource] = []
    engines_used: List[str] = []
    primary_engine: str = ""


class CreateEventResponse(BaseModel):
    success: bool
    message: str


def build_search_query(event: str, location: str, description: str) -> str:
    """
    Construct a focused search query combining Event, Location, and Description.
    Strips conversational question phrases and noise words to help the search engine
    retrieve high-quality, relevant web articles.
    """
    clean_event = event.strip()
    clean_location = re.sub(r"[,;/|]+", " ", location).strip()
    clean_location = re.sub(r"\s+", " ", clean_location)
    clean_desc = description.strip()

    # Remove common conversational filler patterns
    conversational_patterns = [
        r"like\s+what\s+(?:they\s+are|they're)\s+doing",
        r"why\s+(?:they\s+are|are|they're)\s+doing\s+it",
        r"what\s+(?:they\s+are|are\s+they)\s+doing",
        r"information\s+and\s+public\s+discussions\s+related\s+to",
        r"tell\s+me\s+about",
        r"what\s+is\s+happening",
        r"what\s+are\s+the",
    ]
    cleaned_desc = clean_desc
    for pat in conversational_patterns:
        cleaned_desc = re.sub(pat, " ", cleaned_desc, flags=re.IGNORECASE)

    # Extract meaningful keywords from the description (skipping filler words)
    filler_words = {
        "like", "what", "they", "are", "doing", "why", "their", "them", "and",
        "the", "for", "with", "from", "about", "into", "this", "that", "there"
    }
    desc_words = [
        w for w in re.findall(r"[A-Za-z0-9]+", cleaned_desc)
        if w.lower() not in filler_words and len(w) > 2
    ]
    meaningful_desc = " ".join(desc_words[:8])

    # Combine Event + Location + meaningful Description terms
    parts = [clean_event, clean_location]
    if meaningful_desc:
        parts.append(meaningful_desc)

    return " ".join(parts).strip()


async def run_generation_pipeline(
    req: GenerateRequest,
    on_status: Optional[Callable[[str], None]] = None,
) -> GenerateResponse:
    """
    Core pipeline to validate input, perform Wigolo search, and deterministically
    process results into hashtags and keywords.
    """
    event = req.event.strip() if req.event else ""
    location = req.location.strip() if req.location else ""
    description = req.description.strip() if req.description else ""

    missing = []
    if not event:
        missing.append("an event")
    if not location:
        missing.append("a location")
    if not description:
        missing.append("a description")

    if missing:
        if len(missing) == 1:
            msg = f"Please enter {missing[0]}."
        elif len(missing) == 2:
            msg = f"Please enter {missing[0]} and {missing[1]}."
        else:
            msg = "Please enter an event, location, and description."
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)

    # 1. Construct search query using Event + Location + Description
    search_query = build_search_query(event, location, description)
    logger.info("Initiating Wigolo search for query: '%s'", search_query)

    search_engines_used: List[str] = []
    name_map = {
        "duckduckgo": "DuckDuckGo",
        "bing": "Bing",
        "marginalia": "Marginalia",
        "wikipedia": "Wikipedia",
        "brave": "Brave",
        "google": "Google",
        "reddit": "Reddit",
        "youtube": "YouTube",
        "x": "X",
    }

    engine_choice = (req.search_engine or "all").strip().lower()
    engines_arg = engine_choice if engine_choice not in ("all", "") else None

    # Status callback wrapper
    def status_tracker(status_msg: str):
        if on_status:
            try:
                on_status(status_msg)
            except Exception:
                pass

    # 2. Retrieve web content using Wigolo search
    try:
        search_data = await search_web(
            search_query,
            max_results=5,
            engines=engines_arg,
            on_engine_status=status_tracker,
        )
        search_results = search_data.get("results", [])
        for eng in search_data.get("engines_used", []):
            formatted_eng = name_map.get(str(eng).lower(), str(eng).title())
            if formatted_eng not in search_engines_used:
                search_engines_used.append(formatted_eng)

        # If user enabled social platform discussions, query public social domains
        if req.include_social:
            social_query = f"{search_query} (site:reddit.com OR site:youtube.com OR site:x.com OR site:twitter.com)"
            logger.info("Initiating Wigolo social search: '%s'", social_query)
            try:
                social_data = await search_web(
                    social_query,
                    max_results=4,
                    engines=engines_arg,
                    on_engine_status=status_tracker,
                )
                social_results = social_data.get("results", [])
                for eng in social_data.get("engines_used", []):
                    formatted_eng = name_map.get(str(eng).lower(), str(eng).title())
                    if formatted_eng not in search_engines_used:
                        search_engines_used.append(formatted_eng)
                # Combine results, avoiding duplicate URLs
                seen_urls = {r.get("url") for r in search_results if r.get("url")}
                for s_res in social_results:
                    if s_res.get("url") not in seen_urls:
                        search_results.append(s_res)
                        seen_urls.add(s_res.get("url"))
            except Exception as se:
                logger.warning("Social search query failed: %s (continuing with web results)", se)

        # Ensure search_engines_used includes the requested engine if specified
        if engines_arg and not search_engines_used:
            search_engines_used.append(name_map.get(engines_arg, engines_arg.title()))
        elif not search_engines_used:
            search_engines_used = ["Bing", "DuckDuckGo", "Wikipedia"]

    except Exception as e:
        logger.error("Wigolo web search failed: %s", e, exc_info=True)
        err_msg = str(e).strip() or repr(e)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Wigolo search retrieval encountered an error: {err_msg}",
        )

    # 3. Process search results using deterministic Python text processing
    if on_status:
        try:
            on_status("Processing results...")
        except Exception:
            pass

    try:
        processed = process_content(
            event=event,
            location=location,
            description=description,
            search_results=search_results,
            max_keywords=req.max_keywords,
            max_hashtags=req.max_hashtags,
        )
    except Exception as e:
        logger.error("Text processing failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Deterministic text processing error: {e}",
        )

    if on_status:
        try:
            on_status("Generating keywords and hashtags...")
        except Exception:
            pass

    # Return response: Hashtags appear first, Keywords appear second
    sources = [
        SearchSource(
            title=res.get("title", "Web Result"),
            url=res.get("url", ""),
            snippet=res.get("snippet", ""),
        )
        for res in search_results
        if res.get("url")
    ]

    return GenerateResponse(
        hashtags=processed["hashtags"],
        keywords=processed["keywords"],
        sources=sources,
        engines_used=search_engines_used,
    )


async def event_generator(req: GenerateRequest):
    """
    Asynchronous SSE generator that streams search engine detection events in real time,
    followed by the final generated hashtags and keywords.
    """
    loop = asyncio.get_running_loop()
    status_queue: asyncio.Queue = asyncio.Queue()

    def on_status_sync(msg: str):
        loop.call_soon_threadsafe(status_queue.put_nowait, msg)

    task = asyncio.create_task(run_generation_pipeline(req, on_status=on_status_sync))

    last_yield_time = 0.0
    min_display_interval = 0.65  # seconds for user readability

    while not task.done() or not status_queue.empty():
        try:
            status_msg = await asyncio.wait_for(status_queue.get(), timeout=0.15)
            now = asyncio.get_event_loop().time()
            elapsed = now - last_yield_time
            if elapsed < min_display_interval and last_yield_time > 0:
                await asyncio.sleep(min_display_interval - elapsed)

            yield f"data: {json.dumps({'type': 'status', 'message': status_msg})}\n\n"
            last_yield_time = asyncio.get_event_loop().time()
        except asyncio.TimeoutError:
            continue

    try:
        result: GenerateResponse = await task
        # Drain any remaining status messages in queue
        while not status_queue.empty():
            status_msg = status_queue.get_nowait()
            now = asyncio.get_event_loop().time()
            elapsed = now - last_yield_time
            if elapsed < min_display_interval and last_yield_time > 0:
                await asyncio.sleep(min_display_interval - elapsed)
            yield f"data: {json.dumps({'type': 'status', 'message': status_msg})}\n\n"
            last_yield_time = asyncio.get_event_loop().time()

        now = asyncio.get_event_loop().time()
        elapsed = now - last_yield_time
        if elapsed < min_display_interval and last_yield_time > 0:
            await asyncio.sleep(min_display_interval - elapsed)

        result_payload = {
            "type": "result",
            "hashtags": result.hashtags,
            "keywords": result.keywords,
            "sources": [s.model_dump() for s in result.sources],
            "engines_used": result.engines_used,
        }
        yield f"data: {json.dumps(result_payload)}\n\n"
    except HTTPException as he:
        yield f"data: {json.dumps({'type': 'error', 'detail': he.detail})}\n\n"
    except Exception as ex:
        logger.error("SSE pipeline execution failed: %s", ex, exc_info=True)
        yield f"data: {json.dumps({'type': 'error', 'detail': str(ex)})}\n\n"


@app.post("/generate", response_model=GenerateResponse)
async def generate_keywords_and_hashtags(
    req: GenerateRequest,
    request: Request = None,
) -> Any:
    """
    Generate relevant hashtags and keywords for the specified event, location, and description.

    Supports:
    - Real-time Server-Sent Events (SSE) streaming when Accept header includes 'text/event-stream'.
    - Direct JSON GenerateResponse for standard API requests and python test invocations.
    """
    if request is not None and "text/event-stream" in request.headers.get("accept", "").lower():
        return StreamingResponse(
            event_generator(req),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    return await run_generation_pipeline(req)



@app.post("/create-event", response_model=CreateEventResponse)
async def create_new_event() -> CreateEventResponse:
    """
    Reset application state for a new event and clear Wigolo's search/content cache.
    Uses Wigolo's official supported cache clear command:
    wigolo cache clear --url-pattern="*" --json
    """
    logger.info("Executing create-event reset and Wigolo cache clear")
    try:
        res = await clear_cache()
        cleared_count = res.get("cleared", 0)
        return CreateEventResponse(
            success=True,
            message=f"New event created and Wigolo cache cleared ({cleared_count} entries removed).",
        )
    except Exception as e:
        logger.error("Failed to clear Wigolo cache: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear Wigolo cache: {e}",
        )


# Serve frontend static files if directory exists
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
async def root():
    """Serve the single-page application index.html."""
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {"message": "Event Keyword & Hashtag Search API running. Static files not yet created."}

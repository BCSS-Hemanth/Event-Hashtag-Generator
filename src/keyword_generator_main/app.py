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

from keyword_generator_main.text_processor import (
    description_theme_tokens,
    process_content,
)
from keyword_generator_main.translator import (
    detect_language_from_location,
    is_target_script_text,
    resolve_language_selection,
    translate_phrase,
)
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
    languages: Optional[List[str]] = Field(
        None,
        description="Selected language codes (or, ta, te, kn, ml, mr, gu, bn, pa, hi) and/or 'all'",
    )
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
    # Structured event facts (about, leaders, venues, acronyms as [{full, short}], …)
    entities: Optional[Dict[str, Any]] = None
    sources: List[SearchSource] = []
    engines_used: List[str] = []
    primary_engine: str = ""


class CreateEventResponse(BaseModel):
    success: bool
    message: str


def build_search_query(event: str, location: str, description: str) -> str:
    """
    Construct a focused search query combining Event, Location, and Description.
    Prefer user-provided full names / expansions so short forms do not
    retrieve unrelated same-acronym organizations.
    """
    clean_event = event.strip()
    clean_location = re.sub(r"[,;/|]+", " ", location).strip()
    clean_location = re.sub(r"\s+", " ", clean_location)
    clean_desc = description.strip()

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

    filler_words = {
        "like", "what", "they", "are", "doing", "why", "their", "them", "and",
        "the", "for", "with", "from", "about", "into", "this", "that", "there"
    }

    # Prefer quoting a multi-word org/name from description (helps short-form events)
    primary_identity = clean_event
    clauses = [c.strip() for c in re.split(r"[,;]", cleaned_desc) if c.strip()]
    skip = {"of", "and", "the", "for", "in", "at", "a", "an", "on", "to", "by"}
    org_hint = {
        "party", "union", "sangathan", "morcha", "forum", "committee", "front",
        "association", "movement", "alliance", "board", "commission",
    }
    # Only ALL-CAPS tokens count as short forms (not Title Case words)
    event_acro_tokens = {
        t for t in re.findall(r"[A-Za-z]{2,6}", clean_event)
        if t.isupper()
    }
    if clean_event.isupper() and 2 <= len(clean_event) <= 6:
        event_acro_tokens.add(clean_event)

    for clause in clauses:
        words = re.findall(r"[A-Za-z0-9]+", clause)
        meaningful = [w for w in words if w.lower() not in skip]
        if not (2 <= len(meaningful) <= 8):
            continue
        if words and words[0].lower() in skip:
            continue
        initials = "".join(w[0].upper() for w in meaningful if w[0].isalpha())
        has_org_word = any(w.lower() in org_hint for w in meaningful)
        matches_short = initials in event_acro_tokens or any(
            initials.startswith(a) or a.startswith(initials) for a in event_acro_tokens
        )
        if has_org_word or matches_short:
            primary_identity = f"\"{clause.strip()}\""
            break

    desc_words = [
        w for w in re.findall(r"[A-Za-z0-9]+", cleaned_desc)
        if w.lower() not in filler_words and len(w) > 3
    ]
    # Avoid duplicating words already inside the quoted identity
    identity_tokens = {t.lower() for t in re.findall(r"[A-Za-z0-9]+", primary_identity)}
    desc_words = [w for w in desc_words if w.lower() not in identity_tokens]
    meaningful_desc = " ".join(desc_words[:4])

    parts = [primary_identity, clean_event if primary_identity != clean_event else "", clean_location]
    if meaningful_desc:
        parts.append(meaningful_desc)

    return " ".join(p for p in parts if p).strip()


def _description_translation_seed(description: str) -> str:
    """Choose a short description clause that carries distinctive words."""
    glue = {
        "a", "an", "the", "and", "or", "as", "at", "by", "for", "from", "in",
        "of", "on", "to", "with", "over", "about", "after", "before", "their",
        "its", "this", "that", "which", "who", "into", "amid", "under",
    }
    best = ""
    best_score = 0
    for part in re.split(r"[,;|/]+", description or ""):
        candidate = part.strip()
        words = candidate.split()
        if not (2 <= len(words) <= 6):
            continue
        content = [w for w in words if w.lower().strip("().") not in glue and len(w) >= 4]
        if len(content) < 2:
            continue
        score = sum(len(w) for w in content)
        if score > best_score:
            best = candidate
            best_score = score
    return best


def _translation_in_target_script(text: Optional[str], lang_info: Dict[str, Any]) -> Optional[str]:
    """Keep a translation only when it is in the location language's script."""
    if not text or not text.strip():
        return None
    script_range = lang_info.get("range")
    if not script_range or not is_target_script_text(text, tuple(script_range)):
        logger.info(
            "Dropped %s translation outside the %s script: %s",
            lang_info.get("code"),
            lang_info.get("name"),
            text,
        )
        return None
    return text.strip()


def _results_contain_script(
    results: List[Dict[str, Any]],
    script_range: Optional[tuple],
) -> bool:
    """True when any retrieved page text includes characters from the script range."""
    if not results or not script_range:
        return False
    start, end = script_range
    for result in results:
        page_text = " ".join(
            str(result.get(key) or "")
            for key in ("title", "snippet", "content", "markdown")
        )
        if any(start <= ord(ch) <= end for ch in page_text if not ch.isspace()):
            return True
    return False


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

    # Resolve selected languages (UI checklist). Location provides the primary language
    # for defaults and fallback — it does not restrict extraction to that language alone.
    primary_lang = detect_language_from_location(location)
    selected_languages = resolve_language_selection(req.languages)
    if not selected_languages and primary_lang:
        selected_languages = [primary_lang]

    # Ensure the location's primary language is always included and processed first
    # so All/multi-select never drops primary-language terms when others have no content.
    if primary_lang and selected_languages:
        primary_code = primary_lang.get("code")
        without_primary = [
            lang for lang in selected_languages if lang.get("code") != primary_code
        ]
        selected_languages = [primary_lang] + without_primary
    elif primary_lang and not selected_languages:
        selected_languages = [primary_lang]

    regional_languages: List[Dict[str, Any]] = []
    search_language_terms: List[str] = []
    primary_search_terms: List[str] = []
    primary_code = (primary_lang or {}).get("code")

    async def _translate_language_entry(lang_info: Dict[str, Any]) -> Dict[str, Any]:
        """Translate event/location (and a short description seed) for one language."""
        if on_status:
            try:
                on_status(f"Translating event terms to {lang_info['name']}...")
            except Exception:
                pass
        # Yield so SSE can flush the status before network I/O.
        await asyncio.sleep(0)

        translated_event: Optional[str] = None
        translated_location: Optional[str] = None
        translated_seeds: List[str] = []
        desc_seed = _description_translation_seed(description)
        try:
            tasks = [
                asyncio.to_thread(translate_phrase, event, lang_info["code"]),
                asyncio.to_thread(translate_phrase, location, lang_info["code"]),
            ]
            if desc_seed:
                tasks.append(
                    asyncio.to_thread(translate_phrase, desc_seed, lang_info["code"])
                )
            raw_parts = await asyncio.gather(*tasks)
            translated_event = _translation_in_target_script(raw_parts[0], lang_info)
            translated_location = _translation_in_target_script(raw_parts[1], lang_info)
            if desc_seed and len(raw_parts) > 2:
                seed = _translation_in_target_script(raw_parts[2], lang_info)
                if seed:
                    translated_seeds.append(seed)
        except Exception as te:
            logger.warning(
                "Translation for %s (%s) failed: %s",
                lang_info.get("name"),
                lang_info.get("code"),
                te,
            )
        entry = {
            "lang_info": lang_info,
            "translated_event": translated_event,
            "translated_location": translated_location,
            "translated_seeds": translated_seeds,
            "is_primary": bool(primary_code and lang_info.get("code") == primary_code),
        }
        logger.info(
            "Language %s (%s): translated_event=%r translated_location=%r seeds=%r primary=%s",
            lang_info.get("name"),
            lang_info.get("code"),
            translated_event,
            translated_location,
            translated_seeds,
            entry["is_primary"],
        )
        return entry

    # Translate the primary (location) language first so status shows
    # "Translating event terms to Odia..." before search — not buried under All.
    pending_languages: List[Dict[str, Any]] = []
    if selected_languages:
        primary_selected = [
            lang for lang in selected_languages
            if primary_code and lang.get("code") == primary_code
        ]
        if primary_selected:
            pre_search_langs = primary_selected
            pending_languages = [
                lang for lang in selected_languages
                if lang.get("code") != primary_code
            ]
        else:
            # No location primary (or unmatched): translate first selected, rest later.
            pre_search_langs = [selected_languages[0]]
            pending_languages = list(selected_languages[1:])

        for lang_info in pre_search_langs:
            entry = await _translate_language_entry(lang_info)
            regional_languages.append(entry)
            loc_text = str(entry.get("translated_location") or "")
            loc_head = re.split(r"[,;/|]", loc_text)[0].strip()
            expand_terms = [
                entry.get("translated_event"),
                loc_head or None,
            ]
            for term in expand_terms:
                if not term or not str(term).strip():
                    continue
                cleaned = str(term).strip()
                if cleaned not in search_language_terms:
                    search_language_terms.append(cleaned)
                if entry.get("is_primary") and cleaned not in primary_search_terms:
                    primary_search_terms.append(cleaned)

    # 1. Construct search query using Event + Location + Description.
    # When multiple languages are selected, expand the query with the primary
    # language only so other-language gaps do not dilute retrieval.
    search_query = build_search_query(event, location, description)
    query_expand_terms = (
        primary_search_terms
        if len(selected_languages) > 1 and primary_search_terms
        else search_language_terms
    )
    if query_expand_terms:
        # Translations expand retrieval only; keywords/hashtags stay content-backed.
        search_query = f"{search_query} {' '.join(query_expand_terms)}".strip()
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

        # Theme-focused supplemental search from the user's description clauses.
        # Only themes missing from first-pass results are used to widen retrieval.
        theme_tokens = description_theme_tokens(description)
        already_in_query = {
            t.lower()
            for t in re.findall(r"[A-Za-z0-9]+", f"{event} {location}")
            if len(t) > 2
        }
        distinctive = sorted(
            [t for t in theme_tokens if t not in already_in_query and len(t) >= 5],
            key=len,
            reverse=True,
        )[:6]
        if distinctive:
            blob = " ".join(
                str(r.get(k) or "")
                for r in search_results
                for k in ("title", "snippet", "content", "markdown")
            ).lower()
            missing_themes = [t for t in distinctive if t not in blob][:3]
            if missing_themes or not search_results:
                focus = missing_themes or distinctive[:3]
                loc_head = re.split(r"[,;/|]", location)[0].strip()
                theme_query = f"{event} {loc_head} {' '.join(focus)}".strip()
                logger.info("Theme-focused supplemental search: '%s'", theme_query)
                if on_status:
                    try:
                        on_status("Searching description themes...")
                    except Exception:
                        pass
                try:
                    theme_data = await search_web(
                        theme_query,
                        max_results=5,
                        engines=engines_arg,
                        on_engine_status=status_tracker,
                    )
                    seen_urls = {r.get("url") for r in search_results if r.get("url")}
                    for t_res in theme_data.get("results", []):
                        if t_res.get("url") and t_res.get("url") not in seen_urls:
                            search_results.append(t_res)
                            seen_urls.add(t_res.get("url"))
                    for eng in theme_data.get("engines_used", []):
                        formatted_eng = name_map.get(
                            str(eng).lower(), str(eng).title()
                        )
                        if formatted_eng not in search_engines_used:
                            search_engines_used.append(formatted_eng)
                except Exception as te:
                    logger.warning(
                        "Theme-focused search failed: %s (continuing)", te
                    )

        # Primary-language fallback retrieval: when All/multi-select yields no content
        # in the location's primary script, run a focused primary-language search so
        # Odia (etc.) terms are still available instead of empty regional results.
        if primary_lang and primary_search_terms:
            primary_range = primary_lang.get("range")
            if primary_range and not _results_contain_script(
                search_results, tuple(primary_range)
            ):
                base_query = build_search_query(event, location, description)
                primary_query = f"{base_query} {' '.join(primary_search_terms)}".strip()
                if primary_query != search_query:
                    logger.info(
                        "Primary-language fallback search (%s): '%s'",
                        primary_lang.get("name"),
                        primary_query,
                    )
                    if on_status:
                        try:
                            on_status(
                                f"Searching {primary_lang.get('name')} content..."
                            )
                        except Exception:
                            pass
                    try:
                        primary_data = await search_web(
                            primary_query,
                            max_results=5,
                            engines=engines_arg,
                            on_engine_status=status_tracker,
                        )
                        seen_urls = {
                            r.get("url") for r in search_results if r.get("url")
                        }
                        for p_res in primary_data.get("results", []):
                            if p_res.get("url") and p_res.get("url") not in seen_urls:
                                search_results.append(p_res)
                                seen_urls.add(p_res.get("url"))
                        for eng in primary_data.get("engines_used", []):
                            formatted_eng = name_map.get(
                                str(eng).lower(), str(eng).title()
                            )
                            if formatted_eng not in search_engines_used:
                                search_engines_used.append(formatted_eng)
                    except Exception as pe:
                        logger.warning(
                            "Primary-language fallback search failed: %s", pe
                        )

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

    # Translate remaining selected languages after search (All / multi-select).
    # Primary was already translated above so Odia status appears before Bing/etc.
    for lang_info in pending_languages:
        entry = await _translate_language_entry(lang_info)
        regional_languages.append(entry)

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
            regional_languages=regional_languages or None,
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
        entities=processed.get("entities", {}),
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
            "entities": result.entities,
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

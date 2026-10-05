1. Modules & Dependencies Involved
------------------------------------
Python External Packages (in pyproject.toml)

-> fastapi (>=0.142.2): The asynchronous web framework powering the backend REST API endpoints, request validation, and routing.

-> uvicorn (>=0.54.0): The ASGI production web server used to run and serve the FastAPI application.

-> pydantic (included with FastAPI): Data modeling and validation schemas for requests and responses.

External CLI / Tools
---------------------

-> uv: Fast Python package and environment manager (uv.lock, .venv).

-> wigolo CLI (via npx / Node): External search and content retrieval tool used to fetch live web search results and clear search caches.

Standard Library Modules Used
------------------------------

-> asyncio: For non-blocking asynchronous execution of subprocesses and API requests.

-> re: Regular expressions for text cleaning, stripping HTML, and token extraction.

-> collections.Counter: Frequency distribution and n-gram scoring in deterministic text extraction.

-> shutil & sys: Cross-platform path resolution for npx.cmd (Windows) vs npx (POSIX).

-> pathlib.Path: Filesystem path management for static assets.

-> json & logging: Structured CLI output parsing and application logging.


2. What Was Added From the Start (Project Files)
------------------------------------------------

The application was built as a full-stack, modular architecture with zero reliance on LLMs for keyword processing:

keyword_generator_main/
├── pyproject.toml                         # Project metadata, dependencies, script entrypoint
├── test_system.py                         # End-to-end testing script
└── src/
    └── keyword_generator_main/
        ├── __init__.py                    # Main CLI entrypoint (uvicorn launcher)
        ├── app.py                         # FastAPI web server & route handlers
        ├── wigolo_client.py               # Wigolo CLI integration (search & cache clearing)
        ├── text_processor.py              # Pure Python deterministic NLP & keyword engine
        └── static/
            ├── index.html                 # Modern web interface structure
            ├── style.css                  # UI styling (dark/light themes, animations, badges)
            └── app.js                     # Client-side logic, API calls, copy-to-clipboard


Detailed Component Breakdown:
-----------------------------

1. pyproject.toml
- - - - - - - - -

Configured uv_build backend, Python version (>=3.14), dependencies, and added the CLI command keyword-generator-main = "keyword_generator_main:main".


2. __init__.py
 - - - - - - - -

Exposes the main() function that starts Uvicorn pointing to keyword_generator_main.app:app on port 8000 with hot reloading.


3. wigolo_client.py
 - - - - - - - - - -

-> Manages external web retrieval via the Wigolo CLI.
Runs search_web() using asynchronous subprocesses with query formulation and social site filter(reddit.com, x.com, youtube.com).

-> Runs clear_cache() using wigolo cache clear --url-pattern="*" --json.


4. text_processor.py
- - - - - - - - - - -

-> 100% Deterministic Extraction Engine (No LLM required):

-> A curated stopword database filtering conversational filler and web boilerplate.

-> N-gram analysis (unigrams, bigrams, trigrams) with frequency and relevance weightings.

-> Capitalized phrase and entity extraction (locations, organizations, key terminology).

-> Output formatting: #CamelCase hashtags (first) and ranked keyword phrases (second).


5. app.py
- - - - - - 

-> POST /generate: Validates required inputs (event, location, description), invokes wigolo_client,processes retrieved text through text_processor, and formats the response.

-> POST /create-event: Clears server state and triggers cache clearance.

-> GET / & /static: Serves the single-page application and static files.


6. Frontend Suite (static/index.html, static/style.css, static/app.js)
- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

-> Responsive single-page interface.

-> Form with real-time validation and a toggle for public social discussion sources.

-> One-click copy buttons for individual tags or all hashtags/keywords at once.

-> Interactive source links section displaying the web references retrieved.


7. test_system.py
- - - - - - - - -

Test harness verifying validation errors on blank fields, hashtag and keyword generation, and cache clearing.
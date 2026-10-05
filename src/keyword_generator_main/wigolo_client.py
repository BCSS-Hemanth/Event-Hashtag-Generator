"""
Wigolo Client Module

This module provides Python functions to communicate with the Wigolo CLI.
It handles:
1. Web searches using Wigolo's search tool.
2. Clearing Wigolo's search and content cache.
"""

import asyncio
import json
import logging
import os
import shutil
import subprocess
import sys
import threading
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


def _get_npx_command() -> str:
    """Find the proper npx executable on Windows or POSIX."""
    if sys.platform == "win32":
        cmd = shutil.which("npx.cmd") or shutil.which("npx")
        return cmd or "npx.cmd"
    cmd = shutil.which("npx")
    return cmd or "npx"


def _extract_json_from_output(output: str) -> Any:
    """
    Extract the main JSON payload from Wigolo's CLI output.
    Wigolo may emit single-line JSON log messages before or alongside
    the main JSON object or array.
    """
    lines = output.strip().splitlines()
    # Try parsing lines in reverse to find the result object
    for line in reversed(lines):
        line = line.strip()
        if not line:
            continue
        if (line.startswith("{") and line.endswith("}")) or (line.startswith("[") and line.endswith("]")):
            try:
                return json.loads(line)
            except json.JSONDecodeError:
                continue

    # If the output spans multiple lines as a single JSON block:
    # Find the first '{' and matching last '}'
    first_brace = output.find("{")
    last_brace = output.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        candidate = output[first_brace : last_brace + 1]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

    # Fallback to direct json.loads
    return json.loads(output)


def _run_wigolo_subprocess_streaming(
    cmd: List[str],
    on_engine_status: Optional[Callable[[str], None]] = None,
) -> Tuple[int, str, str, Set[str]]:
    """
    Run Wigolo CLI with debug logging enabled and monitor stderr in real-time.
    Whenever Wigolo accesses a specific search source (Bing, DuckDuckGo, Wikipedia, etc.),
    on_engine_status is invoked immediately with 'Searching <Engine>...'.
    """
    env = os.environ.copy()
    env["LOG_LEVEL"] = "debug"

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        bufsize=1,
    )
    detected_engines: Set[str] = set()

    def read_stderr():
        if not proc.stderr:
            return
        for line in proc.stderr:
            line_str = line.strip()
            if not line_str:
                continue
            lower = line_str.lower()
            engine_found = None
            if "scraping bing" in lower or "querying bing" in lower:
                engine_found = "Bing"
            elif "scraping duckduckgo" in lower or "querying duckduckgo" in lower:
                engine_found = "DuckDuckGo"
            elif "querying wikipedia" in lower or "scraping wikipedia" in lower:
                engine_found = "Wikipedia"
            elif "querying marginalia" in lower or "scraping marginalia" in lower:
                engine_found = "Marginalia"
            elif "querying brave" in lower or "scraping brave" in lower:
                engine_found = "Brave"
            elif "querying google" in lower or "scraping google" in lower:
                engine_found = "Google"
            elif "site:reddit.com" in lower or "scraping reddit" in lower or "querying reddit" in lower:
                engine_found = "Reddit"
            elif "site:youtube.com" in lower or "scraping youtube" in lower or "querying youtube" in lower:
                engine_found = "YouTube"
            elif "site:x.com" in lower or "site:twitter.com" in lower or "scraping x" in lower:
                engine_found = "X"

            if engine_found and engine_found not in detected_engines:
                detected_engines.add(engine_found)
                if on_engine_status:
                    try:
                        on_engine_status(f"Searching {engine_found}...")
                    except Exception as err:
                        logger.debug("Error in on_engine_status callback: %s", err)

    t = threading.Thread(target=read_stderr, daemon=True)
    t.start()

    stdout_data = proc.stdout.read() if proc.stdout else ""
    proc.wait()
    t.join()
    return proc.returncode, stdout_data.strip(), "", detected_engines


def _run_wigolo_subprocess(cmd: List[str]) -> Tuple[int, str, str]:
    """Run Wigolo CLI synchronously in a worker thread."""
    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        shell=False,
    )
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


async def search_web(
    query: str,
    max_results: int = 5,
    engines: Optional[str] = None,
    on_engine_status: Optional[Callable[[str], None]] = None,
) -> Dict[str, Any]:
    """
    Search the web using Wigolo's search command.
    Detects the active search source in real-time and invokes on_engine_status.

    Args:
        query: The search query string.
        max_results: Maximum number of search results to return (default 5).
        engines: Optional comma-separated engine overrides.
        on_engine_status: Optional callback receiving 'Searching <Source>...' in real time.

    Returns:
        A dict containing 'results' (list of search result items) and 'engines_used' (list of engines).
    """
    npx_cmd = _get_npx_command()
    cmd = [
        npx_cmd,
        "-y",
        "wigolo",
        "search",
        query,
        f"--max-results={max_results}",
        "--include-content",
        "--include-full-markdown",
        "--json",
    ]

    if engines and engines.strip() and engines.strip().lower() != "all":
        cmd.append(f"--search-engines={engines.strip().lower()}")

    logger.info("Executing Wigolo search: %s (engines=%s)", query, engines or "default")

    # Run Wigolo with real-time stderr stream monitoring
    returncode, stdout_text, stderr_text, detected_engines = await asyncio.to_thread(
        _run_wigolo_subprocess_streaming, cmd, on_engine_status
    )

    if returncode != 0:
        logger.error("Wigolo search failed with code %d: %s", returncode, stderr_text)
        raise RuntimeError(f"Wigolo search failed (code {returncode}): {stderr_text or stdout_text}")

    if not stdout_text:
        return {"results": [], "engines_used": list(detected_engines)}

    try:
        data = _extract_json_from_output(stdout_text)
        if isinstance(data, dict):
            results = data.get("results", [])
            engines_used_list: List[str] = []
            name_map = {
                "bing": "Bing",
                "duckduckgo": "DuckDuckGo",
                "wikipedia": "Wikipedia",
                "marginalia": "Marginalia",
                "brave": "Brave",
                "google": "Google",
                "reddit": "Reddit",
                "youtube": "YouTube",
                "x": "X",
            }
            # Add all detected engines first
            for eng in detected_engines:
                if eng not in engines_used_list:
                    engines_used_list.append(eng)
            # Add from telemetry
            for t in data.get("engine_telemetry", []):
                if isinstance(t, dict) and t.get("name"):
                    raw_name = str(t.get("name")).lower()
                    eng_name = name_map.get(raw_name, str(t.get("name")).title())
                    if eng_name not in engines_used_list:
                        engines_used_list.append(eng_name)
                    # If this engine was confirmed queried but not caught via live log
                    if on_engine_status and eng_name not in detected_engines:
                        detected_engines.add(eng_name)
                        try:
                            on_engine_status(f"Searching {eng_name}...")
                        except Exception:
                            pass
            for eng in data.get("engines_used", []):
                raw_name = str(eng).lower()
                eng_name = name_map.get(raw_name, str(eng).title())
                if eng_name not in engines_used_list:
                    engines_used_list.append(eng_name)
                if on_engine_status and eng_name not in detected_engines:
                    detected_engines.add(eng_name)
                    try:
                        on_engine_status(f"Searching {eng_name}...")
                    except Exception:
                        pass

            return {"results": results, "engines_used": engines_used_list}
        return {"results": [], "engines_used": list(detected_engines)}
    except Exception as e:
        logger.error("Failed to parse Wigolo search output: %s\nOutput: %s", e, stdout_text)
        raise RuntimeError(f"Failed to parse Wigolo search output: {e}") from e


async def clear_cache() -> Dict[str, Any]:
    """
    Clear Wigolo's search and content cache using the officially supported command:
    wigolo cache clear --url-pattern="*" --json

    This safely removes previous event search/content entries without touching
    any configurations, browser engines, or AI models.

    Returns:
        A dict with success status and count of cleared entries.
    """
    npx_cmd = _get_npx_command()
    cmd = [
        npx_cmd,
        "-y",
        "wigolo",
        "cache",
        "clear",
        "--url-pattern=*",
        "--json",
    ]

    logger.info("Executing Wigolo cache clear")

    returncode, stdout_text, stderr_text = await asyncio.to_thread(_run_wigolo_subprocess, cmd)

    if returncode != 0:
        logger.error("Wigolo cache clear failed with code %d: %s", returncode, stderr_text)
        raise RuntimeError(f"Wigolo cache clear failed (code {returncode}): {stderr_text or stdout_text}")

    try:
        data = _extract_json_from_output(stdout_text)
        cleared_count = 0
        if isinstance(data, dict):
            cleared_count = data.get("cleared", 0)
        return {"success": True, "cleared": cleared_count}
    except Exception as e:
        logger.warning("Could not parse cache clear output: %s, raw: %s", e, stdout_text)
        # Still considered success if the process exited with code 0
        return {"success": True, "cleared": 0}

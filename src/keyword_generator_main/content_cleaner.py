"""
Content Cleaner Module

Extracts readable article content and strips navigation menus, boilerplate,
cookie notices, advertisements, and syndicated wire-service duplicates.
"""

import html
import re
from typing import Any, Dict, List, Set

# Universal web chrome and advertisement marker tokens
BOILERPLATE_PATTERNS: List[re.Pattern] = [
    re.compile(r"click here to (?:read|subscribe|download|login|register)", re.I),
    re.compile(r"all rights reserved", re.I),
    re.compile(r"terms (?:of service|and conditions)", re.I),
    re.compile(r"privacy policy", re.I),
    re.compile(r"cookie (?:policy|preferences|consent|settings)", re.I),
    re.compile(r"follow us on (?:twitter|facebook|instagram|youtube|linkedin|x)", re.I),
    re.compile(r"subscribe to our (?:newsletter|channel|updates)", re.I),
    re.compile(r"(?:breaking|latest) news updates?", re.I),
    re.compile(r"photo gallery|video gallery", re.I),
    re.compile(r"advertisement|sponsored content|promoted stories", re.I),
    re.compile(r"download the (?:app|mobile app)", re.I),
    re.compile(r"for any feedback|contact us at", re.I),
    re.compile(r"read more:?|also read:?", re.I),
    re.compile(r"published (?:by|on):?|updated (?:by|on):?", re.I),
    re.compile(r"copyright \d{4}", re.I),
    re.compile(r"business insurance|insurance quotes", re.I),
    re.compile(r"sign in to (?:continue|read|comment)", re.I),
]

# Tags whose inner content is almost always non-editorial noise
STRIP_TAGS: List[re.Pattern] = [
    re.compile(r"<script[\s\S]*?</script>", re.I),
    re.compile(r"<style[\s\S]*?</style>", re.I),
    re.compile(r"<nav[\s\S]*?</nav>", re.I),
    re.compile(r"<footer[\s\S]*?</footer>", re.I),
    re.compile(r"<header[\s\S]*?</header>", re.I),
    re.compile(r"<form[\s\S]*?</form>", re.I),
    re.compile(r"<aside[\s\S]*?</aside>", re.I),
    re.compile(r"<svg[\s\S]*?</svg>", re.I),
    re.compile(r"<noscript[\s\S]*?</noscript>", re.I),
]


def strip_html_and_markup(raw_content: str) -> str:
    """Strip HTML tags, non-editorial blocks, and decode HTML entities."""
    if not raw_content:
        return ""
    text = raw_content

    # 1. Remove non-content structural elements
    for pat in STRIP_TAGS:
        text = pat.sub(" ", text)

    # 2. Convert line break tags to explicit newlines
    text = re.sub(r"<(?:br|p|div|h[1-6]|li)\b[^>]*>", "\n", text, flags=re.I)

    # 3. Strip all remaining HTML tags
    text = re.sub(r"<[^>]+>", " ", text)

    # 4. Decode HTML entities (&amp;, &quot;, &#39;, etc.)
    text = html.unescape(text)

    # 5. Remove URLs
    text = re.sub(r"https?://\S+|www\.\S+", " ", text)

    # 6. Normalize whitespace while preserving paragraphs
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.split("\n")]
    cleaned_lines = [line for line in lines if line]
    return "\n".join(cleaned_lines)


def is_boilerplate_sentence(sentence: str) -> bool:
    """Check if a single sentence is website chrome, advertisement, or navigation junk."""
    s = sentence.strip()
    if len(s) < 15:
        return True

    # Check against known boilerplate regex patterns
    for pat in BOILERPLATE_PATTERNS:
        if pat.search(s):
            return True

    words = s.lower().split()
    # Check if sentence is merely a list of menu links
    if len(words) <= 5 and any(w in {"home", "login", "register", "contact", "menu", "share", "search", "faq"} for w in words):
        return True

    return False


def extract_clean_passages(raw_text: str) -> List[str]:
    """
    Extract substantive, clean passages from raw article text.
    Filters out noise, short fragments, and navigation boilerplate.
    """
    cleaned_text = strip_html_and_markup(raw_text)
    paragraphs = cleaned_text.split("\n")
    passages: List[str] = []

    for para in paragraphs:
        para_clean = para.strip()
        if len(para_clean) < 20:
            continue

        # Split paragraph into sentences
        sentences = re.split(r"(?<=[.?!;])\s+", para_clean)
        clean_sentences = []
        for s in sentences:
            s_stripped = s.strip()
            if not is_boilerplate_sentence(s_stripped):
                clean_sentences.append(s_stripped)

        if clean_sentences:
            passage = " ".join(clean_sentences)
            if len(passage) >= 30:
                passages.append(passage)

    return passages


def deduplicate_syndicated_passages(passages: List[str], similarity_threshold: float = 0.85) -> List[str]:
    """
    Eliminates duplicated news agency wire copies (e.g. identical PTI/ANI syndication)
    using token-level Jaccard overlap.
    """
    unique_passages: List[str] = []
    seen_token_sets: List[Set[str]] = []

    for p in passages:
        tokens = set(re.findall(r"[A-Za-z0-9]+", p.lower()))
        if len(tokens) < 5:
            continue

        is_duplicate = False
        for seen in seen_token_sets:
            inter = len(tokens & seen)
            union = len(tokens | seen)
            if union > 0 and (inter / union) >= similarity_threshold:
                is_duplicate = True
                break

        if not is_duplicate:
            unique_passages.append(p)
            seen_token_sets.append(tokens)

    return unique_passages

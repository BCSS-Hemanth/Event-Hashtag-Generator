"""
Language & Translation Service for Indian Regional Languages.

Detects the target Indian regional language based on the event location
and provides multi-tier resilient translation into Indic scripts.
"""

import json
import logging
import re
import unicodedata
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Canonical list of languages supported by the UI and multilingual extraction.
# Order is stable for the Language dropdown checklist.
SUPPORTED_LANGUAGES: List[Dict[str, Any]] = [
    {"code": "or", "name": "Odia", "range": (0x0B00, 0x0B7F)},
    {"code": "ta", "name": "Tamil", "range": (0x0B80, 0x0BFF)},
    {"code": "te", "name": "Telugu", "range": (0x0C00, 0x0C7F)},
    {"code": "kn", "name": "Kannada", "range": (0x0C80, 0x0CFF)},
    {"code": "ml", "name": "Malayalam", "range": (0x0D00, 0x0D7F)},
    {"code": "mr", "name": "Marathi", "range": (0x0900, 0x097F)},
    {"code": "gu", "name": "Gujarati", "range": (0x0A80, 0x0AFF)},
    {"code": "bn", "name": "Bengali", "range": (0x0980, 0x09FF)},
    {"code": "pa", "name": "Punjabi", "range": (0x0A00, 0x0A7F)},
    {"code": "hi", "name": "Hindi", "range": (0x0900, 0x097F)},
]

SUPPORTED_LANGUAGE_CODES: Dict[str, Dict[str, Any]] = {
    lang["code"]: lang for lang in SUPPORTED_LANGUAGES
}


def get_supported_languages() -> List[Dict[str, Any]]:
    """Return a copy of the supported language catalog for UI / API use."""
    return [dict(lang) for lang in SUPPORTED_LANGUAGES]


def resolve_language_selection(codes: Optional[List[str]]) -> List[Dict[str, Any]]:
    """
    Resolve UI language codes into language metadata dicts.
    Accepts individual codes and/or 'all'. Unknown codes are ignored.
    """
    if not codes:
        return []
    normalized = [str(c).strip().lower() for c in codes if c and str(c).strip()]
    if not normalized:
        return []
    if "all" in normalized:
        return get_supported_languages()
    seen = set()
    resolved: List[Dict[str, Any]] = []
    for code in normalized:
        if code in seen or code not in SUPPORTED_LANGUAGE_CODES:
            continue
        seen.add(code)
        resolved.append(dict(SUPPORTED_LANGUAGE_CODES[code]))
    return resolved


# State and Union Territory mapping to ISO 639-1 language codes & script ranges
STATE_LANGUAGE_MAP: Dict[str, Dict[str, Any]] = {
    # Odisha
    "odisha": {"code": "or", "name": "Odia", "range": (0x0B00, 0x0B7F)},
    "orissa": {"code": "or", "name": "Odia", "range": (0x0B00, 0x0B7F)},
    # Tamil Nadu & Puducherry
    "tamil nadu": {"code": "ta", "name": "Tamil", "range": (0x0B80, 0x0BFF)},
    "tamilnadu": {"code": "ta", "name": "Tamil", "range": (0x0B80, 0x0BFF)},
    "puducherry": {"code": "ta", "name": "Tamil", "range": (0x0B80, 0x0BFF)},
    "pondicherry": {"code": "ta", "name": "Tamil", "range": (0x0B80, 0x0BFF)},
    # Telangana & Andhra Pradesh
    "telangana": {"code": "te", "name": "Telugu", "range": (0x0C00, 0x0C7F)},
    "andhra pradesh": {"code": "te", "name": "Telugu", "range": (0x0C00, 0x0C7F)},
    "andhra": {"code": "te", "name": "Telugu", "range": (0x0C00, 0x0C7F)},
    # Karnataka
    "karnataka": {"code": "kn", "name": "Kannada", "range": (0x0C80, 0x0CFF)},
    # Kerala
    "kerala": {"code": "ml", "name": "Malayalam", "range": (0x0D00, 0x0D7F)},
    "lakshadweep": {"code": "ml", "name": "Malayalam", "range": (0x0D00, 0x0D7F)},
    # Maharashtra & Goa
    "maharashtra": {"code": "mr", "name": "Marathi", "range": (0x0900, 0x097F)},
    "goa": {"code": "mr", "name": "Marathi", "range": (0x0900, 0x097F)},
    # Gujarat & UTs
    "gujarat": {"code": "gu", "name": "Gujarati", "range": (0x0A80, 0x0AFF)},
    "daman": {"code": "gu", "name": "Gujarati", "range": (0x0A80, 0x0AFF)},
    "diu": {"code": "gu", "name": "Gujarati", "range": (0x0A80, 0x0AFF)},
    # West Bengal & Tripura
    "west bengal": {"code": "bn", "name": "Bengali", "range": (0x0980, 0x09FF)},
    "bengal": {"code": "bn", "name": "Bengali", "range": (0x0980, 0x09FF)},
    "tripura": {"code": "bn", "name": "Bengali", "range": (0x0980, 0x09FF)},
    # Punjab & Chandigarh
    "punjab": {"code": "pa", "name": "Punjabi", "range": (0x0A00, 0x0A7F)},
    "chandigarh": {"code": "pa", "name": "Punjabi", "range": (0x0A00, 0x0A7F)},
    # Hindi Belt States & UTs
    "delhi": {"code": "hi", "name": "Hindi", "range": (0x0900, 0x097F)},
    "ncr": {"code": "hi", "name": "Hindi", "range": (0x0900, 0x097F)},
    "uttar pradesh": {"code": "hi", "name": "Hindi", "range": (0x0900, 0x097F)},
    "bihar": {"code": "hi", "name": "Hindi", "range": (0x0900, 0x097F)},
    "madhya pradesh": {"code": "hi", "name": "Hindi", "range": (0x0900, 0x097F)},
    "rajasthan": {"code": "hi", "name": "Hindi", "range": (0x0900, 0x097F)},
    "haryana": {"code": "hi", "name": "Hindi", "range": (0x0900, 0x097F)},
    "uttarakhand": {"code": "hi", "name": "Hindi", "range": (0x0900, 0x097F)},
    "himachal pradesh": {"code": "hi", "name": "Hindi", "range": (0x0900, 0x097F)},
    "jharkhand": {"code": "hi", "name": "Hindi", "range": (0x0900, 0x097F)},
    "chhattisgarh": {"code": "hi", "name": "Hindi", "range": (0x0900, 0x097F)},
}

# Major cities mapped directly to language info in case state name is omitted
CITY_LANGUAGE_MAP: Dict[str, str] = {
    # Odisha
    "bhubaneswar": "odisha",
    "cuttack": "odisha",
    "puri": "odisha",
    "rourkela": "odisha",
    "sambalpur": "odisha",
    "berhampur": "odisha",
    "balasore": "odisha",
    "baleshwar": "odisha",
    # Tamil Nadu
    "chennai": "tamil nadu",
    "madras": "tamil nadu",
    "coimbatore": "tamil nadu",
    "madurai": "tamil nadu",
    "trichy": "tamil nadu",
    "tiruchirappalli": "tamil nadu",
    "salem": "tamil nadu",
    # Telangana & AP
    "hyderabad": "telangana",
    "secunderabad": "telangana",
    "warangal": "telangana",
    "visakhapatnam": "andhra pradesh",
    "vizag": "andhra pradesh",
    "vijayawada": "andhra pradesh",
    "guntur": "andhra pradesh",
    "tirupati": "andhra pradesh",
    # Karnataka
    "bengaluru": "karnataka",
    "bangalore": "karnataka",
    "mysuru": "karnataka",
    "mysore": "karnataka",
    "mangaluru": "karnataka",
    "mangalore": "karnataka",
    "hubli": "karnataka",
    # Kerala
    "thiruvananthapuram": "kerala",
    "trivandrum": "kerala",
    "kochi": "kerala",
    "cochin": "kerala",
    "kozhikode": "kerala",
    "calicut": "kerala",
    "thrissur": "kerala",
    # Maharashtra
    "mumbai": "maharashtra",
    "bombay": "maharashtra",
    "pune": "maharashtra",
    "nagpur": "maharashtra",
    "nashik": "maharashtra",
    "thane": "maharashtra",
    # Gujarat
    "ahmedabad": "gujarat",
    "surat": "gujarat",
    "vadodara": "gujarat",
    "baroda": "gujarat",
    "rajkot": "gujarat",
    "gandhinagar": "gujarat",
    # West Bengal
    "kolkata": "west bengal",
    "calcutta": "west bengal",
    "howrah": "west bengal",
    "durgapur": "west bengal",
    "siliguri": "west bengal",
    # Punjab
    "amritsar": "punjab",
    "ludhiana": "punjab",
    "jalandhar": "punjab",
    "patiala": "punjab",
    # Hindi Belt
    "lucknow": "delhi",
    "kanpur": "delhi",
    "varanasi": "delhi",
    "noida": "delhi",
    "ghaziabad": "delhi",
    "agra": "delhi",
    "patna": "delhi",
    "bhopal": "delhi",
    "indore": "delhi",
    "jaipur": "delhi",
    "jodhpur": "delhi",
    "gurugram": "delhi",
    "gurgaon": "delhi",
    "faridabad": "delhi",
    "ranchi": "delhi",
    "raipur": "delhi",
    "dehradun": "delhi",
}

# Translation cache to avoid redundant network calls within process memory
_TRANSLATION_CACHE: Dict[Tuple[str, str], str] = {}


def detect_language_from_location(location: str) -> Optional[Dict[str, Any]]:
    """
    Detect the official regional Indian language from a location string.
    Checks state/UT names first, then major cities.
    Returns language metadata dict or None if not an Indian location.
    """
    if not location or not location.strip():
        return None

    clean_loc = location.lower().strip()

    # 1. Check for state matches
    for state_key, lang_info in STATE_LANGUAGE_MAP.items():
        # Match as discrete word/phrase boundary
        pattern = r"\b" + re.escape(state_key) + r"\b"
        if re.search(pattern, clean_loc):
            return {
                "state": state_key.title(),
                "code": lang_info["code"],
                "name": lang_info["name"],
                "range": lang_info["range"],
            }

    # 2. Check for city matches
    for city_key, state_key in CITY_LANGUAGE_MAP.items():
        pattern = r"\b" + re.escape(city_key) + r"\b"
        if re.search(pattern, clean_loc):
            lang_info = STATE_LANGUAGE_MAP[state_key]
            return {
                "state": state_key.title(),
                "city": city_key.title(),
                "code": lang_info["code"],
                "name": lang_info["name"],
                "range": lang_info["range"],
            }

    return None


def sanitize_translation(text: str) -> str:
    """Strip XML/TMX/XLIFF formatting tags like '<g id="1">', 'g id="1">', '</g>', or HTML entities leaked by translation engines."""
    if not text:
        return ""
    cleaned = re.sub(r"<\/?g\b[^>]*>", "", text, flags=re.IGNORECASE)
    cleaned = re.sub(r"\bg\s+id=[\"']?\w+[\"']?>?", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"&[a-z]+;|&#\d+;", " ", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+", " ", cleaned)
    cleaned = cleaned.strip()
    # Some engines append stray pipes / danda-like separators
    cleaned = cleaned.strip("|").strip()
    cleaned = re.sub(r"\s*[|]+\s*$", "", cleaned).strip()
    return cleaned


def translate_phrase(text: str, target_lang: str) -> Optional[str]:
    """
    Translate an English phrase into target Indic language.
    Uses multi-tier fallback (Google GTX -> MyMemory -> deep-translator).
    Returns translated string or None on failure.
    """
    text_clean = text.strip()
    if not text_clean:
        return None

    cache_key = (text_clean.lower(), target_lang)
    if cache_key in _TRANSLATION_CACHE:
        return _TRANSLATION_CACHE[cache_key]

    # Tier 1: Direct Google Translate GTX endpoint (fastest, lightweight)
    try:
        url = (
            "https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl="
            + target_lang
            + "&dt=t&q="
            + urllib.parse.quote(text_clean)
        )
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            },
        )
        with urllib.request.urlopen(req, timeout=4) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data and data[0] and data[0][0] and data[0][0][0]:
                translated = sanitize_translation(str(data[0][0][0]))
                if translated:
                    _TRANSLATION_CACHE[cache_key] = translated
                    return translated
    except Exception as e:
        logger.debug("Google GTX translation endpoint failed for '%s': %s", text_clean, e)

    # Tier 2: deep-translator MyMemoryTranslator fallback
    try:
        from deep_translator import MyMemoryTranslator

        src = "en-GB"
        tgt = f"{target_lang}-IN"
        raw_res = MyMemoryTranslator(source=src, target=tgt).translate(text_clean)
        if raw_res:
            res = sanitize_translation(str(raw_res))
            if res:
                _TRANSLATION_CACHE[cache_key] = res
                return res
    except Exception as e:
        logger.debug("MyMemory fallback translation failed for '%s': %s", text_clean, e)

    # Tier 3: deep-translator GoogleTranslator fallback
    try:
        from deep_translator import GoogleTranslator

        raw_res = GoogleTranslator(source="auto", target=target_lang).translate(text_clean)
        if raw_res:
            res = sanitize_translation(str(raw_res))
            if res:
                _TRANSLATION_CACHE[cache_key] = res
                return res
    except Exception as e:
        logger.debug("GoogleTranslator fallback failed for '%s': %s", text_clean, e)

    return None



# Danda punctuation is shared across Indic languages and is not a script marker.
_NEUTRAL_INDIC_CODEPOINTS = {0x0964, 0x0965}


def is_indic_text(text: str) -> bool:
    """Check if the text contains any Indic Unicode characters (U+0900 to U+0D7F)."""
    return any("\u0900" <= ch <= "\u0D7F" for ch in text)


def is_target_script_text(text: str, script_range: Tuple[int, int]) -> bool:
    """
    True when the text is written in the location language's script.

    English letters, digits, and punctuation may sit beside that script.
    A character from any other Indic script rejects the text. Odisha therefore
    keeps Odia and drops Hindi Devanagari, Bengali, Tamil, and the rest.
    """
    if not text or not script_range:
        return False
    start, end = script_range
    saw_target = False
    for ch in text:
        code = ord(ch)
        if start <= code <= end:
            saw_target = True
            continue
        if code in _NEUTRAL_INDIC_CODEPOINTS:
            continue
        if 0x0900 <= code <= 0x0D7F:
            return False
    return saw_target


def _hashtag_char(ch: str) -> bool:
    """Letters, digits, and the vowel signs that belong to those letters."""
    if ch.isalnum():
        return True
    return unicodedata.category(ch) in {"Mn", "Mc", "Me"}


def format_indic_hashtag(phrase: str) -> str:
    """
    Format an Indic script phrase into a clean hashtag.
    Drops spaces and punctuation, keeps vowel signs, and stops at a word
    boundary once the body would pass 25 characters.
    """
    if not phrase:
        return ""
    acc = ""
    for word in re.findall(r"[^\s,;|/]+", phrase):
        piece = "".join(ch for ch in word if _hashtag_char(ch))
        if not piece:
            continue
        if len(acc) + len(piece) > 25:
            break
        acc += piece
    if len(acc) < 3:
        return ""
    return f"#{acc}"

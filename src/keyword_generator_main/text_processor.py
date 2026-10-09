"""
Deterministic Text Processor Module

Extracts event-specific, contextually grounded information:
1. People Involved: Names of individuals, organizers, leaders, officials, and key participants.
2. Specific Locations: States, cities, districts, roads, and venues associated with the event.
3. What the Event is About: Main subject, purpose, key activities, demands, claims, issues, and initiatives.
4. Social & Campaign Hashtags: Well-formed, valid CamelCase tags (#CamelCase, <=25 chars).

IMPORTANT:
- No arbitrary n-grams or random adjacent word combinations.
- Sub-phrases of full entities are suppressed (subsumption).
- Transliteration-aware clustering for spelling variants, prioritizing user's input.
- Content retrieved from web search is strictly vetted against the Ground Truth Anchor.
"""

import difflib
import re
from collections import Counter
from typing import Any, Dict, List, Optional, Set, Tuple

from keyword_generator_main.content_cleaner import (
    deduplicate_syndicated_passages,
    extract_clean_passages,
    is_boilerplate_sentence,
)


# Comprehensive grammatical stopwords and web boilerplate terms
STOP_WORDS: Set[str] = {
    # English grammatical stopwords
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and",
    "any", "are", "aren't", "as", "at", "be", "because", "been", "before", "being",
    "below", "between", "both", "but", "by", "can", "can't", "cannot", "could",
    "couldn't", "did", "didn't", "do", "does", "doesn't", "doing", "don't", "down",
    "during", "each", "few", "for", "from", "further", "had", "hadn't", "has",
    "hasn't", "have", "haven't", "having", "he", "he'd", "he'll", "he's", "her",
    "here", "here's", "hers", "herself", "him", "himself", "his", "how", "how's",
    "i", "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't", "it",
    "it's", "its", "itself", "let's", "me", "more", "most", "mustn't", "my",
    "myself", "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other",
    "ought", "our", "ours", "ourselves", "out", "over", "own", "same", "shan't",
    "she", "she'd", "she'll", "she's", "should", "shouldn't", "so", "some", "such",
    "than", "that", "that's", "the", "their", "theirs", "them", "themselves",
    "then", "there", "there's", "these", "they", "they'd", "they'll", "they're",
    "they've", "this", "those", "through", "to", "too", "under", "until", "up",
    "very", "was", "wasn't", "we", "we'd", "we'll", "we're", "we've", "were",
    "weren't", "what", "what's", "when", "when's", "where", "where's", "which",
    "while", "who", "who's", "whom", "why", "why's", "with", "won't", "would",
    "wouldn't", "you", "you'd", "you'll", "you're", "you've", "your", "yours",
    "yourself", "yourselves",
    # Prepositions and boilerplate often misjoined
    "including", "regarding", "concerning", "following", "amid", "along", "across",
    # Web and document boilerplate
    "http", "https", "www", "com", "org", "net", "pdf", "html", "htm", "url", "page",
    "website", "details", "login", "view", "read", "more", "posted", "updated", "share",
    "author", "published", "comments", "like", "also", "even", "just", "well", "now",
    "one", "two", "three", "first", "last", "new", "many", "much", "said", "says",
    "told", "took", "made", "make"
}

# Finite and action verbs that must not appear in noun phrases
COMMON_FINITE_VERBS: Set[str] = {
    "staged", "demanded", "reported", "joined", "protested", "gathered",
    "rallied", "organized", "announced", "supported", "formed", "faced",
    "held", "called", "urged", "led", "served", "issued", "began",
    "stated", "established", "founded", "conducted", "emphasized",
    "addressed", "investigated", "launched", "participated", "received",
    "passed", "signed", "submitted", "claimed", "arrived", "joins",
    "demands", "calls", "urges", "announces", "speaks", "leads",
    "provides", "offers", "launches", "strives", "empowers", "encourages",
    "implements", "participates", "addresses", "serves", "claims", "says",
    "gain", "offer", "participate", "conduct", "ensure", "strive", "gather",
    "covering", "protest", "protests", "meeting"
}

# Words indicating organization, group, or institution
ORGANIZATION_INDICATORS: Set[str] = {
    "sangathan", "morcha", "party", "union", "association", "department",
    "ministry", "division", "police", "commission", "forum", "committee",
    "board", "council", "trust", "foundation", "movement", "alliance",
    "initiative", "initiatives", "group", "groups", "ngo", "club", "network",
    "authority", "agency", "corps", "force", "bureau", "front", "chhatra",
    "developers", "thoughtworks", "corporation", "society", "congress",
    "sankalp", "parishad", "samiti", "sabha", "dal", "sena"
}

# Words indicating location, venue, or geographical feature
LOCATION_INDICATORS: Set[str] = {
    "road", "rd", "street", "st", "lane", "avenue", "ave", "marg", "chowk",
    "circle", "square", "bypass", "nagar", "sector", "hills", "valley",
    "convention", "center", "centre", "auditorium", "stadium", "hall",
    "complex", "campus", "university", "assembly", "city", "district", "state",
    "gujarat", "odisha", "delhi", "punjab", "bengal", "maharashtra", "telangana",
    "india"
}

# Role titles and honorifics that must not be treated as a person's first name
TITLES_AND_ROLES: Set[str] = {
    "shri", "smt", "dr", "prof", "mr", "mrs", "ms", "convenor", "convener",
    "leader", "minister", "pm", "cm", "president", "secretary", "director",
    "activist", "spokesperson", "spokesman", "chief", "chairperson", "advocate"
}

# Headline tails glued onto person names ("Revanth Reddy Speech" / "… Full")
PERSON_NAME_TRAILING_NOISE: Set[str] = {
    "speech", "full", "live", "video", "interview", "address", "talk", "talks",
    "says", "said", "watch", "highlights", "update", "updates", "news", "press",
    "meet", "meeting", "visit", "visited", "inauguration", "inaugurates",
    "participates", "participation", "honble", "honourable", "honorable",
    "sri", "ji", "garu", "audio", "photos", "photo", "gallery", "clip",
    "statement", "remarks", "message", "special", "exclusive",
}

# Substantive non-person concept words that should not be misclassified as individuals
NON_PERSON_WORDS: Set[str] = {
    "person", "persons", "people", "public", "community", "citizens",
    "fund", "affairs", "safety", "conference", "initiative", "initiatives",
    "development", "computing", "tech", "developer", "developers", "engineering",
    "data", "software", "division", "department", "ministry", "scheme", "yojana",
    "act", "bill", "policy", "portal", "centre", "center", "centres", "service",
    "services", "system", "systems", "reform", "reforms", "error", "errors",
    "protest", "protests", "rally", "rallies", "controversy", "sangathan",
    "morcha", "party", "union", "board", "council", "commission", "program",
    "programme", "project", "mission", "network", "club", "hub", "festival",
    "utsav", "garba", "navratri", "science", "learning", "intelligence", "law",
    "court", "police", "force", "agency", "corps", "bureau", "front", "welfare",
    "harassment", "violence", "crime", "response", "relief", "support", "action",
    "trust", "foundation", "society", "association", "convention", "auditorium",
    "stadium", "hall", "road", "street", "lane", "hills", "valley", "nagar",
    "sector", "chhatra", "yuva", "facts", "fact", "movement", "movements",
    "curriculum", "textbook", "textbooks", "history", "education", "school"
}

# Known collision or satire terms to discard unless user explicitly provided them
KNOWN_COLLISION_PATTERNS: List[str] = [
    "judicial performance",
    "commission on judicial",
    "state agency established",
    "independent state agency",
    "california commission",
    "california judicial",
]

# Incomplete mid-sentence scraps that must never become keywords/hashtags
FRAGMENT_TAIL_WORDS: Set[str] = {
    "became", "forced", "being", "having", "making", "taking", "getting",
    "going", "coming", "according", "including", "regarding", "concerning",
    "following", "during", "after", "before", "while", "when", "where",
    "official", "officials", "withdraws", "launches", "announces",
    "holding", "warning", "latest", "update", "updates", "combined",
    "controversy", "erupted", "want", "wants", "erupts", "says", "said",
}

# Generic web-chrome phrases (not event-specific)
JUNK_PHRASE_BLACKLIST: Set[str] = {
    "latest update", "latest updates", "campaign special", "breaking news",
    "photo gallery", "video gallery", "click here", "read more",
    "looking forward", "every september", "every october", "every november",
    "every december", "every january", "world heritage", "top indian holidays",
    "best outdoor music", "greatest outdoor music", "friendly outdoor",
    "greatest eco", "encamp adventures", "complete guide", "travel tips",
}

# Weak theme words that must not alone justify admitting a phrase
GENERIC_THEME_TOKENS: Set[str] = {
    "outdoor", "outdoors", "music", "musical", "festival", "festivals", "fest",
    "valley", "scenic", "artist", "artists", "indian", "international",
    "independent", "setting", "featuring", "live", "event", "events",
    "experience", "experiences", "travel", "traveller", "travellers",
    "holiday", "holidays", "adventure", "adventures", "eco", "friendly",
    "greatest", "best", "top", "ultimate", "amazing", "perfect", "looking",
    "forward", "every", "september", "october", "november", "december",
    "january", "february", "march", "april", "may", "june", "july", "august",
    "heritage", "world", "interesting", "places", "green", "fields", "pine",
    "forests", "mountains", "days", "day", "encamp", "camping",
}

# Marketing / listicle openers (travel SEO, ranking blurbs)
MARKETING_OPENERS: Set[str] = {
    "every", "looking", "greatest", "best", "top", "ultimate", "amazing",
    "perfect", "must", "friendly", "encamp", "discover", "explore", "enjoy",
    "unforgettable", "iconic", "stunning", "beautiful", "popular", "famous",
    "leading", "premier", "biggest", "largest", "finest",
}

# Clickbait / sensational headline scraps (not event facts)
CLICKBAIT_TOKENS: Set[str] = {
    "allegedly", "thrown", "exposed", "chaos", "drama", "shocking", "viral",
    "outrage", "revealed", "caught", "blast", "slammed", "horrif", "row",
    "tension", "erupted", "clash", "clashes", "fury", "storm",
}

# Lone tokens that are never useful as keywords/hashtags on their own
# (only full phrases like "Cockroach Janta Party" or "Chief Election Commissioner")
ENTITY_GLUE_SINGLETONS: Set[str] = {
    "party", "janata", "janta", "commission", "commissioner", "committee",
    "association", "union", "society", "foundation", "trust", "organization",
    "organisation", "front", "movement", "andolan", "sangh", "dal", "congress",
    "chief", "election", "minister", "president", "convenor", "convener",
    "coordinator", "chairperson", "secretary", "director", "founder",
    "protest", "protesters", "protests", "rally", "march", "yatra",
}

# State -> known cities/venues (used to block geographic bleed)
STATE_GEOGRAPHY: Dict[str, Set[str]] = {
    "maharashtra": {
        "mumbai", "pune", "nagpur", "nashik", "thane", "aurangabad", "kolhapur",
        "shivaji park", "marine drive", "gateway of india", "azad maidan",
    },
    "odisha": {
        "bhubaneswar", "cuttack", "puri", "rourkela", "sambalpur", "berhampur",
    },
    "delhi": {
        "delhi", "new delhi", "noida", "gurugram", "gurgaon", "jantar mantar",
        "india gate", "connaught place", "raisina",
    },
    "haryana": {"ambala", "gurgaon", "gurugram", "faridabad", "hisar", "karnal", "jind"},
    "uttar pradesh": {"lucknow", "noida", "varanasi", "prayagraj", "kanpur", "ayodhya"},
    "karnataka": {"bengaluru", "bangalore", "mysuru", "mysore", "mangaluru"},
    "tamil nadu": {"chennai", "coimbatore", "madurai"},
    "west bengal": {"kolkata", "howrah", "siliguri", "darjeeling"},
    "gujarat": {"ahmedabad", "gandhinagar", "surat", "vadodara", "rajkot"},
    "telangana": {"hyderabad", "secunderabad", "warangal"},
    "andhra pradesh": {"vijayawada", "visakhapatnam", "tirupati", "sriharikota"},
    "punjab": {"chandigarh", "amritsar", "ludhiana", "jalandhar"},
    "rajasthan": {"jaipur", "udaipur", "jodhpur"},
    "bihar": {"patna", "gaya"},
    "jharkhand": {"ranchi", "jamshedpur"},
    "assam": {"guwahati"},
    "uttarakhand": {"dehradun", "haridwar", "joshimath", "rishikesh"},
    "himachal pradesh": {"shimla", "manali"},
    "jammu and kashmir": {"srinagar", "jammu", "gulmarg"},
    "goa": {"panaji", "panjim", "margao"},
    "madhya pradesh": {"bhopal", "indore", "gwalior"},
    "chhattisgarh": {"raipur", "bastar", "jagdalpur"},
}

# Cities/landmarks that imply a specific foreign region (bleed blockers)
LANDMARK_TO_REGION: Dict[str, str] = {
    "jantar mantar": "delhi",
    "india gate": "delhi",
    "shivaji park": "maharashtra",
    "azad maidan": "maharashtra",
    "janata maidan": "odisha",
    "marina beach": "tamil nadu",
}

# Small words skipped when building acronyms from multi-word names
ACRONYM_SKIP_WORDS: Set[str] = {
    "of", "and", "the", "for", "in", "at", "a", "an", "on", "to", "by",
    "or", "&",
}

# Common acronyms to preserve in all-caps when formatting hashtags (formatting only)
KNOWN_ACRONYMS: Set[str] = {
    "gmdc", "fra", "posco", "jsw", "ncr", "ai", "ml", "iot", "it",
    "bjp", "aap", "ngo", "who", "un", "unesco", "usa", "uk", "eu",
}

# Web, publication, and commercial boilerplate phrases to reject unconditionally
WEB_BOILERPLATE_BLACK_LIST: Set[str] = {
    "contact us", "privacy policy", "terms of service", "all rights reserved",
    "business insurance", "insurance quotes", "insurance", "commercial insurance",
    "life insurance", "travel tips", "complete guide", "travel guide", "visitor guide",
    "event guide", "entry fee", "ticket price", "admission fee", "online application",
    "competitive examination", "apply online", "click here", "read more", "view details",
    "login", "register", "sign in", "sign up", "share this", "share on", "breaking news",
    "latest updates", "photo gallery", "video gallery", "subscribe", "newsletter",
    "follow us", "download app", "install app", "advertising", "advertisement",
    "sponsored", "affiliate", "faq", "customer care", "helpline number",
    "terms and conditions", "disclaimer", "cookie policy", "about us", "home page",
    "catching dust", "reveals big", "stories unite", "another reason", "expand tourism",
    "online chit", "grand glimpse", "cultural continuity", "unites artists",
    "every october", "every september", "looking forward", "world heritage",
    "top indian holidays", "best outdoor music", "greatest outdoor music",
    "friendly outdoor", "greatest eco", "encamp adventures", "outdoor adventures",
    "marked by strict fasting", "seminars by global artists",
    "claiming over", "hundreds of", "thousands of", "hindustan times", "times of india",
    "the hindu", "indian express", "ndtv", "news18", "india today", "hindu temple set",
    "state agency", "editorial board", "press release"
}

WEB_BOILERPLATE_SUBSTRINGS: Set[str] = {
    "insurance", "subscribe", "newsletter", "advertisement", "advertising",
    "affiliate", "copyright", "sponsored", "cookie policy", "terms of service",
    "privacy policy", "all rights reserved", "contact us", "download app"
}


def is_web_boilerplate(term: str) -> bool:
    """Check if a term or hashtag is web boilerplate, commercial spam, or site navigation."""
    if not term:
        return True
    cleaned = re.sub(r"[^A-Za-z0-9\s]", "", term.lstrip("#")).strip().lower()
    if not cleaned or len(cleaned) < 2:
        return True
    if cleaned in WEB_BOILERPLATE_BLACK_LIST:
        return True
    # Check if any blacklist phrase is a substantive match
    for bp in WEB_BOILERPLATE_BLACK_LIST:
        if bp == cleaned:
            return True
        if len(bp) >= 8 and (f" {bp} " in f" {cleaned} " or cleaned.startswith(bp) or cleaned.endswith(bp)):
            return True
    # Check forbidden commercial substrings
    for sub in WEB_BOILERPLATE_SUBSTRINGS:
        if sub in cleaned:
            return True
    # Check leading journalistic/conversational filler prefixes
    words = cleaned.split()
    if len(words) >= 2:
        prefix2 = f"{words[0]} {words[1]}"
        if prefix2 in {
            "marked by", "claiming over", "hundreds of", "thousands of",
            "another reason", "complete guide", "travel tips", "travel guide",
            "event guide", "entry fee", "guidelines for", "seminars by"
        }:
            return True
    return False



def clean_text(text: str) -> str:
    """Clean text by removing HTML entities, URLs, and excess whitespace."""
    text = re.sub(r"https?://\S+|www\.\S+", " ", text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def tokenize(text: str) -> List[str]:
    """Split text into lowercase alphanumeric tokens."""
    return [word.lower() for word in re.findall(r"[A-Za-z0-9]+", text) if len(word) > 1]


def phrase_to_acronym(phrase: str) -> Optional[str]:
    """
    Build a short form from a multi-word proper name.
    e.g. 'Central Pollution Control Board' -> 'CPCB'.
    Does not invent a new short form from phrases that already contain an ALL-CAPS acronym token.
    """
    if not phrase:
        return None
    words = [
        w for w in re.findall(r"[A-Za-z0-9]+", phrase)
        if w.lower() not in ACRONYM_SKIP_WORDS and len(w) > 0
    ]
    if len(words) < 2:
        return None
    # If one token is already a 2-6 letter acronym, do not invent a new short form
    existing = [w.upper() for w in words if w.isupper() and 2 <= len(w) <= 6]
    if existing and len(words) <= 3:
        return None
    acro = "".join(w[0].upper() for w in words if w[0].isalpha())
    if 2 <= len(acro) <= 6:
        return acro
    return None


def extract_explicit_acronym_pairs(text: str) -> List[Tuple[str, str]]:
    """
    Extract Full Name (ACRO) and ACRO (Full Name) pairs from free text.
    Returns list of (full_form, acronym) with acronym uppercased.
    """
    pairs: List[Tuple[str, str]] = []
    if not text:
        return pairs

    # Full Name (ACRO)
    for m in re.finditer(
        r"\b([A-Z][A-Za-z0-9]+(?:\s+(?:[A-Z][A-Za-z0-9]+|of|and|the|for|in)){1,6})\s*\(([A-Z]{2,6})\)",
        text,
    ):
        full, acro = m.group(1).strip(), m.group(2).upper()
        if full and acro:
            pairs.append((full, acro))

    # ACRO (Full Name)
    for m in re.finditer(
        r"\b([A-Z]{2,6})\s*\(([A-Z][A-Za-z0-9]+(?:\s+(?:[A-Z][A-Za-z0-9]+|of|and|the|for|in)){1,6})\)",
        text,
    ):
        acro, full = m.group(1).upper(), m.group(2).strip()
        if full and acro:
            pairs.append((full, acro))

    return pairs


def _looks_like_named_entity(phrase: str) -> bool:
    """True for org/event-style multi-word names, not free-form demand phrases."""
    if not phrase:
        return False
    words = phrase.strip().split()
    # Acronym expansions must stay short — never whole sentences/paragraphs
    if not (2 <= len(words) <= 6):
        return False
    if re.search(r"[.!?]", phrase):
        return False
    lower_words = {w.lower() for w in words}
    # Sentence verbs → description scrap, not an org name
    if lower_words & COMMON_FINITE_VERBS:
        return False
    if lower_words & ORGANIZATION_INDICATORS:
        return True
    # Title-ish: majority of words capitalized or all-lowercase org from user desc
    caps = sum(1 for w in words if w[:1].isupper())
    if caps >= max(2, len(words) - 1):
        return True
    # User description often lower/mixed: allow if not demand-like
    demand_like = {
        "fee", "rollback", "debt", "waiver", "legal", "guarantee", "reform",
        "demand", "demands", "protest", "campaign", "student", "safety",
    }
    if lower_words & demand_like and not (lower_words & ORGANIZATION_INDICATORS):
        return False
    return len(words) >= 3


def _is_usable_acronym_full(full: str) -> bool:
    """Reject sentence/paragraph text masquerading as an org expansion."""
    if not full or not _looks_like_named_entity(full):
        return False
    if len(full) > 80:
        return False
    lower_toks = set(tokenize(full))
    # Never treat action scraps as org names ("… Supports NYCS", "… Activity …")
    if lower_toks & (COMMON_FINITE_VERBS | {"supports", "support", "supported", "activity", "activities"}):
        return False
    return True


def _description_clauses(description: str) -> List[str]:
    """Split description into short clauses (periods included — not just commas)."""
    return [
        c.strip()
        for c in re.split(r"[,;.!?\n]+", description or "")
        if c and c.strip()
    ]


def _user_stated_acronyms(event: str, description: str) -> Set[str]:
    """ALL-CAPS short forms the user actually typed (never invented initials)."""
    stated: Set[str] = set()
    blob = f"{event} {description}"
    if event.strip().isupper() and 2 <= len(event.strip()) <= 6:
        stated.add(event.strip().upper())
    for tok in re.findall(r"[A-Za-z0-9]+", blob):
        if tok.isupper() and 2 <= len(tok) <= 6:
            stated.add(tok.upper())
    for _full, acro in extract_explicit_acronym_pairs(blob):
        stated.add(acro.upper())
    return stated


def collect_event_acronyms(
    event: str,
    description: str,
    organizations: List[str],
    about_phrases: List[str],
    *,
    user_description: Optional[str] = None,
) -> List[Dict[str, str]]:
    """
    Acronym policy (no invention):
    - Short forms: only what the user typed (ALL-CAPS tokens) or explicit pairs in *user* text
    - Full forms: only from explicit ``Full (ACRO)`` / ``ACRO (Full)`` in *user* text
    Never builds CJPA/CJPSN/etc. from phrase initials, and never invents expansions
    by matching org/clause initials to a user short.
    """
    by_acro: Dict[str, str] = {}
    user_desc = user_description if user_description is not None else description
    stated = _user_stated_acronyms(event, user_desc)

    # Explicit pairs from USER input only (ignore web corpus "Fake Name (CJPA)" noise)
    for full, acro in extract_explicit_acronym_pairs(f"{event} {user_desc}"):
        if not _is_usable_acronym_full(full):
            continue
        by_acro[acro] = full
        stated.add(acro)

    # Keep bare user-stated shorts with no invented expansion
    for short in stated:
        if short not in by_acro:
            by_acro[short] = ""

    return [{"full": full, "short": acro} for acro, full in by_acro.items()]


def is_marketing_or_listicle_scrap(phrase: str) -> bool:
    """
    Reject travel-SEO / listicle blurbs that ride on generic theme words:
    Looking Forward, Every September, Greatest Eco, Friendly Outdoor, etc.
    """
    if not phrase:
        return True
    words = [w.lower() for w in re.findall(r"[A-Za-z0-9]+", phrase)]
    if not words:
        return True
    lower = " ".join(words)
    if lower in JUNK_PHRASE_BLACKLIST:
        return True
    first, last = words[0], words[-1]
    months = {
        "january", "february", "march", "april", "may", "june",
        "july", "august", "september", "october", "november", "december",
    }
    # "Every September", "Looking Forward"
    if first == "every" and (last in months or len(words) <= 3):
        return True
    if first == "looking" and last in {"forward", "ahead", "back"}:
        return True
    # Ranking / hype openers on short phrases
    if first in MARKETING_OPENERS and len(words) <= 4:
        return True
    # Entirely weak theme tokens (no proper event anchor)
    if words and all(w in GENERIC_THEME_TOKENS | STOP_WORDS for w in words):
        return True
    # Superlative + generic noun: Greatest Eco, Best Outdoor Music
    if first in {"greatest", "best", "top", "ultimate", "finest", "biggest"} and len(words) <= 4:
        return True
    return False


def is_clickbait_headline_scrap(phrase: str) -> bool:
    """Reject sensational headline scraps: Meat Allegedly Thrown, Roadside Drama Exposed."""
    if not phrase:
        return True
    words = [w.lower() for w in re.findall(r"[A-Za-z0-9]+", phrase)]
    if not words:
        return True
    if any(w in CLICKBAIT_TOKENS for w in words):
        return True
    if words[0] in {"various", "several", "many", "some", "multiple"} and len(words) <= 3:
        return True
    if last := words[-1]:
        if last in {"exposed", "caught", "chaos", "drama", "row", "clash"}:
            return True
    return False


def is_incomplete_fragment(phrase: str) -> bool:
    """Reject mid-sentence scraps like 'Online Movement Became' or 'Forced Political'."""
    if not phrase:
        return True
    cleaned = re.sub(r"[^A-Za-z0-9\s\-]", " ", phrase).strip()
    words = cleaned.split()
    if not words:
        return True
    lower = cleaned.lower()
    if lower in JUNK_PHRASE_BLACKLIST:
        return True
    for junk in JUNK_PHRASE_BLACKLIST:
        if junk == lower or f" {junk} " in f" {lower} " or lower.endswith(" " + junk):
            return True
    if is_marketing_or_listicle_scrap(phrase) or is_clickbait_headline_scrap(phrase):
        return True
    last = words[-1].lower()
    first = words[0].lower()
    if last in FRAGMENT_TAIL_WORDS or last in COMMON_FINITE_VERBS:
        return True
    if first in COMMON_FINITE_VERBS:
        return True
    # Short Title-Case scraps that start with weak/generic openers
    if first in {
        "forced", "online", "facing", "leading", "featuring", "holding",
        "hour", "latest", "campaign", "combined", "nationwide", "protesters",
    } | MARKETING_OPENERS and len(words) <= 3:
        return True
    # Trailing filler like "… location"
    if last == "location":
        return True
    # Verb-ended mid-sentence noise
    if last in {"erupted", "gathered", "joined", "reported", "warned", "erupts"}:
        return True
    return False


def has_distinctive_event_signal(phrase: str, anchor: Dict[str, Any]) -> bool:
    """True if phrase shares a non-generic token with the user's event/location/description."""
    p_toks = set(tokenize(phrase)) - STOP_WORDS - GENERIC_THEME_TOKENS - GENERIC_LOCATION_TOKENS
    if not p_toks:
        return False
    event_toks = set(tokenize(anchor.get("event", ""))) - STOP_WORDS - GENERIC_THEME_TOKENS
    loc_toks = set(tokenize(anchor.get("location", ""))) - STOP_WORDS - GENERIC_THEME_TOKENS - GENERIC_LOCATION_TOKENS
    desc_toks = set(tokenize(anchor.get("description", ""))) - STOP_WORDS - GENERIC_THEME_TOKENS
    # Prefer proper event/location anchors; allow distinctive desc tokens (len>=5) only with 2 hits
    if p_toks & event_toks:
        return True
    if p_toks & loc_toks:
        return True
    desc_hit = p_toks & desc_toks
    if len(desc_hit) >= 2:
        return True
    if any(len(t) >= 6 for t in desc_hit):
        return True
    # User-stated acronyms
    for pair in anchor.get("acronym_pairs") or []:
        short = (pair.get("short") or "").lower()
        full_toks = set(tokenize(pair.get("full") or "")) - STOP_WORDS
        if short and short in {t.lower() for t in tokenize(phrase)}:
            return True
        if full_toks and (full_toks & p_toks):
            return True
    return False


def detect_user_state(user_location: str) -> str:
    """Return canonical state key for the user's location, or empty."""
    loc = (user_location or "").lower()
    for state in STATE_GEOGRAPHY:
        if state in loc:
            return state
    # Single-token state names
    for state in STATE_GEOGRAPHY:
        if any(tok == state or tok == state.replace(" ", "") for tok in tokenize(loc)):
            return state
    return ""


def is_location_in_user_scope(place: str, user_location: str) -> bool:
    """Keep places that belong to the user's stated geography; drop cross-region bleed."""
    if not place:
        return False
    place_l = place.lower().strip()
    place_n = normalize_term(_normalize_place_segment(place))
    user_l = (user_location or "").lower()

    # Always keep explicit user location segments (incl. near-typo matches)
    for seg in re.split(r"[,;/|]+", user_location or ""):
        seg = seg.strip().lower()
        if not seg:
            continue
        if seg in place_l or place_l in seg:
            return True
        seg_n = normalize_term(_normalize_place_segment(seg))
        if seg_n and place_n and (
            seg_n in place_n
            or place_n in seg_n
            or difflib.SequenceMatcher(None, seg_n, place_n).ratio() >= 0.82
        ):
            return True
    if any(t in place_l for t in tokenize(user_l) if len(t) > 2 and t not in GENERIC_LOCATION_TOKENS):
        return True

    user_state = detect_user_state(user_location)
    if not user_state:
        return True  # cannot judge — keep

    # Landmark mapped to another state → reject
    for landmark, region in LANDMARK_TO_REGION.items():
        if landmark in place_l and region != user_state:
            return False

    # Known city of another state → reject
    for state, cities in STATE_GEOGRAPHY.items():
        if state == user_state:
            continue
        if place_l == state or place_l in cities or any(c == place_l for c in cities):
            return False
        if state in place_l and state != user_state:
            return False

    # Allowed if in user's state city list or contains state name
    allowed = STATE_GEOGRAPHY.get(user_state, set())
    if place_l in allowed or user_state in place_l:
        return True
    if any(c in place_l for c in allowed):
        return True

    # Generic venue words without foreign-state signal — keep only if not a known foreign city
    return place_l not in {c for cs in STATE_GEOGRAPHY.values() for c in cs}


def extract_user_seed_facts(
    event: str, location: str, description: str
) -> Dict[str, Any]:
    """
    Pull acronyms, key people, and demand/about seeds from user input only.
    Pattern-based (no event-specific hardcoding) so facts reach hashtags/keywords
    even when web results are noisy.
    """
    text = f"{event}. {description}"
    acronyms: Dict[str, str] = {}
    for full, acro in extract_explicit_acronym_pairs(text):
        if _is_usable_acronym_full(full):
            acronyms[acro] = full

    for clause in _description_clauses(f"{event}. {description}"):
        m = re.match(r"^(.+?)\s*\(([A-Z]{2,6})\)\s*$", clause)
        if m:
            full = m.group(1).strip()
            if _is_usable_acronym_full(full):
                acronyms[m.group(2).upper()] = full

    people: List[str] = []
    # Generic role/title + person name (commissioner, minister, convenor, …)
    role_person = (
        r"(?:(?:Chief|Deputy|Joint|Additional|Principal)\s+)?"
        r"(?:[A-Z][a-z]+\s+){0,3}"
        r"(?:Commissioner|Minister|Secretary|President|Convenor|Convener|"
        r"Director|Chairperson|Spokesperson|Leader|Founder|CM|PM)\s+"
        r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})\b"
    )
    for m in re.finditer(role_person, text):
        cand = m.group(1).strip()
        if cand and not is_incomplete_fragment(cand):
            people.append(cand)

    # Capitalized person-like names in the event title
    title_noise = {
        "protest", "against", "chief", "election", "commissioner",
        "activity", "campaign", "movement", "meeting", "conference",
        "minister", "secretary", "president", "director", "convenor",
        "convener", "leader", "official", "party", "union", "forum",
    } | TITLES_AND_ROLES | ORGANIZATION_INDICATORS | LOCATION_INDICATORS | NON_PERSON_WORDS
    for m in re.finditer(r"\b([A-Z][a-z]+)\s+([A-Z][a-z]+)\b", event):
        cand = f"{m.group(1)} {m.group(2)}"
        words = {w.lower() for w in cand.split()}
        if words & title_noise:
            continue
        people.append(cand)

    demands: List[str] = []
    for m in re.finditer(
        r"(?:demanding|seeking|calling\s+for|pressed\s+for)\s+(?:the\s+)?"
        r"([a-zA-Z0-9\s,]{5,80}?)(?=[.;]|\sover\b|\sand\b|$)",
        description,
        re.I,
    ):
        for part in re.split(r",|\band\b", m.group(1).strip()):
            words = [
                w for w in re.findall(r"[A-Za-z0-9]+", part)
                if w.lower() not in STOP_WORDS and w.lower() not in COMMON_FINITE_VERBS
            ]
            if 2 <= len(words) <= 8:
                phrase = " ".join(words).lower()
                if not is_incomplete_fragment(phrase):
                    demands.append(phrase)

    about: List[str] = []
    for m in re.finditer(
        r"(?:over|regarding|about)\s+(?:concerns?\s+about\s+)?"
        r"([a-zA-Z0-9\s\(\)]{5,80}?)(?=[.;]|\sand\b|$)",
        description,
        re.I,
    ):
        chunk = m.group(1).strip()
        # Explicit pairs already harvested from full user text above — do not
        # re-admit noisy chunk pairs here.
        words = [
            w for w in re.findall(r"[A-Za-z0-9]+", chunk)
            if w.lower() not in STOP_WORDS and w.lower() not in {"concerns", "concern"}
        ]
        if 2 <= len(words) <= 8:
            phrase = " ".join(words)
            if not is_incomplete_fragment(phrase):
                about.append(phrase)

    return {
        "acronyms": [{"short": s, "full": f} for s, f in acronyms.items()],
        "people": list(dict.fromkeys(people)),
        "demands": list(dict.fromkeys(demands)),
        "about": list(dict.fromkeys(about)),
    }


GENERIC_LOCATION_TOKENS: Set[str] = {
    "india", "state", "city", "district", "road", "street", "police", "news",
    "today", "area", "hall", "centre", "center", "board", "circle", "square",
    "complex", "campus", "location",
}


def _norm_key(term: str) -> str:
    """Lightweight normalize for early helpers (before normalize_term)."""
    return re.sub(r"[^a-z0-9]+", "", (term or "").lower())


def is_anchor_compatible(phrase: str, anchor: Dict[str, Any], min_overlap: int = 1) -> bool:
    """
    Prefer entities that share substantive tokens with the user's event/location/description.
    Prevents unrelated same-acronym orgs (e.g. wrong expansion of a short event name).
    """
    if not phrase:
        return False
    p_tokens = set(tokenize(phrase)) - STOP_WORDS - GENERIC_LOCATION_TOKENS
    if not p_tokens:
        return False

    # User-defined acronym expansions always pass
    phrase_key = _norm_key(phrase)
    for pair in anchor.get("acronym_pairs", []):
        if phrase_key and phrase_key in {
            _norm_key(pair.get("full", "")),
            _norm_key(pair.get("short", "")),
        }:
            return True

    event_tokens = set(tokenize(anchor.get("event", ""))) - STOP_WORDS
    desc_tokens = set(tokenize(anchor.get("description", ""))) - STOP_WORDS
    loc_tokens = set(tokenize(anchor.get("location", ""))) - STOP_WORDS - GENERIC_LOCATION_TOKENS
    anchor_tokens = (anchor.get("tokens") or set()) - GENERIC_LOCATION_TOKENS

    # Strong: overlaps event or description content words
    if p_tokens & (event_tokens | desc_tokens):
        return True
    if p_tokens & loc_tokens:
        return True
    overlap = p_tokens & anchor_tokens
    return len(overlap) >= min_overlap


def is_strongly_event_relevant(phrase: str, anchor: Dict[str, Any]) -> bool:
    """
    Stricter gate for admitting web-derived tags/keywords into the UI.
    Requires event/description/acronym signal — location-only overlap is not enough.
    """
    if not phrase or is_incomplete_fragment(phrase):
        return False
    phrase_key = _norm_key(phrase)
    for pair in anchor.get("acronym_pairs", []):
        if phrase_key in {
            _norm_key(pair.get("full", "")),
            _norm_key(pair.get("short", "")),
        }:
            return True
        short = (pair.get("short") or "").lower()
        if short and short == phrase_key:
            return True

    p_tokens = set(tokenize(phrase)) - STOP_WORDS - GENERIC_LOCATION_TOKENS
    if not p_tokens:
        # Allow pure short acronyms already validated above
        return bool(re.fullmatch(r"[a-z]{2,6}", phrase_key or ""))

    event_tokens = set(tokenize(anchor.get("event", ""))) - STOP_WORDS - GENERIC_LOCATION_TOKENS
    desc_tokens = set(tokenize(anchor.get("description", ""))) - STOP_WORDS - GENERIC_LOCATION_TOKENS

    if p_tokens & event_tokens:
        return True
    # Need at least 2 description tokens, or 1 distinctive desc token (len>=5)
    desc_hit = p_tokens & desc_tokens
    if len(desc_hit) >= 2:
        return True
    if any(len(t) >= 5 for t in desc_hit):
        return True
    return False


def build_anchor_profile(event: str, location: str, description: str) -> Dict[str, Any]:
    """
    Build a semantic Ground Truth Anchor Profile from the user's explicit input.
    Used to vet external web content and prevent irrelevant topic collisions.
    """
    full_text = f"{event} {location} {description}".strip()
    tokens = {t for t in tokenize(full_text) if t not in STOP_WORDS and len(t) >= 2}

    # Seed acronym pairs from user input alone — never invent expansions from web/clauses
    seed_pairs = collect_event_acronyms(
        event, description, [], [], user_description=description
    )

    return {
        "full_text": full_text,
        "tokens": tokens,
        "event": event.strip(),
        "location": location.strip(),
        "description": description.strip(),
        "acronym_pairs": seed_pairs,
    }


def is_content_relevant(text: str, anchor: Dict[str, Any]) -> bool:
    """
    Evaluate whether a web page or sentence is semantically relevant to the user's event.
    Discards off-target acronym collisions and commercial / off-topic boilerplate.
    """
    t_lower = text.lower()
    u_lower = anchor["full_text"].lower()

    # Reject known collision / satire terms
    for col in KNOWN_COLLISION_PATTERNS:
        if col in t_lower and col not in u_lower:
            return False

    # If user defined a short-form expansion, reject alternate expansions of that acronym
    for pair in anchor.get("acronym_pairs", []):
        short = (pair.get("short") or "").lower()
        full = (pair.get("full") or "").lower()
        if not short or not full:
            continue
        if short in t_lower or re.search(rf"\b{re.escape(short)}\b", t_lower, re.I):
            # Page mentions the short form but not the user's full form,
            # and looks like a different expansion → reject
            if full not in t_lower:
                # Heuristic: another Title Case expansion near the acronym
                other = re.search(
                    rf"\b{re.escape(short)}\b\s*\(([A-Za-z][A-Za-z0-9 ]{{3,60}})\)",
                    text,
                    re.I,
                )
                if other and _norm_key(other.group(1)) != _norm_key(full):
                    return False
                # Short form present but none of the user's full-form tokens → likely wrong sense
                full_tokens = set(tokenize(full)) - STOP_WORDS
                if full_tokens and not (full_tokens & set(tokenize(t_lower))):
                    # Allow only if page also carries other strong event/location anchors
                    loc_toks = set(tokenize(anchor.get("location", ""))) - STOP_WORDS - GENERIC_LOCATION_TOKENS
                    evt_toks = set(tokenize(anchor.get("event", ""))) - STOP_WORDS - {short}
                    if not ((loc_toks | evt_toks) & set(tokenize(t_lower))):
                        return False

    # Discard obvious off-topic commercial / spam pages
    if any(bp in t_lower for bp in [
        "insurance quotes", "business insurance", "hockey association",
        "sports betting", "casino", "credit card", "personal loan"
    ]):
        return False

    t_tokens = set(tokenize(t_lower))
    event_tokens = set(tokenize(anchor.get("event", ""))) - STOP_WORDS - GENERIC_LOCATION_TOKENS
    desc_tokens = set(tokenize(anchor.get("description", ""))) - STOP_WORDS - GENERIC_LOCATION_TOKENS
    loc_tokens = set(tokenize(anchor.get("location", ""))) - STOP_WORDS - GENERIC_LOCATION_TOKENS
    anchor_tokens = anchor.get("tokens", set())

    # Prefer pages that match user-defined full forms / description orgs
    for pair in anchor.get("acronym_pairs", []):
        full_tokens = set(tokenize(pair.get("full", ""))) - STOP_WORDS
        if full_tokens and len(full_tokens & t_tokens) >= max(1, len(full_tokens) - 1):
            return True

    # Strong path: event tokens present
    event_hit = t_tokens.intersection(event_tokens)
    desc_hit = t_tokens.intersection(desc_tokens)
    loc_hit = t_tokens.intersection(loc_tokens)

    if event_hit:
        # Prefer pages that also mention location when user gave one
        if loc_tokens and not loc_hit:
            # Still allow if description overlap is strong (same event, different city coverage)
            if len(desc_hit) >= 2 or len(event_hit) >= 2:
                return True
            return False
        return True

    # No event tokens: require stronger description + location co-occurrence
    if len(desc_hit) >= 3 and (not loc_tokens or loc_hit):
        return True
    if len(desc_hit) >= 2 and loc_hit:
        return True

    substantive_anchor = anchor_tokens - GENERIC_LOCATION_TOKENS
    overlap = t_tokens.intersection(substantive_anchor)
    if len(overlap) >= 3 and (not loc_tokens or loc_hit):
        return True

    return False



def to_hashtag(phrase: str) -> str:
    """
    Deterministically convert a phrase into a clean CamelCase hashtag.
    Strictly eliminates spaces, commas, and punctuation, preserving valid acronyms.
    Caps length at 25 characters without truncating mid-word.
    """
    if not phrase:
        return ""

    cleaned = re.sub(r"['’]s\b", "s", phrase)
    words = re.findall(r"[A-Za-z0-9]+", cleaned)
    if not words:
        return ""

    camel_parts = []
    for word in words:
        w_lower = word.lower()
        if w_lower in {"and", "for", "of", "the", "in", "to", "at", "on", "a", "an"} and len(words) > 2:
            continue
        if w_lower in KNOWN_ACRONYMS or (word.isupper() and 2 <= len(word) <= 5):
            camel_parts.append(word.upper())
        else:
            camel_parts.append(word.capitalize())

    camel = "".join(camel_parts)
    if not camel:
        camel = "".join(word.capitalize() for word in words)

    camel = re.sub(r"[^A-Za-z0-9]", "", camel)
    if not camel:
        return ""

    # Truncate overly long compounds gracefully up to 25 alphanumeric characters
    if len(camel) > 25:
        acc = ""
        for p in camel_parts:
            if len(acc + p) <= 25:
                acc += p
            else:
                break
        camel = acc if len(acc) >= 3 else camel[:25]

    return f"#{camel}"


def _is_invented_acronym_hashtag(body: str, allowed_shorts: Set[str], location: str = "") -> bool:
    """
    True for lookalike invented tags like #CJPA / #CJPSN / #CJPSNOdisha
    when the user only stated #CJP.
    """
    raw = re.sub(r"[^A-Za-z0-9]", "", body or "")
    if not raw:
        return False
    upper = raw.upper()
    allowed = {s.upper() for s in allowed_shorts if s}
    if upper in allowed:
        return False

    # Strip trailing location / region from compound tags (#CJPOdisha is OK if CJP allowed)
    loc_compact = re.sub(r"[^A-Za-z0-9]", "", location or "").upper()
    rest = upper
    if loc_compact and upper.endswith(loc_compact) and len(upper) > len(loc_compact):
        rest = upper[: -len(loc_compact)]
        if rest in allowed:
            return False
    # Also strip common state/city tokens glued on
    for place in list(STATE_GEOGRAPHY.keys()) + [
        c for cities in STATE_GEOGRAPHY.values() for c in cities
    ]:
        p = place.replace(" ", "").upper()
        if len(p) >= 4 and upper.endswith(p) and len(upper) > len(p):
            head = upper[: -len(p)]
            if head in allowed:
                return False
            rest = head
            break

    # Compact ALL-CAPS (or mostly caps) body that extends a known short → invented variant
    if not re.fullmatch(r"[A-Za-z]{2,10}", rest):
        return False
    if not rest.isupper() and not re.fullmatch(r"[A-Z]{2,10}", rest):
        # Mixed CamelCase phrases are handled elsewhere
        if any(ch.islower() for ch in raw):
            return False
    for short in allowed:
        if len(short) < 2:
            continue
        if rest != short and rest.startswith(short) and len(rest) <= len(short) + 4:
            return True
        # Near-miss same family: CJPA vs CJP (prefix 3+)
        if len(short) >= 3 and rest.startswith(short[:3]) and rest != short and len(rest) <= 8:
            return True
    return False


def is_valid_hashtag(tag: str, anchor: Dict[str, Any]) -> bool:
    """Validate a hashtag against structural and relevance rules."""
    if not tag or not tag.startswith("#"):
        return False
    body = tag[1:]
    if not (3 <= len(body) <= 25) or not body.isalnum():
        return False

    body_lower = body.lower()
    user_lower = anchor["full_text"].lower()

    # Reject known collision terms
    for col in KNOWN_COLLISION_PATTERNS:
        if col.replace(" ", "") in body_lower and col not in user_lower:
            return False

    # Disallow month noise suffixes (#JudicialPerformanceSep -> Sep)
    for month in ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]:
        if body_lower.endswith(month) and len(body_lower) > len(month) + 2:
            return False

    # Disallow imperative action verb prefixes (#AddressOdishaEducation)
    for prefix in ["address", "join", "joins", "support", "demand", "demands", "meet", "report"]:
        if body_lower.startswith(prefix) and len(body_lower) > len(prefix) + 2:
            return False

    # Disallow web boilerplate and commercial spam
    if is_web_boilerplate(body_lower):
        return False

    # Block invented acronym variants (#CJPA when user only has CJP)
    stated = _user_stated_acronyms(anchor.get("event", ""), anchor.get("description", ""))
    if _is_invented_acronym_hashtag(body, stated, anchor.get("location", "")):
        return False

    return True


def normalize_term(term: str) -> str:
    """Normalize term for comparison: strip hashtags, punctuation, and lowercase."""
    if not term:
        return ""
    cleaned = re.sub(r"[^A-Za-z0-9\s]", "", term.lstrip("#")).strip().lower()
    return cleaned


def phrase_tokens(phrase: str) -> List[str]:
    """Tokenize a keyword or hashtag body (splits CamelCase hashtag bodies)."""
    if not phrase:
        return []
    body = phrase.lstrip("#").strip()
    # Split CamelCase / acronym boundaries: GyaneshKumar -> Gyanesh Kumar, SIRMaharashtra -> SIR Maharashtra
    body = re.sub(r"([a-z])([A-Z])", r"\1 \2", body)
    body = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", body)
    return [t for t in normalize_term(body).split() if t]


def is_allowed_singleton(phrase: str, allowed: Set[str]) -> bool:
    """True for intentional short forms (acronyms, primary region) only."""
    toks = phrase_tokens(phrase)
    if len(toks) != 1:
        return False
    t = toks[0]
    if t in allowed:
        return True
    # Compact acronym body e.g. CJP, SIR
    raw = re.sub(r"[^A-Za-z0-9]", "", phrase.lstrip("#"))
    return bool(re.fullmatch(r"[A-Za-z]{2,6}", raw)) and raw.lower() in allowed


def is_subphrase_of(shorter: str, longer: str) -> bool:
    """True if shorter's tokens are a proper subset of longer's tokens."""
    a, b = phrase_tokens(shorter), phrase_tokens(longer)
    if not a or not b or len(a) >= len(b):
        return False
    return set(a).issubset(set(b))


def is_name_or_org_fragment(
    phrase: str,
    known_entities: List[str],
    *,
    allowed_singletons: Optional[Set[str]] = None,
) -> bool:
    """
    Reject scrap pieces of fuller entities:
    - 'cockroach' / 'party' when 'Cockroach Janta Party' exists
    - 'gyanesh' / 'kumar' when 'Gyanesh Kumar' exists
    - 'chief' when 'Chief Election Commissioner' exists
    """
    allowed = allowed_singletons or set()
    toks = phrase_tokens(phrase)
    if not toks:
        return True

    if len(toks) == 1:
        if is_allowed_singleton(phrase, allowed):
            return False
        if toks[0] in ENTITY_GLUE_SINGLETONS or toks[0] in STOP_WORDS:
            return True
        for ent in known_entities:
            et = phrase_tokens(ent)
            if len(et) >= 2 and toks[0] in et:
                return True
        # Lone person-like tokens with no acronym/region allowance
        return True

    # Multi-word proper subset of a longer known entity
    for ent in known_entities:
        if is_subphrase_of(phrase, ent):
            return True
    return False


def prefer_full_phrases(
    items: List[str],
    *,
    allowed_singletons: Optional[Set[str]] = None,
) -> List[str]:
    """Drop items that are token-subphrases of another kept item; prefer fuller forms."""
    allowed = allowed_singletons or set()
    kept: List[str] = []
    for item in items:
        if is_allowed_singleton(item, allowed):
            kept.append(item)
            continue
        if is_name_or_org_fragment(item, items, allowed_singletons=allowed):
            continue
        # Drop if any other item is a longer superphrase (keep acronyms separately)
        drop = False
        for other in items:
            if other is item or normalize_term(other) == normalize_term(item):
                continue
            if is_subphrase_of(item, other):
                drop = True
                break
        if not drop:
            kept.append(item)
    # De-dupe preserving order
    out: List[str] = []
    seen: Set[str] = set()
    for k in kept:
        n = normalize_term(k)
        if n and n not in seen:
            out.append(k)
            seen.add(n)
    return out


def normalize_transliteration(text: str) -> str:
    """Normalize common phonetic transliteration variants (Indic / South Asian names)."""
    s = text.lower()
    s = re.sub(r"bh\b", "v", s)
    s = re.sub(r"\bnab", "nav", s)
    s = re.sub(r"ee", "i", s)
    s = re.sub(r"oo", "u", s)
    s = re.sub(r"sh", "s", s)
    return s


def are_fuzzy_duplicates(phrase1: str, phrase2: str) -> bool:
    """Check if two phrases are exact duplicates or transliteration/token variants."""
    w1, w2 = phrase1.strip().lower(), phrase2.strip().lower()
    if w1 == w2:
        return True

    t1 = {w for w in w1.split() if w not in {"in", "of", "for", "and", "the"}}
    t2 = {w for w in w2.split() if w not in {"in", "of", "for", "and", "the"}}
    if t1 and t1 == t2:
        return True

    if normalize_transliteration(w1) == normalize_transliteration(w2):
        return True

    if abs(len(w1) - len(w2)) <= 3 and len(w1) >= 6:
        if difflib.SequenceMatcher(None, w1, w2).ratio() >= 0.84:
            return True

    return False


def _normalize_place_segment(seg: str) -> str:
    """
    Clean a location segment for tags.
    Merges possessives so \"People's Plaza\" -> \"Peoples Plaza\"
    (avoids broken #PeopleSPlaza / #EopleSPlaza from a stray 's' token).
    """
    if not seg:
        return ""
    # People's / Peoples' -> Peoples
    text = re.sub(r"['’]s\b", "s", seg)
    text = re.sub(r"['’]", "", text)
    words = re.findall(r"[A-Za-z0-9]+", text)
    return " ".join(words)


def reconcile_place_name(user_place: str, candidates: List[str]) -> str:
    """
    Prefer a corpus/canonical place name when the user string is a near typo
    (e.g. 'eoples Plaza' / 'Eople s Plaza' -> 'People's Plaza' from web).
    """
    if not user_place:
        return user_place
    u = normalize_term(_normalize_place_segment(user_place))
    if not u or len(u) < 4:
        return user_place

    best = user_place
    best_score = 0.0
    for cand in candidates:
        if not cand:
            continue
        c_raw = cand.strip()
        c = normalize_term(_normalize_place_segment(c_raw))
        if not c or len(c) < 4:
            continue
        # Skip the typo itself / identical normalized form — look for a better spelling
        if c == u:
            continue
        ratio = difflib.SequenceMatcher(None, u, c).ratio()
        # Missing/extra first letter: eoples plaza vs peoples plaza
        if abs(len(u) - len(c)) == 1:
            shorter, longer = (u, c) if len(u) < len(c) else (c, u)
            if longer.endswith(shorter) or longer.startswith(shorter):
                ratio = max(ratio, 0.93)
            if longer[1:] == shorter or longer[:-1] == shorter:
                ratio = max(ratio, 0.93)
        if ratio > best_score:
            best_score = ratio
            best = c_raw

    if best_score >= 0.82:
        return best
    return user_place


def parse_location(location_str: str) -> Dict[str, Any]:
    """Parse location string into individual segments, primary region, and hashtags."""
    if not location_str or not location_str.strip():
        return {"parts": [], "primary_region": "", "hashtags": []}

    raw_segments = [s.strip() for s in re.split(r"[,;/|]+", location_str) if s.strip()]
    parts: List[str] = []
    location_hashtags: List[str] = []

    ROAD_WORDS = {
        "road", "rd", "street", "st", "lane", "avenue", "ave", "marg", "chowk",
        "circle", "square", "bypass", "nagar", "sector", "plaza",
    }
    VENUE_WORDS = {"plaza", "park", "garden", "maidan", "stadium", "ground", "hall"}

    for seg in raw_segments:
        cleaned_seg = _normalize_place_segment(seg)
        words = cleaned_seg.split()
        if not words:
            continue
        parts.append(cleaned_seg)

        tag = to_hashtag(cleaned_seg)
        if tag and tag not in location_hashtags:
            location_hashtags.append(tag)

        if len(words) > 1 and words[-1].lower() in ROAD_WORDS:
            landmark_words = words[:-1]
            landmark_tag = to_hashtag(" ".join(landmark_words))
            if landmark_tag and landmark_tag not in location_hashtags:
                location_hashtags.append(landmark_tag)

    # Prefer a city/state as primary region — not a venue/plaza typo
    primary_region = ""
    for p in reversed(parts):  # city often last: "... Hyderabad"
        lower = p.lower()
        pwords = lower.split()
        if any(w in VENUE_WORDS or w in ROAD_WORDS for w in pwords):
            continue
        if lower in STATE_GEOGRAPHY or any(
            lower == c or c in lower for cities in STATE_GEOGRAPHY.values() for c in cities
        ):
            primary_region = p
            break
        if not primary_region:
            primary_region = p
    if not primary_region and parts:
        primary_region = parts[-1]

    return {
        "parts": parts,
        "primary_region": primary_region,
        "hashtags": location_hashtags,
    }


def repair_location_info(
    loc_info: Dict[str, Any],
    venues: List[str],
    locs: List[str],
    corpus: str = "",
) -> Dict[str, Any]:
    """Rewrite typo'd user location parts using near-matching corpus venues."""
    candidates: List[str] = list(dict.fromkeys(list(venues) + list(locs)))
    # Pull Title-Case multi-word places from corpus (e.g. People's Plaza)
    _pw = r"[A-Z][A-Za-z0-9]*(?:['’]s)?"
    _ps = r"(?:Plaza|Park|Road|Street|Maidan|Garden|Hall|Stadium|Marg|Chowk)"
    for m in re.finditer(rf"\b((?:{_pw}(?:\s+{_pw}){{0,3}}\s+{_ps}))\b", corpus or ""):
        candidates.append(m.group(1).strip())

    repaired_parts: List[str] = []
    for part in loc_info.get("parts") or []:
        repaired_parts.append(reconcile_place_name(part, candidates))

    primary = loc_info.get("primary_region") or ""
    if primary:
        primary = reconcile_place_name(primary, candidates)
        # If primary still looks like a venue, prefer a city-like part
        p_l = primary.lower()
        if any(w in p_l for w in ("plaza", "park", "road", "street", "maidan")):
            for p in reversed(repaired_parts):
                if not any(w in p.lower() for w in ("plaza", "park", "road", "street", "maidan")):
                    primary = p
                    break

    hashtags: List[str] = []
    for p in repaired_parts:
        tag = to_hashtag(p)
        if tag and tag not in hashtags:
            hashtags.append(tag)

    return {
        "parts": repaired_parts,
        "primary_region": primary,
        "hashtags": hashtags,
    }


def looks_like_place_or_scheme(name: str) -> bool:
    """True if a capitalized phrase is a venue/city/landmark/scheme, not a person."""
    if not name:
        return True
    n = name.lower().strip()
    words = set(n.split())
    if words & LOCATION_INDICATORS:
        return True
    if words & {
        "revision", "scheme", "mission", "yojana", "park", "maidan", "road",
        "marg", "chowk", "campus", "college", "university", "temple", "border",
        "plaza", "stadium", "hall", "intensive", "special", "electoral",
    }:
        return True
    for landmark in LANDMARK_TO_REGION:
        if landmark in n:
            return True
    for cities in STATE_GEOGRAPHY.values():
        if n in cities:
            return True
        for c in cities:
            if len(c) >= 5 and c in n:
                return True
    for state in STATE_GEOGRAPHY:
        if state in n:
            return True
    return False


def strip_person_name_noise(phrase: str) -> str:
    """Drop headline tails: 'Revanth Reddy Speech' / 'Revanth Reddy Full' -> 'Revanth Reddy'."""
    if not phrase:
        return ""
    words = phrase.strip().split()
    while words and words[-1].lower().rstrip(".,;:") in PERSON_NAME_TRAILING_NOISE:
        words = words[:-1]
    while words and words[0].lower().rstrip(".,;:") in TITLES_AND_ROLES | {"honble", "honourable", "honorable", "sri"}:
        words = words[1:]
    return " ".join(words)


def _clean_person_name(full: str) -> Optional[str]:
    """Return a cleaned plausible person name, or None."""
    if not full or is_web_boilerplate(full) or is_incomplete_fragment(full):
        return None
    full = strip_person_name_noise(full)
    if looks_like_place_or_scheme(full):
        return None
    words = full.split()
    role_prefixes = {
        "participant", "participants", "leader", "leaders", "activist",
        "spokesperson", "organizer", "organiser", "member", "members",
        "farmer", "farmers", "student", "students", "commissioner",
        "minister", "chief", "election",
    }
    while words and words[0].lower() in role_prefixes:
        words = words[1:]
    # Strip trailing noise again after role trim
    while words and words[-1].lower() in PERSON_NAME_TRAILING_NOISE | NON_PERSON_WORDS:
        words = words[:-1]
    if not (2 <= len(words) <= 4):
        return None
    for w in words:
        lw = w.lower()
        if (
            lw in COMMON_FINITE_VERBS
            or lw in STOP_WORDS
            or lw in NON_PERSON_WORDS
            or lw in LOCATION_INDICATORS
            or lw in ORGANIZATION_INDICATORS
            or lw in FRAGMENT_TAIL_WORDS
            or lw in role_prefixes
            or lw in TITLES_AND_ROLES
            or lw in PERSON_NAME_TRAILING_NOISE
        ):
            return None
    l1 = words[0].lower()
    if l1 in {
        "high", "supreme", "class", "district", "central", "state", "national",
        "public", "school", "social", "rural", "urban", "sentenced", "civil",
        "digital", "emerging", "student", "online", "forced", "human",
        "shambhu", "border", "main", "special", "intensive",
    }:
        return None
    if words[-1].lower() in {
        "according", "reports", "stated", "unites", "reveals", "indoor",
        "ground", "lane", "border", "road", "campus", "university", "college",
        "park", "mantar", "revision",
    } | PERSON_NAME_TRAILING_NOISE:
        return None
    return " ".join(words)


def phrase_to_matching_hashtag(phrase: str) -> str:
    """Convert a keyword phrase into the matching hashtag (1:1 pairing)."""
    if not phrase:
        return ""
    p = phrase.strip()
    if re.fullmatch(r"[A-Za-z]{2,6}", p):
        return f"#{p.upper()}"
    # Prefer full name body over trailing (ACRO)
    p2 = re.sub(r"\s*\([A-Z]{2,6}\)\s*$", "", p).strip()
    return to_hashtag(p2 or p)


def extract_people(text: str) -> List[str]:
    """Identify individual leaders, convenors, officials, and key figures."""
    people: List[str] = []

    # 0. Role / agency patterns: "led by X", "organized by X", "addressed by X"
    p_agency = (
        r"\b(?:led|organised|organized|spearheaded|convened|addressed|inaugurated|"
        r"headed|chaired|founded|started)\s+by\s+"
        r"(?:Shri|Smt|Dr|Prof|Mr|Mrs|Ms\.?)?\s*"
        r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})\b"
    )
    for m in re.finditer(p_agency, text, re.IGNORECASE):
        cand = m.group(1).strip()
        cand = " ".join(w[:1].upper() + w[1:] for w in cand.split())
        cleaned = _clean_person_name(cand)
        if cleaned:
            people.append(cleaned)

    # 1. Title/Role + Person Name
    p_title = (
        r"\b(?:Shri|Smt|Dr|Prof|Mr|Mrs|Ms|Convenor|Convener|Leader|Minister|PM|CM|"
        r"President|Secretary|Director|Activist|Spokesperson|Advocate|Organiser|"
        r"Organizer|Chief|Chairperson|Coordinator|Founder)\s+"
        r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})\b"
    )
    for m in re.finditer(p_title, text):
        cleaned = _clean_person_name(m.group(1).strip())
        if cleaned:
            people.append(cleaned)

    # 2. Standalone Capitalized Names of Individuals
    p_name = r"\b([A-Z][a-z]+)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b"
    for m in re.finditer(p_name, text):
        cleaned = _clean_person_name(m.group(0).strip())
        if cleaned:
            people.append(cleaned)

    return people


def classify_people_roles(people: List[str], text: str) -> Tuple[List[str], List[str]]:
    """
    Split people into main_leaders vs other participating figures using nearby role cues.
    """
    leaders: List[str] = []
    participants: List[str] = []
    t_lower = text.lower()
    leader_cues = (
        "led by", "convenor", "convener", "founder", "president", "chief",
        "minister", "cm ", "pm ", "organised by", "organized by", "spearheaded",
        "chairperson", "coordinator", "main leader", "key leader",
    )

    for person in people:
        p_lower = person.lower()
        idx = t_lower.find(p_lower)
        window = t_lower[max(0, idx - 40): idx + len(p_lower) + 40] if idx >= 0 else ""
        if any(cue in window for cue in leader_cues) or any(cue in t_lower and p_lower in t_lower for cue in ("led by " + p_lower, "convenor " + p_lower)):
            leaders.append(person)
        else:
            participants.append(person)

    # If no cue-based leaders, treat top unique people as leaders/participants split
    if not leaders and people:
        uniq = list(dict.fromkeys(people))
        leaders = uniq[:2]
        participants = uniq[2:]
    else:
        # Keep participants free of leaders
        lead_set = {normalize_term(x) for x in leaders}
        participants = [p for p in participants if normalize_term(p) not in lead_set]

    return list(dict.fromkeys(leaders)), list(dict.fromkeys(participants))


def clean_org_phrase(phrase: str) -> str:
    """Clean organization candidate phrase by removing leading verbs, articles, and prepositions."""
    if is_web_boilerplate(phrase):
        return ""
    phrase = phrase.strip()
    words = phrase.split()
    while words and (words[0].lower() in COMMON_FINITE_VERBS or words[0].lower() in STOP_WORDS or words[0].lower() in {"join", "joins", "boost", "boosts", "held", "staged"}):
        words = words[1:]
    while words and (words[-1].lower() in COMMON_FINITE_VERBS or words[-1].lower() in STOP_WORDS):
        words = words[:-1]
    if len(words) >= 1:
        res = " ".join(words)
        if is_web_boilerplate(res):
            return ""
        return res
    return ""


def extract_organizations(text: str, anchor: Optional[Dict[str, Any]] = None) -> List[str]:
    """Identify organizations, committees, student bodies, departments, NGOs."""
    orgs: List[str] = []
    anchor = anchor or {}

    # Seed with user-defined full forms (always keep)
    for pair in anchor.get("acronym_pairs", []):
        full = (pair.get("full") or "").strip()
        short = (pair.get("short") or "").strip()
        if full and len(full.split()) >= 2:
            orgs.append(full)
        if short and re.fullmatch(r"[A-Z]{2,6}", short.upper()):
            orgs.append(short.upper())

    # 1. Multi-word title-cased phrases containing organizational indicators
    pattern = r"\b[A-Z][a-zA-Z0-9]+(?:\s+(?:for|of|and|the|in)\s+[A-Z][a-zA-Z0-9]+|\s+[A-Z][a-zA-Z0-9]+){1,5}\b"
    for m in re.finditer(pattern, text):
        raw_phrase = m.group().strip()
        phrase = clean_org_phrase(raw_phrase)
        if not phrase or is_incomplete_fragment(phrase):
            continue
        # Reject runaway concatenations (event+location+description mashed together)
        if len(phrase.split()) > 6:
            continue

        if " and " in phrase:
            left, right = phrase.split(" and ", 1)
            left_clean = clean_org_phrase(left)
            right_clean = clean_org_phrase(right)
            left_words = set(left_clean.lower().split())
            right_words = set(right_clean.lower().split())
            if (left_words & ORGANIZATION_INDICATORS) and (right_words & ORGANIZATION_INDICATORS):
                orgs.append(left_clean)
                orgs.append(right_clean)
                continue

        words = phrase.lower().split()
        if any(w in ORGANIZATION_INDICATORS for w in words):
            orgs.append(phrase)

    # 2. Ministry / Department
    p_min = r"\b(?:Ministry|Department)\s+of\s+[A-Z][a-z]+(?:\s+(?:and|for|the)\s+[A-Z][a-z]+|\s+[A-Z][a-z]+){0,3}\b"
    for m in re.finditer(p_min, text):
        clean_m = clean_org_phrase(m.group())
        if clean_m and not is_incomplete_fragment(clean_m):
            orgs.append(clean_m)

    # 3. Capitalized entity ending with an organization indicator
    p_org_ind = (
        r"\b[A-Z][a-zA-Z0-9]+(?:\s+[A-Z][a-zA-Z0-9]+){0,3}\s+"
        r"(?:Division|Police|Sangathan|Morcha|Union|Party|Trust|Foundation|"
        r"Council|Commission|Board|Authority|Bureau|Force|Agency|Society|Federation|Front)\b"
    )
    for m in re.finditer(p_org_ind, text):
        clean_o = clean_org_phrase(m.group())
        if clean_o and clean_o.lower() not in {"the division", "division", "the group", "the committee"}:
            if not is_incomplete_fragment(clean_o):
                orgs.append(clean_o)

    # 4. Known / user acronyms only (do not invent random ALLCAPS noise)
    known_acros = set(KNOWN_ACRONYMS)
    for pair in anchor.get("acronym_pairs", []):
        known_acros.add((pair.get("short") or "").lower())
    for m in re.finditer(r"\b[A-Z]{2,6}\b", text):
        acr = m.group()
        if acr.lower() in known_acros:
            orgs.append(acr)

    filtered: List[str] = []
    for o in orgs:
        if o.lower() in {"the division", "division", "the group", "the committee"}:
            continue
        if is_incomplete_fragment(o):
            continue
        # Drop social-handle style "… Official" noise
        if o.lower().endswith(" official") or o.lower().endswith(" official page"):
            continue

        drop = False
        o_norm = _norm_key(o)
        for pair in anchor.get("acronym_pairs", []):
            short = (pair.get("short") or "").upper()
            full = pair.get("full") or ""
            if not short or not full:
                continue
            if o.upper() == short or o_norm == _norm_key(full):
                continue
            # Same short-form initials as a user-defined expansion, but different full name → reject
            gen = phrase_to_acronym(o)
            if gen == short and o_norm != _norm_key(full):
                drop = True
                break
            # Multi-word org that does not share tokens with the user's expansion for that short form
            if len(o.split()) >= 3:
                full_toks = set(tokenize(full)) - STOP_WORDS
                org_toks = set(tokenize(o)) - STOP_WORDS
                if full_toks and not (full_toks & org_toks) and short.lower() in o.lower():
                    drop = True
                    break
        if drop:
            continue
        if anchor and not is_anchor_compatible(o, anchor) and o.upper() not in {
            (p.get("short") or "").upper() for p in anchor.get("acronym_pairs", [])
        }:
            if not (set(tokenize(o)) & (set(tokenize(anchor.get("description", ""))) | set(tokenize(anchor.get("event", ""))))):
                continue
        filtered.append(o)

    return filtered


def extract_locations(text: str, user_location: str) -> Tuple[List[str], List[str]]:
    """
    Identify locations and venues.
    Returns (all_locations, venues_specific).
    """
    locs: List[str] = []
    venues: List[str] = []

    segs = [s.strip() for s in re.split(r"[,;/|]+", user_location) if s.strip()]
    for s in segs:
        clean_s = _normalize_place_segment(s)
        if clean_s and clean_s.lower() not in STOP_WORDS:
            locs.append(clean_s)

    # Allow possessives: People's Plaza, St. Mary's Road
    _place_word = r"[A-Z][A-Za-z0-9]*(?:['’]s)?"
    _place_suffix = (
        r"(?:Road|Marg|Chowk|Circle|Square|Nagar|Sector|Hills|Convention|Center|Centre|"
        r"Auditorium|Stadium|Campus|Assembly|College|University|School|Maidan|Gate|"
        r"Ground|Hall|Complex|Border|Plaza|Temple|Park)"
    )
    venue_pattern = rf"\b(?:{_place_word}(?:\s+{_place_word}){{0,4}}\s+{_place_suffix})\b"
    for m in re.finditer(venue_pattern, text):
        v = m.group().strip()
        if not is_incomplete_fragment(v):
            venues.append(v)
            locs.append(v)

    # "held at / outside / near X"
    for m in re.finditer(
        rf"\b(?:held\s+at|held\s+in|outside|near|at)\s+"
        rf"({_place_word}(?:\s+{_place_word}){{0,4}}"
        rf"(?:\s+{_place_suffix})?)",
        text,
    ):
        v = m.group(1).strip()
        if len(v) >= 4 and not is_incomplete_fragment(v) and v.lower() not in STOP_WORDS:
            venues.append(v)
            locs.append(v)

    KNOWN_CITIES = {
        "bhubaneswar", "cuttack", "puri", "delhi", "new delhi", "noida", "gurugram",
        "hyderabad", "secunderabad", "ahmedabad", "gandhinagar", "vadodara", "surat",
        "mumbai", "pune", "bengaluru", "chennai", "kolkata", "chandigarh", "jaipur",
        "srinagar", "shimla", "lucknow", "patna", "ranchi", "guwahati", "raipur",
    }
    for city in KNOWN_CITIES:
        if re.search(rf"\b{city}\b", text, re.IGNORECASE):
            locs.append(city.title())

    return locs, venues


def clean_concept_phrase(phrase: str) -> str:
    """Clean a candidate concept phrase by removing prepositional tails, punctuation, and verbs."""
    if is_web_boilerplate(phrase):
        return ""
    phrase = phrase.strip()
    phrase = re.sub(r"['’]s\b", "", phrase)
    phrase = re.sub(r"[.,;!?]+$", "", phrase)
    # Strip prepositional tails like 'in Odisha', 'regarding historical facts', 'across the state'
    phrase = re.sub(r"\b(?:in|at|across|along|regarding|concerning|amid)\s+[A-Za-z0-9\s]+$", "", phrase, flags=re.IGNORECASE)
    phrase = re.sub(r"[.,;!?]+$", "", phrase)
    words = phrase.strip().lower().split()
    while words and (words[0] in STOP_WORDS or words[0] in COMMON_FINITE_VERBS):
        words = words[1:]
    while words and (words[-1] in STOP_WORDS or words[-1] in COMMON_FINITE_VERBS):
        words = words[:-1]
    if len(words) >= 1:
        res = " ".join(words)
        if is_web_boilerplate(res):
            return ""
        return res
    return ""


def extract_demands_and_issues(text: str, anchor: Dict[str, Any]) -> Tuple[List[str], List[str]]:
    """
    Identify demands/goals and 'what it is about' topics.
    Returns (demands, about_topics).
    """
    demands: List[str] = []
    about: List[str] = []

    demand_triggers = [
        r"(?:protests?|protesting|demonstrations?|rallies|rally)\s+(?:over|against|on|regarding|for)\s+([a-zA-Z0-9\s,]{3,70}?)(?=[.;]|\s+(?:in|at|by|from|outside|across|after|amid)\s+[A-Z]|$)",
        r"(?:demands?|demanded|demanding|urged|urging|seeking|calling\s+for|pressed\s+for|pressing\s+for)\s+(?:immediate\s+)?([a-zA-Z0-9\s,]{3,70}?)(?=[.;]|\s+(?:in|at|by|from)\s+[A-Z]|$)",
        r"(?:aims?\s+to|aimed\s+at|goal(?:s)?\s+(?:of|is|are)|objective(?:s)?\s+(?:of|is|are))\s+([a-zA-Z0-9\s,]{3,70}?)(?=[.;]|\s+(?:in|at|by|from)\s+[A-Z]|$)",
        r"(?:controversy|backlash|concerns?|dispute)\s+(?:over|regarding|surrounding|after)\s+([a-zA-Z0-9\s,]{3,70}?)(?=[.;]|\s+(?:in|at|by|from)\s+[A-Z]|$)",
        r"(?:correction|revision|resignation|withdrawal|repeal|implementation)\s+of\s+([a-zA-Z0-9\s,]{3,55}?)(?=[.;]|\s+(?:in|at|by|from)\s+[A-Z]|$)",
    ]
    about_triggers = [
        r"(?:covering|focused\s+on|focuses\s+on|discussing|related\s+to|about)\s+([a-zA-Z0-9\s,]{3,70}?)(?=[.;]|\s+(?:in|at|by|from)\s+[A-Z]|$)",
        r"(?:initiative|initiatives|program|programs|helpline|campaign|movement|agitation)\s+(?:for|on|against|over)\s+([a-zA-Z0-9\s,]{3,55}?)(?=[.;]|\s+(?:in|at|by|from)\s+[A-Z]|$)",
    ]

    def _admit(raw: str, bucket: List[str]):
        for sub in re.split(r",|\band\b", raw):
            clean_c = clean_concept_phrase(sub)
            words = clean_c.split()
            if (
                len(clean_c) >= 3
                and 2 <= len(words) <= 8
                and len(clean_c) <= 80
                and clean_c not in COMMON_FINITE_VERBS
                and not is_web_boilerplate(clean_c)
                and not is_incomplete_fragment(clean_c)
                and not (set(w.lower() for w in words) & COMMON_FINITE_VERBS)
            ):
                bucket.append(clean_c)

    for pat in demand_triggers:
        for m in re.finditer(pat, text, re.IGNORECASE):
            _admit(m.group(1).strip(), demands)

    for pat in about_triggers:
        for m in re.finditer(pat, text, re.IGNORECASE):
            _admit(m.group(1).strip(), about)

    # User description clauses → about / topic seeds (skip pure org names)
    desc_clauses = re.split(r"[,;]", anchor["description"])
    for cl in desc_clauses:
        clean_c = clean_concept_phrase(cl)
        words = clean_c.split()
        if not (1 <= len(words) <= 5):
            continue
        if is_web_boilerplate(clean_c) or is_incomplete_fragment(clean_c):
            continue
        # Multi-word org indicators belong to orgs, not about
        if any(w in ORGANIZATION_INDICATORS for w in words) and len(words) >= 2:
            continue
        about.append(clean_c)

    scheme_pattern = r"\b[A-Z][a-zA-Z0-9]+(?:\s+[A-Z][a-zA-Z0-9]+){0,2}\s+(?:Fund|Centres|Center|Scheme|Mission|Yojana|Act)\b"
    for m in re.finditer(scheme_pattern, text):
        clean_s = m.group().strip()
        if clean_s.lower() not in {"fund", "scheme", "act"} and not is_web_boilerplate(clean_s):
            about.append(clean_s)

    return demands, about


def process_content(
    event: str,
    location: str,
    description: str,
    search_results: List[Dict[str, Any]],
    max_keywords: Optional[int] = None,
    max_hashtags: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Deterministically processes web search content into event facts:
    - What it is about
    - Main leaders / participating figures
    - Demands / goals
    - Where it is held (venues + regions)
    - Organizations and short forms (acronyms)
    Then emits hashtags and keywords prioritized around those facts.
    """
    anchor = build_anchor_profile(event, location, description)
    relevant_corpus_parts: List[str] = []
    found_hashtags: List[str] = []

    # Seed user facts first so relevance can use acronym expansions
    user_seeds = extract_user_seed_facts(event, location, description)
    for pair in user_seeds.get("acronyms", []):
        if pair.get("short") and pair.get("full"):
            existing = {p.get("short"): p for p in (anchor.get("acronym_pairs") or [])}
            existing[pair["short"]] = pair
            anchor["acronym_pairs"] = list(existing.values())

    page_passages: List[str] = []

    for r in search_results:
        title = r.get("title", "")
        snip = r.get("snippet", "")
        body = r.get("content", "") or r.get("markdown", "")
        # Strip HTML/chrome and drop boilerplate before relevance gating
        body_passages = extract_clean_passages(body[:8000] if body else "")
        body_clean = " ".join(body_passages)[:4000] if body_passages else clean_text((body or "")[:4000])
        combined = f"{title}. {snip}. {body_clean}"
        cleaned = clean_text(combined)

        if not is_content_relevant(cleaned, anchor):
            continue

        page_tags = re.findall(r"#([A-Za-z0-9_]{3,28})", cleaned)
        page_kept = 0
        sentences = re.split(r"(?<=[.?!;])\s+|\n+", cleaned)
        for s in sentences:
            s_clean = s.strip()
            if len(s_clean) <= 12 or is_boilerplate_sentence(s_clean):
                continue
            # Sentence-level gate: keep only event-relevant sentences
            if not (
                is_content_relevant(s_clean, anchor)
                or is_strongly_event_relevant(s_clean, anchor)
            ):
                continue
            relevant_corpus_parts.append(s_clean)
            page_kept += 1

        if page_kept > 0 and body_passages:
            page_passages.extend(body_passages)

        # Hashtags only from pages that contributed kept sentences (or a strong title)
        title_snip = clean_text(f"{title}. {snip}")
        if page_kept > 0 or is_strongly_event_relevant(title_snip, anchor):
            found_hashtags.extend(page_tags)

    if not relevant_corpus_parts:
        relevant_corpus_parts.append(anchor["full_text"])

    # Prefer deduped editorial passages when available; fall back to filtered sentences
    unique_passages = deduplicate_syndicated_passages(page_passages) if page_passages else []
    corpus = " ".join(unique_passages) if unique_passages else " ".join(relevant_corpus_parts)
    if unique_passages and relevant_corpus_parts:
        # Keep sentence-level gate signal for people/org extraction coverage
        corpus = f"{corpus} {' '.join(relevant_corpus_parts)}"

    user_people = [
        p for p in (user_seeds.get("people") or [])
        if p and not looks_like_place_or_scheme(p)
    ]
    # People from already-filtered corpus sentences + user seeds
    people_raw = []
    for p in extract_people(corpus) + user_people:
        cleaned = _clean_person_name(p) if p else None
        if cleaned and not looks_like_place_or_scheme(cleaned):
            people_raw.append(cleaned)
    orgs = extract_organizations(corpus, anchor)
    locs, venues = extract_locations(corpus, location)
    demands, about_topics = extract_demands_and_issues(corpus, anchor)

    demands = list(user_seeds.get("demands") or []) + list(demands)
    about_topics = list(user_seeds.get("about") or []) + list(about_topics)

    locs = [l for l in locs if is_location_in_user_scope(l, location)]
    venues = [v for v in venues if is_location_in_user_scope(v, location)]

    # Demands / about must carry distinctive event signal (not generic "outdoor/music" SEO)
    demands = [
        d for d in demands
        if d and not is_incomplete_fragment(d) and not is_marketing_or_listicle_scrap(d)
        and has_distinctive_event_signal(d, anchor)
    ]
    about_topics = [
        a for a in about_topics
        if a and not is_incomplete_fragment(a) and not is_marketing_or_listicle_scrap(a)
        and has_distinctive_event_signal(a, anchor)
    ]

    main_leaders, participants = classify_people_roles(people_raw, corpus)
    for p in user_people:
        if p not in main_leaders and p not in participants:
            main_leaders.insert(0, p)

    acronyms = collect_event_acronyms(
        event,
        f"{description}. {corpus[:2500]}",
        [o for o in orgs if _looks_like_named_entity(o) or re.fullmatch(r"[A-Z]{2,6}", o or "")],
        [],
        user_description=description,
    )
    merged_acro: Dict[str, str] = {
        p["short"]: p["full"] for p in acronyms if p.get("short") and p.get("full")
    }
    for p in (anchor.get("acronym_pairs") or []) + (user_seeds.get("acronyms") or []):
        if p.get("short") and p.get("full"):
            merged_acro[p["short"]] = p["full"]
    # Drop sentence-length "expansions"; keep bare event acronyms as short-only
    for tok in re.findall(r"[A-Za-z0-9]+", event):
        if tok.isupper() and 2 <= len(tok) <= 6 and tok not in merged_acro:
            merged_acro[tok] = ""
    cleaned_pairs: List[Dict[str, str]] = []
    for s, f in merged_acro.items():
        if f and not _is_usable_acronym_full(f):
            f = ""
        cleaned_pairs.append({"short": s, "full": f})
    acronyms = cleaned_pairs

    cleaned_orgs: List[str] = []
    for o in orgs:
        if is_incomplete_fragment(o):
            continue
        if len(o) > 80 or re.search(r"[.!?]", o) or len(o.split()) > 8:
            continue
        if o.lower().endswith(" official"):
            continue
        if o.lower() in {d.lower() for d in demands} or o.lower() in {a.lower() for a in about_topics}:
            if not (set(tokenize(o)) & ORGANIZATION_INDICATORS):
                continue
        cleaned_orgs.append(o)
    orgs = cleaned_orgs
    for pair in acronyms:
        if pair["full"] and pair["full"] not in orgs:
            orgs.insert(0, pair["full"])
        if pair["short"] and pair["short"] not in orgs:
            orgs.insert(0, pair["short"])

    loc_info = repair_location_info(
        parse_location(location), venues, locs, corpus=corpus[:4000]
    )
    # Drop typo'd user venue strings when a repaired corpus form exists
    repaired_norms = {normalize_term(_normalize_place_segment(p)) for p in (loc_info.get("parts") or [])}
    venues = [
        reconcile_place_name(v, list(venues) + list(loc_info.get("parts") or []))
        for v in venues
    ]
    locs = [
        reconcile_place_name(l, list(venues) + list(loc_info.get("parts") or []))
        for l in locs
    ]
    # Prefer repaired spelling; drop near-duplicate typo forms
    def _dedupe_places(items: List[str]) -> List[str]:
        out: List[str] = []
        seen: Set[str] = set()
        for it in items:
            n = normalize_term(_normalize_place_segment(it))
            if not n or n in seen:
                continue
            # Skip if a better-spelled variant already kept
            skip = False
            for kept in out:
                if are_fuzzy_duplicates(n, normalize_term(_normalize_place_segment(kept))):
                    skip = True
                    break
            if skip:
                continue
            out.append(it)
            seen.add(n)
        return out

    venues = _dedupe_places(venues)
    locs = _dedupe_places(locs)
    primary_reg = loc_info.get("primary_region", "")
    clean_event = event.strip()

    # Allowed short forms only: acronyms + user geography tokens (never name/org scraps)
    allowed_shorts = {p["short"].lower() for p in acronyms if p.get("short")}
    for part in loc_info.get("parts") or []:
        n = normalize_term(part)
        if n and n not in STOP_WORDS and n not in ENTITY_GLUE_SINGLETONS:
            allowed_shorts.add(n)
    if primary_reg:
        allowed_shorts.add(normalize_term(primary_reg))
    # Canonical full entities — used to block scrap tokens like "party" / "kumar"
    known_full_entities: List[str] = [
        e for e in dict.fromkeys(
            [clean_event]
            + [p.get("full", "") for p in acronyms]
            + list(main_leaders)
            + list(participants)
            + [o for o in orgs if len(phrase_tokens(o)) >= 2]
            + list(venues)
            + list(demands)
            + list(about_topics)
            + ([primary_reg] if primary_reg else [])
        )
        if e and normalize_term(e)
    ]

    # --- HASHTAGS (fact-first into the only UI lists) ---
    hashtags: List[str] = []
    seen_ht_norm: Set[str] = set()

    def add_hashtag(tag: str):
        if not tag:
            return
        body0 = tag.lstrip("#")
        if (
            is_web_boilerplate(tag)
            or is_incomplete_fragment(body0)
            or is_marketing_or_listicle_scrap(body0)
            or is_clickbait_headline_scrap(body0)
        ):
            return
        if not tag.startswith("#"):
            tag = f"#{tag}"
        if is_name_or_org_fragment(tag, known_full_entities, allowed_singletons=allowed_shorts):
            return
        if not is_valid_hashtag(tag, anchor):
            return
        t_norm = normalize_term(tag)
        if t_norm in seen_ht_norm or len(t_norm) < 2:
            return

        for existing in list(hashtags):
            if is_subphrase_of(tag, existing) and not is_allowed_singleton(tag, allowed_shorts):
                return
            if is_subphrase_of(existing, tag) and not is_allowed_singleton(existing, allowed_shorts):
                hashtags.remove(existing)
                seen_ht_norm.discard(normalize_term(existing))

        if max_hashtags is None or len(hashtags) < max_hashtags:
            hashtags.append(tag)
            seen_ht_norm.add(t_norm)

    # A. Event identity + short forms (from user/org expansions)
    add_hashtag(to_hashtag(clean_event))
    for pair in acronyms:
        if pair.get("short"):
            add_hashtag(f"#{pair['short']}")
        if pair.get("full") and _is_usable_acronym_full(pair["full"]):
            add_hashtag(to_hashtag(pair["full"]))
        if pair.get("short") and primary_reg:
            add_hashtag(to_hashtag(f"{pair['short']} {primary_reg}"))

    # B. Region / in-scope venues
    if primary_reg:
        add_hashtag(to_hashtag(primary_reg))
    for loc_tag in loc_info.get("hashtags", []):
        add_hashtag(loc_tag)
    for v in list(dict.fromkeys(venues))[:4]:
        if not is_location_in_user_scope(v, location):
            continue
        v_l = v.lower()
        ustate = detect_user_state(location)
        if ustate and any(
            lm in v_l and region != ustate for lm, region in LANDMARK_TO_REGION.items()
        ):
            continue
        if len(to_hashtag(v)) <= 25:
            add_hashtag(to_hashtag(v))

    # C. About / demands
    for topic in list(dict.fromkeys(about_topics + demands))[:6]:
        tag = to_hashtag(topic)
        if 4 <= len(tag) <= 25:
            add_hashtag(tag)

    # D. Organizations — full names or known acronyms only (never "Party" / "Commission")
    for o in orgs:
        o_toks = phrase_tokens(o)
        if len(o_toks) > 4 or len(to_hashtag(o)) > 25 or is_incomplete_fragment(o):
            continue
        if len(o_toks) == 1 and normalize_term(o) not in allowed_shorts:
            continue
        o_norm = normalize_term(o)
        if (
            is_strongly_event_relevant(o, anchor)
            or o_norm in {normalize_term(p.get("full", "")) for p in acronyms}
            or o_norm in {normalize_term(p.get("short", "")) for p in acronyms}
            or bool(set(tokenize(o)) & (set(tokenize(event)) | set(tokenize(description))))
        ):
            add_hashtag(to_hashtag(o))

    # E. People — full names only (e.g. Gyanesh Kumar, not Gyanesh / Kumar)
    for p in (main_leaders + participants)[:6]:
        if 2 <= len(phrase_tokens(p)) <= 4 and len(to_hashtag(p)) <= 22:
            add_hashtag(to_hashtag(p))

    # F. Web hashtags — must match event/description/acronym (never location-only)
    web_tag_budget = 5
    web_added = 0
    for raw in found_hashtags:
        if web_added >= web_tag_budget:
            break
        body = re.sub(r"[^A-Za-z0-9]", "", raw)
        body_l = body.lower()
        if is_incomplete_fragment(raw):
            continue
        # Reject invented acronym lookalikes from the web (#CJPA, #CJPSN, #CJPSNOdisha)
        if _is_invented_acronym_hashtag(body, allowed_shorts, location):
            continue
        # Compact ALL-CAPS web tags must be exact known shorts (not near-misses)
        if re.fullmatch(r"[A-Za-z]{2,10}", body) and body.isupper() and body_l not in allowed_shorts:
            # Allow exact region-compound of a known short (#CJPOdisha)
            if not any(
                body_l == f"{s}{normalize_term(primary_reg)}"
                for s in allowed_shorts
                if primary_reg and len(s) <= 6
            ):
                continue
        spaced = re.sub(r"([a-z])([A-Z])", r"\1 \2", raw)
        user_state = detect_user_state(location)
        if user_state:
            skip_landmark = False
            for landmark, region in LANDMARK_TO_REGION.items():
                if landmark.replace(" ", "") in body_l and region != user_state:
                    skip_landmark = True
                    break
            if skip_landmark:
                continue
        if body_l in allowed_shorts or is_strongly_event_relevant(raw, anchor) or is_strongly_event_relevant(spaced, anchor):
            before = len(hashtags)
            add_hashtag(f"#{raw}")
            if len(hashtags) > before:
                web_added += 1

    # --- KEYWORDS (same facts; no separate Event Facts UI) ---
    keywords: List[str] = []
    seen_kw_norm: Set[str] = set()
    acronym_fulls = {normalize_term(p.get("full", "")) for p in acronyms}
    acronym_shorts = {normalize_term(p.get("short", "")) for p in acronyms}
    seeded_people = {normalize_term(p) for p in user_people}

    def add_keyword(item: str, *, require_strong: bool = True):
        if not item or len(item) < 2:
            return
        # Normalize person+headline scraps before gating
        stripped = strip_person_name_noise(item)
        if stripped and stripped != item and 2 <= len(stripped.split()) <= 4:
            maybe_person = _clean_person_name(stripped)
            if maybe_person:
                item = maybe_person
            else:
                item = stripped
        if (
            is_web_boilerplate(item)
            or is_incomplete_fragment(item)
            or is_marketing_or_listicle_scrap(item)
            or is_clickbait_headline_scrap(item)
        ):
            return
        if is_name_or_org_fragment(item, known_full_entities, allowed_singletons=allowed_shorts):
            return
        # Never emit sentence/paragraph scraps as keywords
        if re.search(r"[.!?]", item) or len(item) > 100:
            return
        toks = phrase_tokens(item)
        if len(toks) > 12:
            return
        # Reject phrases that carry invented acronym lookalikes (CJPSN, CJPA, …)
        for tok in re.findall(r"\b[A-Za-z]{2,8}\b", item):
            if tok.isupper() and _is_invented_acronym_hashtag(tok, allowed_shorts, location):
                return
        norm = normalize_term(item)
        if norm in STOP_WORDS or norm in COMMON_FINITE_VERBS or len(norm) < 2:
            return
        if norm in seen_ht_norm or norm in seen_kw_norm:
            return
        if norm.split() and norm.split()[-1] == "location":
            return
        # People / titles must be full phrases (not "Gyanesh" or "Chief")
        if len(toks) == 1 and norm not in acronym_shorts and norm not in allowed_shorts:
            return
        # Non-entity scraps need distinctive event/location tokens (not just "outdoor")
        is_seeded = norm in acronym_fulls or norm in acronym_shorts or norm in seeded_people
        if not is_seeded and len(toks) >= 2 and not has_distinctive_event_signal(item, anchor):
            # Allow known people / venues / orgs already extracted
            known_norms = {
                normalize_term(x)
                for x in (main_leaders + participants + venues + locs + orgs)
                if x
            }
            if norm not in known_norms:
                return
        if require_strong:
            if is_seeded:
                pass
            elif len(toks) >= 2 and not has_distinctive_event_signal(item, anchor):
                return

        for ex in list(keywords):
            if is_subphrase_of(item, ex) and not is_allowed_singleton(item, allowed_shorts):
                return
            if is_subphrase_of(ex, item) and not is_allowed_singleton(ex, allowed_shorts):
                keywords.remove(ex)
                seen_kw_norm.discard(normalize_term(ex))
                continue
            if are_fuzzy_duplicates(norm, normalize_term(ex)):
                return

        if max_keywords is None or len(keywords) < max_keywords:
            keywords.append(item.strip())
            seen_kw_norm.add(norm)

    for t, _ in Counter(about_topics).most_common():
        if len(phrase_tokens(t)) < 2:
            continue
        add_keyword(t, require_strong=True)
    for pair in acronyms:
        # Only emit "Full (ACRO)" when the user explicitly provided that pair
        full, short = pair.get("full") or "", pair.get("short") or ""
        if full and _is_usable_acronym_full(full) and short:
            add_keyword(f"{full} ({short})", require_strong=False)
            add_keyword(full, require_strong=False)
        elif short:
            add_keyword(short, require_strong=False)
    for d, _ in Counter(demands).most_common():
        if len(phrase_tokens(d)) < 2:
            continue
        add_keyword(d, require_strong=True)
    # People: full names only (2+ tokens)
    for p, _ in Counter(main_leaders).most_common():
        if len(phrase_tokens(p)) >= 2:
            add_keyword(p, require_strong=False)
    for p, _ in Counter(participants).most_common():
        if len(phrase_tokens(p)) >= 2:
            add_keyword(p, require_strong=False)
    for o, _ in Counter(orgs).most_common():
        o_toks = phrase_tokens(o)
        # Org acronyms OK; otherwise require multi-word full name
        if len(o_toks) == 1 and normalize_term(o) not in acronym_shorts:
            continue
        if is_strongly_event_relevant(o, anchor) or normalize_term(o) in acronym_fulls | acronym_shorts:
            add_keyword(o, require_strong=False)
        elif set(tokenize(o)) & (set(tokenize(anchor.get("event", ""))) | set(tokenize(anchor.get("description", "")))):
            add_keyword(o, require_strong=False)
    for v, _ in Counter(venues).most_common():
        if not is_location_in_user_scope(v, location):
            continue
        if len(phrase_tokens(v)) < 2 and normalize_term(v) not in allowed_shorts:
            continue
        v_l = v.lower()
        ustate = detect_user_state(location)
        if ustate and any(
            lm in v_l and region != ustate for lm, region in LANDMARK_TO_REGION.items()
        ):
            continue
        add_keyword(v, require_strong=False)
    for l, _ in Counter(locs).most_common():
        if normalize_term(l) in {normalize_term(v) for v in venues}:
            continue
        if not is_location_in_user_scope(l, location):
            continue
        if len(phrase_tokens(l)) < 2 and normalize_term(l) not in allowed_shorts:
            continue
        l_l = l.lower()
        ustate = detect_user_state(location)
        if ustate and any(
            lm in l_l and region != ustate for lm, region in LANDMARK_TO_REGION.items()
        ):
            continue
        add_keyword(l, require_strong=False)

    # Event title as keyword only when it stays phrase-length (not a long sentence)
    if primary_reg and primary_reg.lower() != clean_event.lower():
        combo = f"{clean_event} {primary_reg}".strip()
        if len(phrase_tokens(combo)) <= 8:
            add_keyword(combo.lower(), require_strong=False)
    elif len(phrase_tokens(clean_event)) <= 8:
        add_keyword(clean_event.lower(), require_strong=False)

    # Keep lists independent: hashtags = short social tags; keywords = search phrases.
    # They may share core entities (e.g. person names) but are not forced 1:1 copies.
    hashtags[:] = [
        h for h in prefer_full_phrases(hashtags, allowed_singletons=allowed_shorts)
        if not is_clickbait_headline_scrap(h.lstrip("#"))
        and not is_marketing_or_listicle_scrap(h.lstrip("#"))
    ]
    keywords[:] = prefer_full_phrases(keywords, allowed_singletons=allowed_shorts)
    if max_hashtags is not None:
        hashtags[:] = hashtags[:max_hashtags]
    if max_keywords is not None:
        keywords[:] = keywords[:max_keywords]

    people_all = list(dict.fromkeys(main_leaders + participants + people_raw))

    return {
        "hashtags": hashtags,
        "keywords": keywords,
        "entities": {
            "about": list(dict.fromkeys(about_topics)),
            "main_leaders": list(dict.fromkeys(main_leaders)),
            "participants": list(dict.fromkeys(participants)),
            "people": people_all,
            "demands_and_issues": list(dict.fromkeys(demands)),
            "venues": list(dict.fromkeys(venues)),
            "locations": list(dict.fromkeys(locs)),
            "organizations": list(dict.fromkeys(orgs)),
            "acronyms": acronyms,
        },
    }

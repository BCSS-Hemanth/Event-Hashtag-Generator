"""
Deterministic Text Processor Module

Processes web search content retrieved by Wigolo to extract:
1. Hashtags (formatted as #CamelCase, deduplicated, derived from web content).
2. Keywords (salient noun phrases, organizations, legal terms, and key concepts).

IMPORTANT:
This processing is completely deterministic using standard Python text-processing
techniques (n-gram analysis, frequency scoring, capitalized entity extraction).
NO LLM or AI generation is used.
"""

import re
from collections import Counter
from typing import Any, Dict, List, Optional, Set, Tuple

# Comprehensive English stopwords and web boilerplate terms
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
    # Conversational & non-substantive filler words
    "like", "also", "said", "say", "says", "told", "even", "just", "well", "now",
    "one", "two", "three", "first", "last", "new", "many", "much", "get", "make",
    "made", "take", "took", "know", "see", "look", "come", "go", "went", "back",
    "way", "good", "people", "time", "year", "years", "day", "days", "may", "might",
    "per", "etc", "using", "used", "via", "re", "including", "related", "various",
    # Web boilerplate
    "http", "https", "www", "com", "org", "net", "html", "htm", "url", "page",
    "website", "click", "view", "read", "more", "details", "contact", "copyright",
    "rights", "reserved", "terms", "privacy", "policy", "login", "sign", "search",
    "results", "updated", "posted", "share", "facebook", "twitter", "linkedin",
    "youtube", "instagram", "whatsapp", "email", "author", "published", "comments",
}


def clean_text(text: str) -> str:
    """Clean text by removing HTML entities, URLs, and excess whitespace."""
    text = re.sub(r"https?://\S+|www\.\S+", " ", text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def extract_capitalized_entities(text: str) -> List[str]:
    """
    Extract multi-word proper nouns, legal titles, organizations, and acronyms.
    Examples from web results:
    - 'Citizens for Justice and Peace'
    - 'Forest Rights Act'
    - 'High Court', 'Gram Sabha', 'Dhinkia'
    - 'POSCO', 'JSW Steel'
    """
    entities = []

    # Pattern for title-cased multi-word phrases (e.g. 'Citizens for Justice and Peace', 'Forest Rights Act')
    title_pattern = r"\b[A-Z][a-z]+(?:\s+(?:for|of|and|the|in|de)\s+[A-Z][a-z]+|\s+[A-Z][a-z]+){1,4}\b"
    for match in re.finditer(title_pattern, text):
        phrase = match.group().strip()
        words = phrase.split()
        # Ensure it is not just common sentence starter words
        if words[0].lower() not in STOP_WORDS and len(phrase) > 5:
            entities.append(phrase)

    # Pattern for notable all-caps acronyms (e.g. 'CJP', 'FRA', 'POSCO', 'JSW', 'NCR')
    acronym_pattern = r"\b[A-Z]{2,6}\b"
    for match in re.finditer(acronym_pattern, text):
        acronym = match.group()
        if acronym.lower() not in STOP_WORDS and acronym not in {"HTML", "HTTP", "HTTPS", "URL", "PDF"}:
            entities.append(acronym)

    return entities


def extract_raw_hashtags_from_text(text: str) -> List[str]:
    """Find any hashtags already written in web text or snippets."""
    matches = re.findall(r"#([A-Za-z0-9_]{3,30})", text)
    valid_hashtags = []
    for match in matches:
        clean_tag = match.strip("_")
        if clean_tag and not clean_tag.isdigit() and clean_tag.lower() not in STOP_WORDS:
            valid_hashtags.append(f"#{clean_tag}")
    return valid_hashtags


# Known acronyms to preserve in all-caps for hashtags
KNOWN_ACRONYMS: Set[str] = {
    "gmdc", "cjp", "fra", "posco", "jsw", "ncr", "ai", "ml", "iot", "it",
    "delhi", "bjp", "aap", "ngo", "who", "un", "unesco", "usa", "uk", "eu"
}


def to_hashtag(phrase: str) -> str:
    """
    Deterministically convert a phrase into a clean CamelCase hashtag.
    Preserves uppercase for common acronyms (e.g. 'GMDC Road' -> '#GMDCRoad').
    Strictly removes all spaces, commas, punctuation, and caps length at 25 chars.
    """
    if not phrase:
        return ""
    # Normalize possessives (Women's -> Womens)
    cleaned = re.sub(r"['’]s\b", "s", phrase)
    words = re.findall(r"[A-Za-z0-9]+", cleaned)
    if not words:
        return ""

    camel_parts = []
    for word in words:
        w_lower = word.lower()
        # Skip minor prepositions in multi-word phrases
        if w_lower in {"and", "for", "of", "the", "in", "to", "at", "on", "a", "an"} and len(words) > 2:
            continue
        if w_lower in KNOWN_ACRONYMS or (word.isupper() and 2 <= len(word) <= 5):
            camel_parts.append(word.upper())
        else:
            camel_parts.append(word.capitalize())

    camel = "".join(camel_parts)
    if not camel:
        camel = "".join(word.capitalize() for word in words)

    # Strictly alphanumeric after '#'
    camel = re.sub(r"[^A-Za-z0-9]", "", camel)
    if not camel:
        return ""

    # Truncate overly long hashtag compounds (max 25 characters)
    if len(camel) > 24:
        camel = camel[:24]

    return f"#{camel}"


def parse_location(location_str: str) -> Dict[str, Any]:
    """
    Parse a detailed or multi-part location string (e.g. 'gmdc road, gujarat, india')
    into individual parts, recognized regions/landmarks, and clean hashtags.

    Handles:
    - Multi-segment inputs separated by commas, semicolons, slashes, or pipes.
    - Landmark extraction (e.g. 'GMDC Road' -> '#GMDCRoad' and landmark '#GMDC').
    - State/country extraction (e.g. 'Gujarat' -> '#Gujarat', 'India' -> '#India').
    - Primary region identification for combined hashtags.
    """
    if not location_str or not location_str.strip():
        return {"parts": [], "primary_region": "", "hashtags": []}

    # Split on commas, semicolons, slashes, or pipes
    raw_segments = [s.strip() for s in re.split(r"[,;/|]+", location_str) if s.strip()]

    parts: List[str] = []
    location_hashtags: List[str] = []

    ROAD_WORDS = {
        "road", "rd", "street", "st", "lane", "ln", "avenue", "ave",
        "marg", "chowk", "circle", "square", "cross", "bypass", "nagar", "sector"
    }

    for seg in raw_segments:
        words = re.findall(r"[A-Za-z0-9]+", seg)
        if not words:
            continue
        cleaned_seg = " ".join(words)
        parts.append(cleaned_seg)

        # Generate a hashtag for the whole segment (e.g. "gmdc road" -> #GMDCRoad, "gujarat" -> #Gujarat)
        tag = to_hashtag(cleaned_seg)
        if tag and tag not in location_hashtags:
            location_hashtags.append(tag)

        # If segment ends with road/st/marg (e.g. "gmdc road"), also generate landmark hashtag (#GMDC)
        if len(words) > 1 and words[-1].lower() in ROAD_WORDS:
            landmark_words = words[:-1]
            landmark_tag = to_hashtag(" ".join(landmark_words))
            if landmark_tag and landmark_tag not in location_hashtags:
                location_hashtags.append(landmark_tag)

    # Determine primary region: the first segment that is NOT just a street/road name
    primary_region = ""
    for p in parts:
        lower = p.lower()
        words = lower.split()
        if not any(w in ROAD_WORDS for w in words):
            primary_region = p
            break
    if not primary_region and parts:
        primary_region = parts[0]

    return {
        "parts": parts,
        "primary_region": primary_region,
        "hashtags": location_hashtags,
    }


def tokenize(text: str) -> List[str]:
    """Split text into lowercase alphanumeric tokens."""
    return [word.lower() for word in re.findall(r"[A-Za-z0-9]+", text) if len(word) > 1]


def extract_candidate_phrases(text: str) -> List[str]:
    """
    Extract meaningful 2-word and 3-word phrases from text.
    Strictly ensures no token in the phrase is a stopword or noise word.
    """
    tokens = tokenize(text)
    candidates: List[str] = []

    # 1-grams (single strong keywords: length >= 4, not numbers or stopwords)
    for word in tokens:
        if word not in STOP_WORDS and len(word) >= 4 and not word.isdigit():
            candidates.append(word)

    # 2-grams (both words must be substantive, no stopwords)
    for i in range(len(tokens) - 1):
        w1, w2 = tokens[i], tokens[i + 1]
        if w1 not in STOP_WORDS and w2 not in STOP_WORDS:
            if not (w1.isdigit() or w2.isdigit()):
                candidates.append(f"{w1} {w2}")

    # 3-grams (substantive phrases, middle can be 'of' or 'for', start and end cannot be stopwords)
    for i in range(len(tokens) - 2):
        w1, w2, w3 = tokens[i], tokens[i + 1], tokens[i + 2]
        if w1 not in STOP_WORDS and w3 not in STOP_WORDS:
            if w2 in {"of", "for", "and", "in"} or w2 not in STOP_WORDS:
                candidates.append(f"{w1} {w2} {w3}")

    return candidates


def process_content(
    event: str,
    location: str,
    description: str,
    search_results: List[Dict[str, Any]],
    max_keywords: Optional[int] = None,
    max_hashtags: Optional[int] = None,
) -> Dict[str, List[str]]:
    """
    Deterministically processes content returned by Wigolo and extracts:
    1. Hashtags (first) - authentic social, campaign, and location tags
    2. Keywords (second) - salient substantive topic phrases and entities

    IMPORTANT:
    Hashtags and Keywords are strictly decoupled. Hashtags are social discovery
    and movement tags (#CamelCase, valid syntax, no spaces/commas), while Keywords
    are search and subject concepts (plain text phrases).
    """
    search_text_pieces: List[str] = []
    found_hashtags: List[str] = []
    capitalized_entities: List[str] = []

    for result in search_results:
        title = result.get("title", "")
        snippet = result.get("snippet", "")
        # Also grab full content/markdown if available from Wigolo
        body = result.get("markdown", "") or result.get("content", "")

        combined = f"{title} {snippet} {body[:4000]}"
        cleaned = clean_text(combined)
        search_text_pieces.append(cleaned)

        # Extract real entities & hashtags from web content
        capitalized_entities.extend(extract_capitalized_entities(cleaned))
        found_hashtags.extend(extract_raw_hashtags_from_text(cleaned))

    full_web_text = " ".join(search_text_pieces)

    # If web search returned no text (offline or empty), fallback to user input
    if not full_web_text.strip():
        full_web_text = f"{event} {location} {description}"

    # Parse location components and primary region
    loc_info = parse_location(location)
    primary_region = loc_info.get("primary_region", "")
    clean_event = event.strip()
    clean_desc = description.strip()

    # 1. Count frequency of capitalized entities (organizations, campaigns, laws)
    entity_counts = Counter(capitalized_entities)

    # 2. Extract n-gram candidate phrases from web text
    phrase_candidates = extract_candidate_phrases(full_web_text)
    phrase_counts = Counter(phrase_candidates)

    # 3. Score candidates based on web frequency and length
    scored_items: List[Tuple[str, float]] = []

    # Score named entities (give them a quality boost because they represent real entities)
    for entity, count in entity_counts.items():
        clean_ent = entity.strip()
        words = clean_ent.split()
        if len(words) >= 2 or (len(clean_ent) >= 3 and clean_ent.isupper()):
            # Multi-word proper nouns or acronyms
            score = float(count) * 2.5
            scored_items.append((clean_ent, score))

    # Score general keyphrases
    for phrase, count in phrase_counts.items():
        words = phrase.split()
        score = float(count)
        if len(words) == 2:
            score *= 1.4
        elif len(words) == 3:
            score *= 1.8
        scored_items.append((phrase, score))

    # Sort descending by score
    scored_items.sort(key=lambda x: x[1], reverse=True)

    # 4. Filter and Select Rich Multi-Word Keywords
    selected_keywords: List[str] = []
    seen_keywords: Set[str] = set()

    # Seed with event + primary region (clean and focused)
    if primary_region and primary_region.lower() != clean_event.lower():
        primary_event_kw = f"{clean_event} {primary_region}".strip().lower()
        if len(primary_event_kw) > 3:
            selected_keywords.append(primary_event_kw)
            seen_keywords.add(primary_event_kw)
    else:
        clean_event_kw = clean_event.strip().lower()
        if len(clean_event_kw) > 3:
            selected_keywords.append(clean_event_kw)
            seen_keywords.add(clean_event_kw)

    # Keywords should prioritize multi-word phrases and informative entities over single generic words
    for item, _ in scored_items:
        norm = item.strip().lower()

        # Skip short items or stopwords
        if len(norm) < 4 or norm in STOP_WORDS:
            continue

        # Skip isolated generic single words like 'school', 'errors', 'support'
        # unless it is an established acronym like 'CJP' or 'GMDC'
        words = norm.split()
        if len(words) == 1 and not item.isupper() and len(norm) < 8:
            continue

        # Skip exact duplicate coverage
        is_duplicate = False
        for existing in seen_keywords:
            if norm == existing or (len(norm) > 6 and norm in existing) or (len(existing) > 6 and existing in norm):
                is_duplicate = True
                break

        if not is_duplicate:
            display_val = item.strip() if any(c.isupper() for c in item) else norm
            selected_keywords.append(display_val)
            seen_keywords.add(norm)

        if max_keywords is not None and len(selected_keywords) >= max_keywords:
            break

    # 5. Extract and Construct Distinct Campaign, Social, and Regional Hashtags
    # Hashtags are social discovery tags (movements, campaigns, locations).
    # They should NOT duplicate the list of extracted keywords!
    selected_hashtags: List[str] = []
    seen_hashtags: Set[str] = set()

    def add_hashtag(tag: str):
        if not tag:
            return
        # Clean and ensure proper hashtag format (no spaces, commas, or special chars)
        cleaned_tag = re.sub(r"[^A-Za-z0-9]", "", tag.lstrip("#"))
        if not cleaned_tag:
            return
        final_tag = f"#{cleaned_tag}"
        # A good hashtag is between 3 and 25 characters, not a stopword
        if cleaned_tag.lower() in STOP_WORDS or len(cleaned_tag) < 3 or len(cleaned_tag) > 25:
            return
        if final_tag.lower() not in seen_hashtags and (max_hashtags is None or len(selected_hashtags) < max_hashtags):
            selected_hashtags.append(final_tag)
            seen_hashtags.add(final_tag.lower())

    # A. Core Event Hashtag (e.g. "Women's Safety" -> #WomensSafety)
    event_tag = to_hashtag(clean_event)
    add_hashtag(event_tag)

    # B. Combined Event + Primary Region
    if primary_region:
        primary_reg_tag = to_hashtag(primary_region).lstrip("#")
        is_safety = any(w in clean_event.lower() for w in ["safety", "secure", "protection", "women"])
        is_fest = any(w in clean_event.lower() for w in ["festival", "celebration", "fest", "carnival", "navratri", "garba", "utsav"])

        if is_safety:
            add_hashtag(f"#Safe{primary_reg_tag}")
        elif is_fest:
            add_hashtag(f"#Vibrant{primary_reg_tag}")
            add_hashtag(f"#{primary_reg_tag}Festival")

        # Clean event + region hashtag (e.g. #NavratriGujarat, #WomensSafetyGujarat)
        combined_event_reg = to_hashtag(f"{clean_event} {primary_region}")
        if len(combined_event_reg) <= 25:
            add_hashtag(combined_event_reg)

    # C. Location-Specific Social Hashtags (e.g. #Gujarat, #India, #GMDCRoad, #GMDC)
    for loc_tag in loc_info.get("hashtags", []):
        add_hashtag(loc_tag)

    # D. Real Hashtags Discovered from Web & Social Snippets
    # (Twitter, Reddit, blogs, news hashtags found by Wigolo)
    for tag in found_hashtags:
        add_hashtag(tag)

    # E. Authentic Campaign/Movement Organizations & Named Entities from Web Content
    # (Only high-confidence proper nouns & established organizations, e.g. 'Citizens for Justice and Peace', 'Forest Rights Act')
    for entity in capitalized_entities:
        words = entity.split()
        # Must be 2-3 words (not an entire sentence) and recognized as an entity/organization
        if 2 <= len(words) <= 4:
            tag = to_hashtag(entity)
            if len(tag) <= 24:
                add_hashtag(tag)

    # F. Context-Aware Campaign & Movement Tags based on Event Nature
    # Rather than dumping arbitrary noun phrases, provide real social movement/action tags
    combined_context = f"{clean_event} {clean_desc}".lower()

    if any(k in combined_context for k in ["festival", "navratri", "garba", "diwali", "celebration", "cultural", "dance", "music", "concert", "utsav"]):
        for tag in ["#FestivalVibes", "#CultureAndHeritage", "#Celebrations", "#FestiveSeason"]:
            add_hashtag(tag)
    elif any(k in combined_context for k in ["women", "woman", "safety", "crime", "protect", "violence", "harassment"]):
        for tag in ["#SafetyFirst", "#WomenEmpowerment", "#PublicSafety", "#CommunityWatch"]:
            add_hashtag(tag)
    elif any(k in combined_context for k in ["tech", "software", "ai", "cloud", "developer", "conference", "hackathon"]):
        for tag in ["#TechCommunity", "#Innovation", "#Developers", "#FutureTech"]:
            add_hashtag(tag)
    elif any(k in combined_context for k in ["sport", "cricket", "football", "tournament", "championship", "league", "marathon"]):
        for tag in ["#SportsCommunity", "#MatchDay", "#GameOn", "#Championship"]:
            add_hashtag(tag)
    elif any(k in combined_context for k in ["climate", "environment", "forest", "green", "pollution", "nature", "earth"]):
        for tag in ["#ClimateAction", "#SaveOurPlanet", "#Sustainability", "#GreenFuture"]:
            add_hashtag(tag)
    elif any(k in combined_context for k in ["health", "medical", "hospital", "doctor", "wellness", "mental health"]):
        for tag in ["#PublicHealth", "#HealthAwareness", "#WellnessMatters"]:
            add_hashtag(tag)
    elif any(k in combined_context for k in ["student", "school", "education", "college", "university", "exam"]):
        for tag in ["#EducationFirst", "#StudentSupport", "#FutureLeaders"]:
            add_hashtag(tag)
    elif any(k in combined_context for k in ["protest", "strike", "rally", "demonstration", "march"]):
        for tag in ["#ProtestNews", "#StandTogether", "#VoiceOfPeople"]:
            add_hashtag(tag)

    # G. Regional News / Updates Tag (sanitized and clean, e.g. #GujaratUpdates)
    if primary_region:
        primary_reg_clean = to_hashtag(primary_region).lstrip("#")
        add_hashtag(f"#{primary_reg_clean}Updates")

    # IMPORTANT: Hashtags must appear first, Keywords second
    return {
        "hashtags": selected_hashtags if max_hashtags is None else selected_hashtags[:max_hashtags],
        "keywords": selected_keywords if max_keywords is None else selected_keywords[:max_keywords],
    }


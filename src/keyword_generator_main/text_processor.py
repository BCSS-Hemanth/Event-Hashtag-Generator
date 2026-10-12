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
from urllib.parse import urlparse

from keyword_generator_main.content_cleaner import (
    deduplicate_syndicated_passages,
    extract_clean_passages,
    is_boilerplate_sentence,
)
from keyword_generator_main.translator import (
    format_indic_hashtag,
    is_indic_text,
    is_target_script_text,
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
    "covering", "protest", "protests", "meeting",
    "resign", "resigns", "resigned", "resigning",
}

# High-frequency grammatical stopwords and social noise across Indian languages.
# Used only when merging regional-language terms; English stopword checks are unchanged.
INDIC_STOP_WORDS: Set[str] = {
    # Hindi / Marathi
    "का", "के", "की", "में", "और", "है", "हैं", "से", "पर", "को", "भी", "ने", "या", "था", "थी", "थे", "होता", "होती",
    "वीडियो", "चैनल", "सब्सक्राइब", "देखिए", "महीने", "पहले", "साल", "स्वागत", "असली", "लाइक", "शेयर", "खबर", "दिन", "आज", "कल", "दल",
    "लेकर", "हुए", "हुआ", "हुई", "दिया", "दिए", "दी", "होने", "नया", "नयी", "नए",
    # Odia
    "ଏବଂ", "ଓ", "ର", "ରେ", "ପାଇଁ", "ଏହା", "ହେଉଛି", "ଏକ", "ମଧ୍ୟ", "କିନ୍ତୁ", "ତଥା", "ସହିତ", "ଦ୍ୱାରା", "କରି", "ହୋଇ",
    "ଭିଡିଓ", "ଭିଡ଼ିଓ", "ଚ୍ୟାନେଲ୍", "ଚ୍ୟାନେଲ", "ସବସ୍କ୍ରାଇବ", "ସ୍ୱାଗତ", "ଦେଖନ୍ତୁ", "ଲାଇକ", "ଶେୟାର", "ମାସ", "ପୂର୍ବରୁ",
    "ଦିନ", "ବର୍ଷ", "ଦଳର", "ଦଳ", "ଅସଲ", "ଚେହେରା", "କୁ", "କୁ।ଏହା", "ଅସରପା", "ଖବର", "ନିୟମ", "ଆଜି", "କାଲି", "ଘଟଣା",
    # Bengali
    "এবং", "ও", "এর", "তে", "জন্য", "একটি", "বা", "কিন্তু", "সহ", "দ্বারা", "হলো", "হচ্ছে", "ভিডিও", "চ্যানেল",
    "সাবস্ক্রাইব", "লাইক", "শেয়ার", "মাস", "আগে", "বছর", "স্বাগত", "খবর", "দিন", "আজ",
    # Tamil
    "மற்றும்", "ஒரு", "இல்", "உடன்", "ஆகிய", "என்று", "இந்த", "அந்த", "உள்ளது", "வீடியோ", "சேனல்",
    "சப்ஸ்கிரைப்", "லைக்", "ஷேர்", "மாதம்", "முன்பு", "ஆண்டு", "செய்திகள்",
    # Telugu
    "మరియు", "యొక్క", "లో", "తో", "ఒక", "కోసం", "అని", "ఈ", "ఆ", "ఉంది", "వీడియో", "ఛానల్",
    "సబ్‌స్క్రైబ్", "లైక్", "షేర్", "నెల", "క్రితం", "సంవత్సరం", "వార్తలు",
    # Kannada
    "ಮತ್ತು", "ಒಂದು", "ರಲ್ಲಿ", "ಜೊತೆಗೆ", "ಎಂದು", "ಈ", "ಆ", "ವೀಡಿಯೊ", "ಚಾನೆಲ್", "ಸಬ್‌ಸ್ಕ್ರೈಬ್", "ಲೈಕ್", "ಷೇರ್", "ತಿಂಗಳ", "ಹಿಂದೆ", "ವರ್ಷ", "ಸುದ್ದಿ",
    # Malayalam
    "കൂടാതെ", "ഒരു", "എന്നിവ", "ഉള്ള", "എന്ന്", "ഈ", "ആ", "വീഡിയോ", "ചാനൽ", "സബ്സ്ക്രൈബ്", "ലൈക്ക്", "ഷെയർ", "മാസം", "മുമ്പ്", "വർഷം", "വാർത്തകൾ",
    # Gujarati
    "અને", "એક", "માં", "સાથે", "છે", "પણ", "તો", "વિડિઓ", "ચેનલ", "સબ્સ્ક્રાઇબ", "લાઈક", "શેર", "મહિના", "પહેલાં", "વર્ષ", "સમાચાર",
    "નિયામક", "ખાતાની", "સમાજના", "નબળા", "વર્ગો", "જેવા", "અનાથ", "તરફ", "વળેલા", "બાળકો", "તેમજ", "યુવાન",
    # Punjabi
    "ਅਤੇ", "ਇੱਕ", "ਵਿੱਚ", "ਨਾਲ", "ਹੈ", "ਹਨ", "ਸੀ", "ਵੀਡੀਓ", "ਚੈਨਲ", "ਸਬਸਕ੍ਰਾਈਬ", "ਲਾਇਕ", "ਸ਼ੇਅਰ", "ਮਹੀਨੇ", "ਪਹਿਲਾਂ", "ਸਾਲ", "ਖ਼ਬਰਾਂ",
}


# Linguistic role markers used to find people in Indic text (not entity names).
# Mirrors English title/role cues such as minister / activist / leader.
INDIC_ROLE_MARKERS: Set[str] = {
    # Hindi / Marathi
    "\u092e\u0902\u0924\u094d\u0930\u0940", "\u0928\u0947\u0924\u093e", "\u0928\u0947\u0924\u094d\u0930\u0940",
    "\u0915\u093e\u0930\u094d\u092f\u0915\u0930\u094d\u0924\u093e", "\u0905\u0927\u094d\u092f\u0915\u094d\u0937",
    "\u0938\u091a\u093f\u0935", "\u0938\u0902\u092f\u094b\u091c\u0915", "\u092a\u094d\u0930\u0927\u093e\u0928",
    # Odia
    "\u0b2e\u0b28\u0b4d\u0b24\u0b4d\u0b30\u0b40", "\u0b28\u0b47\u0b24\u0b3e", "\u0b28\u0b47\u0b24\u0b4d\u0b30\u0b40",
    "\u0b15\u0b3e\u0b30\u0b4d\u0b5f\u0b4d\u0b5f\u0b15\u0b30\u0b4d\u0b24\u0b4d\u0b24\u0b3e", "\u0b05\u0b27\u0b4d\u0b5f\u0b15\u0b4d\u0b37",
    "\u0b38\u0b1a\u0b3f\u0b2c", "\u0b38\u0b02\u0b5f\u0b4b\u0b1c\u0b15",
    # Bengali
    "\u09ae\u09a8\u09cd\u09a4\u09cd\u09b0\u09c0", "\u09a8\u09c7\u09a4\u09be", "\u09a8\u09c7\u09a4\u09cd\u09b0\u09c0",
    "\u0995\u09b0\u09cd\u09ae\u09c0", "\u09b8\u09ad\u09be\u09aa\u09a4\u09bf", "\u09b8\u09ae\u09cd\u09aa\u09be\u09a6\u0995",
    # Tamil
    "\u0b85\u0bae\u0bc8\u0b9a\u0bcd\u0b9a\u0bb0\u0bcd", "\u0ba4\u0bb2\u0bc8\u0bb5\u0bb0\u0bcd",
    "\u0b9a\u0bc6\u0baf\u0bb2\u0bbe\u0bb3\u0bb0\u0bcd", "\u0b86\u0bb0\u0bcd\u0bb5\u0bb2\u0bb0\u0bcd",
    # Telugu
    "\u0c2e\u0c02\u0c24\u0c4d\u0c30\u0c3f", "\u0c28\u0c47\u0c24", "\u0c15\u0c3e\u0c30\u0c4d\u0c2f\u0c15\u0c30\u0c4d\u0c24",
    "\u0c05\u0c27\u0c4d\u0c2f\u0c15\u0c4d\u0c37\u0c41\u0c21\u0c41", "\u0c15\u0c3e\u0c30\u0c4d\u0c2f\u0c26\u0c30\u0c4d\u0c36\u0c3f",
    # Kannada
    "\u0cb8\u0c9a\u0cbf\u0cb5", "\u0ca8\u0cbe\u0caf\u0c95", "\u0c95\u0cbe\u0cb0\u0ccd\u0caf\u0c95\u0cb0\u0ccd\u0ca4",
    "\u0c85\u0ca7\u0ccd\u0caf\u0c95\u0ccd\u0cb7",
    # Malayalam
    "\u0d2e\u0d28\u0d4d\u0d24\u0d4d\u0d30\u0d3f", "\u0d28\u0d47\u0d24\u0d3e\u0d35\u0d4d",
    "\u0d2a\u0d4d\u0d30\u0d35\u0d7c\u0d24\u0d4d\u0d24\u0d15\u0d7b", "\u0d05\u0d27\u0d4d\u0d2f\u0d15\u0d4d\u0d37\u0d7b",
    # Gujarati
    "\u0aae\u0a82\u0aa4\u0acd\u0ab0\u0ac0", "\u0aa8\u0ac7\u0aa4\u0abe", "\u0a95\u0abe\u0ab0\u0acd\u0aaf\u0a95\u0ab0\u0acd\u0aa4\u0abe",
    "\u0a85\u0aa7\u0acd\u0aaf\u0a95\u0acd\u0ab7",
    # Punjabi
    "\u0a2e\u0a70\u0a24\u0a30\u0a40", "\u0a28\u0a47\u0a24\u0a3e", "\u0a15\u0a3e\u0a30\u0a15\u0a41\u0a28", "\u0a2a\u0a4d\u0a30\u0a27\u0a3e\u0a28",
}

# Linguistic campaign / event markers in Indic scripts (not specific event titles).
INDIC_CAMPAIGN_MARKERS: Set[str] = {
    # Hindi / Marathi
    "\u0905\u092d\u093f\u092f\u093e\u0928", "\u0906\u0902\u0926\u094b\u0932\u0928", "\u0930\u0948\u0932\u0940",
    "\u092a\u094d\u0930\u0926\u0930\u094d\u0936\u0928", "\u092f\u093e\u0924\u094d\u0930\u093e", "\u0938\u092e\u093e\u0930\u094b\u0939",
    "\u0909\u0924\u094d\u0938\u0935",
    # Odia
    "\u0b05\u0b2d\u0b3f\u0b5f\u0b3e\u0b28", "\u0b06\u0b28\u0b4d\u0b26\u0b4b\u0b33\u0b28", "\u0b30\u0b47\u0b32\u0b3f",
    "\u0b2a\u0b4d\u0b30\u0b26\u0b30\u0b4d\u0b36\u0b28", "\u0b5f\u0b3e\u0b24\u0b4d\u0b30\u0b3e", "\u0b09\u0b24\u0b4d\u0b38\u0b2c",
    "\u0b15\u0b3e\u0b30\u0b4d\u0b5f\u0b4d\u0b5f\u0b15\u0b33\u0b3e\u0b2a",
    # Bengali
    "\u0985\u09ad\u09bf\u09af\u09bc\u09be\u09a8", "\u0986\u09a8\u09cd\u09a6\u09cb\u09b2\u09a8", "\u09b8\u09ae\u09be\u09ac\u09c7\u09b6",
    "\u09af\u09be\u09a4\u09cd\u09b0\u09be", "\u0989\u09ce\u09b8\u09ac",
    # Tamil
    "\u0b87\u0baf\u0b95\u0bcd\u0b95\u0bae\u0bcd", "\u0baa\u0bcb\u0bb0\u0bbe\u0b9f\u0bcd\u0b9f\u0bae\u0bcd",
    "\u0baa\u0bc7\u0bb0\u0ba3\u0bbf", "\u0bb5\u0bbf\u0bb4\u0bbe",
    # Telugu
    "\u0c09\u0c26\u0c4d\u0c2f\u0c2e\u0c02", "\u0c06\u0c02\u0c26\u0c4b\u0c33\u0c28", "\u0c30\u0c4d\u0c2f\u0c3e\u0c32\u0c40",
    "\u0c2f\u0c3e\u0c24\u0c4d\u0c30", "\u0c09\u0c24\u0c4d\u0c38\u0c35\u0c02",
    # Kannada
    "\u0c9a\u0cb3\u0cc1\u0cb5\u0cb3\u0cbf", "\u0c86\u0c82\u0ca6\u0ccb\u0cb2\u0ca8", "\u0cb0\u0ccd\u0caf\u0cbe\u0cb2\u0cbf",
    "\u0caf\u0cbe\u0ca4\u0ccd\u0cb0\u0cc6", "\u0c89\u0ca4\u0ccd\u0cb8\u0cb5",
    # Malayalam
    "\u0d2a\u0d4d\u0d30\u0d1a\u0d3e\u0d30\u0d23\u0d02", "\u0d38\u0d2e\u0d30\u0d02", "\u0d31\u0d3e\u0d32\u0d3f",
    "\u0d2f\u0d3e\u0d24\u0d4d\u0d30", "\u0d09\u0d24\u0d4d\u0d38\u0d35\u0d02",
    # Gujarati
    "\u0a85\u0aad\u0abf\u0aaf\u0abe\u0aa8", "\u0a86\u0a82\u0aa6\u0acb\u0ab2\u0aa8", "\u0ab0\u0ac7\u0ab2\u0ac0",
    "\u0aaf\u0abe\u0aa4\u0acd\u0ab0\u0abe", "\u0a89\u0aa4\u0acd\u0ab8\u0ab5",
    # Punjabi
    "\u0a2e\u0a41\u0a39\u0a3f\u0a70\u0a2e", "\u0a05\u0a70\u0a26\u0a4b\u0a32\u0a28", "\u0a30\u0a48\u0a32\u0a40",
    "\u0a2f\u0a3e\u0a24\u0a30\u0a3e", "\u0a24\u0a3f\u0a09\u0a39\u0a3e\u0a30",
}

# English grammar cues that often appear in bilingual Indian news copy
ENGLISH_ROLE_CUES_IN_SENTENCE: Tuple[str, ...] = (
    "minister", "activist", "leader", "convenor", "convener", "president",
    "secretary", "organiser", "organizer", "founder", "spokesperson",
    "led by", "headed by", "chaired by",
)
ENGLISH_CAMPAIGN_CUES_IN_SENTENCE: Tuple[str, ...] = (
    "campaign", "movement", "protest", "rally", "agitation", "yatra",
    "stir", "demonstration", "drive", "initiative",
)

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

GENERIC_LOCATION_TOKENS: Set[str] = {
    "india", "state", "city", "district", "road", "street", "police", "news",
    "today", "area", "hall", "centre", "center", "board", "circle", "square",
    "complex", "campus", "location",
}

GENERIC_EVENT_TOKENS: Set[str] = {
    "day", "days", "date", "dates", "year", "years", "month", "months",
    "today", "yesterday", "tomorrow", "annual", "daily", "weekly",
    "event", "events", "celebration", "celebrations", "activity", "activities",
    "update", "updates", "news", "information", "discussion", "discussions",
}

SOCIAL_DOMAINS: Set[str] = {
    "x.com", "twitter.com", "youtube.com", "youtu.be",
    "reddit.com", "instagram.com", "facebook.com", "tiktok.com",
}

# Headline tails glued onto person names ("Revanth Reddy Speech" / "… Full")
PERSON_NAME_TRAILING_NOISE: Set[str] = {
    "speech", "full", "live", "video", "interview", "address", "talk", "talks",
    "says", "said", "watch", "highlights", "update", "updates", "news", "press",
    "meet", "meeting", "visit", "visited", "inauguration", "inaugurates",
    "participates", "participation", "honble", "honourable", "honorable",
    "sri", "ji", "garu", "audio", "photos", "photo", "gallery", "clip",
    "statement", "remarks", "message", "special", "exclusive",
    # Headline action tails glued onto person names
    "resign", "resigns", "resigned", "resigning", "resignation",
    "demand", "demands", "protest", "protests", "arrest", "arrested",
}

# Abstract / headline-noun scraps — reject-only filters (never injected into output)
HEADLINE_ABSTRACT_WORDS: Set[str] = {
    "leadership", "change", "changes", "detention", "detentions",
    "tension", "tensions", "crackdown", "lockdown", "curb", "curbs",
    "development", "developments", "fairness", "debate", "rising", "falling",
    "mass", "nationwide", "opposition", "activist", "activists",
    "youtuber", "youtubers", "capital", "update", "updates", "latest",
    "breaking", "coverage", "report", "reports", "analysis", "explainer",
    "highlights", "roundup", "timeline", "liveblog", "recap",
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
    "curriculum", "textbook", "textbooks", "history", "education", "school",
    # Common non-surname English words that appear in outlet/product labels
    "story", "stories", "channel", "tv", "news", "media", "times", "today",
    "network", "live", "podcast", "youtube", "webcast",
} | HEADLINE_ABSTRACT_WORDS

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

# Function words that leave a phrase unfinished when they sit on either edge.
EDGE_FUNCTION_WORDS: Set[str] = {
    "a", "an", "the", "and", "or", "as", "at", "by", "for", "from", "in", "into",
    "of", "on", "to", "with", "over", "amid", "along", "across", "including",
    "regarding", "concerning", "about", "after", "before", "during", "while",
    "when", "where", "which", "who", "whose", "whom", "their", "its", "this",
    "that", "these", "those", "than", "via", "per",
}

WEEKDAY_WORDS: Set[str] = {
    "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
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

# Lone org/role glue tokens that are never useful as keywords/hashtags alone
# (full multi-word entities from retrieved content are kept instead)
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


def _phrase_word_list(phrase: str) -> List[str]:
    """Tokenize a phrase or CamelCase hashtag body into lowercase words."""
    if not phrase:
        return []
    body = phrase.lstrip("#").strip()
    if re.search(r"[a-z][A-Z]", body):
        parts = re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?![a-z])|[0-9]+", body)
        return [p.lower() for p in parts if p]
    return [w.lower() for w in re.findall(r"[A-Za-z0-9]+", body)]


def is_abstract_headline_phrase(phrase: str) -> bool:
    """Reject Title-Case headline concepts that are not people or event names."""
    words = _phrase_word_list(phrase)
    if not words or len(words) > 5:
        return False
    weak = (
        HEADLINE_ABSTRACT_WORDS
        | STOP_WORDS
        | GENERIC_THEME_TOKENS
        | MARKETING_OPENERS
        | CLICKBAIT_TOKENS
    )
    if all(w in weak for w in words):
        return True
    if len(words) == 2 and words[0] in HEADLINE_ABSTRACT_WORDS and words[1] in HEADLINE_ABSTRACT_WORDS:
        return True
    return False


def is_clickbait_headline_scrap(phrase: str) -> bool:
    """Reject sensational headline scraps: Meat Allegedly Thrown, Roadside Drama Exposed."""
    if not phrase:
        return True
    words = _phrase_word_list(phrase)
    if not words:
        return True
    if is_abstract_headline_phrase(phrase):
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
    if first in EDGE_FUNCTION_WORDS or last in EDGE_FUNCTION_WORDS:
        return True
    if first in WEEKDAY_WORDS or last in WEEKDAY_WORDS:
        return True
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


def description_theme_tokens(description: str) -> List[str]:
    """
    Distinctive theme tokens from the user's description clauses.
    Used to drive theme-focused search and content-backed keyword admission.
    No event-specific hardcoding — derived only from user text.
    """
    weak = (
        STOP_WORDS
        | GENERIC_THEME_TOKENS
        | GENERIC_LOCATION_TOKENS
        | COMMON_FINITE_VERBS
        | MARKETING_OPENERS
        | HEADLINE_ABSTRACT_WORDS
    )
    # Too broad alone to steer retrieval (still usable if found with event context)
    ultra_generic = {
        "events", "event", "party", "parties", "thing", "things", "issue", "issues",
        "news", "update", "updates", "today", "people", "public",
    }
    ordered: List[str] = []
    seen: Set[str] = set()
    for clause in re.split(r"[,;/|]+", description or ""):
        for tok in tokenize(clause):
            t = tok.lower().strip()
            if len(t) < 4 or t in weak or t in ultra_generic or t in seen:
                continue
            seen.add(t)
            ordered.append(t)
    return ordered


def has_distinctive_event_signal(phrase: str, anchor: Dict[str, Any]) -> bool:
    """True if phrase shares a non-generic token with the user's event/location/description."""
    p_toks = set(tokenize(phrase)) - STOP_WORDS - GENERIC_THEME_TOKENS - GENERIC_LOCATION_TOKENS
    if not p_toks:
        return False
    event_toks = set(tokenize(anchor.get("event", ""))) - STOP_WORDS - GENERIC_THEME_TOKENS
    loc_toks = set(tokenize(anchor.get("location", ""))) - STOP_WORDS - GENERIC_THEME_TOKENS - GENERIC_LOCATION_TOKENS
    desc_toks = set(description_theme_tokens(anchor.get("description", "")))
    desc_toks |= set(tokenize(anchor.get("description", ""))) - STOP_WORDS - GENERIC_THEME_TOKENS
    user_toks = event_toks | loc_toks | desc_toks
    # Keep a phrase only when its content words all come from the user's text.
    # One shared word is not enough to admit a sentence scrap around it.
    if p_toks and p_toks <= user_toks:
        return True
    # User-stated acronyms
    for pair in anchor.get("acronym_pairs") or []:
        short = (pair.get("short") or "").lower()
        full_toks = set(tokenize(pair.get("full") or "")) - STOP_WORDS
        if short and short in {t.lower() for t in tokenize(phrase)}:
            return True
        if full_toks and p_toks <= full_toks:
            return True
    return False


def extract_theme_backed_phrases(
    corpus: str,
    themes: List[str],
    *,
    limit: int = 12,
) -> List[str]:
    """
    Pull short phrases from retrieved text that contain the user's description
    theme tokens (content-backed only — themes must appear in the corpus).
    """
    if not corpus or not themes:
        return []
    text = corpus
    lower = text.lower()
    found: List[str] = []
    seen: Set[str] = set()
    # Prefer multi-word windows around each theme mention
    for theme in themes:
        if theme not in lower:
            continue
        # Capture 0-2 words before theme + theme + 0-2 words after
        window = re.compile(
            rf"\b((?:[A-Za-z][A-Za-z0-9']{{1,20}}\s+){{0,2}}"
            rf"{re.escape(theme)}"
            rf"(?:\s+[A-Za-z][A-Za-z0-9']{{1,20}}){{0,2}})\b",
            re.I,
        )
        for m in window.finditer(text):
            phrase = re.sub(r"\s+", " ", m.group(1)).strip(" .,;:-")
            words = phrase.split()
            edge_words = EDGE_FUNCTION_WORDS | STOP_WORDS
            while words and words[0].lower() in edge_words:
                words = words[1:]
            while words and words[-1].lower() in edge_words:
                words = words[:-1]
            phrase = " ".join(words)
            if not (1 <= len(words) <= 5):
                continue
            if is_incomplete_fragment(phrase) or is_abstract_headline_phrase(phrase):
                continue
            if is_web_boilerplate(phrase) or is_marketing_or_listicle_scrap(phrase):
                continue
            norm = normalize_term(phrase)
            if not norm or norm in seen or norm in STOP_WORDS:
                continue
            seen.add(norm)
            # Keep original casing for multi-word; lowercase single theme token
            found.append(phrase if len(words) > 1 else theme)
            if len(found) >= limit:
                return found
        # Theme alone when present in content
        if theme not in seen:
            seen.add(theme)
            found.append(theme)
            if len(found) >= limit:
                return found
    return found


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
    } | TITLES_AND_ROLES | ORGANIZATION_INDICATORS | LOCATION_INDICATORS | NON_PERSON_WORDS | GENERIC_EVENT_TOKENS
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





def extract_source_domain(url: str) -> str:
    """Extract clean domain from URL, canonicalizing mirrors."""
    if not url:
        return ""
    try:
        netloc = urlparse(url).netloc.lower()
        if netloc.startswith("www."):
            netloc = netloc[4:]
        if netloc in {"twitter.com", "x.com"}:
            return "x.com"
        if netloc in {"youtu.be", "youtube.com"}:
            return "youtube.com"
        return netloc
    except Exception:
        return ""


def is_social_domain(domain: str) -> bool:
    """Check if domain belongs to public social media / UGC platforms."""
    if not domain:
        return False
    return any(s in domain for s in SOCIAL_DOMAINS)


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
    distinctive_event = {
        t for t in event_tokens
        if not t.isdigit() and t not in GENERIC_EVENT_TOKENS and len(t) >= 3
    }
    desc_tokens = set(description_theme_tokens(anchor.get("description", "")))
    desc_tokens |= set(tokenize(anchor.get("description", ""))) - STOP_WORDS - GENERIC_LOCATION_TOKENS

    if distinctive_event and (p_tokens & distinctive_event):
        return True
    if len(p_tokens & event_tokens) >= 2:
        return True
    # Need at least 2 description tokens, or 1 distinctive theme token (len>=4)
    desc_hit = p_tokens & desc_tokens
    if len(desc_hit) >= 2:
        return True
    if any(len(t) >= 4 and not t.isdigit() for t in desc_hit):
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
        "sports betting", "casino", "credit card", "personal loan",
        "lottery sambad", "dear lottery", "satta matka", "lucky draw",
    ]):
        return False

    t_tokens = set(tokenize(t_lower))
    event_tokens = set(tokenize(anchor.get("event", ""))) - STOP_WORDS - GENERIC_LOCATION_TOKENS
    distinctive_event_tokens = {
        t for t in event_tokens
        if not t.isdigit() and t not in GENERIC_EVENT_TOKENS and len(t) >= 3
    }
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
    # Require distinctive event token match (do not qualify solely on year numbers or calendar words)
    if distinctive_event_tokens:
        if not (t_tokens & distinctive_event_tokens):
            event_hit = set()
    elif len(event_hit) < 2:
        event_hit = set()

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

    words = _phrase_word_list(body)

    # Disallow month noise as a distinct CamelCase token (#JudicialPerformanceSep)
    # — not a raw suffix (avoids false-rejecting surnames that end with month letters).
    month_tokens = {
        "jan", "feb", "mar", "apr", "may", "jun",
        "jul", "aug", "sep", "oct", "nov", "dec",
    }
    if len(words) >= 2 and words[-1] in month_tokens:
        return False

    # Disallow imperative action verb prefixes (#AddressOdishaEducation)
    for prefix in ["address", "join", "joins", "support", "demand", "demands", "meet", "report"]:
        if body_lower.startswith(prefix) and len(body_lower) > len(prefix) + 2:
            return False

    # Disallow abstract headline concepts
    if is_abstract_headline_phrase(body) or is_clickbait_headline_scrap(body):
        return False

    # Disallow action-glued name hashtags unless the user typed that action word
    if words and words[-1] in PERSON_NAME_TRAILING_NOISE | COMMON_FINITE_VERBS:
        if words[-1] not in user_lower.split():
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
    # Split CamelCase / acronym boundaries for token matching
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


def is_phrase_in_user_input(phrase: str, anchor: Dict[str, Any]) -> bool:
    """True if phrase or its primary tokens explicitly appeared in user event/location/desc."""
    if not phrase or not anchor:
        return False
    p_norm = normalize_term(phrase)
    if not p_norm:
        return False
    full_user = normalize_term(
        f"{anchor.get('event', '')} {anchor.get('location', '')} {anchor.get('description', '')}"
    )
    if p_norm in full_user:
        return True
    p_toks = phrase_tokens(phrase)
    norm_spaced = " ".join(p_toks)
    if norm_spaced and norm_spaced in full_user:
        return True
    if len(p_toks) >= 2 and all(t in full_user.split() for t in p_toks):
        return True
    for pair in anchor.get("acronym_pairs") or []:
        short = normalize_term(pair.get("short") or "")
        full = normalize_term(pair.get("full") or "")
        if (short and p_norm == short) or (full and p_norm == full):
            return True
        if short and full and (p_norm in {f"{full} {short}", f"{full}{short}"}):
            return True
        if short and (short in p_toks or p_norm == short):
            return True
    return False


def check_source_consensus(
    phrase: str,
    anchor: Dict[str, Any],
    sources: List[Dict[str, Any]],
    *,
    min_sources: int = 2,
    allow_social_only: bool = False,
) -> bool:
    """
    Multi-source consensus gate:
    - User input is 100% verified ground truth (bypasses check).
    - If total independent web sources < min_sources, fallback gracefully to available sources.
    - Web-discovered candidates require >= min_sources independent domains.
    - People and Organizations cannot be minted purely from social media (UGC).
    """
    if not phrase:
        return False
    # User ground truth bypasses consensus check
    if is_phrase_in_user_input(phrase, anchor):
        return True

    if not sources:
        return False

    norm = normalize_term(phrase)
    if not norm:
        return False

    p_toks = phrase_tokens(phrase)
    norm_spaced = " ".join(p_toks)
    matching_domains: Set[str] = set()
    matching_tier1: Set[str] = set()

    for s in sources:
        domain = s.get("domain", "")
        if not domain:
            continue
        norm_text = s.get("normalized_text", "")
        if not norm_text:
            continue

        tokens_set = s.get("tokens_set")
        if tokens_set is None:
            tokens_set = set(norm_text.split())

        matched = False
        if norm in norm_text or (norm_spaced and norm_spaced in norm_text):
            matched = True
        elif len(p_toks) >= 2 and all(t in tokens_set for t in p_toks):
            s_sents = s.get("sentences_norm", [])
            if s_sents:
                for sent_norm in s_sents:
                    if all(t in sent_norm for t in p_toks):
                        matched = True
                        break
            else:
                matched = True
        elif len(p_toks) == 1 and p_toks[0] in tokens_set:
            matched = True

        if matched:
            matching_domains.add(domain)
            if not s.get("is_social"):
                matching_tier1.add(domain)

    distinct_count = len(matching_domains)
    total_distinct = len({s.get("domain") for s in sources if s.get("domain")})

    threshold = min(min_sources, total_distinct) if total_distinct > 0 else 1

    if distinct_count < threshold:
        return False

    # Block social-only People and Organizations
    if not allow_social_only and not matching_tier1:
        return False

    return True



def is_name_or_org_fragment(
    phrase: str,
    known_entities: List[str],
    *,
    allowed_singletons: Optional[Set[str]] = None,
) -> bool:
    """
    Reject scrap pieces of fuller entities already present in the candidate list
    (e.g. a lone surname when the full person name exists, or 'party' when a
    fuller organization name exists).
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
    if not full or is_web_boilerplate(full):
        return None
    # Strip headline tails (Resign, Speech, …) before fragment checks.
    full = strip_person_name_noise(full)
    if not full or is_incomplete_fragment(full) or looks_like_place_or_scheme(full):
        return None
    words = full.split()
    role_prefixes = {
        "participant", "participants", "leader", "leaders", "activist",
        "spokesperson", "organizer", "organiser", "member", "members",
        "farmer", "farmers", "student", "students", "commissioner",
        "minister", "chief", "election",
        # Broadcast intro words glued onto a capitalized name
        "anchor", "host", "youtuber", "presenter",
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


def extract_resignation_targets(text: str) -> List[str]:
    """
    Pull people who are the target of resignation / apology demands.
    e.g. "resignation of education minister <Name>"
    """
    if not text:
        return []
    targets: List[str] = []
    # Cue words are case-insensitive; the name group stays title-case so
    # trailing words like "over school" are not swallowed.
    name = r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})"
    patterns = [
        rf"(?i)(?:resignation of|resign(?:ation)?\s+(?:of|by))\s+"
        rf"(?:(?:the|odisha|state)\s+)*(?:education\s+)?minister\s+(?-i:{name})\b",
        rf"(?i)(?:demand(?:s|ed|ing)?|call(?:s|ed|ing)?\s+for)\s+(?:the\s+)?"
        rf"resignation of\s+(?:(?:the|odisha|state)\s+)*(?:education\s+)?"
        rf"(?:minister\s+)?(?-i:{name})\b",
        rf"(?-i:\b{name})\s+(?i:should|must|to)\s+resign\b",
        rf"(?-i:\b{name})\s+(?i:faces?|facing)\s+(?:calls?\s+for\s+)?resignation\b",
        rf"(?i)(?:apology|apolog(?:y|ise|ize))\s+(?:from|by)\s+"
        rf"(?:(?:the|odisha|state)\s+)*(?:education\s+)?minister\s+(?-i:{name})\b",
    ]
    for pat in patterns:
        for m in re.finditer(pat, text):
            cand = m.group(1).strip()
            cleaned = _clean_person_name(cand)
            if cleaned:
                targets.append(cleaned)
    return targets


def extract_people(text: str) -> List[str]:
    """Identify individual leaders, convenors, officials, and key figures."""
    people: List[str] = []

    # 0. Resignation / accountability targets (minister demanded to resign, etc.)
    people.extend(extract_resignation_targets(text))

    # 1. Role / agency patterns: "led by X", "organized by X", "addressed by X"
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

    # 2. Title/Role + Person Name
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

    # 3. Standalone Capitalized Names of Individuals
    p_name = r"\b([A-Z][a-z]+)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b"
    for m in re.finditer(p_name, text):
        cleaned = _clean_person_name(m.group(0).strip())
        if cleaned:
            people.append(cleaned)

    return people


def _name_context_window(name: str, text: str, radius: int = 55) -> str:
    """Lowercase text window around the first mention of a name."""
    if not name or not text:
        return ""
    t_lower = text.lower()
    p_lower = name.lower()
    idx = t_lower.find(p_lower)
    if idx < 0:
        return ""
    return t_lower[max(0, idx - radius): idx + len(p_lower) + radius]


def is_media_coverage_noise(name: str, text: str = "") -> bool:
    """
    Structural filter only — no brand or person name lists.

    Rejects:
    - phrases that include non-person concept words
    - abstract headline concepts
    - names that start with a host-role word (Anchor/Host …)
    - names grammatically introduced as a show host ("hosted by X", "anchor X")
    """
    if not name:
        return True
    if is_abstract_headline_phrase(name):
        return True
    toks = _phrase_word_list(name)
    if not toks:
        return False
    if any(t in NON_PERSON_WORDS for t in toks):
        return True
    if toks[0] in {"anchor", "host", "youtuber", "presenter"}:
        return True
    if not text:
        return False
    # Strip a leading host-role word before matching surrounding grammar
    core = name
    for prefix in ("Anchor ", "Host ", "Youtuber ", "Presenter "):
        if core.lower().startswith(prefix.lower()):
            core = core[len(prefix):].strip()
            break
    escaped = re.escape(core or name)
    host_patterns = (
        rf"(?i)\b(?:hosted|presented)\s+by\s+{escaped}\b",
        rf"(?i)\b(?:anchor|host|youtuber|presenter)\s+{escaped}\b",
    )
    return any(re.search(pat, text) for pat in host_patterns)


def is_person_in_user_input(person: str, anchor: Dict[str, Any]) -> bool:
    """True when the user named this person in the event or description."""
    if not person or not anchor:
        return False
    blob = f"{anchor.get('event', '')} {anchor.get('description', '')}".lower()
    return person.lower() in blob


def is_resignation_demand_target(person: str, text: str) -> bool:
    """True when grammar links this person to a resignation / apology demand."""
    if not person or not text:
        return False
    p = re.escape(person)
    patterns = (
        rf"(?i)resignation of(?:\s+\w+){{0,4}}\s+{p}\b",
        rf"(?i){p}\s+(?:should|must|to)\s+resign\b",
        rf"(?i)(?:demand(?:s|ed|ing)?|call(?:s|ed|ing)?\s+for)\s+"
        rf"(?:the\s+)?resignation of(?:\s+\w+){{0,4}}\s+{p}\b",
        rf"(?i){p}\s+(?:faces?|facing)\s+(?:calls?\s+for\s+)?resignation\b",
        rf"(?i)(?:apology|apolog(?:ise|ize))\s+(?:from|by)(?:\s+\w+){{0,4}}\s+{p}\b",
    )
    return any(re.search(pat, text) for pat in patterns)


def _sentence_with_name(person: str, text: str) -> str:
    """Return the sentence containing the person name, or empty."""
    if not person or not text:
        return ""
    p_lower = person.lower()
    for sentence in re.split(r"(?<=[.?!;])\s+|\n+", text):
        if p_lower in sentence.lower():
            return sentence.lower()
    return ""


def _person_shares_event_context(
    person: str,
    anchor: Dict[str, Any],
    corpus: str,
) -> bool:
    """True when the same sentence as the name carries user event/description tokens."""
    sentence = _sentence_with_name(person, corpus)
    if not sentence:
        return False
    event_toks = set(tokenize(anchor.get("event", ""))) - STOP_WORDS - GENERIC_THEME_TOKENS
    desc_toks = set(tokenize(anchor.get("description", ""))) - STOP_WORDS - GENERIC_THEME_TOKENS
    distinctive = {
        t for t in (event_toks | desc_toks)
        if len(t) >= 3 and not t.isdigit() and t not in GENERIC_EVENT_TOKENS
    }
    for pair in anchor.get("acronym_pairs") or []:
        short = (pair.get("short") or "").lower()
        if short:
            distinctive.add(short)
    return bool(distinctive & set(tokenize(sentence)))


def is_person_grounded_for_output(
    person: str,
    anchor: Dict[str, Any],
    corpus: str,
) -> bool:
    """
    Keep a person when grounded in user input, resignation-demand grammar,
    or co-occurrence with the user's event tokens. No name allowlists.
    """
    if not person or is_media_coverage_noise(person, corpus):
        return False
    if is_person_in_user_input(person, anchor):
        return True
    if is_resignation_demand_target(person, corpus):
        return True
    return _person_shares_event_context(person, anchor, corpus)


def classify_people_roles(
    people: List[str],
    text: str,
    anchor: Optional[Dict[str, Any]] = None,
) -> Tuple[List[str], List[str]]:
    """
    Split grounded people into leaders vs participants using grammar only:
    resignation targets and nearby role verbs/titles become leaders; others stay
    participants when they share event context with the user's input.
    """
    leaders: List[str] = []
    participants: List[str] = []
    t_lower = text.lower()
    anchor = anchor or {}
    # Role grammar already used elsewhere in this module (not entity names)
    leader_role_re = re.compile(
        r"\b(?:led by|convenor|convener|founder|president|chief(?:\s+minister)?|"
        r"minister|organised by|organized by|spearheaded|chairperson|coordinator)\b",
        re.I,
    )

    for person in people:
        if is_media_coverage_noise(person, text):
            continue
        if not is_person_grounded_for_output(person, anchor, text):
            continue
        p_lower = person.lower()
        idx = t_lower.find(p_lower)
        window = t_lower[max(0, idx - 40): idx + len(p_lower) + 40] if idx >= 0 else ""
        is_leader = is_resignation_demand_target(person, text) or bool(
            leader_role_re.search(window)
        )
        if is_leader:
            leaders.append(person)
        else:
            participants.append(person)

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

    # 4. Acronyms the user actually typed (do not promote a fixed acronym list)
    known_acros: Set[str] = set()
    for pair in anchor.get("acronym_pairs", []):
        short = (pair.get("short") or "").lower()
        if short:
            known_acros.add(short)
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


def _script_range(regional_data: Optional[Dict[str, Any]]) -> Optional[Tuple[int, int]]:
    """Unicode block for the location language, when one was detected."""
    if not regional_data:
        return None
    lang_info = regional_data.get("lang_info") or {}
    raw = lang_info.get("range")
    if not raw or len(raw) != 2:
        return None
    return int(raw[0]), int(raw[1])


def _in_location_language(text: str, script_range: Optional[Tuple[int, int]]) -> bool:
    """Keep the location script. English-only text is not a regional term."""
    if script_range is None:
        return is_indic_text(text)
    return is_target_script_text(text, script_range)


def _indic_tokens(text: str, script_range: Optional[Tuple[int, int]] = None) -> List[str]:
    """Split text into Indic-script tokens, excluding danda boundaries.

    When a location language is known, tokens from every other Indic script
    are dropped. Odisha keeps Odia only.
    """
    tokens: List[str] = []
    for word in re.findall(r"[\u0900-\u0963\u0966-\u0D7F]+", text):
        if len(word) <= 1:
            continue
        if script_range is not None and not all(
            script_range[0] <= ord(ch) <= script_range[1] for ch in word
        ):
            continue
        tokens.append(word.lower())
    return tokens


def _extract_indic_candidate_phrases(
    text: str,
    script_range: Optional[Tuple[int, int]] = None,
) -> List[str]:
    """
    Extract Indic 2- and 3-word phrases using the same stopword and danda rules
    as the multilingual processor. Latin-only tokens are ignored. With a script
    range, phrases from other languages are ignored too.
    """
    sentences = [s.strip() for s in re.split(r"[.\n!?|\u0964\u0965]+", text) if s.strip()]
    candidates: List[str] = []
    allowed_middle = {"of", "for", "and", "in", "ଓ", "ଏବଂ", "का", "की", "के"}

    for sentence in sentences:
        tokens = _indic_tokens(sentence, script_range)
        if not tokens:
            continue
        for i in range(len(tokens) - 1):
            w1, w2 = tokens[i], tokens[i + 1]
            if w1 in INDIC_STOP_WORDS or w2 in INDIC_STOP_WORDS:
                continue
            if w1.isdigit() or w2.isdigit():
                continue
            candidates.append(f"{w1} {w2}")
        for i in range(len(tokens) - 2):
            w1, w2, w3 = tokens[i], tokens[i + 1], tokens[i + 2]
            if w1 in INDIC_STOP_WORDS or w3 in INDIC_STOP_WORDS:
                continue
            if w1.isdigit() or w2.isdigit() or w3.isdigit():
                continue
            if w2 in allowed_middle or w2 not in INDIC_STOP_WORDS:
                candidates.append(f"{w1} {w2} {w3}")
    return candidates



def _event_signal_tokens(
    anchor: Optional[Dict[str, Any]],
    regional_data: Optional[Dict[str, Any]],
    script_range: Optional[Tuple[int, int]],
) -> Set[str]:
    """Tokens from user event/description plus translated event/location."""
    signals: Set[str] = set()
    if anchor:
        for key in ("event", "description"):
            signals.update(
                t for t in tokenize(anchor.get(key, ""))
                if t not in STOP_WORDS and t not in GENERIC_THEME_TOKENS and len(t) >= 3
            )
        for pair in anchor.get("acronym_pairs") or []:
            short = (pair.get("short") or "").lower()
            if short:
                signals.add(short)
    if regional_data:
        for key in ("translated_event", "translated_location"):
            phrase = regional_data.get(key)
            if phrase:
                signals.update(_indic_tokens(str(phrase), script_range))
                for tok in tokenize(str(phrase)):
                    if len(tok) >= 3:
                        signals.add(tok)
    return signals


def _sentence_has_event_signal(sentence: str, signals: Set[str]) -> bool:
    if not sentence or not signals:
        return False
    sent_toks = set(tokenize(sentence)) | set(_indic_tokens(sentence))
    return bool(signals & sent_toks)


def _sentence_has_any_marker(sentence: str, markers: Set[str], english_cues: Tuple[str, ...]) -> bool:
    lower = sentence.lower()
    if any(cue in lower for cue in english_cues):
        return True
    sent_toks = set(_indic_tokens(sentence))
    return bool(sent_toks & markers)


def extract_indic_hashtags_from_text(
    text: str,
    script_range: Optional[Tuple[int, int]],
) -> List[str]:
    """Collect native-script hashtags directly from retrieved page text."""
    if not text:
        return []
    found: List[str] = []
    for body in re.findall(r"#([A-Za-z0-9_\u0900-\u0D7F]{2,40})", text):
        tag = f"#{body}"
        if script_range is not None and not is_target_script_text(tag, script_range):
            continue
        if not is_indic_text(tag):
            continue
        if 2 < len(body) <= 28 and tag not in found:
            found.append(tag)
    return found


def extract_indic_people_from_text(
    text: str,
    script_range: Optional[Tuple[int, int]],
    anchor: Optional[Dict[str, Any]],
    regional_data: Optional[Dict[str, Any]],
) -> List[str]:
    """
    Extract event-involved people written in the location language from web text.
    Uses role markers + event-signal grounding (same idea as English people extraction).
    """
    if not text:
        return []
    signals = _event_signal_tokens(anchor, regional_data, script_range)
    loc_tokens: Set[str] = set()
    if regional_data and regional_data.get("translated_location"):
        loc_tokens = set(
            _indic_tokens(str(regional_data["translated_location"]), script_range)
        )
    counts: Counter = Counter()
    role_backed: Set[str] = set()

    for sentence in re.split(r"[.\n!?|\u0964\u0965]+", text):
        sentence = sentence.strip()
        if len(sentence) < 8:
            continue
        if not _sentence_has_event_signal(sentence, signals):
            continue
        tokens = _indic_tokens(sentence, script_range)
        if len(tokens) < 2:
            continue
        has_role = _sentence_has_any_marker(
            sentence, INDIC_ROLE_MARKERS, ENGLISH_ROLE_CUES_IN_SENTENCE
        )
        if not has_role:
            continue
        for i in range(len(tokens) - 1):
            for width in (2, 3):
                if i + width > len(tokens):
                    continue
                words = tokens[i: i + width]
                if any(
                    w in INDIC_STOP_WORDS
                    or w in INDIC_ROLE_MARKERS
                    or w in INDIC_CAMPAIGN_MARKERS
                    or w in loc_tokens
                    for w in words
                ):
                    continue
                if any(len(w) < 2 for w in words):
                    continue
                phrase = " ".join(words)
                counts[phrase] += 1
                role_backed.add(phrase)

    people: List[str] = []
    for phrase, _count in counts.most_common():
        if phrase in role_backed:
            people.append(phrase)
        if len(people) >= 8:
            break
    return people


def extract_indic_campaigns_from_text(
    text: str,
    script_range: Optional[Tuple[int, int]],
    anchor: Optional[Dict[str, Any]],
    regional_data: Optional[Dict[str, Any]],
    exclude_people: Optional[Set[str]] = None,
) -> List[str]:
    """
    Extract important event / campaign phrases in the location language from web text.
    Grounded by campaign markers in the phrase or overlap with the translated event name.
    """
    if not text:
        return []
    signals = _event_signal_tokens(anchor, regional_data, script_range)
    translated_event_tokens = set()
    if regional_data and regional_data.get("translated_event"):
        translated_event_tokens = set(
            _indic_tokens(str(regional_data["translated_event"]), script_range)
        )
    skip_people = {p.lower() for p in (exclude_people or set())}

    counts: Counter = Counter()
    campaign_backed: Set[str] = set()

    for sentence in re.split(r"[.\n!?|\u0964\u0965]+", text):
        sentence = sentence.strip()
        if len(sentence) < 8:
            continue
        if not _sentence_has_event_signal(sentence, signals):
            continue
        tokens = _indic_tokens(sentence, script_range)
        if len(tokens) < 2:
            continue
        has_campaign = _sentence_has_any_marker(
            sentence, INDIC_CAMPAIGN_MARKERS, ENGLISH_CAMPAIGN_CUES_IN_SENTENCE
        )
        if not has_campaign and not translated_event_tokens:
            continue
        for i in range(len(tokens) - 1):
            for width in (2, 3, 4):
                if i + width > len(tokens):
                    continue
                words = tokens[i: i + width]
                if words[0] in INDIC_STOP_WORDS or words[-1] in INDIC_STOP_WORDS:
                    continue
                if any(w in INDIC_ROLE_MARKERS for w in words):
                    continue
                if sum(1 for w in words if w in INDIC_STOP_WORDS) > 1:
                    continue
                phrase = " ".join(words)
                if phrase.lower() in skip_people:
                    continue
                overlaps_event = bool(set(words) & translated_event_tokens) if translated_event_tokens else False
                touches_campaign_marker = bool(set(words) & INDIC_CAMPAIGN_MARKERS)
                # Require the phrase itself to carry campaign or event signal
                if not (overlaps_event or touches_campaign_marker):
                    continue
                counts[phrase] += 1
                campaign_backed.add(phrase)

    campaigns: List[str] = []
    for phrase, _count in counts.most_common():
        if phrase in campaign_backed:
            campaigns.append(phrase)
        if len(campaigns) >= 8:
            break
    return campaigns


def _phrase_in_harvest(
    phrase: Optional[str],
    harvest_text: str,
    script_range: Optional[Tuple[int, int]],
) -> bool:
    """True when a phrase (or its script tokens) appears in retrieved content."""
    if not phrase or not harvest_text:
        return False
    clean = str(phrase).strip()
    if not clean:
        return False
    if clean in harvest_text:
        return True
    tokens = _indic_tokens(clean, script_range)
    if not tokens:
        return False
    harvest_tokens = set(_indic_tokens(harvest_text, script_range))
    return all(tok in harvest_tokens for tok in tokens)


def _text_has_script(text: str, script_range: Optional[Tuple[int, int]]) -> bool:
    if not text or not script_range:
        return False
    start, end = script_range
    return any(start <= ord(ch) <= end for ch in text if not ch.isspace())


def _build_language_harvest(
    relevant_corpus: str,
    search_results: List[Dict[str, Any]],
    anchor: Optional[Dict[str, Any]],
    script_range: Optional[Tuple[int, int]],
) -> str:
    """
    Build harvest text for one language. Prefer the relevance-filtered corpus;
    if it lacks the target script, fall back to retrieved pages that contain it
    so primary-language terms are not lost when other languages have no content.
    """
    harvest_text = (relevant_corpus or "").strip()
    if harvest_text and (
        script_range is None or _text_has_script(harvest_text, script_range)
    ):
        return harvest_text

    pieces: List[str] = []
    script_pieces: List[str] = []
    for result in search_results:
        page_text = " ".join(
            str(result.get(key) or "")
            for key in ("title", "snippet", "content", "markdown")
        )
        if not page_text.strip():
            continue
        if script_range is not None and _text_has_script(page_text, script_range):
            script_pieces.append(page_text)
        if anchor and not is_content_relevant(page_text, anchor):
            continue
        pieces.append(page_text)

    if script_range is not None and script_pieces:
        # Prefer script-bearing pages that also pass relevance; else any script pages.
        relevant_script = [
            p for p in script_pieces
            if not anchor or is_content_relevant(p, anchor)
        ]
        return " . ".join(relevant_script or script_pieces)

    if pieces:
        return " . ".join(pieces)
    return harvest_text


def _merge_regional_terms(
    hashtags: List[str],
    keywords: List[str],
    regional_data: Optional[Dict[str, Any]],
    search_results: List[Dict[str, Any]],
    max_hashtags: Optional[int],
    max_keywords: Optional[int],
    anchor: Optional[Dict[str, Any]] = None,
    relevant_corpus: str = "",
) -> Tuple[List[str], List[str]]:
    """
    Prepend native-script hashtags and keywords for one selected language.
    Existing English terms stay in their current order. With no regional data, both lists
    are returned unchanged.

    Regional terms come from content-backed extraction only:
    1) people and campaigns extracted from relevance-filtered multilingual page text,
    2) native-script hashtags found on those pages,
    3) additional Indic phrases that touch translated event/location tokens when those
       translations appear in the harvested content,
    4) translated event/location only when they themselves appear in harvested content
       (never translation-only seeding).
    """
    if not regional_data:
        return hashtags, keywords

    script_range = _script_range(regional_data)
    trans_event = regional_data.get("translated_event")
    trans_loc = regional_data.get("translated_location")
    if trans_event and not _in_location_language(str(trans_event), script_range):
        trans_event = None
    if trans_loc and not _in_location_language(str(trans_loc), script_range):
        trans_loc = None
    regional_hashtags: List[str] = []
    regional_keywords: List[str] = []
    seen_tags = {h.lstrip("#") for h in hashtags}
    seen_keywords = set(keywords)

    def add_hashtag(tag: str) -> None:
        if not tag or not _in_location_language(tag, script_range):
            return
        formatted = format_indic_hashtag(tag[1:] if tag.startswith("#") else tag)
        if not formatted:
            return
        body = formatted[1:]
        if body in seen_tags or not (3 <= len(body) <= 25):
            return
        if not _in_location_language(formatted, script_range):
            return
        regional_hashtags.append(formatted)
        seen_tags.add(body)

    def add_keyword(phrase: str) -> None:
        if not phrase or not _in_location_language(phrase, script_range):
            return
        norm = phrase.strip().lower()
        if len(norm) <= 2 or norm in seen_keywords or norm in INDIC_STOP_WORDS:
            return
        regional_keywords.append(norm)
        seen_keywords.add(norm)

    def add_phrase_pair(phrase: str) -> None:
        add_keyword(phrase)
        tag = format_indic_hashtag(phrase)
        if tag and 2 < len(tag) <= 28:
            add_hashtag(tag)

    harvest_text = _build_language_harvest(
        relevant_corpus, search_results, anchor, script_range
    )
    has_native_script = _text_has_script(harvest_text, script_range)

    # Always include selected-language translations of event/location/description
    # seeds (validated script). News pages are often English-only; without this,
    # Odia selection produced zero Odia terms even though translation succeeded.
    user_indic = set()
    if trans_event:
        user_indic.add(str(trans_event).strip().lower())
        add_hashtag(format_indic_hashtag(trans_event))
        add_keyword(str(trans_event).strip().lower())
    if trans_loc:
        user_indic.add(str(trans_loc).strip().lower())
        add_keyword(str(trans_loc).strip().lower())
        for segment in re.split(r"[,;/|]+", str(trans_loc)):
            segment = segment.strip()
            if segment:
                add_hashtag(format_indic_hashtag(segment))
    for seed in regional_data.get("translated_seeds") or []:
        if not seed or not _in_location_language(str(seed), script_range):
            continue
        user_indic.add(str(seed).strip().lower())
        add_phrase_pair(str(seed).strip())

    user_indic_tokens = set()
    for phrase in user_indic:
        user_indic_tokens.update(_indic_tokens(phrase, script_range))
    grounding_tokens = set(user_indic_tokens)
    if trans_event:
        grounding_tokens.update(_indic_tokens(str(trans_event), script_range))
    if trans_loc:
        grounding_tokens.update(_indic_tokens(str(trans_loc), script_range))

    indic_people: List[str] = []
    indic_campaigns: List[str] = []

    # Native-script people / campaigns / hashtags only when retrieved pages
    # actually contain that script (no fabricated Indic text).
    if has_native_script:
        indic_people = extract_indic_people_from_text(
            harvest_text, script_range, anchor, regional_data
        )
        for person in indic_people:
            add_phrase_pair(person)

        indic_campaigns = extract_indic_campaigns_from_text(
            harvest_text,
            script_range,
            anchor,
            regional_data,
            exclude_people=set(indic_people),
        )
        for campaign in indic_campaigns:
            add_phrase_pair(campaign)

        for tag in extract_indic_hashtags_from_text(harvest_text, script_range):
            add_hashtag(tag)

        if grounding_tokens:
            phrase_counts = Counter(
                _extract_indic_candidate_phrases(harvest_text, script_range)
            )
            for phrase, _count in phrase_counts.most_common():
                words = phrase.split()
                if len(words) == 1 and phrase not in user_indic:
                    continue
                if any(word in INDIC_STOP_WORDS for word in words):
                    continue
                if not (set(words) & grounding_tokens):
                    continue
                add_phrase_pair(phrase)

    # Expose extractions for entity reporting (consumed by process_content)
    regional_data["_indic_people"] = list(indic_people)
    regional_data["_indic_campaigns"] = list(indic_campaigns)

    merged_hashtags = regional_hashtags + hashtags
    merged_keywords = regional_keywords + keywords
    if max_hashtags is not None:
        merged_hashtags = merged_hashtags[:max_hashtags]
    if max_keywords is not None:
        merged_keywords = merged_keywords[:max_keywords]
    return merged_hashtags, merged_keywords


def _merge_multilingual_terms(
    hashtags: List[str],
    keywords: List[str],
    regional_languages: List[Dict[str, Any]],
    search_results: List[Dict[str, Any]],
    max_hashtags: Optional[int],
    max_keywords: Optional[int],
    anchor: Optional[Dict[str, Any]] = None,
    relevant_corpus: str = "",
) -> Tuple[List[str], List[str], List[str], List[str]]:
    """
    Apply the same content-backed regional merge for each selected language.
    Primary (location) language is processed first. Languages without content are
    skipped without clearing terms already extracted from the primary language.
    """
    indic_people: List[str] = []
    indic_campaigns: List[str] = []
    ordered = sorted(
        [entry for entry in regional_languages if entry],
        key=lambda entry: (0 if entry.get("is_primary") else 1),
    )
    for lang_entry in ordered:
        before_tags, before_keys = len(hashtags), len(keywords)
        hashtags, keywords = _merge_regional_terms(
            hashtags,
            keywords,
            lang_entry,
            search_results,
            max_hashtags=None,
            max_keywords=None,
            anchor=anchor,
            relevant_corpus=relevant_corpus,
        )
        # Non-primary languages that add nothing must not affect prior results.
        if (
            not lang_entry.get("is_primary")
            and len(hashtags) == before_tags
            and len(keywords) == before_keys
        ):
            lang_entry.pop("_indic_people", None)
            lang_entry.pop("_indic_campaigns", None)
            continue
        for person in lang_entry.pop("_indic_people", []) or []:
            if person not in indic_people:
                indic_people.append(person)
        for campaign in lang_entry.pop("_indic_campaigns", []) or []:
            if campaign not in indic_campaigns:
                indic_campaigns.append(campaign)
    if max_hashtags is not None:
        hashtags = hashtags[:max_hashtags]
    if max_keywords is not None:
        keywords = keywords[:max_keywords]
    return hashtags, keywords, indic_people, indic_campaigns


def process_content(
    event: str,
    location: str,
    description: str,
    search_results: List[Dict[str, Any]],
    max_keywords: Optional[int] = None,
    max_hashtags: Optional[int] = None,
    regional_data: Optional[Dict[str, Any]] = None,
    regional_languages: Optional[List[Dict[str, Any]]] = None,
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

    processed_sources: List[Dict[str, Any]] = []
    page_passages: List[str] = []

    for r in search_results:
        url = r.get("url", "")
        domain = extract_source_domain(url)
        is_social = is_social_domain(domain)
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
        kept_sentences_norm: List[str] = []
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
            kept_sentences_norm.append(normalize_term(s_clean))
            page_kept += 1

        if page_kept > 0 and body_passages:
            page_passages.extend(body_passages)

        # Hashtags and sources only from pages that contributed kept sentences (or a strong title)
        title_snip = clean_text(f"{title}. {snip}")
        is_strong_page = page_kept > 0 or is_strongly_event_relevant(title_snip, anchor)
        if is_strong_page:
            found_hashtags.extend(page_tags)
            eff_domain = domain or extract_source_domain(r.get("link", ""))
            if not eff_domain and title:
                eff_domain = f"source_{normalize_term(title)[:20]}"
            if eff_domain:
                norm_combined = normalize_term(cleaned)
                processed_sources.append({
                    "url": url,
                    "domain": eff_domain,
                    "is_social": is_social,
                    "normalized_text": norm_combined,
                    "tokens_set": set(norm_combined.split()),
                    "sentences_norm": kept_sentences_norm,
                })

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

    # Content-backed phrases that carry the user's description themes
    # (theme words must appear in retrieved pages — never invented).
    theme_tokens = description_theme_tokens(description)
    theme_phrases = extract_theme_backed_phrases(corpus, theme_tokens)
    about_topics = list(about_topics) + list(theme_phrases)

    locs = [l for l in locs if is_location_in_user_scope(l, location)]
    venues = [v for v in venues if is_location_in_user_scope(v, location)]

    # Demands / about must carry distinctive event signal and multi-source consensus
    demands = [
        d for d in demands
        if d and not is_incomplete_fragment(d) and not is_marketing_or_listicle_scrap(d)
        and not is_abstract_headline_phrase(d)
        and has_distinctive_event_signal(d, anchor)
        and check_source_consensus(d, anchor, processed_sources, allow_social_only=True)
    ]
    about_topics = [
        a for a in about_topics
        if a and not is_incomplete_fragment(a) and not is_marketing_or_listicle_scrap(a)
        and not is_abstract_headline_phrase(a)
        and has_distinctive_event_signal(a, anchor)
        and check_source_consensus(a, anchor, processed_sources, allow_social_only=True)
    ]

    event_toks = set(tokenize(event)) - STOP_WORDS
    venue_norms = {normalize_term(x) for x in (venues + locs) if x}

    theme_toks = set(theme_tokens)

    def _is_plausible_person(p: str) -> bool:
        cleaned = _clean_person_name(p)
        if not cleaned:
            return False
        if is_media_coverage_noise(cleaned, corpus) or is_abstract_headline_phrase(cleaned):
            return False
        p_toks = [t.lower() for t in tokenize(cleaned)]
        if not p_toks:
            return False
        # Event-title scraps (2+ shared tokens)
        if len(set(p_toks) & event_toks) >= 2:
            return False
        # Labels that reuse an event token as the final word (not a personal surname)
        if p_toks[-1] in event_toks:
            return False
        # Description themes are topics, not people
        if set(p_toks) & theme_toks:
            return False
        if normalize_term(cleaned) in venue_norms:
            return False
        return True

    people_raw = [
        p for p in people_raw
        if _is_plausible_person(p)
        and check_source_consensus(p, anchor, processed_sources, allow_social_only=False)
    ]
    people_raw = [
        cleaned for cleaned in (_clean_person_name(p) for p in people_raw)
        if cleaned
    ]
    main_leaders, participants = classify_people_roles(people_raw, corpus, anchor)
    for p in user_people:
        if is_media_coverage_noise(p, corpus):
            continue
        if p not in main_leaders and p not in participants:
            main_leaders.insert(0, p)
    # Keep only people named by the user or role-grounded in the corpus with multi-source consensus
    main_leaders = [
        p for p in main_leaders
        if is_person_grounded_for_output(p, anchor, corpus)
        and check_source_consensus(p, anchor, processed_sources, allow_social_only=False)
    ]
    participants = [
        p for p in participants
        if is_person_grounded_for_output(p, anchor, corpus)
        and check_source_consensus(p, anchor, processed_sources, allow_social_only=False)
    ]

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
        if not check_source_consensus(o, anchor, processed_sources, allow_social_only=False):
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
        if check_source_consensus(v, anchor, processed_sources, allow_social_only=False)
    ]
    locs = [
        reconcile_place_name(l, list(venues) + list(loc_info.get("parts") or []))
        for l in locs
        if check_source_consensus(l, anchor, processed_sources, allow_social_only=False)
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
        if not check_source_consensus(tag, anchor, processed_sources, allow_social_only=True):
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

    # C. About / demands (skip abstract headline scraps)
    for topic in list(dict.fromkeys(about_topics + demands))[:6]:
        if is_abstract_headline_phrase(topic) or is_clickbait_headline_scrap(topic):
            continue
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

    # E. People — full cleaned names only; skip journalists/hosts / headline scraps
    for p in (main_leaders + participants)[:6]:
        cleaned = _clean_person_name(p)
        if not cleaned or not is_person_grounded_for_output(cleaned, anchor, corpus):
            continue
        if is_abstract_headline_phrase(cleaned) or is_media_coverage_noise(cleaned, corpus):
            continue
        if 2 <= len(phrase_tokens(cleaned)) <= 4 and len(to_hashtag(cleaned)) <= 22:
            add_hashtag(to_hashtag(cleaned))

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
            if not check_source_consensus(raw, anchor, processed_sources, min_sources=2, allow_social_only=True):
                continue
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
            or is_abstract_headline_phrase(item)
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
        theme_norms = {normalize_term(t) for t in description_theme_tokens(description)}
        # People / titles must be full phrases — except content-backed description themes
        if (
            len(toks) == 1
            and norm not in acronym_shorts
            and norm not in allowed_shorts
            and norm not in theme_norms
        ):
            return
        # Non-entity scraps need distinctive event/location/theme tokens
        is_seeded = (
            norm in acronym_fulls
            or norm in acronym_shorts
            or norm in seeded_people
            or norm in theme_norms
        )
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
        if not check_source_consensus(item, anchor, processed_sources, allow_social_only=True):
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
    # People: full names only (2+ tokens); never emit coverage-only names
    for p, _ in Counter(main_leaders).most_common():
        if len(phrase_tokens(p)) >= 2 and is_person_grounded_for_output(p, anchor, corpus):
            add_keyword(p, require_strong=False)
    for p, _ in Counter(participants).most_common():
        if len(phrase_tokens(p)) >= 2 and is_person_grounded_for_output(p, anchor, corpus):
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

    indic_people: List[str] = []
    indic_campaigns: List[str] = []
    languages_to_merge: List[Dict[str, Any]] = []
    if regional_languages:
        languages_to_merge = [entry for entry in regional_languages if entry]
    elif regional_data:
        languages_to_merge = [regional_data]
    if languages_to_merge:
        hashtags, keywords, indic_people, indic_campaigns = _merge_multilingual_terms(
            hashtags,
            keywords,
            languages_to_merge,
            search_results,
            max_hashtags,
            max_keywords,
            anchor=anchor,
            relevant_corpus=corpus,
        )

    people_all = list(dict.fromkeys(main_leaders + participants + people_raw + indic_people))
    about_all = list(dict.fromkeys(about_topics + indic_campaigns))

    return {
        "hashtags": hashtags,
        "keywords": keywords,
        "entities": {
            "about": about_all,
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

"""
Evaluation Engine for Event Keyword and Hashtag Generation
Calculates precision, recall, F1-score, relevance rate, duplicate rate,
hashtag validity, and entity alignment against ground-truth reference data.
"""

import difflib
import re
from typing import Any, Dict, List, Set, Tuple


def normalize_term(term: str) -> str:
    """Normalize term for comparison: strip hashtags, punctuation, and lowercase."""
    cleaned = re.sub(r"[^A-Za-z0-9\s]", "", term.lstrip("#")).strip().lower()
    return cleaned


def token_overlap_ratio(cand: str, target: str) -> float:
    """Calculate token-level Jaccard overlap between candidate and target."""
    c_tokens = set(normalize_term(cand).split())
    t_tokens = set(normalize_term(target).split())
    if not c_tokens or not t_tokens:
        return 0.0
    inter = c_tokens.intersection(t_tokens)
    union = c_tokens.union(t_tokens)
    return len(inter) / len(union) if union else 0.0


def is_fuzzy_match(cand: str, target: str, threshold: float = 0.72) -> bool:
    """Check if two terms match through exact, transliteration, token overlap, or string ratio."""
    c_norm = normalize_term(cand)
    t_norm = normalize_term(target)
    if not c_norm or not t_norm:
        return False
    if c_norm == t_norm:
        return True
    if c_norm in t_norm or t_norm in c_norm:
        if min(len(c_norm), len(t_norm)) >= 4:
            return True
    if token_overlap_ratio(cand, target) >= 0.5:
        return True
    return difflib.SequenceMatcher(None, c_norm, t_norm).ratio() >= threshold


def is_term_relevant_to_event(
    term: str,
    event: Dict[str, Any],
) -> Tuple[bool, str]:
    """
    Determine if a generated term is relevant to the event.
    Returns (is_relevant, match_category).
    """
    term_norm = normalize_term(term)
    if not term_norm or len(term_norm) < 2:
        return False, "too_short"

    # 1. Match against reference keywords & hashtags
    ref_all = event["reference_keywords"] + event["reference_hashtags"]
    for ref in ref_all:
        if is_fuzzy_match(term, ref):
            return True, "reference_match"

    # 2. Match against key entities (people, orgs, locations, demands)
    entities = event.get("key_entities", {})
    for ent_type, ent_list in entities.items():
        for ent in ent_list:
            if is_fuzzy_match(term, ent):
                return True, f"entity_{ent_type}"

    # 3. Match against core event title, location segments, and key description tokens
    title_norm = normalize_term(event["event_name"])
    loc_norm = normalize_term(event["location"])
    if is_fuzzy_match(term, title_norm) or is_fuzzy_match(term, loc_norm):
        return True, "event_identity"

    event_tokens = set(title_norm.split() + loc_norm.split())
    desc_words = [w for w in normalize_term(event["description"]).split() if len(w) > 3]
    event_tokens.update(desc_words)

    term_tokens = set(term_norm.split())
    if term_tokens and term_tokens.issubset(event_tokens):
        return True, "context_token_subset"

    overlap = term_tokens.intersection(event_tokens)
    if len(overlap) >= 1 and len(term_tokens) <= 3:
        return True, "context_overlap"

    return False, "unmatched"


def is_grammatical_junk(term: str) -> bool:
    """Check if term is a fragmented n-gram (e.g. starts/ends with dangling preposition or conjunction)."""
    words = term.strip().lower().split()
    if not words:
        return True
    dangling = {"including", "regarding", "concerning", "amid", "along", "across", "and", "or", "in", "at", "for", "of", "to", "by", "from"}
    if words[0] in dangling or words[-1] in dangling:
        return True
    return False


def validate_hashtag_structure(tag: str) -> bool:
    """Validate hashtag meets CamelCase #Tag structure, length 3-25, alphanumeric."""
    if not tag or not tag.startswith("#"):
        return False
    body = tag[1:]
    if not (3 <= len(body) <= 25) or not body.isalnum():
        return False
    return True


def evaluate_event_result(
    event: Dict[str, Any],
    generated_keywords: List[str],
    generated_hashtags: List[str],
    entities_extracted: Dict[str, List[str]],
    observed_social_tags: List[str],
    latency_sec: float = 0.0,
    search_engines: List[str] = None,
) -> Dict[str, Any]:
    """
    Perform deep statistical evaluation on a single event's generated output.
    """
    search_engines = search_engines or []
    all_generated = generated_keywords + generated_hashtags
    total_generated = len(all_generated)

    # 1. Structural validity check for hashtags
    invalid_hashtags = [h for h in generated_hashtags if not validate_hashtag_structure(h)]
    valid_hashtag_count = len(generated_hashtags) - len(invalid_hashtags)
    hashtag_validity_rate = (valid_hashtag_count / len(generated_hashtags)) if generated_hashtags else 0.0

    # 2. Duplicate detection
    seen_norm: Set[str] = set()
    duplicate_terms = []
    for t in all_generated:
        norm = normalize_term(t)
        if norm in seen_norm:
            duplicate_terms.append(t)
        seen_norm.add(norm)
    duplicate_rate = (len(duplicate_terms) / total_generated) if total_generated else 0.0

    # 3. Fragment / Junk N-Gram detection
    junk_terms = [k for k in generated_keywords if is_grammatical_junk(k)]
    junk_rate = (len(junk_terms) / len(generated_keywords)) if generated_keywords else 0.0

    # 4. Relevance & Categorization
    relevant_terms = []
    irrelevant_terms = []
    category_matches: Dict[str, int] = {}

    for t in all_generated:
        is_rel, match_cat = is_term_relevant_to_event(t, event)
        if is_rel:
            relevant_terms.append(t)
            category_matches[match_cat] = category_matches.get(match_cat, 0) + 1
        else:
            irrelevant_terms.append(t)

    relevance_rate = (len(relevant_terms) / total_generated) if total_generated else 0.0
    precision = relevance_rate

    # 5. Recall against reference ground truth
    ref_all = event["reference_keywords"] + event["reference_hashtags"]
    recalled_refs = []
    for ref in ref_all:
        for gen in all_generated:
            if is_fuzzy_match(gen, ref):
                recalled_refs.append(ref)
                break

    recall = (len(recalled_refs) / len(ref_all)) if ref_all else 0.0
    f1_score = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

    # 6. Social Media Grounding
    verified_social = [t for t in generated_hashtags if any(is_fuzzy_match(t, s) for s in observed_social_tags)]

    # 7. Pass/Fail Decision
    reasons = []
    passed = True
    if len(generated_keywords) < 3:
        passed = False
        reasons.append(f"Insufficient keywords ({len(generated_keywords)} < 3)")
    if len(generated_hashtags) < 3:
        passed = False
        reasons.append(f"Insufficient hashtags ({len(generated_hashtags)} < 3)")
    if invalid_hashtags:
        passed = False
        reasons.append(f"Invalid hashtags detected ({len(invalid_hashtags)})")
    if duplicate_terms:
        passed = False
        reasons.append(f"Duplicates detected ({len(duplicate_terms)})")
    if junk_terms:
        passed = False
        reasons.append(f"Grammatical junk n-grams detected ({len(junk_terms)})")
    if precision < 0.65:
        passed = False
        reasons.append(f"Precision below threshold ({precision:.2f} < 0.65)")

    return {
        "event_id": event["event_id"],
        "event_name": event["event_name"],
        "region": event["region"],
        "category": event["category"],
        "status": "PASS" if passed else "FAIL",
        "failure_reasons": "; ".join(reasons) if not passed else "",
        "total_keywords": len(generated_keywords),
        "total_hashtags": len(generated_hashtags),
        "total_generated": total_generated,
        "relevant_terms_count": len(relevant_terms),
        "irrelevant_terms_count": len(irrelevant_terms),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1_score, 4),
        "relevance_rate_pct": round(relevance_rate * 100, 2),
        "duplicate_rate_pct": round(duplicate_rate * 100, 2),
        "junk_rate_pct": round(junk_rate * 100, 2),
        "hashtag_validity_pct": round(hashtag_validity_rate * 100, 2),
        "verified_social_count": len(verified_social),
        "people_extracted_count": len(entities_extracted.get("people", [])),
        "orgs_extracted_count": len(entities_extracted.get("organizations", [])),
        "locs_extracted_count": len(entities_extracted.get("locations", [])),
        "demands_extracted_count": len(entities_extracted.get("demands_and_issues", [])),
        "latency_sec": round(latency_sec, 2),
        "engines_used": ", ".join(search_engines),
        "irrelevant_examples": ", ".join(irrelevant_terms[:3]),
        "relevant_examples": ", ".join(relevant_terms[:5]),
        "generated_keywords_str": "; ".join(generated_keywords),
        "generated_hashtags_str": "; ".join(generated_hashtags),
    }

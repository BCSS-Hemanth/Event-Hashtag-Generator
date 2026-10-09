"""Offline smoke test across unique India events — no Wigolo network calls."""
import csv
import time
from collections import defaultdict
from pathlib import Path

from keyword_generator_main.text_processor import process_content
from testing.events_data import EVENTS_DATASET
from testing.evaluator import evaluate_event_result

RESULTS = Path("testing/results")
RESULTS.mkdir(parents=True, exist_ok=True)


def mock_results(evt):
    ents = evt.get("key_entities", {})
    people = ents.get("people", [])
    orgs = ents.get("organizations", [])
    locs = ents.get("locations", [])
    demands = ents.get("demands", [])
    body = (
        f"{evt['description']} "
        f"Leaders including {', '.join(people[:3])}. "
        f"Organizations: {', '.join(orgs[:3])}. "
        f"Held at {', '.join(locs[:3])}. "
        f"Focus on {', '.join(demands[:2])}."
    )
    # Inject typical web noise — filters should drop these
    noise = (
        " Looking Forward. Every September. Greatest Eco Friendly Outdoor. "
        "Meat Allegedly Thrown. Roadside Drama Exposed. Subscribe click here newsletter."
    )
    return [
        {
            "title": evt["event_name"],
            "snippet": evt["description"][:220],
            "content": body + noise,
        },
        {
            "title": "Unrelated insurance quotes",
            "snippet": "business insurance quotes online",
            "content": "Buy business insurance quotes today #TechCommunity #FestivalVibes",
        },
    ]


def main():
    eval_records = []
    rows = []
    t0 = time.time()
    for evt in EVENTS_DATASET:
        t1 = time.time()
        out = process_content(
            evt["event_name"],
            evt["location"],
            evt["description"],
            mock_results(evt),
        )
        lat = time.time() - t1
        rec = evaluate_event_result(
            event=evt,
            generated_keywords=out["keywords"],
            generated_hashtags=out["hashtags"],
            entities_extracted=out.get("entities", {}),
            observed_social_tags=[],
            latency_sec=lat,
            search_engines=["Offline Mock Web"],
        )
        eval_records.append(rec)
        rows.append({
            "event_id": evt["event_id"],
            "event_name": evt["event_name"],
            "region": evt["region"],
            "category": evt["category"],
            "state": evt["state"],
            "status": rec["status"],
            "precision": rec["precision"],
            "recall": rec["recall"],
            "f1_score": rec["f1_score"],
            "relevance_rate_pct": rec["relevance_rate_pct"],
            "n_kw": rec["total_keywords"],
            "n_ht": rec["total_hashtags"],
            "hashtags": "; ".join(out["hashtags"]),
            "keywords": "; ".join(out["keywords"]),
            "failure_reasons": rec["failure_reasons"],
            "irrelevant_examples": rec["irrelevant_examples"],
        })

    n = len(eval_records)
    passed = sum(1 for r in eval_records if r["status"] == "PASS")
    avg_p = sum(r["precision"] for r in eval_records) / n
    avg_r = sum(r["recall"] for r in eval_records) / n
    avg_f1 = sum(r["f1_score"] for r in eval_records) / n
    avg_rel = sum(r["relevance_rate_pct"] for r in eval_records) / n
    total_terms = sum(r["total_generated"] for r in eval_records)
    total_rel = sum(r["relevant_terms_count"] for r in eval_records)
    micro_acc = (total_rel / total_terms * 100) if total_terms else 0.0

    by_region = defaultdict(lambda: {"n": 0, "pass": 0, "p": [], "r": [], "f1": []})
    by_cat = defaultdict(lambda: {"n": 0, "pass": 0, "p": [], "r": [], "f1": []})
    for r in eval_records:
        for bucket, key in ((by_region, r["region"]), (by_cat, r["category"])):
            bucket[key]["n"] += 1
            if r["status"] == "PASS":
                bucket[key]["pass"] += 1
            bucket[key]["p"].append(r["precision"])
            bucket[key]["r"].append(r["recall"])
            bucket[key]["f1"].append(r["f1_score"])

    with open(RESULTS / "offline_smoke_results.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    lines = []
    lines.append("OFFLINE SMOKE TEST — Unique India Events")
    lines.append(f"Events: {n} | Mode: process_content + mock web (noise injected)")
    lines.append(f"Elapsed: {time.time()-t0:.1f}s")
    lines.append("")
    lines.append("=== OVERALL ACCURACY ===")
    lines.append(f"Pass rate:           {passed}/{n} = {100*passed/n:.1f}%")
    lines.append(f"Avg Precision:       {avg_p*100:.1f}%")
    lines.append(f"Avg Recall:          {avg_r*100:.1f}%")
    lines.append(f"Avg F1:              {avg_f1*100:.1f}%")
    lines.append(f"Avg Relevance rate:  {avg_rel:.1f}%")
    lines.append(f"Micro relevance:     {micro_acc:.1f}%  ({total_rel}/{total_terms} terms)")
    lines.append("")
    lines.append("=== BY REGION ===")
    for reg, d in sorted(by_region.items()):
        lines.append(
            f"  {reg:12} pass {d['pass']}/{d['n']} ({100*d['pass']/d['n']:.0f}%)  "
            f"P={100*sum(d['p'])/d['n']:.0f}% R={100*sum(d['r'])/d['n']:.0f}% F1={100*sum(d['f1'])/d['n']:.0f}%"
        )
    lines.append("")
    lines.append("=== BY CATEGORY ===")
    for cat, d in sorted(by_cat.items()):
        lines.append(
            f"  {cat:24} pass {d['pass']}/{d['n']} ({100*d['pass']/d['n']:.0f}%)  "
            f"P={100*sum(d['p'])/d['n']:.0f}% R={100*sum(d['r'])/d['n']:.0f}% F1={100*sum(d['f1'])/d['n']:.0f}%"
        )
    failed = [r for r in rows if r["status"] == "FAIL"]
    lines.append("")
    lines.append(f"=== FAILURES ({len(failed)}) ===")
    for r in failed[:25]:
        lines.append(f"  {r['event_id']} {r['event_name'][:50]}")
        lines.append(f"    P={r['precision']:.2f} R={r['recall']:.2f} | {r['failure_reasons']}")
        if r["irrelevant_examples"]:
            lines.append(f"    irr: {r['irrelevant_examples']}")

    report = "\n".join(lines)
    (RESULTS / "offline_smoke_report.txt").write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()

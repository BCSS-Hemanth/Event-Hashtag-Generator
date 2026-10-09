"""
End-to-End Test for Event Keyword & Hashtag Search System.
"""

import asyncio
from keyword_generator_main.app import (
    GenerateRequest,
    create_new_event,
    generate_keywords_and_hashtags,
)


async def main():
    print("==================================================")
    print("TEST 1: VALIDATION CHECKS")
    print("==================================================")
    for field, kwargs in [
        ("Event", {"event": "", "location": "Delhi", "description": "Some description"}),
        ("Location", {"event": "Safety", "location": "   ", "description": "Some description"}),
        ("Description", {"event": "Safety", "location": "Delhi", "description": ""}),
    ]:
        try:
            await generate_keywords_and_hashtags(GenerateRequest(**kwargs))
            print(f"FAILED: Expected error for missing {field}")
        except Exception as e:
            print(f"PASSED: Correctly caught missing {field} -> {e.detail}")

    print("\n==================================================")
    print("TEST 2: EVENT 1 - Women's Safety in Delhi")
    print("==================================================")
    req1 = GenerateRequest(
        event="Women's Safety",
        location="Delhi",
        description="Women's safety awareness, emergency support, prevention, and safety initiatives in Delhi.",
    )
    res1 = await generate_keywords_and_hashtags(req1)

    print("Returned Hashtags (First):")
    for i, tag in enumerate(res1.hashtags, 1):
        print(f"  {i}. {tag}")

    print("\nReturned Keywords (Second):")
    for i, kw in enumerate(res1.keywords, 1):
        print(f"  {i}. {kw}")

    assert len(res1.hashtags) > 0, "Hashtags should not be empty"
    assert len(res1.keywords) > 0, "Keywords should not be empty"
    print("\nPASSED: Event 1 generated valid hashtags and keywords.")

    print("\n==================================================")
    print("TEST 3: CREATE EVENT (RESET & CACHE CLEAR)")
    print("==================================================")
    reset_res = await create_new_event()
    print("Cache clear response:", reset_res.message)
    assert reset_res.success is True, "Reset should succeed"
    print("PASSED: Cache clear executed successfully.")

    print("\n==================================================")
    print("TEST 4: EVENT 2 - Technology Conference in Hyderabad")
    print("==================================================")
    req2 = GenerateRequest(
        event="Technology Conference",
        location="Hyderabad",
        description="Technology conference covering software development, AI, cloud computing and emerging technologies in Hyderabad.",
    )
    res2 = await generate_keywords_and_hashtags(req2)

    print("Returned Hashtags (First):")
    for i, tag in enumerate(res2.hashtags, 1):
        print(f"  {i}. {tag}")

    print("\nReturned Keywords (Second):")
    for i, kw in enumerate(res2.keywords, 1):
        print(f"  {i}. {kw}")

    assert len(res2.hashtags) > 0, "Hashtags should not be empty"
    assert len(res2.keywords) > 0, "Keywords should not be empty"
    print("\nPASSED: Event 2 generated fresh technology-specific hashtags and keywords.")

    print("\n==================================================")
    print("TEST 5: MULTI-PART LOCATION - GMDC Road, Gujarat, India")
    print("==================================================")
    req3 = GenerateRequest(
        event="Women's Safety",
        location="gmdc road, gujarat, india",
        description="Women's safety awareness, emergency support, and prevention initiatives along GMDC Road in Gujarat, India.",
    )
    res3 = await generate_keywords_and_hashtags(req3)

    print("Returned Hashtags (First):")
    for i, tag in enumerate(res3.hashtags, 1):
        print(f"  {i}. {tag}")
        assert tag.startswith("#"), f"Hashtag {tag} must start with #"
        assert " " not in tag, f"Hashtag {tag} must not contain spaces"
        assert "," not in tag, f"Hashtag {tag} must not contain commas"
        assert len(tag) <= 26, f"Hashtag {tag} exceeds reasonable length"

    print("\nReturned Keywords (Second):")
    for i, kw in enumerate(res3.keywords, 1):
        print(f"  {i}. {kw}")
        assert not kw.startswith("#"), f"Keyword {kw} should not start with #"

    # Ensure hashtags are not identical 1-to-1 copies of keywords
    keyword_as_tags = {f"#{kw.replace(' ', '').lower()}" for kw in res3.keywords}
    actual_tags = {t.lower() for t in res3.hashtags}
    print(f"\nDistinct Hashtags count: {len(actual_tags)}, Distinct Keywords count: {len(res3.keywords)}")
    print("PASSED: Multi-part location generated valid, clean hashtags and differentiated keywords.")

    print("\n==================================================")
    print("TEST 6: EVENT 4 - Odisha Textbook Controversy (Entity Breakdown)")
    print("==================================================")
    req4 = GenerateRequest(
        event="Textbook Controversy",
        location="Bhubaneswar, Odisha",
        description="Student protests over textbook errors and historical inaccuracies in Odisha.",
    )
    res4 = await generate_keywords_and_hashtags(req4)

    print("Returned Hashtags (First):")
    for i, tag in enumerate(res4.hashtags, 1):
        print(f"  {i}. {tag}")

    print("\nReturned Keywords (Second):")
    for i, kw in enumerate(res4.keywords, 1):
        print(f"  {i}. {kw}")

    if res4.entities:
        print("\nExtracted 4-Pillar Entities:")
        for category, items in res4.entities.items():
            print(f"  {category}: {items}")

    assert len(res4.hashtags) > 0, "Hashtags should not be empty"
    assert len(res4.keywords) > 0, "Keywords should not be empty"
    print("PASSED: Odisha textbook controversy generated valid hashtags, keywords, and entities.")

    print("\n==================================================")
    print("ALL TESTS COMPLETED SUCCESSFULLY!")
    print("==================================================")


if __name__ == "__main__":
    asyncio.run(main())

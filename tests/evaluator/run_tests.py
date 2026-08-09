import json
import os

from app.evaluation.evaluator import evaluate_lesson
from app.retrieval.retriever import retrieve_top_k

TEST_DIR = os.path.dirname(__file__)
TEST_CASES_PATH = os.path.join(TEST_DIR, "test_cases.json")
TOPIC = "Introduction to RAG (Retrieval-Augmented Generation)"


def run():
    with open(TEST_CASES_PATH, "r", encoding="utf-8") as f:
        suite = json.load(f)

    grounding_context = retrieve_top_k(TOPIC)

    results = []
    for case in suite["test_cases"]:
        lesson_path = os.path.join(TEST_DIR, case["lesson_file"])
        with open(lesson_path, "r", encoding="utf-8") as f:
            lesson = f.read()

        evaluation = evaluate_lesson(
            topic=TOPIC,
            grounding_context=grounding_context,
            lesson=lesson,
            attempt_number=1,
        )
        actual_fail_ids = sorted(c.id for c in evaluation.failed_checks())
        expected_fail_ids = sorted(case["expected_fail"])
        results.append(
            {
                "id": case["id"],
                "name": case["name"],
                "expected": expected_fail_ids,
                "actual": actual_fail_ids,
                "match": actual_fail_ids == expected_fail_ids,
                "evaluation": evaluation,
            }
        )

    _print_report(results)
    return results


def _print_report(results: list[dict]) -> None:
    print("=" * 70)
    print("EVALUATOR TEST SUITE RESULTS")
    print("=" * 70)
    for r in results:
        status = "MATCH" if r["match"] else "MISMATCH"
        print(f"[{status}] {r['id']} - {r['name']}")
        print(f"    expected FAIL: {r['expected'] or 'none'}")
        print(f"    actual   FAIL: {r['actual'] or 'none'}")
        if not r["match"]:
            extra = sorted(set(r["actual"]) - set(r["expected"]))
            missing = sorted(set(r["expected"]) - set(r["actual"]))
            checks_by_id = {c.id: c for c in r["evaluation"].checks}
            if extra:
                print(f"    unexpected secondary failure(s) -- test-isolation issue: {extra}")
                for check_id in extra:
                    c = checks_by_id[check_id]
                    print(f"      [{c.id}] evidence: {c.evidence}")
                    print(f"      [{c.id}] fix: {c.fix}")
            if missing:
                print(f"    failed to detect expected failure(s): {missing}")
        print()

    matched = sum(1 for r in results if r["match"])
    print(f"Detection rate: {matched}/{len(results)} cases matched expected failures exactly")


if __name__ == "__main__":
    run()

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PYTHON_ENGINE = PROJECT_ROOT / "python-engine"

sys.path.insert(0, str(PYTHON_ENGINE))

from app.rules.batch_rules import evaluate_batch_rules

CONFIG_PATH = PYTHON_ENGINE / "config" / "rules.json"

with CONFIG_PATH.open("r", encoding="utf-8") as file:
    config = json.load(file)


TEST_CASES = [
    {
        "name": "On-time arrival",
        "created": "2026-11-10T09:00:00",
        "received": "2026-11-10T09:30:00",
        "expected_failures": 0,
    },
    {
        "name": "Exactly at SLA boundary",
        "created": "2026-11-10T09:00:00",
        "received": "2026-11-10T10:00:00",
        "expected_failures": 0,
    },
    {
        "name": "Late arrival",
        "created": "2026-11-10T09:00:00",
        "received": "2026-11-10T10:30:00",
        "expected_failures": 1,
    },
]


all_passed = True

print("\nDQ009 - BATCH TIMELINESS TEST")
print("=" * 75)

for case in TEST_CASES:
    results = evaluate_batch_rules(
        batch_created_at=case["created"],
        batch_received_at=case["received"],
        rules_config=config,
    )

    if len(results) != 1:
        raise AssertionError("Expected exactly one DQ009 result.")

    result = results[0]

    actual_failures = result["failed_count"]
    expected_failures = case["expected_failures"]

    passed_test = actual_failures == expected_failures
    all_passed = all_passed and passed_test

    print(f"\nTest: {case['name']}")
    print(f"Delay: {result['delay_minutes']} minutes")
    print(f"SLA: {result['sla_tolerance_minutes']} minutes")
    print(f"Checked: {result['checked_count']}")
    print(f"Passed: {result['passed_count']}")
    print(f"Failed: {result['failed_count']}")
    print(f"Test status: {'PASS' if passed_test else 'FAIL'}")


print("\n" + "=" * 75)

if all_passed:
    print("ALL DQ009 TESTS PASSED")
else:
    print("DQ009 TEST FAILURE")
    raise SystemExit(1)

print("=" * 75)

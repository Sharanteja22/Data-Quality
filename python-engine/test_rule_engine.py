
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PYTHON_ENGINE = PROJECT_ROOT / "python-engine"

sys.path.insert(0, str(PYTHON_ENGINE))

from app.ingestion.csv_loader import load_csv
from app.rules.rule_engine import evaluate_all_rules


CONFIG_PATH = PYTHON_ENGINE / "config" / "rules.json"

with CONFIG_PATH.open("r", encoding="utf-8") as file:
    config = json.load(file)


SCENARIOS = [
    {
        "name": "Scenario A - Critical duplicate",
        "file": PROJECT_ROOT / "data/generated/scenario_a_high_score_critical_block.csv",
        "run_id": "RUN001",
        "created": "2026-11-10T09:00:00",
        "received": "2026-11-10T09:30:00",
        "expected_failures":11,
    },
    {
        "name": "Scenario B - Warning only",
        "file": PROJECT_ROOT / "data/generated/scenario_b_warning_only.csv",
        "run_id": "RUN002",
        "created": "2026-11-10T09:00:00",
        "received": "2026-11-10T09:30:00",
        "expected_failures": 130,
    },
    {
        "name": "Scenario C - Corrected replay",
        "file": PROJECT_ROOT / "data/corrected/scenario_c_corrected_replay.csv",
        "run_id": "RUN003",
        "created": "2026-11-10T09:00:00",
        "received": "2026-11-10T09:30:00",
        "expected_failures": 0,
    },
]


all_passed = True

for scenario in SCENARIOS:
    records, metadata = load_csv(
        scenario["file"],
        run_id=scenario["run_id"],
    )

    results = evaluate_all_rules(
        records=records,
        rules_config=config,
        batch_created_at=scenario["created"],
        batch_received_at=scenario["received"],
    )

    total_failures = sum(
        result["failed_count"] for result in results
    )

    test_passed = (
        len(results) == 9
        and total_failures == scenario["expected_failures"]
    )

    all_passed = all_passed and test_passed

    print("\n" + "=" * 80)
    print(scenario["name"])
    print("=" * 80)

    for result in results:
        print(
            f"{result['rule_id']} | "
            f"Checked: {result['checked_count']} | "
            f"Passed: {result['passed_count']} | "
            f"Failed: {result['failed_count']}"
        )

    print(f"\nRecords: {metadata['record_count']}")
    print(f"Rules evaluated: {len(results)}")
    print(f"Total rule failures: {total_failures}")
    print(
        f"Integration test: {'PASS' if test_passed else 'FAIL'}"
    )


print("\n" + "=" * 80)

if all_passed:
    print("ALL INTEGRATION TESTS PASSED")
else:
    print("INTEGRATION TEST FAILURE")
    raise SystemExit(1)

print("=" * 80)

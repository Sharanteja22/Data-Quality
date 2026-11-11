
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PYTHON_ENGINE = PROJECT_ROOT / "python-engine"

sys.path.insert(0, str(PYTHON_ENGINE))

from app.ingestion.csv_loader import load_csv
from app.rules.rule_engine import evaluate_all_rules
from app.exceptions.exception_manager import generate_exceptions


CONFIG_PATH = PYTHON_ENGINE / "config" / "rules.json"

with CONFIG_PATH.open("r", encoding="utf-8") as file:
    config = json.load(file)


SCENARIOS = [
    {
        "name": "Scenario A - Critical duplicate",
        "file": PROJECT_ROOT / "data/generated/scenario_a_high_score_critical_block.csv",
        "run_id": "RUN001",
        "expected_exceptions": 11,
    },
    {
        "name": "Scenario B - Warning only",
        "file": PROJECT_ROOT / "data/generated/scenario_b_warning_only.csv",
        "run_id": "RUN002",
        "expected_exceptions": 130,
    },
    {
        "name": "Scenario C - Corrected replay",
        "file": PROJECT_ROOT / "data/corrected/scenario_c_corrected_replay.csv",
        "run_id": "RUN003",
        "expected_exceptions": 0,
    },
]


all_passed = True

for scenario in SCENARIOS:

    records, _ = load_csv(
        scenario["file"],
        scenario["run_id"],
    )

    rule_results = evaluate_all_rules(
        records=records,
        rules_config=config,
        batch_created_at="2026-11-10T09:00:00",
        batch_received_at="2026-11-10T09:30:00",
    )

    exceptions = generate_exceptions(
        records=records,
        rule_results=rule_results,
    )

    expected = scenario["expected_exceptions"]
    actual = len(exceptions)

    # Check that every generated exception has a unique ID.
    exception_ids = [
        item["exception_id"] for item in exceptions
    ]

    unique_ids = len(exception_ids) == len(set(exception_ids))

    # Summarize exceptions by rule.
    counts_by_rule = {}

    for exception in exceptions:
        rule_id = exception["rule_id"]
        counts_by_rule[rule_id] = (
            counts_by_rule.get(rule_id, 0) + 1
        )

    test_passed = actual == expected and unique_ids
    all_passed = all_passed and test_passed

    print("\n" + "=" * 80)
    print(scenario["name"])
    print("=" * 80)

    print(f"Expected exceptions: {expected}")
    print(f"Actual exceptions: {actual}")
    print(f"Unique exception IDs: {unique_ids}")
    print(f"Exceptions by rule: {counts_by_rule}")

    if exceptions:
        print("\nFirst exception:")
        print(exceptions[0])

    if scenario["run_id"] == "RUN001":
        duplicate_exception = next(
            (
                item for item in exceptions
                if item["rule_id"] == "DQ006"
            ),
            None,
        )

        print("\nDuplicate exception:")
        print(duplicate_exception)

    print(f"\nTest result: {'PASS' if test_passed else 'FAIL'}")


print("\n" + "=" * 80)

if all_passed:
    print("ALL EXCEPTION TESTS PASSED")
else:
    print("EXCEPTION TEST FAILURE")
    raise SystemExit(1)

print("=" * 80)

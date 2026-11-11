
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PYTHON_ENGINE = PROJECT_ROOT / "python-engine"

sys.path.insert(0, str(PYTHON_ENGINE))

from app.ingestion.csv_loader import load_csv
from app.rules.record_rules import evaluate_record_rules


CONFIG_PATH = PYTHON_ENGINE / "config" / "rules.json"

with CONFIG_PATH.open("r", encoding="utf-8") as file:
    rules_config = json.load(file)


SCENARIOS = [
    {
        "name": "Scenario A - High score with critical block",
        "file": PROJECT_ROOT / "data/generated/scenario_a_high_score_critical_block.csv",
        "run_id": "RUN001",
        "expected_failures": {
            "DQ001": 0,
            "DQ002": 0,
            "DQ003": 0,
            "DQ004": 0,
            "DQ005": 5,
            "DQ006": 1,
            "DQ007": 5,
            "DQ008": 0,
        },
    },
    {
        "name": "Scenario B - Warning only",
        "file": PROJECT_ROOT / "data/generated/scenario_b_warning_only.csv",
        "run_id": "RUN002",
        "expected_failures": {
            "DQ001": 0,
            "DQ002": 0,
            "DQ003": 0,
            "DQ004": 0,
            "DQ005": 65,
            "DQ006": 0,
            "DQ007": 65,
            "DQ008": 0,
        },
    },
    {
        "name": "Scenario C - Corrected replay",
        "file": PROJECT_ROOT / "data/corrected/scenario_c_corrected_replay.csv",
        "run_id": "RUN003",
        "expected_failures": {
            "DQ001": 0,
            "DQ002": 0,
            "DQ003": 0,
            "DQ004": 0,
            "DQ005": 0,
            "DQ006": 0,
            "DQ007": 0,
            "DQ008": 0,
        },
    },
]


all_passed = True

for scenario in SCENARIOS:
    records, metadata = load_csv(
        scenario["file"],
        run_id=scenario["run_id"],
    )

    results = evaluate_record_rules(records, rules_config)

    print("\n" + "=" * 85)
    print(scenario["name"])
    print("=" * 85)

    for result in results:
        rule_id = result["rule_id"]
        actual = result["failed_count"]
        expected = scenario["expected_failures"][rule_id]

        passed = actual == expected
        all_passed = all_passed and passed

        status = "PASS" if passed else "FAIL"

        print(
            f"{rule_id} | "
            f"Expected failures: {expected:3} | "
            f"Actual failures: {actual:3} | "
            f"{status}"
        )

    print(f"Records loaded: {metadata['record_count']}")
    print(f"Rules evaluated: {len(results)}")


print("\n" + "=" * 85)

if all_passed:
    print("ALL SCENARIO TESTS PASSED SUCCESSFULLY")
else:
    print("SOME SCENARIO TESTS FAILED - INVESTIGATION REQUIRED")

print("=" * 85)

if not all_passed:
    raise SystemExit(1)

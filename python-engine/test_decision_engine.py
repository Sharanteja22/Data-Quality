
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PYTHON_ENGINE = PROJECT_ROOT / "python-engine"

sys.path.insert(0, str(PYTHON_ENGINE))

from app.ingestion.csv_loader import load_csv
from app.rules.rule_engine import evaluate_all_rules
from app.scoring.score_calculator import calculate_data_quality_score
from app.blocking.decision_engine import make_batch_decision


CONFIG_PATH = PYTHON_ENGINE / "config" / "rules.json"

with CONFIG_PATH.open("r", encoding="utf-8") as file:
    config = json.load(file)


SCENARIOS = [
    {
        "name": "Scenario A - Critical duplicate",
        "file": PROJECT_ROOT / "data/generated/scenario_a_high_score_critical_block.csv",
        "run_id": "RUN001",
        "expected_status": "BLOCK",
        "expected_publication": False,
    },
    {
        "name": "Scenario B - Warning only",
        "file": PROJECT_ROOT / "data/generated/scenario_b_warning_only.csv",
        "run_id": "RUN002",
        "expected_status": "WARN",
        "expected_publication": True,
    },
    {
        "name": "Scenario C - Corrected replay",
        "file": PROJECT_ROOT / "data/corrected/scenario_c_corrected_replay.csv",
        "run_id": "RUN003",
        "expected_status": "PASS",
        "expected_publication": True,
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

    score_result = calculate_data_quality_score(
        rule_results,
        config,
    )

    decision = make_batch_decision(
        rule_results=rule_results,
        score_result=score_result,
        rules_config=config,
    )

    test_passed = (
        decision["final_status"] == scenario["expected_status"]
        and decision["publication_allowed"]
        == scenario["expected_publication"]
    )

    all_passed = all_passed and test_passed

    print("\n" + "=" * 80)
    print(scenario["name"])
    print("=" * 80)

    print(f"Overall score: {score_result['overall_score']}%")
    print(f"Score status: {score_result['score_status']}")
    print(f"Final status: {decision['final_status']}")
    print(f"Publication allowed: {decision['publication_allowed']}")

    print(
        "Blocking rule failures:",
        [item["rule_id"] for item in decision["blocking_rule_failures"]],
    )

    print(
        "Nonblocking rule failures:",
        [item["rule_id"] for item in decision["nonblocking_rule_failures"]],
    )

    print("Decision reasons:", decision["decision_reasons"])
    print(f"Test result: {'PASS' if test_passed else 'FAIL'}")


print("\n" + "=" * 80)

if all_passed:
    print("ALL DECISION ENGINE TESTS PASSED")
else:
    print("DECISION ENGINE TEST FAILURE")
    raise SystemExit(1)

print("=" * 80)

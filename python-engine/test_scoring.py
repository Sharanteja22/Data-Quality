
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PYTHON_ENGINE = PROJECT_ROOT / "python-engine"

sys.path.insert(0, str(PYTHON_ENGINE))

from app.ingestion.csv_loader import load_csv
from app.rules.rule_engine import evaluate_all_rules
from app.scoring.score_calculator import calculate_data_quality_score


CONFIG_PATH = PYTHON_ENGINE / "config" / "rules.json"

with CONFIG_PATH.open("r", encoding="utf-8") as file:
    config = json.load(file)


SCENARIOS = [
    {
        "name": "Scenario A - Critical duplicate",
        "file": PROJECT_ROOT / "data/generated/scenario_a_high_score_critical_block.csv",
        "run_id": "RUN001",
    },
    {
        "name": "Scenario B - Warning only",
        "file": PROJECT_ROOT / "data/generated/scenario_b_warning_only.csv",
        "run_id": "RUN002",
    },
    {
        "name": "Scenario C - Corrected replay",
        "file": PROJECT_ROOT / "data/corrected/scenario_c_corrected_replay.csv",
        "run_id": "RUN003",
    },
]


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

    print("\n" + "=" * 80)
    print(scenario["name"])
    print("=" * 80)

    print("\nRULE PASS RATES")

    for rule_id, pass_rate in score_result["rule_pass_rates"].items():
        print(f"{rule_id}: {pass_rate}%")

    print("\nDIMENSION SCORES")

    for dimension, details in score_result["dimension_scores"].items():
        print(
            f"{dimension}: "
            f"{details['score']}% "
            f"({details['status']})"
        )

    print("\nOVERALL SCORE")
    print(f"Score: {score_result['overall_score']}")
    print(f"Status: {score_result['score_status']}")

print("\n" + "=" * 80)
print("SCORING TEST EXECUTION COMPLETED")
print("=" * 80)

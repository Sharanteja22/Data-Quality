
import copy
import json
from pathlib import Path

import pandas as pd

from app.ingestion.csv_loader import load_csv
from app.pipeline import process_batch


PROJECT_ROOT = Path(__file__).resolve().parent.parent

CONFIG_PATH = (
    PROJECT_ROOT / "python-engine" / "config" / "rules.json"
)

SAMPLE_FILE = (
    PROJECT_ROOT
    / "data" / "corrected"
    / "scenario_c_corrected_replay.csv"
)


def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


def run_failure_test(test_name, records, config, run_id):
    print("\n" + "=" * 65)
    print(test_name)
    print("=" * 65)

    result = process_batch(
        records=records,
        run_id=run_id,
        rules_config=config,
        batch_created_at="2026-11-10T09:00:00",
        batch_received_at="2026-11-10T09:30:00",
    )

    print("Pipeline status:", result.get("pipeline_status"))
    print("Publication allowed:", result.get("publication_allowed"))

    if result.get("pipeline_status") == "FAILED":
        print("Error type:", result.get("error_type"))
        print("Error:", result.get("error"))

    decision = result.get("decision_result", {})
    print("Decision:", decision)

    # Common safety assertions for every failure test.
    assert result.get("pipeline_status") == "FAILED", (
        "Expected pipeline status FAILED."
    )

    assert result.get("publication_allowed") is False, (
        "Publication must not be allowed after a pipeline failure."
    )

    print("Test result: PASS")


def main():
    config = load_config()

    # Load a valid dataset for tests that need normal input records.
    records, metadata = load_csv(
        file_path=SAMPLE_FILE,
        run_id="FAILURE_TEST_BASE",
    )

    print("Base dataset ingestion:", metadata["ingestion_status"])

    # TEST 1: Empty DataFrame.
    run_failure_test(
        test_name="TEST 1 - Empty DataFrame",
        records=pd.DataFrame(),
        config=copy.deepcopy(config),
        run_id="FAILURE_TEST_001",
    )

    # TEST 2: Invalid / missing rule configuration.
    run_failure_test(
        test_name="TEST 2 - Empty rule configuration",
        records=records.copy(),
        config={},
        run_id="FAILURE_TEST_002",
    )

    # TEST 3: Required record columns missing.
    incomplete_records = pd.DataFrame({
        "transaction_id": ["TX001"],
        "customer_id": ["CUST001"],
    })

    run_failure_test(
        test_name="TEST 3 - Missing record columns",
        records=incomplete_records,
        config=copy.deepcopy(config),
        run_id="FAILURE_TEST_003",
    )

    # TEST 4: Disable all rules in the required Timeliness dimension.
    missing_dimension_config = copy.deepcopy(config)

    for rule in missing_dimension_config["rules"]:
        if rule["dimension"].upper() == "TIMELINESS":
            rule["is_active"] = False

    run_failure_test(
        test_name="TEST 4 - Required dimension not evaluated",
        records=records.copy(),
        config=missing_dimension_config,
        run_id="FAILURE_TEST_004",
    )

    print("\n" + "=" * 65)
    print("ALL PIPELINE FAILURE TESTS PASSED")
    print("=" * 65)


if __name__ == "__main__":
    main()

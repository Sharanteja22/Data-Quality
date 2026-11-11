
from pathlib import Path

from app.ingestion.csv_loader import load_csv
from app.pipeline import process_batch


PROJECT_ROOT = Path(__file__).resolve().parent.parent

RULES_CONFIG_PATH = (
    PROJECT_ROOT / "python-engine" / "config" / "rules.json"
)

DATASET_PATHS = {
    "Scenario A - Critical blocking": (
        PROJECT_ROOT
        / "data" / "generated"
        / "scenario_a_high_score_critical_block.csv"
    ),
    "Scenario B - Warning only": (
        PROJECT_ROOT
        / "data" / "generated"
        / "scenario_b_warning_only.csv"
    ),
    "Scenario C - Corrected replay": (
        PROJECT_ROOT
        / "data" / "corrected"
        / "scenario_c_corrected_replay.csv"
    ),
}


def load_rules_config():
    import json

    with open(RULES_CONFIG_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


def main():
    rules_config = load_rules_config()

    for index, (scenario_name, file_path) in enumerate(
        DATASET_PATHS.items(), start=1
    ):
        run_id = f"TEST_RUN_{index:03d}"

        print("\n" + "=" * 65)
        print(scenario_name)
        print("=" * 65)

        # Load the CSV and attach technical record metadata.
        records, metadata = load_csv(
            file_path=file_path,
            run_id=run_id,
        )

        print("Ingestion status:", metadata["ingestion_status"])
        print("Records loaded:", metadata["record_count"])

        # Use a 30-minute arrival delay for this integration test.
        result = process_batch(
            records=records,
            run_id=run_id,
            rules_config=rules_config,
            batch_created_at="2026-11-10T09:00:00",
            batch_received_at="2026-11-10T09:30:00",
        )

        print("\nPipeline status:", result["pipeline_status"])

        if result["pipeline_status"] == "FAILED":
            print("Error type:", result.get("error_type"))
            print("Error:", result.get("error"))
            continue

        print("Run ID:", result["run_id"])
        print("Record count:", result["record_count"])
        print("Rules evaluated:", len(result["rule_results"]))
        print("Overall score:", result["score_result"])
        print("Decision:", result["decision_result"])
        print("Exception count:", result["exception_count"])
        print(
            "Publication allowed:",
            result["publication_allowed"],
        )

    print("\nPipeline integration test completed.")


if __name__ == "__main__":
    main()


import json
from pathlib import Path

from app.storage.snowflake_reader import fetch_batch_records
from app.pipeline import process_batch


PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "python-engine" / "config" / "rules.json"


def load_rules_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


def run_pipeline(run_id, batch_created_at, batch_received_at):

    print(f"\nProcessing run: {run_id}")

    # Step 1: Read records from Snowflake.
    records = fetch_batch_records(run_id)

    print("Records retrieved:", len(records))

    # Step 2: Load rule configuration.
    rules_config = load_rules_config()

    # Step 3: Execute the existing DQ pipeline.
    result = process_batch(
        records=records,
        run_id=run_id,
        rules_config=rules_config,
        batch_created_at=batch_created_at,
        batch_received_at=batch_received_at,
    )

    # Step 4: Display evaluation summary.
    print("\n========== DQ RESULT ==========")
    print("Run ID:", result["run_id"])
    print("Pipeline status:", result["pipeline_status"])

    if result["pipeline_status"] == "COMPLETED":

        print("Overall score:", result["score_result"]["overall_score"])

        print(
            "Dimension scores:",
            result["score_result"]["dimension_scores"]
        )

        print(
            "Final decision:",
            result["decision_result"]["final_status"]
        )

        print(
            "Publication allowed:",
            result["publication_allowed"]
        )

        print("Total exceptions:", result["exception_count"])

        print("\nRule results:")

        for rule in result["rule_results"]:
            print(
                rule["rule_id"],
                "| Checked:", rule["checked_count"],
                "| Passed:", rule["passed_count"],
                "| Failed:", rule["failed_count"],
            )

    else:
        print("Error type:", result.get("error_type"))
        print("Error:", result.get("error"))

    return result



if __name__ == "__main__":

    runs = [
        {
            "run_id": "BATCH001_RUN001",
            "created_at": "2026-11-10T09:00:00",
            "received_at": "2026-11-10T09:30:00",
        },
        {
            "run_id": "BATCH002_RUN001",
            "created_at": "2026-11-10T09:00:00",
            "received_at": "2026-11-10T09:30:00",
        },
        {
            "run_id": "BATCH001_RUN002",
            "created_at": "2026-11-10T09:00:00",
            "received_at": "2026-11-10T09:30:00",
        },
    ]

    results = []

    for run in runs:
        result = run_pipeline(
            run_id=run["run_id"],
            batch_created_at=run["created_at"],
            batch_received_at=run["received_at"],
        )
        results.append(result)

    print("\n========== FINAL RUN SUMMARY ==========")

    for result in results:
        if result["pipeline_status"] == "COMPLETED":
            print(
                result["run_id"],
                "| Score:", result["score_result"]["overall_score"],
                "| Decision:", result["decision_result"]["final_status"],
                "| Exceptions:", result["exception_count"],
            )
        else:
            print(
                result["run_id"],
                "| FAILED:",
                result.get("error"),
            )

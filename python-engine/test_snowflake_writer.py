
from app.storage.snowflake_reader import fetch_batch_records
from app.storage.snowflake_writer import persist_pipeline_result
from app.pipeline import process_batch

import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
# print("Project root:", PROJECT_ROOT)
CONFIG_PATH = PROJECT_ROOT / "python-engine" / "config" / "rules.json"



def main():

    runs = [
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

    with open(CONFIG_PATH, "r", encoding="utf-8") as file:
        rules_config = json.load(file)

    for run in runs:

        run_id = run["run_id"]

        print(f"\nProcessing {run_id}")

        records = fetch_batch_records(run_id)

        result = process_batch(
            records=records,
            run_id=run_id,
            rules_config=rules_config,
            batch_created_at=run["created_at"],
            batch_received_at=run["received_at"],
        )

        if result["pipeline_status"] != "COMPLETED":
            raise RuntimeError(
                f"Pipeline failed for {run_id}: {result.get('error')}"
            )

        persist_pipeline_result(result)


if __name__ == "__main__":
    main()

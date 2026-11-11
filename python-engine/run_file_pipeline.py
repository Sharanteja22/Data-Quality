
import json
import sys
from pathlib import Path

import pandas as pd

from app.ingestion.csv_loader import load_csv
from app.pipeline import process_batch


# Locate the python-engine directory
ENGINE_ROOT = Path(__file__).resolve().parent

# Load the existing DQ rules configuration
CONFIG_PATH = ENGINE_ROOT / "config" / "rules.json"


def load_rules_config():
    with CONFIG_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def dataframe_to_json_records(records):
    """
    Convert the Pandas DataFrame into JSON-compatible dictionaries.

    Missing values are converted to None so that Spring Boot
    receives valid JSON null values instead of NaN.
    """
    clean_records = records.astype(object).where(
        pd.notna(records),
        None
    )

    return clean_records.to_dict(orient="records")


def run_file_pipeline(
    file_path,
    run_id,
    batch_created_at,
    batch_received_at
):
    try:
        # Step 1: Load and validate the CSV
        records, metadata = load_csv(
            file_path=file_path,
            run_id=run_id
        )

        # Step 2: Load the existing rules configuration
        rules_config = load_rules_config()

        # Step 3: Execute the existing data quality pipeline
        result = process_batch(
            records=records,
            run_id=run_id,
            rules_config=rules_config,
            batch_created_at=batch_created_at,
            batch_received_at=batch_received_at
        )

        # Step 4: Add ingestion metadata
        result["ingestion_metadata"] = metadata

        # Step 5: Add all source records for Spring Boot persistence
        result["records"] = dataframe_to_json_records(records)

        return result

    except Exception as error:
        return {
            "run_id": run_id,
            "pipeline_status": "FAILED",
            "error_type": type(error).__name__,
            "error": str(error),
            "publication_allowed": False
        }


if __name__ == "__main__":

    if len(sys.argv) != 5:
        print(json.dumps({
            "pipeline_status": "FAILED",
            "error": (
                "Usage: python run_file_pipeline.py "
                "<csv_path> <run_id> "
                "<batch_created_at> <batch_received_at>"
            ),
            "publication_allowed": False
        }))
        sys.exit(1)

    csv_path = sys.argv[1]
    run_id = sys.argv[2]
    batch_created_at = sys.argv[3]
    batch_received_at = sys.argv[4]

    result = run_file_pipeline(
        file_path=csv_path,
        run_id=run_id,
        batch_created_at=batch_created_at,
        batch_received_at=batch_received_at
    )

    # Output only JSON so Spring Boot can parse it
    print(json.dumps(result, default=str))

    if result.get("pipeline_status") != "COMPLETED":
        sys.exit(1)

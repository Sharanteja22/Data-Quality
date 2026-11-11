import csv
import uuid
from pathlib import Path

import pandas as pd


REQUIRED_COLUMNS = [
    "transaction_id",
    "customer_id",
    "account_id",
    "transaction_date",
    "amount",
    "currency",
    "country",
    "transaction_type",
    "status",
    "created_at",
]



class IngestionError(Exception):
    """Base exception for CSV ingestion failures."""


class SchemaValidationError(IngestionError):
    """Raised when required CSV columns are missing or invalid."""



def validate_schema(file_path: str | Path) -> None:

    file_path = Path(file_path)

    if not file_path.exists():
        raise IngestionError(
            f"CSV file does not exist: {file_path}"
        )

    if not file_path.is_file():
        raise IngestionError(
            f"Provided path is not a file: {file_path}"
        )

    try:
        with file_path.open(
            mode="r",
            encoding="utf-8-sig",
            newline=""
        ) as csv_file:
            reader = csv.reader(csv_file)
            headers = next(reader, None)
    except (OSError, UnicodeError, csv.Error) as error:
        raise IngestionError(
            f"Unable to read CSV header: {error}"
        ) from error
    if not headers:
        raise SchemaValidationError(
            "CSV file is empty or does not contain a header."
        )

    if len(headers) != len(set(headers)):
        raise SchemaValidationError(
            "CSV contains duplicate column names."
        )

    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in headers
    ]
    if missing_columns:
        raise SchemaValidationError(
            f"Missing required columns: {missing_columns}"
        )


def load_csv(
    file_path: str | Path,
    run_id: str
) -> tuple[pd.DataFrame, dict]:

    if not run_id or not run_id.strip():
        raise ValueError("run_id cannot be empty.")
    file_path = Path(file_path)
    validate_schema(file_path)

    try:
        df = pd.read_csv(
            file_path,
            dtype=str,
            encoding="utf-8-sig",
            keep_default_na=True,
            skip_blank_lines=False,
            on_bad_lines="error"
        )

    except (OSError, UnicodeError, pd.errors.ParserError) as error:
        raise IngestionError(
            f"Unable to load CSV data: {error}"
        ) from error

    df.insert(
        0,
        "record_id",
        [str(uuid.uuid4()) for _ in range(len(df))]
    )
    df.insert(
        1,
        "run_id",
        run_id
    )

    df.insert(
        2,
        "source_row_number",
        range(2, len(df) + 2)
    )

    metadata = {
        "run_id": run_id,
        "file_name": file_path.name,
        "record_count": len(df),
        "column_count": len(REQUIRED_COLUMNS),
        "source_columns": [
            column
            for column in df.columns
            if column not in (
                "record_id",
                "run_id",
                "source_row_number"
            )
        ],
        "ingestion_status": "SUCCESS"
    }

    return df, metadata



if __name__ == "__main__":

    project_root = Path(__file__).resolve().parents[3]

    sample_file = (
        project_root
        / "data"
        / "generated"
        / "scenario_a_high_score_critical_block.csv"
    )

    transactions, metadata = load_csv(
        sample_file,
        run_id="RUN001"
    )

    print("\nINGESTION SUCCESSFUL")
    print("-" * 50)

    print("Metadata:")
    print(metadata)

    print("\nFirst five records:")
    print(transactions.head().to_string(index=False))

    print("\nDataFrame shape:")
    print(transactions.shape)

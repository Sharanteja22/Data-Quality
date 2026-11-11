
from __future__ import annotations

import uuid
from typing import Any

import pandas as pd


def _display_value(value: Any) -> str:
    """Format a value for a readable exception description."""
    if pd.isna(value):
        return "<missing>"

    return str(value).strip()


def _build_record_description(
    rule_id: str,
    record: pd.Series,
    records: pd.DataFrame,
) -> str:
    """Build a rule-specific explanation for a failed record."""

    row_number = record["source_row_number"]
    transaction_id = _display_value(record["transaction_id"])

    if rule_id == "DQ001":
        return (
            f"Customer ID is missing for transaction "
            f"{transaction_id} at source row {row_number}."
        )

    if rule_id == "DQ002":
        return (
            f"Account ID is missing for transaction "
            f"{transaction_id} at source row {row_number}."
        )

    if rule_id == "DQ003":
        amount = _display_value(record["amount"])
        return (
            f"Invalid transaction amount '{amount}' for "
            f"transaction {transaction_id} at source row {row_number}. "
            "Amount must be numeric and greater than zero."
        )

    if rule_id == "DQ004":
        currency = _display_value(record["currency"])
        return (
            f"Unsupported currency '{currency}' for transaction "
            f"{transaction_id} at source row {row_number}."
        )

    if rule_id == "DQ005":
        transaction_type = _display_value(record["transaction_type"])
        return (
            f"Invalid transaction type '{transaction_type}' for "
            f"transaction {transaction_id} at source row {row_number}. "
            "Allowed values are CREDIT and DEBIT."
        )

    if rule_id == "DQ006":
        duplicate_id = record["transaction_id"]

        earlier_records = records[
            (records["transaction_id"] == duplicate_id)
            & (
                records["source_row_number"]
                < row_number
            )
        ]

        if not earlier_records.empty:
            first_row = earlier_records.iloc[0]["source_row_number"]

            return (
                f"Duplicate transaction_id {duplicate_id} found "
                f"at source rows {first_row} and {row_number}."
            )

        return (
            f"Duplicate transaction_id {duplicate_id} found "
            f"at source row {row_number}."
        )

    if rule_id == "DQ007":
        country = _display_value(record["country"])
        currency = _display_value(record["currency"])

        return (
            f"Country/currency mismatch for transaction "
            f"{transaction_id} at source row {row_number}: "
            f"country is '{country}' but currency is '{currency}'."
        )

    if rule_id == "DQ008":
        transaction_date = _display_value(record["transaction_date"])
        created_at = _display_value(record["created_at"])

        return (
            f"Invalid transaction date relationship for transaction "
            f"{transaction_id} at source row {row_number}: "
            f"transaction_date='{transaction_date}', "
            f"created_at='{created_at}'."
        )

    return (
        f"Rule {rule_id} failed for transaction {transaction_id} "
        f"at source row {row_number}."
    )


def _build_batch_description(result: dict[str, Any]) -> str:
    """Build the description for a batch-level failure."""

    delay = result.get("delay_minutes")
    tolerance = result.get("sla_tolerance_minutes")

    return (
        f"Batch arrived after the configured SLA. "
        f"Actual delay: {delay} minutes; "
        f"allowed delay: {tolerance} minutes."
    )


def generate_exceptions(
    records: pd.DataFrame,
    rule_results: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Generate one exception for each failed record-level rule check.

    A failed batch-level rule generates one exception with no record_id.
    """

    required_columns = {
        "record_id",
        "run_id",
        "source_row_number",
        "transaction_id",
    }

    missing_columns = required_columns.difference(records.columns)

    if missing_columns:
        raise ValueError(
            f"Records are missing columns: {sorted(missing_columns)}"
        )

    exceptions = []

    for result in rule_results:

        if result["failed_count"] <= 0:
            continue

        rule_id = result["rule_id"]

        # Batch-level exception: one exception for the batch/run.
        if rule_id == "DQ009":
            exceptions.append(
                {
                    "exception_id": str(uuid.uuid4()),
                    "run_id": records["run_id"].iloc[0],
                    "rule_id": rule_id,
                    "record_id": None,
                    "source_row_number": None,
                    "transaction_id": None,
                    "severity": result["severity"],
                    "description": _build_batch_description(result),
                    "assigned_to": result["owner"],
                    "status": "OPEN",
                    "resolution_notes": None,
                }
            )

            continue

        failed_record_ids = set(result.get("failed_record_ids", []))

        failed_records = records[
            records["record_id"].isin(failed_record_ids)
        ]

        if len(failed_records) != result["failed_count"]:
            raise ValueError(
                f"Could not identify all failed records for {rule_id}. "
                f"Expected {result['failed_count']}, "
                f"identified {len(failed_records)}."
            )

        for _, record in failed_records.iterrows():

            exceptions.append(
                {
                    "exception_id": str(uuid.uuid4()),
                    "run_id": record["run_id"],
                    "rule_id": rule_id,
                    "record_id": record["record_id"],
                    "source_row_number": int(
                        record["source_row_number"]
                    ),
                    "transaction_id": record["transaction_id"],
                    "severity": result["severity"],
                    "description": _build_record_description(
                        rule_id,
                        record,
                        records,
                    ),
                    "assigned_to": result["owner"],
                    "status": "OPEN",
                    "resolution_notes": None,
                }
            )

    return exceptions

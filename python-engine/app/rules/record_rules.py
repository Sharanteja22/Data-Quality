
from __future__ import annotations

from typing import Any

import pandas as pd


def _is_present(series: pd.Series) -> pd.Series:
    """Treat null, empty and whitespace-only values as missing."""
    return series.notna() & series.astype("string").str.strip().ne("")


def _get_parameters(config: dict[str, Any]) -> dict[str, Any]:
    return config.get("parameters", {})


def _get_rule_definitions(config: dict[str, Any]) -> list[dict[str, Any]]:
    rules = config.get("rules", [])

    if not isinstance(rules, list):
        raise ValueError("The 'rules' configuration must be a list.")

    return rules


def _evaluate_condition(
    rule_id: str,
    records: pd.DataFrame,
    parameters: dict[str, Any],
) -> pd.Series:
    """Return True for passing records and False for failing records."""

    if rule_id == "DQ001":
        return _is_present(records["customer_id"])

    if rule_id == "DQ002":
        return _is_present(records["account_id"])

    if rule_id == "DQ003":
        amounts = pd.to_numeric(records["amount"], errors="coerce")
        return amounts.notna() & amounts.gt(0)

    if rule_id == "DQ004":
        allowed_currencies = parameters.get(
            "allowed_currencies", ["INR", "USD", "EUR"]
        )
        return records["currency"].isin(allowed_currencies)

    if rule_id == "DQ005":
        allowed_types = parameters.get(
            "allowed_transaction_types", ["CREDIT", "DEBIT"]
        )
        return records["transaction_type"].isin(allowed_types)

    if rule_id == "DQ006":
        transaction_ids_present = _is_present(records["transaction_id"])
        duplicate_ids = records["transaction_id"].duplicated(keep="first")
        return transaction_ids_present & ~duplicate_ids

    if rule_id == "DQ007":
        country_currency_map = parameters.get(
            "country_currency_map",
            {"India": "INR", "USA": "USD", "UK": "EUR"},
        )
        expected_currency = records["country"].map(country_currency_map)
        return (
            expected_currency.notna()
            & records["currency"].eq(expected_currency)
        )

    if rule_id == "DQ008":
        transaction_dates = pd.to_datetime(
            records["transaction_date"], errors="coerce"
        )
        created_dates = pd.to_datetime(
            records["created_at"], errors="coerce"
        )
        return (
            transaction_dates.notna()
            & created_dates.notna()
            & transaction_dates.le(created_dates)
        )

    raise ValueError(f"Unsupported record-level rule: {rule_id}")


def evaluate_record_rules(
    records: pd.DataFrame,
    rules_config: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    Evaluate all active record-level rules.

    Returns one result object per active record-level rule.
    """

    required_columns = {
        "record_id",
        "transaction_id",
        "customer_id",
        "account_id",
        "transaction_date",
        "amount",
        "currency",
        "country",
        "transaction_type",
        "created_at",
    }

    missing_columns = required_columns.difference(records.columns)
    if missing_columns:
        raise ValueError(
            f"Records are missing required columns: {sorted(missing_columns)}"
        )

    parameters = _get_parameters(rules_config)
    rule_definitions = _get_rule_definitions(rules_config)

    results = []

    for rule in rule_definitions:
        if not rule.get("is_active", True):
            continue

        rule_id = rule["rule_id"]

        # DQ009 is evaluated separately because it applies to the batch.
        if rule.get("rule_type", "RECORD").upper() != "RECORD":
            continue

        passed_mask = _evaluate_condition(rule_id, records, parameters)
        passed_mask = passed_mask.fillna(False).astype(bool)
        failed_mask = ~passed_mask

        failed_records = records.loc[failed_mask]

        results.append(
            {
                "rule_id": rule_id,
                "rule_name": rule["rule_name"],
                "dimension": rule["dimension"],
                "severity": rule["severity"],
                "rule_weight": rule["rule_weight"],
                "is_blocking": rule["is_blocking"],
                "owner": rule["owner"],
                "checked_count": int(len(records)),
                "passed_count": int(passed_mask.sum()),
                "failed_count": int(failed_mask.sum()),
                "failed_record_ids": failed_records["record_id"].tolist(),
            }
        )

    return results
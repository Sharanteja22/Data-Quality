from datetime import datetime
from typing import Any

def evaluate_batch_rules(
    batch_created_at: str,
    batch_received_at: str,
    rules_config: dict[str, Any],
) -> list[dict[str, Any]]:

    rules = rules_config.get("rules", [])
    parameters = rules_config.get("parameters", {})

    results = []

    for rule in rules:
        if not rule.get("is_active", True):
            continue

        if rule.get("rule_type", "").upper() != "BATCH":
            continue

        if rule["rule_id"] != "DQ009":
            continue

        sla_minutes = parameters.get("sla_tolerance_minutes")

        if sla_minutes is None:
            raise ValueError(
                "DQ009 cannot be evaluated: SLA tolerance is not configured."
            )

        if sla_minutes < 0:
            raise ValueError("SLA tolerance cannot be negative.")

        created_time = datetime.fromisoformat(batch_created_at)
        received_time = datetime.fromisoformat(batch_received_at)

        delay_minutes = (
            received_time - created_time
        ).total_seconds() / 60

        passed = 0 <= delay_minutes <= sla_minutes

        results.append(
            {
                "rule_id": "DQ009",
                "rule_name": rule["rule_name"],
                "dimension": rule["dimension"],
                "severity": rule["severity"],
                "rule_weight": rule["rule_weight"],
                "is_blocking": rule["is_blocking"],
                "owner": rule["owner"],
                "checked_count": 1,
                "passed_count": 1 if passed else 0,
                "failed_count": 0 if passed else 1,
                "delay_minutes": delay_minutes,
                "sla_tolerance_minutes": sla_minutes,
            }
        )

    return results

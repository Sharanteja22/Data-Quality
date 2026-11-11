
from typing import Any

from app.rules.record_rules import evaluate_record_rules
from app.rules.batch_rules import evaluate_batch_rules


def evaluate_all_rules(
    records,
    rules_config: dict[str, Any],
    batch_created_at: str,
    batch_received_at: str,
) -> list[dict[str, Any]]:
    record_results = evaluate_record_rules(
        records=records,
        rules_config=rules_config,
    )

    batch_results = evaluate_batch_rules(
        batch_created_at=batch_created_at,
        batch_received_at=batch_received_at,
        rules_config=rules_config,
    )

    all_results = record_results + batch_results

    expected_rule_count = sum(
        1
        for rule in rules_config.get("rules", [])
        if rule.get("is_active", True)
    )

    if len(all_results) != expected_rule_count:
        raise RuntimeError(
            "Rule evaluation incomplete: "
            f"expected {expected_rule_count} active rules, "
            f"evaluated {len(all_results)}."
        )

    return all_results

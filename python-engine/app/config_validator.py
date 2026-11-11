import sys
import logging  
class ConfigValidationError(Exception):
    """Raised when the data-quality rules configuration is invalid."""


REQUIRED_SECTIONS = [
    "dimension_weights",
    "blocking_severities",
    "thresholds",
    "rules",
    "parameters",
]

REQUIRED_RULE_FIELDS = [
    "rule_id",
    "rule_name",
    "dimension",
    "severity",
    "rule_weight",
    "is_blocking",
    "owner",
    "is_active",
    "rule_type",
]

REQUIRED_DIMENSIONS = {
    "COMPLETENESS",
    "VALIDITY",
    "UNIQUENESS",
    "CONSISTENCY",
    "TIMELINESS",
}


def validate_rules_config(config: dict) -> None:
    """
    Validate the structure and essential values of rules.json.

    Raises ConfigValidationError if the configuration is invalid.
    """

    if not isinstance(config, dict):
        raise ConfigValidationError(
            "Rules configuration must be a dictionary."
        )

    missing_sections = [
        section
        for section in REQUIRED_SECTIONS
        if section not in config
    ]

    if missing_sections:
        raise ConfigValidationError(
            f"Missing required configuration sections: {missing_sections}"
        )

    # Validate dimension weights.
    dimension_weights = config["dimension_weights"]

    if not isinstance(dimension_weights, dict):
        raise ConfigValidationError(
            "dimension_weights must be a dictionary."
        )

    missing_dimensions = (
        REQUIRED_DIMENSIONS - set(dimension_weights.keys())
    )

    if missing_dimensions:
        raise ConfigValidationError(
            f"Missing dimension weights: {sorted(missing_dimensions)}"
        )

    for dimension, weight in dimension_weights.items():
        if not isinstance(weight, (int, float)) or isinstance(weight, bool):
            raise ConfigValidationError(
                f"Invalid weight for dimension {dimension}."
            )

        if weight < 0:
            raise ConfigValidationError(
                f"Dimension weight cannot be negative: {dimension}."
            )

    total_dimension_weight = sum(dimension_weights.values())

    if total_dimension_weight <= 0:
        raise ConfigValidationError(
            "Total dimension weight must be greater than zero."
        )

    # Validate blocking severities.
    if not isinstance(config["blocking_severities"], list):
        raise ConfigValidationError(
            "blocking_severities must be a list."
        )

    # Validate thresholds.
    thresholds = config["thresholds"]

    if not isinstance(thresholds, dict):
        raise ConfigValidationError(
            "thresholds must be a dictionary."
        )

    if "PASS" not in thresholds or "WARN" not in thresholds:
        raise ConfigValidationError(
            "thresholds must contain PASS and WARN values."
        )

    if thresholds["WARN"] > thresholds["PASS"]:
        raise ConfigValidationError(
            "WARN threshold cannot be greater than PASS threshold."
        )

    # Validate rules.
    rules = config["rules"]

    if not isinstance(rules, list) or not rules:
        raise ConfigValidationError(
            "rules must be a non-empty list."
        )

    seen_rule_ids = set()

    for index, rule in enumerate(rules):
        if not isinstance(rule, dict):
            raise ConfigValidationError(
                f"Rule at index {index} must be a dictionary."
            )

        missing_fields = [
            field
            for field in REQUIRED_RULE_FIELDS
            if field not in rule
        ]

        if missing_fields:
            raise ConfigValidationError(
                f"Rule at index {index} is missing fields: {missing_fields}"
            )

        rule_id = rule["rule_id"]

        if not isinstance(rule_id, str) or not rule_id.strip():
            raise ConfigValidationError(
                f"Invalid rule_id at index {index}."
            )

        if rule_id in seen_rule_ids:
            raise ConfigValidationError(
                f"Duplicate rule_id found: {rule_id}."
            )

        seen_rule_ids.add(rule_id)

        if rule["dimension"].upper() not in REQUIRED_DIMENSIONS:
            raise ConfigValidationError(
                f"Unknown dimension in rule {rule_id}: "
                f"{rule['dimension']}."
            )

        if (
            not isinstance(rule["rule_weight"], (int, float))
            or isinstance(rule["rule_weight"], bool)
            or rule["rule_weight"] < 0
        ):
            raise ConfigValidationError(
                f"Invalid rule_weight for {rule_id}."
            )

        if not isinstance(rule["is_active"], bool):
            raise ConfigValidationError(
                f"is_active must be boolean for {rule_id}."
            )

        if not isinstance(rule["is_blocking"], bool):
            raise ConfigValidationError(
                f"is_blocking must be boolean for {rule_id}."
            )

    # Validate parameters.
    if not isinstance(config["parameters"], dict):
        raise ConfigValidationError(
            "parameters must be a dictionary."
        )

    logging.info("Rules configuration validation successful.")

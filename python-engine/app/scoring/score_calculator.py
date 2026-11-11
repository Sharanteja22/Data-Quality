
from typing import Any


def calculate_rule_pass_rate(
    passed_count: int,
    checked_count: int,
) -> float | None:
    """
    Calculate the percentage of records passing a rule.

    Returns None when no records were checked.
    """

    if checked_count < 0 or passed_count < 0:
        raise ValueError("Rule counts cannot be negative.")

    if passed_count > checked_count:
        raise ValueError("Passed count cannot exceed checked count.")

    if checked_count == 0:
        return None

    return round((passed_count / checked_count) * 100, 4)


def calculate_dimension_scores(
    rule_results: list[dict[str, Any]],
    rules_config: dict[str, Any],
) -> dict[str, Any]:
    """
    Calculate weighted scores for all five dimensions.

    Rule weights are used within each dimension.
    Dimension weights are used later for the overall score.
    """

    dimension_weights = rules_config["dimension_weights"]

    dimension_scores = {}

    for dimension in dimension_weights:

        dimension_rules = [
            result
            for result in rule_results
            if result["dimension"] == dimension
        ]

        if not dimension_rules:
            dimension_scores[dimension] = {
                "score": None,
                "status": "NOT_EVALUATED",
                "rule_count": 0,
            }
            continue

        weighted_score = 0.0
        total_rule_weight = 0.0
        evaluated_rule_count = 0

        for result in dimension_rules:

            rule_weight = result["rule_weight"]

            pass_rate = calculate_rule_pass_rate(
                result["passed_count"],
                result["checked_count"],
            )

            if pass_rate is None:
                continue

            weighted_score += pass_rate * rule_weight
            total_rule_weight += rule_weight
            evaluated_rule_count += 1

        if total_rule_weight == 0:
            dimension_scores[dimension] = {
                "score": None,
                "status": "NOT_EVALUATED",
                "rule_count": len(dimension_rules),
            }
            continue

        score = weighted_score / total_rule_weight

        dimension_scores[dimension] = {
            "score": round(score, 4),
            "status": "EVALUATED",
            "rule_count": evaluated_rule_count,
        }

    return dimension_scores


def calculate_overall_score(
    dimension_scores: dict[str, Any],
    rules_config: dict[str, Any],
) -> dict[str, Any]:
    """
    Calculate the overall weighted data quality score.

    All five required dimensions must be evaluated.
    No dimension is silently assigned a score of 100.
    """

    dimension_weights = rules_config["dimension_weights"]

    missing_dimensions = [
        dimension
        for dimension in dimension_weights
        if dimension not in dimension_scores
        or dimension_scores[dimension]["score"] is None
    ]

    if missing_dimensions:
        return {
            "overall_score": None,
            "score_status": "NOT_EVALUATED",
            "missing_dimensions": missing_dimensions,
        }

    weighted_total = 0.0
    total_dimension_weight = 0.0

    for dimension, weight in dimension_weights.items():

        score = dimension_scores[dimension]["score"]

        weighted_total += score * weight
        total_dimension_weight += weight

    if total_dimension_weight == 0:
        return {
            "overall_score": None,
            "score_status": "NOT_EVALUATED",
            "missing_dimensions": [],
        }

    overall_score = weighted_total / total_dimension_weight

    thresholds = rules_config["thresholds"]

    pass_threshold = thresholds["PASS"]
    warn_threshold = thresholds["WARN"]

    if overall_score >= pass_threshold:
        score_status = "PASS"
    elif overall_score >= warn_threshold:
        score_status = "WARN"
    else:
        score_status = "BLOCK"

    return {
        "overall_score": round(overall_score, 4),
        "score_status": score_status,
        "missing_dimensions": [],
    }


def calculate_data_quality_score(
    rule_results: list[dict[str, Any]],
    rules_config: dict[str, Any],
) -> dict[str, Any]:
    """
    Main scoring entry point.
    """

    dimension_scores = calculate_dimension_scores(
        rule_results,
        rules_config,
    )

    overall_result = calculate_overall_score(
        dimension_scores,
        rules_config,
    )

    rule_pass_rates = {}

    for result in rule_results:
        rule_pass_rates[result["rule_id"]] = calculate_rule_pass_rate(
            result["passed_count"],
            result["checked_count"],
        )

    return {
        "rule_pass_rates": rule_pass_rates,
        "dimension_scores": dimension_scores,
        "overall_score": overall_result["overall_score"],
        "score_status": overall_result["score_status"],
        "missing_dimensions": overall_result["missing_dimensions"],
    }

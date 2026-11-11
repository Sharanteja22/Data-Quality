
from typing import Any


def make_batch_decision(
    rule_results: list[dict[str, Any]],
    score_result: dict[str, Any],
    rules_config: dict[str, Any],
) -> dict[str, Any]:
    """
    Determine the final batch status and publication permission.

    Decision precedence:
    1. Missing overall score / required dimension -> FAILED.
    2. Failed blocking rule -> BLOCK.
    3. Score below WARN threshold -> BLOCK.
    4. Score below PASS threshold or nonblocking failures -> WARN.
    5. Otherwise -> PASS.
    """

    # A missing score means the required quality evaluation
    # could not be completed.
    overall_score = score_result.get("overall_score")

    if overall_score is None or score_result.get("score_status") == "NOT_EVALUATED":
        return {
            "final_status": "FAILED",
            "publication_allowed": False,
            "decision_reasons": [
                "Overall score could not be evaluated.",
                *score_result.get("missing_dimensions", []),
            ],
            "blocking_rule_failures": [],
            "nonblocking_rule_failures": [],
        }

    blocking_severities = set(
        rules_config.get("blocking_severities", [])
    )

    blocking_failures = []
    nonblocking_failures = []

    for result in rule_results:

        # Ignore rules which did not fail.
        if result["failed_count"] <= 0:
            continue

        rule_is_blocking = (
            result["is_blocking"]
            and result["severity"] in blocking_severities
        )

        failure_details = {
            "rule_id": result["rule_id"],
            "rule_name": result["rule_name"],
            "severity": result["severity"],
            "failed_count": result["failed_count"],
            "owner": result["owner"],
        }

        if rule_is_blocking:
            blocking_failures.append(failure_details)
        else:
            nonblocking_failures.append(failure_details)

    thresholds = rules_config["thresholds"]
    pass_threshold = thresholds["PASS"]
    warn_threshold = thresholds["WARN"]

    reasons = []

    # A failed blocking rule overrides the numerical score.
    if blocking_failures:
        final_status = "BLOCK"
        reasons.append("One or more blocking rules failed.")

    elif overall_score < warn_threshold:
        final_status = "BLOCK"
        reasons.append(
            f"Overall score {overall_score}% is below "
            f"the WARN threshold of {warn_threshold}%."
        )

    elif overall_score < pass_threshold:
        final_status = "WARN"
        reasons.append(
            f"Overall score {overall_score}% is below "
            f"the PASS threshold of {pass_threshold}%."
        )

    elif nonblocking_failures:
        final_status = "WARN"
        reasons.append(
            "One or more nonblocking data quality rules failed."
        )

    else:
        final_status = "PASS"
        reasons.append(
            "All active rules passed and the overall score "
            "meets the PASS threshold."
        )

    publication_allowed = final_status in ("PASS", "WARN")

    return {
        "final_status": final_status,
        "publication_allowed": publication_allowed,
        "overall_score": overall_score,
        "decision_reasons": reasons,
        "blocking_rule_failures": blocking_failures,
        "nonblocking_rule_failures": nonblocking_failures,
    }

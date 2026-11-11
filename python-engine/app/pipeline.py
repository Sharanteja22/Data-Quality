
from typing import Any
import traceback

import pandas as pd

from app.rules.rule_engine import evaluate_all_rules
from app.scoring.score_calculator import calculate_data_quality_score
from app.blocking.decision_engine import make_batch_decision
from app.exceptions.exception_manager import generate_exceptions
from app.config_validator import validate_rules_config

def process_batch(
    records: pd.DataFrame,
    run_id: str,
    rules_config: dict[str, Any],
    batch_created_at: str,
    batch_received_at: str,
) -> dict[str, Any]:
    """
    Execute the complete data-quality evaluation pipeline for one batch run.

    This function:
      1. Evaluates all configured data-quality rules.
      2. Calculates dimension and overall quality scores.
      3. Determines PASS, WARN, BLOCK, or FAILED.
      4. Generates exception details for failed rules.
      5. Returns one structured response for the calling backend.

    Note:
      This function does not write to Snowflake or publish transactions.
      Spring Boot will own persistence and the final publication gate.
    """

    try:
        # Basic input validation
        if records is None or not isinstance(records, pd.DataFrame):
            raise ValueError("records must be a valid Pandas DataFrame.")

        if records.empty:
            raise ValueError("The batch contains no records to evaluate.")

        if not run_id or not run_id.strip():
            raise ValueError("run_id is required.")

        # Validate configuration before executing any rules.
        validate_rules_config(rules_config)

        # Step 1: Evaluate all nine data-quality rules.
        rule_results = evaluate_all_rules(
            records=records,
            rules_config=rules_config,
            batch_created_at=batch_created_at,
            batch_received_at=batch_received_at,
        )

        # Step 2: Calculate dimension scores and overall score.
        score_result = calculate_data_quality_score(
            rule_results=rule_results,
            rules_config=rules_config,
        )

        # Step 3: Determine the batch decision.
        decision_result = make_batch_decision(
            rule_results=rule_results,
            score_result=score_result,
            rules_config=rules_config,
        )

        # Step 4: Generate exception details.
        exceptions = generate_exceptions(
            records=records,
            rule_results=rule_results,
        )

        # Step 4.1: Check whether the business evaluation is complete.
        final_status = decision_result.get("final_status")

        if final_status == "FAILED":
            return {
                "run_id": run_id,
                "record_count": int(len(records)),
                "pipeline_status": "FAILED",
                "error_type": "EvaluationIncomplete",
                "error": (
                    "The data-quality evaluation could not produce "
                    "a valid decision because one or more required "
                    "dimensions were not evaluated."
                ),
                "rule_results": rule_results,
                "score_result": score_result,
                "decision_result": decision_result,
                "exception_count": len(exceptions),
                "exceptions": exceptions,
                "publication_allowed": False,
            }

        # Step 5: Build the consolidated response.
        response = {
            "run_id": run_id,
            "record_count": int(len(records)),
            "pipeline_status": "COMPLETED",
            "rule_results": rule_results,
            "score_result": score_result,
            "decision_result": decision_result,
            "exception_count": len(exceptions),
            "exceptions": exceptions,
            "publication_allowed": decision_result.get(
                "publication_allowed", False
            ),
        }

        return response

    except Exception as exc:
        # Do not allow an engine failure to be treated as a successful run.
        return {
            "run_id": run_id,
            "record_count": (
                int(len(records))
                if isinstance(records, pd.DataFrame)
                else 0
            ),
            "pipeline_status": "FAILED",
            "error": str(exc),
            "error_type": type(exc).__name__,
            "decision_result": {
                "decision": "FAILED",
                "publication_allowed": False,
                "reason": "The data-quality pipeline could not complete.",
            },
            "publication_allowed": False,
        }


import uuid

from app.storage.snowflake_connection import get_snowflake_connection


def persist_pipeline_result(result: dict) -> None:
    """
    Persist one completed Python DQ pipeline result
    into the existing Snowflake tables.
    """

    run_id = result["run_id"]

    if result["pipeline_status"] != "COMPLETED":
        raise ValueError(
            f"Cannot persist incomplete pipeline result for {run_id}"
        )

    rule_results = result["rule_results"]
    score_result = result["score_result"]
    decision_result = result["decision_result"]

    dimension_scores = score_result["dimension_scores"]

    # Extract dimension scores.
    completeness = dimension_scores.get("Completeness", {}).get("score")
    validity = dimension_scores.get("Validity", {}).get("score")
    uniqueness = dimension_scores.get("Uniqueness", {}).get("score")
    consistency = dimension_scores.get("Consistency", {}).get("score")
    timeliness = dimension_scores.get("Timeliness", {}).get("score")

    # Count critical and high failures.
    critical_failures = sum(
        r["failed_count"]
        for r in rule_results
        if r["severity"] == "CRITICAL"
    )

    high_failures = sum(
        r["failed_count"]
        for r in rule_results
        if r["severity"] == "HIGH"
    )

    # Warning count represents failed nonblocking checks.
    warning_count = sum(
        r["failed_count"]
        for r in rule_results
        if not r["is_blocking"]
    )

    connection = get_snowflake_connection()
    cursor = connection.cursor()

    try:
        # Make repeated persistence of the same run safe.
        cursor.execute(
            "DELETE FROM DQ_EXCEPTIONS WHERE RUN_ID = %s",
            (run_id,)
        )

        cursor.execute(
            "DELETE FROM DQ_RULE_RESULTS WHERE RUN_ID = %s",
            (run_id,)
        )

        # Update the existing batch run.
        cursor.execute(
            """
            UPDATE BATCH_RUNS
            SET
                COMPLETENESS_SCORE = %s,
                VALIDITY_SCORE = %s,
                UNIQUENESS_SCORE = %s,
                CONSISTENCY_SCORE = %s,
                TIMELINESS_SCORE = %s,
                OVERALL_SCORE = %s,
                CRITICAL_FAILURES = %s,
                HIGH_FAILURES = %s,
                WARNING_COUNT = %s,
                FINAL_STATUS = %s,
                PUBLICATION_ALLOWED = %s,
                EXECUTED_AT = CURRENT_TIMESTAMP()
            WHERE RUN_ID = %s
            """,
            (
                completeness,
                validity,
                uniqueness,
                consistency,
                timeliness,
                score_result["overall_score"],
                critical_failures,
                high_failures,
                warning_count,
                decision_result["final_status"],
                result["publication_allowed"],
                run_id,
            )
        )

        # Insert one result for each evaluated rule.
        rule_rows = []

        for rule in rule_results:
            checked = rule["checked_count"]
            failed = rule["failed_count"]

            failure_rate = (
                round((failed / checked) * 100, 2)
                if checked > 0
                else None
            )

            rule_status = "FAIL" if failed > 0 else "PASS"

            rule_rows.append(
                (
                    str(uuid.uuid4()),
                    run_id,
                    rule["rule_id"],
                    checked,
                    rule["passed_count"],
                    failed,
                    0,
                    rule_status,
                    failure_rate,
                )
            )

        cursor.executemany(
            """
            INSERT INTO DQ_RULE_RESULTS (
                RESULT_ID,
                RUN_ID,
                RULE_ID,
                CHECKED_COUNT,
                PASSED_COUNT,
                FAILED_COUNT,
                SKIPPED_COUNT,
                RULE_STATUS,
                FAILURE_RATE,
                EXECUTED_AT
            )
            VALUES (
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, CURRENT_TIMESTAMP()
            )
            """,
            rule_rows,
        )

        # Insert individual exceptions.
        exceptions = result["exceptions"]

        if exceptions:
            exception_rows = [
                (
                    exception["exception_id"],
                    exception["run_id"],
                    exception["rule_id"],
                    exception["record_id"],
                    exception["severity"],
                    exception["description"],
                    exception["assigned_to"],
                    exception["status"],
                    exception["resolution_notes"],
                )
                for exception in exceptions
            ]

            cursor.executemany(
                """
                INSERT INTO DQ_EXCEPTIONS (
                    EXCEPTION_ID,
                    RUN_ID,
                    RULE_ID,
                    RECORD_ID,
                    SEVERITY,
                    DESCRIPTION,
                    ASSIGNED_TO,
                    STATUS,
                    RESOLUTION_NOTES
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                exception_rows,
            )

        connection.commit()

        print(f"Successfully persisted run: {run_id}")
        print(f"Rule results inserted: {len(rule_rows)}")
        print(f"Exceptions inserted: {len(exceptions)}")

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()

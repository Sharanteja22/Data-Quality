
package com.teja.data_quality_backend.repository;

import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Repository;

import java.sql.Timestamp;
import java.time.LocalDateTime;

import com.teja.data_quality_backend.model.BatchRecord;
import java.sql.Types;
import java.util.List;
import java.util.Map;

import com.teja.data_quality_backend.model.RuleResult;
import com.teja.data_quality_backend.model.DQException;

@Repository
public class BatchRepository {

    private final JdbcTemplate jdbcTemplate;

    public BatchRepository(JdbcTemplate snowflakeJdbcTemplate) {
        this.jdbcTemplate = snowflakeJdbcTemplate;
    }

    public void createBatch(
            String batchId,
            String fileName,
            String sourceSystem,
            LocalDateTime receivedAt
    ) {

        String sql = """
            INSERT INTO BATCHES (
                BATCH_ID,
                FILE_NAME,
                SOURCE_SYSTEM,
                RECORD_COUNT,
                RAW_S3_KEY,
                SOURCE_CHECKSUM,
                RECEIVED_AT,
                EXPECTED_AT,
                BATCH_STATUS
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """;

        jdbcTemplate.update(
                sql,
                batchId,
                fileName,
                sourceSystem,
                null,
                null,
                null,
                Timestamp.valueOf(receivedAt),
                null,
                "RECEIVED"
        );
    }

    public void createInitialRun(
            String runId,
            String batchId,
            LocalDateTime executedAt
    ) {

        String sql = """
            INSERT INTO BATCH_RUNS (
                RUN_ID,
                BATCH_ID,
                PARENT_RUN_ID,
                RUN_NUMBER,
                RUN_TYPE,
                INPUT_S3_KEY,
                RULESET_VERSION,
                COMPLETENESS_SCORE,
                VALIDITY_SCORE,
                UNIQUENESS_SCORE,
                CONSISTENCY_SCORE,
                TIMELINESS_SCORE,
                OVERALL_SCORE,
                CRITICAL_FAILURES,
                HIGH_FAILURES,
                WARNING_COUNT,
                FINAL_STATUS,
                PUBLICATION_ALLOWED,
                EXECUTED_AT
            )
            VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
            """;

        jdbcTemplate.update(
                sql,
                runId,
                batchId,
                null,
                1,
                "INITIAL",
                null,
                "1.0",
                null,
                null,
                null,
                null,
                null,
                null,
                0,
                0,
                0,
                null,
                false,
                Timestamp.valueOf(executedAt)
        );
    }

    public void markBatchProcessed(String batchId) {

        String sql = """
            UPDATE BATCHES
            SET BATCH_STATUS = ?
            WHERE BATCH_ID = ?
            """;

        jdbcTemplate.update(sql, "PROCESSED", batchId);
    }


    public void updateBatchRecordCount(String batchId, int recordCount) {

        String sql = """
            UPDATE BATCHES
            SET RECORD_COUNT = ?,
                BATCH_STATUS = ?
            WHERE BATCH_ID = ?
            """;

        jdbcTemplate.update(sql, recordCount, "PROCESSED", batchId);
    }

    public void updateRunResults(
            String runId,
            java.math.BigDecimal completenessScore,
            java.math.BigDecimal validityScore,
            java.math.BigDecimal uniquenessScore,
            java.math.BigDecimal consistencyScore,
            java.math.BigDecimal timelinessScore,
            java.math.BigDecimal overallScore,
            int criticalFailures,
            int highFailures,
            int warningCount,
            String finalStatus,
            boolean publicationAllowed
    ) {

        String sql = """
            UPDATE BATCH_RUNS
            SET COMPLETENESS_SCORE = ?,
                VALIDITY_SCORE = ?,
                UNIQUENESS_SCORE = ?,
                CONSISTENCY_SCORE = ?,
                TIMELINESS_SCORE = ?,
                OVERALL_SCORE = ?,
                CRITICAL_FAILURES = ?,
                HIGH_FAILURES = ?,
                WARNING_COUNT = ?,
                FINAL_STATUS = ?,
                PUBLICATION_ALLOWED = ?
            WHERE RUN_ID = ?
            """;

        jdbcTemplate.update(
                sql,
                completenessScore,
                validityScore,
                uniquenessScore,
                consistencyScore,
                timelinessScore,
                overallScore,
                criticalFailures,
                highFailures,
                warningCount,
                finalStatus,
                publicationAllowed,
                runId
        );
    }


    public void insertBatchRecords(List<BatchRecord> records) {

        String sql = """
            INSERT INTO BATCH_RECORDS (
                RECORD_ID,
                RUN_ID,
                SOURCE_ROW_NUMBER,
                TRANSACTION_ID,
                CUSTOMER_ID,
                ACCOUNT_ID,
                TRANSACTION_DATE,
                AMOUNT,
                CURRENCY,
                COUNTRY,
                TRANSACTION_TYPE,
                STATUS,
                CREATED_AT
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """;

        jdbcTemplate.batchUpdate(
            sql,
            records,
            100,
            (ps, record) -> {

                ps.setString(1, record.recordId());
                ps.setString(2, record.runId());
                ps.setInt(3, record.sourceRowNumber());

                ps.setString(4, record.transactionId());
                ps.setString(5, record.customerId());
                ps.setString(6, record.accountId());

                if (record.transactionDate() != null) {
                    ps.setTimestamp(
                        7,
                        Timestamp.valueOf(record.transactionDate())
                    );
                } else {
                    ps.setNull(7, Types.TIMESTAMP);
                }

                if (record.amount() != null) {
                    ps.setBigDecimal(8, record.amount());
                } else {
                    ps.setNull(8, Types.DECIMAL);
                }

                ps.setString(9, record.currency());
                ps.setString(10, record.country());
                ps.setString(11, record.transactionType());
                ps.setString(12, record.status());

                if (record.createdAt() != null) {
                    ps.setTimestamp(
                        13,
                        Timestamp.valueOf(record.createdAt())
                    );
                } else {
                    ps.setNull(13, Types.TIMESTAMP);
                }
            }
        );
    }


    public void insertRuleResults(List<RuleResult> results) {

        String sql = """
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
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """;

        Timestamp executedAt = Timestamp.from(
                java.time.Instant.now()
        );

        jdbcTemplate.batchUpdate(
            sql,
            results,
            100,
            (ps, result) -> {

                ps.setString(1, result.resultId());
                ps.setString(2, result.runId());
                ps.setString(3, result.ruleId());

                ps.setInt(4, result.checkedCount());
                ps.setInt(5, result.passedCount());
                ps.setInt(6, result.failedCount());
                ps.setInt(7, result.skippedCount());

                ps.setString(8, result.ruleStatus());

                if (result.failureRate() != null) {
                    ps.setBigDecimal(9, result.failureRate());
                } else {
                    ps.setNull(9, java.sql.Types.DECIMAL);
                }

                ps.setTimestamp(10, executedAt);
            }
        );
    }


    public void insertDQExceptions(List<DQException> exceptions) {

        // String sql = """
        //     INSERT INTO DQ_EXCEPTIONS (
        //         EXCEPTION_ID,
        //         'EXC-' || UPPER(SUBSTR(REPLACE(EXCEPTION_ID, '-', ''), 1, 12)) AS DISPLAY_EXCEPTION_ID,
        //         RUN_ID,
        //         RULE_ID,
        //         RECORD_ID,
        //         SEVERITY,
        //         DESCRIPTION,
        //         ASSIGNED_TO
        //     )
        //     VALUES (?, ?, ?, ?, ?, ?, ?)
        //     """;
        String sql = """
            INSERT INTO DQ_EXCEPTIONS (
                EXCEPTION_ID,
                RUN_ID,
                RULE_ID,
                RECORD_ID,
                SEVERITY,
                DESCRIPTION,
                ASSIGNED_TO
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """;
        jdbcTemplate.batchUpdate(
            sql,
            exceptions,
            100,
            (ps, exception) -> {

                ps.setString(1, exception.exceptionId());
                ps.setString(2, exception.runId());
                ps.setString(3, exception.ruleId());

                if (exception.recordId() != null) {
                    ps.setString(4, exception.recordId());
                } else {
                    ps.setNull(4, java.sql.Types.VARCHAR);
                }

                ps.setString(5, exception.severity());
                ps.setString(6, exception.description());
                ps.setString(7, exception.assignedTo());
            }
        );
    }


    public void markBatchFailed(String batchId) {

        String sql = """
            UPDATE BATCHES
            SET BATCH_STATUS = 'FAILED'
            WHERE BATCH_ID = ?
            """;

        jdbcTemplate.update(sql, batchId);
    }


    public void markRunFailed(String runId) {

        String sql = """
            UPDATE BATCH_RUNS
            SET FINAL_STATUS = 'FAILED',
                PUBLICATION_ALLOWED = FALSE
            WHERE RUN_ID = ?
            """;

        jdbcTemplate.update(sql, runId);
    }

    public boolean isPublicationAllowed(String runId) {

    String sql = """
        SELECT PUBLICATION_ALLOWED
        FROM BATCH_RUNS
        WHERE RUN_ID = ?
        """;

    Boolean allowed = jdbcTemplate.queryForObject(
            sql,
            Boolean.class,
            runId
    );

    return Boolean.TRUE.equals(allowed);
}


    public void updateBatchStorageDetails(
            String batchId,
            String s3Key,
            String checksum
    ) {

        String sql = """
            UPDATE BATCHES
            SET RAW_S3_KEY = ?,
                SOURCE_CHECKSUM = ?
            WHERE BATCH_ID = ?
            """;

        jdbcTemplate.update(sql, s3Key, checksum, batchId);
    }

    public void updateRunInputS3Key(String runId, String s3Key) {

        String sql = """
            UPDATE BATCH_RUNS
            SET INPUT_S3_KEY = ?
            WHERE RUN_ID = ?
            """;

        jdbcTemplate.update(sql, s3Key, runId);
    }

    public void updateRunQuarantineKey(String runId, String quarantineS3Key) {

        String sql = """
            UPDATE BATCH_RUNS
            SET QUARANTINE_S3_KEY = ?
            WHERE RUN_ID = ?
            """;

        jdbcTemplate.update(sql, quarantineS3Key, runId);
    }


    public String getRunInputS3Key(String runId) {

        String sql = """
            SELECT INPUT_S3_KEY
            FROM BATCH_RUNS
            WHERE RUN_ID = ?
            """;

        return jdbcTemplate.queryForObject(
                sql,
                String.class,
                runId
        );
    }


public List<Map<String, Object>> getAllBatches() {

    String sql = """
        SELECT *,
               REPLACE(BATCH_ID, 'BATCH-', 'BAT-') AS DISPLAY_BATCH_ID
        FROM BATCHES
        ORDER BY RECEIVED_AT DESC
        """;

    return jdbcTemplate.queryForList(sql);
}

    public Map<String, Object> getBatchById(String batchId) {

        String sql = """
            SELECT *,
                   REPLACE(BATCH_ID, 'BATCH-', 'BAT-') AS DISPLAY_BATCH_ID
            FROM BATCHES
            WHERE BATCH_ID = ?
            """;

        return jdbcTemplate.queryForMap(sql, batchId);
    }

    public List<Map<String, Object>> getBatchRuns(String batchId) {

        String sql = """
            SELECT *
            FROM BATCH_RUNS
            WHERE BATCH_ID = ?
            ORDER BY RUN_NUMBER DESC
            """;

        return jdbcTemplate.queryForList(sql, batchId);
    }

    public List<Map<String, Object>> getBatchRecords(String runId) {

        String sql = """
            SELECT *
            FROM BATCH_RECORDS
            WHERE RUN_ID = ?
            ORDER BY SOURCE_ROW_NUMBER
            """;

        return jdbcTemplate.queryForList(sql, runId);
    }


    public Map<String, Object> getRunScorecard(String runId) {

        String sql = """
            SELECT
                RUN_ID,
                BATCH_ID,
                RUN_NUMBER,
                RUN_TYPE,
                RULESET_VERSION,
                COMPLETENESS_SCORE,
                VALIDITY_SCORE,
                UNIQUENESS_SCORE,
                CONSISTENCY_SCORE,
                TIMELINESS_SCORE,
                OVERALL_SCORE,
                CRITICAL_FAILURES,
                HIGH_FAILURES,
                WARNING_COUNT,
                FINAL_STATUS,
                PUBLICATION_ALLOWED,
                EXECUTED_AT,
                INPUT_S3_KEY,
                QUARANTINE_S3_KEY
            FROM BATCH_RUNS
            WHERE RUN_ID = ?
            """;

        return jdbcTemplate.queryForMap(sql, runId);
    }

    public List<Map<String, Object>> getRuleResults(String runId) {

        String sql = """
            SELECT
                RR.RESULT_ID,
                RR.RUN_ID,
                RR.RULE_ID,
                DR.RULE_NAME,
                DR.DIMENSION,
                DR.SEVERITY,
                DR.OWNER,
                DR.IS_BLOCKING,
                RR.CHECKED_COUNT,
                RR.PASSED_COUNT,
                RR.FAILED_COUNT,
                RR.SKIPPED_COUNT,
                RR.RULE_STATUS,
                RR.FAILURE_RATE,
                RR.EXECUTED_AT
            FROM DQ_RULE_RESULTS RR
            JOIN DQ_RULES DR
                ON RR.RULE_ID = DR.RULE_ID
            WHERE RR.RUN_ID = ?
            ORDER BY DR.DIMENSION, RR.RULE_ID
            """;

        return jdbcTemplate.queryForList(sql, runId);
    }

    public List<Map<String, Object>> getRunExceptions(String runId) {

        String sql = """
            SELECT
                EXCEPTION_ID,
                'EXC-' || UPPER(SUBSTR(REPLACE(EXCEPTION_ID, '-', ''), 1, 12)) AS DISPLAY_EXCEPTION_ID,
                RUN_ID,
                RULE_ID,
                RECORD_ID,
                SEVERITY,
                DESCRIPTION,
                ASSIGNED_TO,
                STATUS,
                RESOLUTION_NOTES,
                CREATED_AT,
                RESOLVED_AT
            FROM DQ_EXCEPTIONS
            WHERE RUN_ID = ?
            ORDER BY CREATED_AT DESC
            """;

        return jdbcTemplate.queryForList(sql, runId);
    }



    public int updateException(
            String exceptionId,
            String status,
            String assignedTo,
            String resolutionNotes) {

        String sql = """
            UPDATE DQ_EXCEPTIONS
            SET STATUS = ?,
                ASSIGNED_TO = ?,
                RESOLUTION_NOTES = ?,
                RESOLVED_AT = CASE
                    WHEN ? = 'RESOLVED' THEN CURRENT_TIMESTAMP()
                    ELSE NULL
                END
            WHERE EXCEPTION_ID = ?
            """;

        return jdbcTemplate.update(
                sql,
                status,
                assignedTo,
                resolutionNotes,
                status,
                exceptionId
        );
    }



    public Map<String, Object> getLatestRunForBatch(String batchId) {

        String sql = """
            SELECT *
            FROM BATCH_RUNS
            WHERE BATCH_ID = ?
            ORDER BY RUN_NUMBER DESC
            LIMIT 1
            """;

        return jdbcTemplate.queryForMap(sql, batchId);
    }



public void createReplayRun(
        String runId,
        String batchId,
        String parentRunId,
        int runNumber,
        String s3Key,
        LocalDateTime executedAt) {

    String sql = """
        INSERT INTO BATCH_RUNS (
            RUN_ID,
            BATCH_ID,
            PARENT_RUN_ID,
            RUN_NUMBER,
            RUN_TYPE,
            INPUT_S3_KEY,
            RULESET_VERSION,
            COMPLETENESS_SCORE,
            VALIDITY_SCORE,
            UNIQUENESS_SCORE,
            CONSISTENCY_SCORE,
            TIMELINESS_SCORE,
            OVERALL_SCORE,
            CRITICAL_FAILURES,
            HIGH_FAILURES,
            WARNING_COUNT,
            FINAL_STATUS,
            PUBLICATION_ALLOWED,
            EXECUTED_AT
        )
        VALUES (
            ?, ?, ?, ?, 'REPLAY', ?, '1.0',
            NULL, NULL, NULL, NULL, NULL, NULL,
            0, 0, 0, NULL, FALSE, ?
        )
        """;

    jdbcTemplate.update(
            sql,
            runId,
            batchId,
            parentRunId,
            runNumber,
            s3Key,
            Timestamp.valueOf(executedAt)
    );
}


public void updateRunInputChecksum(
        String runId,
        String checksum) {

    String sql = """
        UPDATE BATCH_RUNS
        SET INPUT_CHECKSUM = ?
        WHERE RUN_ID = ?
        """;

    jdbcTemplate.update(sql, checksum, runId);
}

}


package com.teja.data_quality_backend.service;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.teja.data_quality_backend.client.PythonEngineClient;
import com.teja.data_quality_backend.repository.BatchRepository;

import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.math.BigDecimal;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.UUID;
import java.util.List;
import java.util.Map;
import com.teja.data_quality_backend.model.BatchRecord;
import java.util.ArrayList;
import java.time.LocalDate;
import java.time.format.DateTimeParseException;
import com.teja.data_quality_backend.model.ExceptionUpdateRequest;

import com.teja.data_quality_backend.model.BatchRecord;
import com.teja.data_quality_backend.model.RuleResult;
import com.teja.data_quality_backend.model.DQException;
import com.teja.data_quality_backend.model.ExceptionUpdateRequest;

import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HexFormat;
import java.util.LinkedHashMap;

import com.teja.data_quality_backend.service.S3Service;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.locks.ReentrantLock;

@Service
public class BatchService {

    private final PythonEngineClient pythonEngineClient;
    private final BatchRepository batchRepository;
    private final S3Service s3Service;
    private final ConcurrentHashMap<String, ReentrantLock> replayLocks =
        new ConcurrentHashMap<>();
    private static final Logger log = LoggerFactory.getLogger(BatchService.class);
    public BatchService(
            PythonEngineClient pythonEngineClient,
            BatchRepository batchRepository,
            S3Service s3Service) {

        this.pythonEngineClient = pythonEngineClient;
        this.batchRepository = batchRepository;
        this.s3Service = s3Service;
    }

    

    public JsonNode processBatch(MultipartFile file)
            throws IOException, InterruptedException {
        validateCsvFile(file);
        String batchId = generateBatchId();
        String runId = batchId + "_RUN001";

        LocalDateTime receivedAt = LocalDateTime.now();
        LocalDateTime createdAt = receivedAt;

        Path temporaryFile = Files.createTempFile(
                "data-quality-upload-", ".csv"
        );

        try {

            // 1. Save original upload temporarily.
            file.transferTo(temporaryFile);

            // 2. Upload original file to S3.
            String s3Key = s3Service.uploadRawFile(
                    temporaryFile,
                    batchId,
                    file.getOriginalFilename()
            );

            // 3. Calculate SHA-256 checksum.
            String checksum = calculateSha256(temporaryFile);

            // 4. Register batch in Snowflake.
            batchRepository.createBatch(
                    batchId,
                    file.getOriginalFilename(),
                    "DATA_QUALITY_API",
                    receivedAt
            );

            // 5. Store S3 key and checksum.
            batchRepository.updateBatchStorageDetails(
                    batchId,
                    s3Key,
                    checksum
            );

            // 6. Register initial run.
            batchRepository.createInitialRun(
                    runId,
                    batchId,
                    receivedAt
            );

            batchRepository.updateRunInputS3Key(runId, s3Key);

            // 7. Execute Python DQ engine.
            JsonNode result = pythonEngineClient.executePipeline(
                    temporaryFile,
                    runId,
                    createdAt,
                    receivedAt
            );

            // 8. Handle successful Python execution.
            if ("COMPLETED".equals(
                    result.path("pipeline_status").asText())) {

                try {

                    persistEvaluationResults(
                            result,
                            batchId,
                            runId
                    );

                } catch (Exception exception) {

                    // Persistence failure must never allow publication.
                    batchRepository.markBatchFailed(batchId);
                    batchRepository.markRunFailed(runId);

                    // Attempt quarantine without hiding the original error.
                    try {
                        quarantineBatch(batchId, runId);
                    } catch (Exception quarantineException) {
                        exception.addSuppressed(quarantineException);
                    }

                    throw new IllegalStateException(
                            "Failed to persist data quality results",
                            exception
                    );
                }

            } else {

                // 9. Python pipeline execution failed.
                batchRepository.markBatchFailed(batchId);
                batchRepository.markRunFailed(runId);

                // Quarantine the original file.
                quarantineBatch(batchId, runId);
            }

            // 10. Add upload metadata to API response.
            if (result instanceof ObjectNode response) {

                response.put("batch_id", batchId);
                response.put("file_name", file.getOriginalFilename());
                response.put("file_size", file.getSize());
                response.put("s3_key", s3Key);
                response.put("source_checksum", checksum);
            }

            return result;

        } finally {
            Files.deleteIfExists(temporaryFile);
        }
    }

    private void persistEvaluationResults(
            JsonNode result,
            String batchId,
            String runId) {

        // 1. Persist parsed batch records.
        persistBatchRecords(result, runId);

        // 2. Persist rule-level evaluation results.
        persistRuleResults(result, runId);

        // 3. Persist individual DQ exceptions.
        persistDQExceptions(result, runId);

        JsonNode scoreResult = result.path("score_result");
        JsonNode dimensions = scoreResult.path("dimension_scores");
        JsonNode decision = result.path("decision_result");

        // 4. Extract dimension scores.
        BigDecimal completeness =
                getScore(dimensions, "COMPLETENESS");

        BigDecimal validity =
                getScore(dimensions, "VALIDITY");

        BigDecimal uniqueness =
                getScore(dimensions, "UNIQUENESS");

        BigDecimal consistency =
                getScore(dimensions, "CONSISTENCY");

        BigDecimal timeliness =
                getScore(dimensions, "TIMELINESS");

        BigDecimal overallScore =
                getDecimal(scoreResult, "overall_score");

        // 5. Count blocking failures.
        int criticalFailures = countFailedRecords(
                decision.path("blocking_rule_failures"),
                "CRITICAL"
        );

        int highFailures = countFailedRecords(
                decision.path("blocking_rule_failures"),
                "HIGH"
        );

        // 6. Count nonblocking failed records.
        int warningCount = countAllFailedRecords(
                decision.path("nonblocking_rule_failures")
        );

        String finalStatus =
                decision.path("final_status").asText();

        boolean publicationAllowed =
                decision.path("publication_allowed").asBoolean(false);

        int recordCount =
                result.path("record_count").asInt();

        // 7. Update batch metadata.
        batchRepository.updateBatchRecordCount(
                batchId,
                recordCount
        );

        // 8. Persist final run decision.
        batchRepository.updateRunResults(
                runId,
                completeness,
                validity,
                uniqueness,
                consistency,
                timeliness,
                overallScore,
                criticalFailures,
                highFailures,
                warningCount,
                finalStatus,
                publicationAllowed
        );

        // 9. Quarantine BLOCK runs.
        if ("BLOCK".equalsIgnoreCase(finalStatus)) {
            quarantineBatch(batchId, runId);
        }
    }

    private void quarantineBatch(String batchId, String runId) {

        try {
            // Find the original S3 input key.
            String sourceS3Key =
                    batchRepository.getRunInputS3Key(runId);

            if (sourceS3Key == null || sourceS3Key.isBlank()) {
                throw new IllegalStateException(
                        "Original S3 input key is missing for run: " + runId
                );
            }

            // Extract original filename from the S3 key.
            String originalFileName =
                    java.nio.file.Path.of(sourceS3Key)
                            .getFileName()
                            .toString();

            // Copy original file into quarantine.
            String quarantineS3Key =
                    s3Service.copyToQuarantine(
                            sourceS3Key,
                            batchId,
                            runId,
                            originalFileName
                    );

            // Persist quarantine location in Snowflake.
            batchRepository.updateRunQuarantineKey(
                    runId,
                    quarantineS3Key
            );

            log.info(
                    "Batch {} quarantined successfully. S3 key: {}",
                    batchId,
                    quarantineS3Key
            );

        } catch (Exception exception) {

            log.error(
                    "Quarantine operation failed for batch {} and run {}",
                    batchId,
                    runId,
                    exception
            );

            throw new IllegalStateException(
                    "Batch is BLOCKED, but quarantine operation failed.",
                    exception
            );
        }
    }


    private BigDecimal getScore(
            JsonNode dimensions,
            String dimensionName) {

        JsonNode score = dimensions
                .path(dimensionName)
                .path("score");

        if (score.isMissingNode() || score.isNull()
                || !score.isNumber()) {
            return null;
        }

        return score.decimalValue();
    }

    private BigDecimal getDecimal(
            JsonNode parent,
            String fieldName) {

        JsonNode value = parent.path(fieldName);

        if (value.isMissingNode() || value.isNull()
                || !value.isNumber()) {
            return null;
        }

        return value.decimalValue();
    }

    private int countFailedRecords(
            JsonNode failures,
            String severity) {

        int count = 0;

        if (failures.isArray()) {
            for (JsonNode failure : failures) {

                if (severity.equals(
                        failure.path("severity").asText())) {

                    count += failure.path("failed_count").asInt();
                }
            }
        }

        return count;
    }

    private int countAllFailedRecords(JsonNode failures) {

        int count = 0;

        if (failures.isArray()) {
            for (JsonNode failure : failures) {
                count += failure.path("failed_count").asInt();
            }
        }

        return count;
    }

    private String generateBatchId() {

        String date = LocalDateTime.now().format(
                DateTimeFormatter.ofPattern("yyyyMMdd")
        );

        String uniqueId = UUID.randomUUID()
                .toString()
                .substring(0, 5)
                .toUpperCase();

        return "BAT-" + date + "-" + uniqueId;
    }


    private void persistBatchRecords(JsonNode result, String runId) {

        JsonNode recordsNode = result.path("records");

        if (!recordsNode.isArray()) {
            throw new IllegalStateException(
                    "Python response does not contain a valid records array"
            );
        }

        List<BatchRecord> records = new ArrayList<>();

        for (JsonNode node : recordsNode) {

            BatchRecord record = new BatchRecord(
                    getText(node, "record_id"),
                    getText(node, "run_id"),
                    node.path("source_row_number").asInt(),
                    getText(node, "transaction_id"),
                    getText(node, "customer_id"),
                    getText(node, "account_id"),
                    parseDateTime(node, "transaction_date"),
                    parseAmount(node, "amount"),
                    getText(node, "currency"),
                    getText(node, "country"),
                    getText(node, "transaction_type"),
                    getText(node, "status"),
                    parseDateTime(node, "created_at")
            );

            if (!runId.equals(record.runId())) {
                throw new IllegalStateException(
                        "Record run_id does not match the current batch run"
                );
            }

            if (record.recordId() == null || record.recordId().isBlank()) {
                throw new IllegalStateException(
                        "Record ID is missing"
                );
            }

            records.add(record);
        }

        int expectedCount = result.path("record_count").asInt();

        if (records.size() != expectedCount) {
            throw new IllegalStateException(
                    "Record count mismatch. Expected: "
                            + expectedCount + ", Received: " + records.size()
            );
        }

        batchRepository.insertBatchRecords(records);
    }


    private String getText(JsonNode node, String fieldName) {

        JsonNode value = node.path(fieldName);

        if (value.isMissingNode() || value.isNull()) {
            return null;
        }

        String text = value.asText();

        return text.isBlank() ? null : text;
    }


    private BigDecimal parseAmount(JsonNode node, String fieldName) {

        String value = getText(node, fieldName);

        if (value == null) {
            return null;
        }

        try {
            return new BigDecimal(value);
        } catch (NumberFormatException exception) {
            // Invalid amounts are retained as null in the numeric Snowflake column.
            // The original CSV remains the source of the unmodified value.
            return null;
        }
    }


    private LocalDateTime parseDateTime(JsonNode node, String fieldName) {

        String value = getText(node, fieldName);

        if (value == null) {
            return null;
        }

        try {
            // Supports timestamps such as 2026-11-09 13:24:00
            return LocalDateTime.parse(
                    value.replace(" ", "T")
            );

        } catch (DateTimeParseException exception) {

            try {
                // Supports date-only values such as 2026-11-09
                return LocalDate.parse(value).atStartOfDay();

            } catch (DateTimeParseException ignored) {
                return null;
            }
        }
    }


    private void persistRuleResults(JsonNode result, String runId) {

        JsonNode ruleResultsNode = result.path("rule_results");

        if (!ruleResultsNode.isArray()) {
            throw new IllegalStateException(
                    "Python response does not contain rule_results array"
            );
        }

        List<RuleResult> ruleResults = new ArrayList<>();

        for (JsonNode node : ruleResultsNode) {

            int checkedCount = node.path("checked_count").asInt();
            int passedCount = node.path("passed_count").asInt();
            int failedCount = node.path("failed_count").asInt();

            int skippedCount = node.path("skipped_count").asInt(0);

            BigDecimal failureRate = null;

            if (checkedCount > 0) {
                failureRate = BigDecimal.valueOf(
                        failedCount * 100.0 / checkedCount
                ).setScale(2, java.math.RoundingMode.HALF_UP);
            }

            String ruleStatus;

            if (checkedCount == 0) {
                ruleStatus = "NOT_EVALUATED";
            } else if (failedCount == 0) {
                ruleStatus = "PASS";
            } else {
                ruleStatus = "FAIL";
            }

            RuleResult ruleResult = new RuleResult(
                    UUID.randomUUID().toString(),
                    runId,
                    node.path("rule_id").asText(),
                    checkedCount,
                    passedCount,
                    failedCount,
                    skippedCount,
                    ruleStatus,
                    failureRate
            );

            ruleResults.add(ruleResult);
        }

        if (ruleResults.isEmpty()) {
            throw new IllegalStateException(
                    "No rule results were returned by Python"
            );
        }

        if (ruleResults.size() != 9) {
            throw new IllegalStateException(
                    "Expected 9 rule results but received "
                            + ruleResults.size()
            );
        }

        batchRepository.insertRuleResults(ruleResults);
    }


    private void persistDQExceptions(JsonNode result, String runId) {

        JsonNode exceptionsNode = result.path("exceptions");

        if (!exceptionsNode.isArray()) {
            throw new IllegalStateException(
                    "Python response does not contain exceptions array"
            );
        }

        List<DQException> exceptions = new ArrayList<>();

        for (JsonNode node : exceptionsNode) {

            String exceptionRunId = node.path("run_id").asText();

            if (!runId.equals(exceptionRunId)) {
                throw new IllegalStateException(
                        "Exception run_id does not match current run"
                );
            }

            String recordId = null;

            if (!node.path("record_id").isMissingNode()
                    && !node.path("record_id").isNull()) {

                recordId = node.path("record_id").asText();
            }

            DQException exception = new DQException(
                    node.path("exception_id").asText(),
                    runId,
                    node.path("rule_id").asText(),
                    recordId,
                    node.path("severity").asText(),
                    node.path("description").asText(),
                    node.path("assigned_to").asText()
            );

            exceptions.add(exception);
        }

        if (!exceptions.isEmpty()) {
            batchRepository.insertDQExceptions(exceptions);
        }
    }


    public void validatePublication(String runId) {

        boolean allowed =
                batchRepository.isPublicationAllowed(runId);

        if (!allowed) {
            throw new IllegalStateException(
                    "Publication prohibited: batch failed the data quality gate"
            );
        }
    }


    private String calculateSha256(Path filePath) throws IOException {

        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");

            try (var inputStream = Files.newInputStream(filePath)) {
                byte[] buffer = new byte[8192];
                int bytesRead;

                while ((bytesRead = inputStream.read(buffer)) != -1) {
                    digest.update(buffer, 0, bytesRead);
                }
            }

            return HexFormat.of().formatHex(digest.digest());

        } catch (NoSuchAlgorithmException exception) {
            throw new IllegalStateException(
                    "SHA-256 algorithm is unavailable",
                    exception
            );
        }
    }


    public List<Map<String, Object>> getAllBatches() {
        return batchRepository.getAllBatches();
    }

    public Map<String, Object> getBatchDetails(String batchId) {

        Map<String, Object> batch =
                batchRepository.getBatchById(batchId);

        List<Map<String, Object>> runs =
                batchRepository.getBatchRuns(batchId);

        Map<String, Object> response = new LinkedHashMap<>();
        response.put("batch", batch);
        response.put("runs", runs);

        return response;
    }

    public List<Map<String, Object>> getBatchRecords(String batchId) {

        // Find the latest run for this batch.
        List<Map<String, Object>> runs =
                batchRepository.getBatchRuns(batchId);

        if (runs.isEmpty()) {
            throw new IllegalArgumentException(
                    "No runs found for batch: " + batchId
            );
        }

        String runId = String.valueOf(runs.get(0).get("RUN_ID"));

        return batchRepository.getBatchRecords(runId);
    }


    public Map<String, Object> getRunScorecard(String runId) {
        return batchRepository.getRunScorecard(runId);
    }

    public List<Map<String, Object>> getRuleResults(String runId) {
        return batchRepository.getRuleResults(runId);
    }

    public List<Map<String, Object>> getRunExceptions(String runId) {
        return batchRepository.getRunExceptions(runId);
    }


    public void updateException(
            String exceptionId,
            ExceptionUpdateRequest request) {

        int updated = batchRepository.updateException(
                exceptionId,
                request.status(),
                request.assignedTo(),
                request.resolutionNotes()
        );

        if (updated == 0) {
            throw new IllegalArgumentException(
                    "Exception not found: " + exceptionId
            );
        }
    }



    private JsonNode replayBatchInternal(
            String batchId,
            MultipartFile file)
            throws IOException, InterruptedException {

        // 1. Find the latest run.
        Map<String, Object> previousRun =
                batchRepository.getLatestRunForBatch(batchId);

        String parentRunId =
                String.valueOf(previousRun.get("RUN_ID"));

        int previousRunNumber =
                ((Number) previousRun.get("RUN_NUMBER")).intValue();

        int newRunNumber = previousRunNumber + 1;

        String previousStatus =
            String.valueOf(previousRun.get("FINAL_STATUS"));

        if (!"BLOCK".equalsIgnoreCase(previousStatus)
                && !"FAILED".equalsIgnoreCase(previousStatus)) {

            throw new IllegalStateException(
                    "Replay is allowed only for BLOCK or FAILED batches."
            );
        }
        String runId = batchId + "_RUN"
                + String.format("%03d", newRunNumber);

        LocalDateTime receivedAt = LocalDateTime.now();

        Path temporaryFile = Files.createTempFile(
                "data-quality-replay-", ".csv"
        );

        try {

            // 2. Save corrected CSV temporarily.
            file.transferTo(temporaryFile);

            // 3. Upload corrected CSV to S3.
            String correctedS3Key =
                    s3Service.uploadCorrectedFile(
                            temporaryFile,
                            batchId,
                            runId,
                            file.getOriginalFilename()
                    );

            // 4. Calculate checksum.
            String checksum = calculateSha256(temporaryFile);

            // 5. Create new replay run.
            batchRepository.createReplayRun(
                    runId,
                    batchId,
                    parentRunId,
                    newRunNumber,
                    correctedS3Key,
                    receivedAt
            );
            batchRepository.updateRunInputChecksum(
                    runId,
                    checksum
            );

            // 6. Execute Python DQ engine.
            JsonNode result = pythonEngineClient.executePipeline(
                    temporaryFile,
                    runId,
                    receivedAt,
                    receivedAt
            );

            // 7. Persist new evaluation results.
            if ("COMPLETED".equals(
                    result.path("pipeline_status").asText())) {

                try {
                    persistEvaluationResults(
                            result,
                            batchId,
                            runId
                    );

                } catch (Exception exception) {

                    batchRepository.markBatchFailed(batchId);
                    batchRepository.markRunFailed(runId);

                    try {
                        quarantineBatch(batchId, runId);
                    } catch (Exception quarantineException) {
                        exception.addSuppressed(quarantineException);
                    }

                    throw new IllegalStateException(
                            "Replay result persistence failed",
                            exception
                    );
                }

            } else {

                batchRepository.markBatchFailed(batchId);
                batchRepository.markRunFailed(runId);
                quarantineBatch(batchId, runId);
            }

            // 8. Add replay metadata to response.
            if (result instanceof ObjectNode response) {

                response.put("batch_id", batchId);
                response.put("run_id", runId);
                response.put("parent_run_id", parentRunId);
                response.put("run_number", newRunNumber);
                response.put("run_type", "REPLAY");
                response.put("s3_key", correctedS3Key);
                response.put("source_checksum", checksum);
            }

            return result;

        } finally {
            Files.deleteIfExists(temporaryFile);
        }
    }

    public JsonNode replayBatch(
        String batchId,
        MultipartFile file)
        throws IOException, InterruptedException {
            validateBatchId(batchId);
            validateCsvFile(file);
    ReentrantLock lock = replayLocks.computeIfAbsent(
            batchId,
            key -> new ReentrantLock()
    );

    lock.lock();

    try {
        return replayBatchInternal(batchId, file);
    } finally {
        lock.unlock();
    }
}


    private void validateCsvFile(MultipartFile file) {

        if (file == null || file.isEmpty()) {
            throw new IllegalArgumentException(
                    "CSV file cannot be empty."
            );
        }

        if (file.getSize() > 10 * 1024 * 1024) {
            throw new IllegalArgumentException(
                    "CSV file must not exceed 10 MB."
            );
        }

        String filename = file.getOriginalFilename();

        if (filename == null || filename.isBlank()) {
            throw new IllegalArgumentException(
                    "Filename is required."
            );
        }

        if (!filename.toLowerCase().endsWith(".csv")) {
            throw new IllegalArgumentException(
                    "Only CSV files are supported."
            );
        }

        if (filename.contains("/") || filename.contains("\\")
                || filename.contains("..")) {
            throw new IllegalArgumentException(
                    "Invalid filename."
            );
        }
    }


    private void validateBatchId(String batchId) {

        if (batchId == null
                || !batchId.matches("[A-Za-z0-9_-]{1,50}")) {
            throw new IllegalArgumentException(
                    "Invalid batch ID."
            );
        }
    }
}

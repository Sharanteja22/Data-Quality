
package com.teja.data_quality_backend.client;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.LocalDateTime;
import java.util.concurrent.TimeUnit;

@Component
public class PythonEngineClient {

    @Value("${python.engine.executable}")
    private String pythonExecutable;

    @Value("${python.engine.script}")
    private String pythonScript;

    private final ObjectMapper objectMapper;

    public PythonEngineClient(ObjectMapper objectMapper) {
        this.objectMapper = objectMapper;
    }

    public JsonNode executePipeline(
            Path csvPath,
            String runId,
            LocalDateTime batchCreatedAt,
            LocalDateTime batchReceivedAt
    ) throws IOException, InterruptedException {

        Path outputLog = Files.createTempFile(
                "dq-python-output-", ".json"
        );

        Path errorLog = Files.createTempFile(
                "dq-python-error-", ".log"
        );

        Process process = null;

        try {
            ProcessBuilder processBuilder = new ProcessBuilder(
                    pythonExecutable,
                    pythonScript,
                    csvPath.toAbsolutePath().toString(),
                    runId,
                    batchCreatedAt.toString(),
                    batchReceivedAt.toString()
            );

            // Redirect output to files instead of OS pipes.
            // This prevents the process output deadlock.
            processBuilder.redirectOutput(outputLog.toFile());
            processBuilder.redirectError(errorLog.toFile());

            long startTime = System.currentTimeMillis();

            process = processBuilder.start();

            boolean completed = process.waitFor(
                    5, TimeUnit.MINUTES
            );

            if (!completed) {

                process.destroyForcibly();

                // Ensure the process has actually terminated
                // before attempting to delete its log files.
                process.waitFor();

                throw new IOException(
                        "Python data quality engine timed out."
                );
            }

            long executionTime =
                    System.currentTimeMillis() - startTime;

            String output = Files.readString(outputLog);
            String errorOutput = Files.readString(errorLog);

            if (output.isBlank()) {
                throw new IOException(
                        "Python engine returned empty output. "
                                + errorOutput
                );
            }

            JsonNode result = objectMapper.readTree(output);

            if (process.exitValue() != 0
                    && !"FAILED".equals(
                            result.path("pipeline_status").asText()
                    )) {

                throw new IOException(
                        "Python engine failed: " + errorOutput
                );
            }

            System.out.println(
                    "Python engine execution time: "
                            + executionTime + " ms"
            );

            return result;

        } finally {

            // Process must finish before deleting its log files.
            if (process != null && process.isAlive()) {
                process.destroyForcibly();
                process.waitFor();
            }

            Files.deleteIfExists(outputLog);
            Files.deleteIfExists(errorLog);
        }
    }
}

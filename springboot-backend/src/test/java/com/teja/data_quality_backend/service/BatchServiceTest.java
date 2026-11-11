
package com.teja.data_quality_backend.service;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.teja.data_quality_backend.client.PythonEngineClient;
import com.teja.data_quality_backend.repository.BatchRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.mock.web.MockMultipartFile;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import org.junit.jupiter.api.Test;
import org.springframework.mock.web.MockMultipartFile;

import java.nio.file.Path;

import static org.mockito.ArgumentMatchers.*;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.Objects;

class BatchServiceTest {

    private PythonEngineClient pythonEngineClient;
    private BatchRepository batchRepository;
    private S3Service s3Service;

    private BatchService batchService;

    private ObjectMapper objectMapper;

    @BeforeEach
    void setUp() {
        pythonEngineClient = mock(PythonEngineClient.class);
        batchRepository = mock(BatchRepository.class);
        s3Service = mock(S3Service.class);

        batchService = new BatchService(
                pythonEngineClient,
                batchRepository,
                s3Service
        );

        objectMapper = new ObjectMapper();
    }

    @Test
    void shouldRejectEmptyFile() {

        MockMultipartFile file = new MockMultipartFile(
                "file",
                "transactions.csv",
                "text/csv",
                new byte[0]
        );

        assertThrows(
                IllegalArgumentException.class,
                () -> batchService.processBatch(file)
        );

        verifyNoInteractions(
                pythonEngineClient,
                batchRepository,
                s3Service
        );
    }

    @Test
    void shouldRejectNonCsvFile() {

        MockMultipartFile file = new MockMultipartFile(
                "file",
                "transactions.txt",
                "text/plain",
                "sample data".getBytes()
        );

        assertThrows(
                IllegalArgumentException.class,
                () -> batchService.processBatch(file)
        );

        verifyNoInteractions(
                pythonEngineClient,
                batchRepository,
                s3Service
        );
    }

    @Test
    void shouldStopProcessingWhenS3UploadFails() throws Exception {

        MockMultipartFile file = new MockMultipartFile(
                "file",
                "transactions.csv",
                "text/csv",
                "transaction_id,amount\nTX001,100".getBytes()
        );

        when(s3Service.uploadRawFile(
                any(Path.class),
                anyString(),
                anyString()
        )).thenThrow(new RuntimeException("S3 upload failed"));

        assertThrows(
                RuntimeException.class,
                () -> batchService.processBatch(file)
        );

        verify(s3Service).uploadRawFile(
                any(Path.class),
                anyString(),
                anyString()
        );

        verifyNoInteractions(pythonEngineClient);
        }

        @Test
void shouldMarkBatchFailedWhenPythonPipelineFails() throws Exception {

    MockMultipartFile file = new MockMultipartFile(
            "file",
            "transactions.csv",
            "text/csv",
            "transaction_id,amount\nTX001,100".getBytes()
    );

    when(s3Service.uploadRawFile(
            any(Path.class),
            anyString(),
            anyString()
    )).thenReturn("raw/test/transactions.csv");
    when(batchRepository.getRunInputS3Key(anyString()))
            .thenReturn("raw/test/transactions.csv");
    when(s3Service.copyToQuarantine(
            anyString(),
            anyString(),
            anyString(),
            anyString()
    )).thenReturn("quarantine/test/transactions.csv");

    when(pythonEngineClient.executePipeline(
            any(Path.class),
            anyString(),
            any(),
            any()
    )).thenReturn(objectMapper.readTree("""
        {
          "pipeline_status": "FAILED",
          "error": "Invalid CSV schema"
        }
        """));


    JsonNode response = batchService.processBatch(file);

    assertEquals("FAILED", response.path("pipeline_status").asText());

    verify(batchRepository).markBatchFailed(anyString());
    verify(batchRepository).markRunFailed(anyString());
}

private JsonNode loadFixture(String filename) throws Exception {

    try (InputStream input = Objects.requireNonNull(
            getClass().getResourceAsStream(
                    "/fixtures/" + filename
            ),
            "Missing fixture: " + filename
    )) {
        return objectMapper.readTree(input);
    }
}

private MockMultipartFile validCsv() {

    return new MockMultipartFile(
            "file",
            "transactions.csv",
            "text/csv",
            "transaction_id,amount\nTX001,100".getBytes(
                    StandardCharsets.UTF_8
            )
    );
}

private void mockStorage() throws Exception {

    when(s3Service.uploadRawFile(
            any(Path.class),
            anyString(),
            anyString()
    )).thenReturn("raw/test/transactions.csv");

    when(batchRepository.getRunInputS3Key(anyString()))
            .thenReturn("raw/test/transactions.csv");

    when(s3Service.copyToQuarantine(
            anyString(),
            anyString(),
            anyString(),
            anyString()
    )).thenReturn("quarantine/test/transactions.csv");
}
@Test
void shouldAllowPublicationForPassBatch() throws Exception {

    mockStorage();

    when(pythonEngineClient.executePipeline(
            any(Path.class),
            anyString(),
            any(),
            any()
    )).thenAnswer(invocation ->
        loadFixtureForRun(
                "pass-result.json",
                invocation.getArgument(1, String.class)
        )
);

    JsonNode result = batchService.processBatch(validCsv());

    assertEquals("PASS",
            result.path("decision_result").path("final_status").asText());

    verify(batchRepository).updateRunResults(
            anyString(),
            any(), any(), any(), any(), any(), any(),
            anyInt(), anyInt(), anyInt(),
            eq("PASS"),
            eq(true)
    );
}

@Test
void shouldAllowPublicationForWarnBatch() throws Exception {

    mockStorage();

    when(pythonEngineClient.executePipeline(
            any(Path.class),
            anyString(),
            any(),
            any()
    )).thenAnswer(invocation ->
        loadFixtureForRun(
                "warn-result.json",
                invocation.getArgument(1, String.class)
        )
);
    JsonNode result = batchService.processBatch(validCsv());

    assertEquals("WARN",
            result.path("decision_result").path("final_status").asText());

    verify(batchRepository).updateRunResults(
            anyString(),
            any(), any(), any(), any(), any(), any(),
            anyInt(), anyInt(), anyInt(),
            eq("WARN"),
            eq(true)
    );
}


@Test
void shouldBlockPublicationWhenCriticalRuleFails() throws Exception {

    mockStorage();

    when(pythonEngineClient.executePipeline(
            any(Path.class),
            anyString(),
            any(),
            any()
    )).thenAnswer(invocation ->
        loadFixtureForRun(
                "block-result.json",
                invocation.getArgument(1, String.class)
        )
);
    JsonNode result = batchService.processBatch(validCsv());

    assertEquals(
            "BLOCK",
            result.path("decision_result")
                    .path("final_status").asText()
    );

    assertFalse(
            result.path("decision_result")
                    .path("publication_allowed").asBoolean()
    );

    verify(batchRepository).updateRunResults(
            anyString(),
            any(), any(), any(), any(), any(), any(),
            anyInt(), anyInt(), anyInt(),
            eq("BLOCK"),
            eq(false)
    );

    verify(s3Service).copyToQuarantine(
            eq("raw/test/transactions.csv"),
            anyString(),
            anyString(),
            eq("transactions.csv")
    );
}
private JsonNode loadFixtureForRun(
        String filename,
        String actualRunId
) throws Exception {

    ObjectNode root = (ObjectNode) loadFixture(filename);

    // Update the main run ID.
    root.put("run_id", actualRunId);

    // Update every record's run ID.
    JsonNode records = root.path("records");

    if (records.isArray()) {
        for (JsonNode record : records) {
            if (record instanceof ObjectNode object) {
                object.put("run_id", actualRunId);
            }
        }
    }

    // Update every exception's run ID.
    JsonNode exceptions = root.path("exceptions");

    if (exceptions.isArray()) {
        for (JsonNode exception : exceptions) {
            if (exception instanceof ObjectNode object) {
                object.put("run_id", actualRunId);
            }
        }
    }

    return root;
}

}


package com.teja.data_quality_backend.controller;

import com.fasterxml.jackson.databind.JsonNode;
import com.teja.data_quality_backend.service.BatchService;

import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

@RestController
@RequestMapping("/api/batches")
public class BatchController {

    private final BatchService batchService;

    public BatchController(BatchService batchService) {
        this.batchService = batchService;
    }

    @PostMapping(
            value = "/upload",
            consumes = MediaType.MULTIPART_FORM_DATA_VALUE,
            produces = MediaType.APPLICATION_JSON_VALUE
    )
    public ResponseEntity<String> uploadBatch(
            @RequestParam("file") MultipartFile file) {

        if (file == null || file.isEmpty()) {
            return ResponseEntity.badRequest()
                    .body("{\"error\":\"Please upload a non-empty CSV file.\"}");
        }

        String fileName = file.getOriginalFilename();

        if (fileName == null ||
                !fileName.toLowerCase().endsWith(".csv")) {

            return ResponseEntity.badRequest()
                    .body("{\"error\":\"Only CSV files are supported.\"}");
        }

        try {
            JsonNode result = batchService.processBatch(file);

            // Serialize the complete JSON tree and return it directly.
            return ResponseEntity.ok()
                    .contentType(MediaType.APPLICATION_JSON)
                    .body(result.toString());

        } catch (InterruptedException exception) {

            Thread.currentThread().interrupt();

            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body("{\"error\":\"Data quality processing was interrupted.\"}");

        } catch (Exception exception) {

            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .contentType(MediaType.APPLICATION_JSON)
                    .body("{\"error\":\"Unable to process uploaded batch.\"}");
        }
    }

    @GetMapping
    public ResponseEntity<?> getAllBatches() {
        return ResponseEntity.ok(batchService.getAllBatches());
    }

    @GetMapping("/{batchId}")
    public ResponseEntity<?> getBatchDetails(
            @PathVariable String batchId) {

        return ResponseEntity.ok(
                batchService.getBatchDetails(batchId)
        );
    }

    @GetMapping("/{batchId}/records")
    public ResponseEntity<?> getBatchRecords(
            @PathVariable String batchId) {

        return ResponseEntity.ok(
                batchService.getBatchRecords(batchId)
        );
    }

    

}


package com.teja.data_quality_backend.controller;

import com.teja.data_quality_backend.service.BatchService;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/runs")
public class PublicationController {

    private final BatchService batchService;

    public PublicationController(BatchService batchService) {
        this.batchService = batchService;
    }

    @GetMapping("/{runId}/publication-check")
    public ResponseEntity<Map<String, Object>> checkPublication(
            @PathVariable String runId) {

        try {
            batchService.validatePublication(runId);

            return ResponseEntity.ok(Map.of(
                    "run_id", runId,
                    "publication_allowed", true,
                    "message", "Batch passed the publication gate"
            ));

        } catch (IllegalStateException exception) {

            return ResponseEntity.status(HttpStatus.FORBIDDEN)
                    .body(Map.of(
                            "run_id", runId,
                            "publication_allowed", false,
                            "message", exception.getMessage()
                    ));
        }
    }
}

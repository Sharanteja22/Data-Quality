package com.teja.data_quality_backend.controller;

import com.teja.data_quality_backend.service.BatchService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.Map;
import java.util.List;

@RestController
@RequestMapping("/api/runs")
public class RunController {

    private final BatchService batchService;

    public RunController(BatchService batchService) {
        this.batchService = batchService;
    }

    @GetMapping("/{runId}/scorecard")
    public ResponseEntity<?> getScorecard(
            @PathVariable String runId) {

        return ResponseEntity.ok(
                batchService.getRunScorecard(runId)
        );
    }

    @GetMapping("/{runId}/rule-results")
    public ResponseEntity<?> getRuleResults(
            @PathVariable String runId) {

        return ResponseEntity.ok(
                batchService.getRuleResults(runId)
        );
    }

    @GetMapping("/{runId}/exceptions")
    public ResponseEntity<?> getExceptions(
            @PathVariable String runId) {

        return ResponseEntity.ok(
                batchService.getRunExceptions(runId)
        );
    }
}

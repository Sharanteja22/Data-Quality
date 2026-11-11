
package com.teja.data_quality_backend.controller;

import com.teja.data_quality_backend.service.BatchService;

import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;
import com.fasterxml.jackson.databind.JsonNode;
@RestController
@RequestMapping("/api/batches")
public class ReplayController {

    private final BatchService batchService;

    public ReplayController(BatchService batchService) {
        this.batchService = batchService;
    }


@PostMapping(
    value = "/{batchId}/replay",
    consumes = MediaType.MULTIPART_FORM_DATA_VALUE,
    produces = MediaType.APPLICATION_JSON_VALUE
)
public ResponseEntity<String> replayBatch(
        @PathVariable String batchId,
        @RequestParam("file") MultipartFile file)
        throws Exception {

    if (file.isEmpty()) {
        return ResponseEntity.badRequest()
                .body("{\"error\":\"Corrected CSV file is required\"}");
    }

    JsonNode result = batchService.replayBatch(batchId, file);

    return ResponseEntity.ok()
            .contentType(MediaType.APPLICATION_JSON)
            .body(result.toString());
}


}

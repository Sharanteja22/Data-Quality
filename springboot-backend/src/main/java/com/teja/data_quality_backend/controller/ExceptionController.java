
package com.teja.data_quality_backend.controller;

import com.teja.data_quality_backend.model.ExceptionUpdateRequest;
import com.teja.data_quality_backend.service.BatchService;

import jakarta.validation.Valid;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/exceptions")
public class ExceptionController {

    private final BatchService batchService;

    public ExceptionController(BatchService batchService) {
        this.batchService = batchService;
    }

    @PatchMapping("/{exceptionId}")
    public ResponseEntity<?> updateException(
            @PathVariable String exceptionId,
            @Valid @RequestBody ExceptionUpdateRequest request) {

        batchService.updateException(exceptionId, request);

        return ResponseEntity.ok(
                java.util.Map.of(
                        "message", "Exception updated successfully",
                        "exception_id", exceptionId,
                        "status", request.status()
                )
        );
    }
}

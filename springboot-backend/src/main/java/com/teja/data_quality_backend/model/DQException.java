
package com.teja.data_quality_backend.model;

public record DQException(
        String exceptionId,
        String runId,
        String ruleId,
        String recordId,
        String severity,
        String description,
        String assignedTo
) {
}

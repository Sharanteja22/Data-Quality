
package com.teja.data_quality_backend.model;

import java.math.BigDecimal;
import java.time.LocalDateTime;

public record BatchRecord(
        String recordId,
        String runId,
        Integer sourceRowNumber,
        String transactionId,
        String customerId,
        String accountId,
        LocalDateTime transactionDate,
        BigDecimal amount,
        String currency,
        String country,
        String transactionType,
        String status,
        LocalDateTime createdAt
) {
}

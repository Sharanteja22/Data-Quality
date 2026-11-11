
package com.teja.data_quality_backend.model;

import java.math.BigDecimal;

public record RuleResult(
        String resultId,
        String runId,
        String ruleId,
        int checkedCount,
        int passedCount,
        int failedCount,
        int skippedCount,
        String ruleStatus,
        BigDecimal failureRate
) {
}

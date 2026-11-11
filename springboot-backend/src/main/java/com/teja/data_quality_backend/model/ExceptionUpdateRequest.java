
package com.teja.data_quality_backend.model;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;

public record ExceptionUpdateRequest(

    @NotBlank
    @Pattern(regexp = "OPEN|IN_PROGRESS|RESOLVED")
    String status,

    String assignedTo,

    String resolutionNotes
) {}

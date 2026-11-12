package com.teja.data_quality_backend.auth.dto;

public record AuthResponse(
        String accessToken,
        String tokenType,
        long expiresIn,
        UserSummary user
) {
    public record UserSummary(String userId, String fullName, String email, String role) {}
}

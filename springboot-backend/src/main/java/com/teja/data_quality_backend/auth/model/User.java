package com.teja.data_quality_backend.auth.model;

public record User(
        String userId,
        String fullName,
        String email,
        String passwordHash,
        String role,
        String status
) {}

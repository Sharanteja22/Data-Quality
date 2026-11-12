package com.teja.data_quality_backend.auth.controller;

import com.teja.data_quality_backend.auth.dto.AuthResponse;
import com.teja.data_quality_backend.auth.dto.LoginRequest;
import com.teja.data_quality_backend.auth.dto.RegisterRequest;
import com.teja.data_quality_backend.auth.service.AuthService;
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/auth")
public class AuthController {
    private final AuthService authService;

    public AuthController(AuthService authService) {
        this.authService = authService;
    }

    @PostMapping("/register")
    public ResponseEntity<AuthResponse> register(@Valid @RequestBody RegisterRequest request) {
        return ResponseEntity.ok(authService.register(request));
    }

    @PostMapping("/login")
    public ResponseEntity<AuthResponse> login(@Valid @RequestBody LoginRequest request) {
        return ResponseEntity.ok(authService.login(request));
    }

    @GetMapping("/me")
    public ResponseEntity<Map<String, Object>> me(Authentication authentication) {
        AuthResponse.UserSummary user = authService.getCurrentUser(authentication.getName());
        return ResponseEntity.ok(Map.of(
                "user_id", user.userId(),
                "full_name", user.fullName(),
                "email", user.email(),
                "role", user.role()
        ));
    }
}

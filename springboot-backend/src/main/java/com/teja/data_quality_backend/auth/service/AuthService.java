package com.teja.data_quality_backend.auth.service;

import com.teja.data_quality_backend.auth.dto.AuthResponse;
import com.teja.data_quality_backend.auth.dto.LoginRequest;
import com.teja.data_quality_backend.auth.dto.RegisterRequest;
import com.teja.data_quality_backend.auth.model.User;
import com.teja.data_quality_backend.auth.repository.UserRepository;
import com.teja.data_quality_backend.auth.security.JwtService;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.authentication.BadCredentialsException;
import org.springframework.stereotype.Service;

import java.util.Locale;
import java.util.UUID;

@Service
public class AuthService {
    private final UserRepository users;
    private final PasswordEncoder passwordEncoder;
    private final JwtService jwtService;
    private final String bootstrapAdminEmail;

    public AuthService(UserRepository users, PasswordEncoder passwordEncoder,
                       JwtService jwtService,
                       @Value("${app.auth.bootstrap-admin-email:}") String bootstrapAdminEmail) {
        this.users = users;
        this.passwordEncoder = passwordEncoder;
        this.jwtService = jwtService;
        this.bootstrapAdminEmail = bootstrapAdminEmail;
    }

    public synchronized AuthResponse register(RegisterRequest request) {
        String email = request.email().trim().toLowerCase(Locale.ROOT);
        if (users.emailExists(email)) {
            throw new IllegalArgumentException("An account with this email already exists.");
        }

        // First account is ADMIN for a single-instance initial setup.
        // Later registrations are always OPERATOR; never accept role from the client.
        String role = users.countUsers() == 0 ? "ADMIN" : "OPERATOR";
        if (!bootstrapAdminEmail.isBlank()) {
            role = email.equalsIgnoreCase(bootstrapAdminEmail.trim()) ? "ADMIN" : "OPERATOR";
        }

        User user = new User(
                UUID.randomUUID().toString(),
                request.fullName().trim(),
                email,
                passwordEncoder.encode(request.password()),
                role,
                "ACTIVE"
        );
        users.insert(user);
        return createResponse(user);
    }

    public AuthResponse login(LoginRequest request) {
        User user = users.findByEmail(request.email().trim()).orElseThrow(
                () -> new BadCredentialsException("Invalid email or password."));
        if (!"ACTIVE".equalsIgnoreCase(user.status())
                || !passwordEncoder.matches(request.password(), user.passwordHash())) {
            throw new BadCredentialsException("Invalid email or password.");
        }
        return createResponse(user);
    }

    public AuthResponse.UserSummary getCurrentUser(String userId) {
        // Token subject is the immutable USER_ID. Resolve current role/status from DB.
        User user = users.findById(userId).orElseThrow(
                () -> new IllegalArgumentException("User account not found."));
        if (!"ACTIVE".equalsIgnoreCase(user.status())) {
            throw new IllegalStateException("User account is inactive.");
        }
        return new AuthResponse.UserSummary(user.userId(), user.fullName(), user.email(), user.role());
    }

    private AuthResponse createResponse(User user) {
        return new AuthResponse(
                jwtService.generateToken(user),
                "Bearer",
                jwtService.getExpirationMillis(),
                new AuthResponse.UserSummary(user.userId(), user.fullName(), user.email(), user.role())
        );
    }
}

package com.teja.data_quality_backend.auth.repository;

import com.teja.data_quality_backend.auth.model.User;
import org.springframework.dao.EmptyResultDataAccessException;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Repository;

import java.util.Optional;

@Repository
public class UserRepository {
    private final JdbcTemplate jdbc;

    public UserRepository(JdbcTemplate snowflakeJdbcTemplate) {
        this.jdbc = snowflakeJdbcTemplate;
    }

    public long countUsers() {
        Long count = jdbc.queryForObject("SELECT COUNT(*) FROM USERS", Long.class);
        return count == null ? 0 : count;
    }

    public boolean emailExists(String email) {
        Integer count = jdbc.queryForObject(
                "SELECT COUNT(*) FROM USERS WHERE LOWER(EMAIL) = LOWER(?)",
                Integer.class, email);
        return count != null && count > 0;
    }

    public Optional<User> findByEmail(String email) {
        try {
            User user = jdbc.queryForObject("""
                    SELECT USER_ID, FULL_NAME, EMAIL, PASSWORD_HASH, USER_ROLE, STATUS
                    FROM USERS WHERE LOWER(EMAIL) = LOWER(?)
                    """, (rs, rowNum) -> new User(
                    rs.getString("USER_ID"),
                    rs.getString("FULL_NAME"),
                    rs.getString("EMAIL"),
                    rs.getString("PASSWORD_HASH"),
                    rs.getString("USER_ROLE"),
                    rs.getString("STATUS")
            ), email);
            return Optional.ofNullable(user);
        } catch (EmptyResultDataAccessException ex) {
            return Optional.empty();
        }
    }


    public Optional<User> findById(String userId) {
        try {
            User user = jdbc.queryForObject("""
                    SELECT USER_ID, FULL_NAME, EMAIL, PASSWORD_HASH, USER_ROLE, STATUS
                    FROM USERS WHERE USER_ID = ?
                    """, (rs, rowNum) -> new User(
                    rs.getString("USER_ID"),
                    rs.getString("FULL_NAME"),
                    rs.getString("EMAIL"),
                    rs.getString("PASSWORD_HASH"),
                    rs.getString("USER_ROLE"),
                    rs.getString("STATUS")
            ), userId);
            return Optional.ofNullable(user);
        } catch (EmptyResultDataAccessException ex) {
            return Optional.empty();
        }
    }

    public void insert(User user) {
        jdbc.update("""
                INSERT INTO USERS (USER_ID, FULL_NAME, EMAIL, PASSWORD_HASH, USER_ROLE, STATUS, CREATED_AT)
                VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP())
                """,
                user.userId(), user.fullName(), user.email(), user.passwordHash(),
                user.role(), user.status());
    }
}

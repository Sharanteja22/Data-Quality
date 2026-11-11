
package com.teja.data_quality_backend.controller;

import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.LinkedHashMap;
import java.util.Map;

@RestController
@RequestMapping("/api/health")
public class SnowflakeHealthController {

    private final JdbcTemplate jdbcTemplate;

    public SnowflakeHealthController(
            JdbcTemplate snowflakeJdbcTemplate) {
        this.jdbcTemplate = snowflakeJdbcTemplate;
    }

    @GetMapping("/snowflake")
    public Map<String, Object> checkSnowflakeConnection() {

        String sql = """
            SELECT
                CURRENT_ACCOUNT() AS ACCOUNT,
                CURRENT_ORGANIZATION_NAME() AS ORGANIZATION,
                CURRENT_WAREHOUSE() AS WAREHOUSE,
                CURRENT_DATABASE() AS DATABASE,
                CURRENT_SCHEMA() AS SCHEMA,
                CURRENT_ROLE() AS ROLE
            """;

        Map<String, Object> result =
                jdbcTemplate.queryForMap(sql);

        Map<String, Object> response = new LinkedHashMap<>();

        response.put("status", "CONNECTED");
        response.put("message", "Spring Boot connected to Snowflake successfully");
        response.put("snowflake_details", result);

        return response;
    }
}

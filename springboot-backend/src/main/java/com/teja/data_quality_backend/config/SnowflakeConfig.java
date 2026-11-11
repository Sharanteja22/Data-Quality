
package com.teja.data_quality_backend.config;

import com.zaxxer.hikari.HikariDataSource;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.jdbc.core.JdbcTemplate;

import javax.sql.DataSource;

@Configuration
public class SnowflakeConfig {

    @Value("${snowflake.url}")
    private String url;

    @Value("${snowflake.username}")
    private String username;

    @Value("${snowflake.password}")
    private String password;

    @Value("${snowflake.warehouse}")
    private String warehouse;

    @Value("${snowflake.database}")
    private String database;

    @Value("${snowflake.schema}")
    private String schema;

    @Value("${snowflake.role}")
    private String role;

    @Bean
    public DataSource snowflakeDataSource() {

        HikariDataSource dataSource = new HikariDataSource();

        dataSource.setJdbcUrl(url);
        dataSource.setUsername(username);
        dataSource.setPassword(password);
        dataSource.setDriverClassName(
                "net.snowflake.client.jdbc.SnowflakeDriver"
        );

        dataSource.setMaximumPoolSize(5);
        dataSource.setMinimumIdle(1);
        dataSource.setConnectionTimeout(30000);

        dataSource.addDataSourceProperty(
                "warehouse", warehouse
        );
        dataSource.addDataSourceProperty(
                "database", database
        );
        dataSource.addDataSourceProperty(
                "schema", schema
        );
        dataSource.addDataSourceProperty(
                "role", role
        );

        return dataSource;
    }

    @Bean
    public JdbcTemplate snowflakeJdbcTemplate(
            DataSource snowflakeDataSource) {

        return new JdbcTemplate(snowflakeDataSource);
    }
}


package com.teja.data_quality_backend;

import javax.sql.DataSource;

import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.bean.override.mockito.MockitoBean;

@SpringBootTest(properties = {
        "snowflake.url=jdbc:snowflake://test-account.snowflakecomputing.com",
        "snowflake.username=test-user",
        "snowflake.password=test-password",
        "snowflake.warehouse=TEST_WH",
        "snowflake.database=TEST_DB",
        "snowflake.schema=TEST_SCHEMA",
        "snowflake.role=TEST_ROLE"
})
class DataQualityBackendApplicationTests {

    @MockitoBean(name = "snowflakeDataSource")
    DataSource snowflakeDataSource;

    @Test
    void contextLoads() {
    }
}

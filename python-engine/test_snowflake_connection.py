
from app.storage.snowflake_connection import get_snowflake_connection


def test_snowflake_connection():
    connection = None

    try:
        connection = get_snowflake_connection()

        cursor = connection.cursor()

        try:
            cursor.execute("""
                SELECT
                    CURRENT_WAREHOUSE(),
                    CURRENT_DATABASE(),
                    CURRENT_SCHEMA(),
                    CURRENT_USER()
            """)

            result = cursor.fetchone()

            print("\nSnowflake connection successful!")
            print("Warehouse:", result[0])
            print("Database:", result[1])
            print("Schema:", result[2])
            print("User:", result[3])

        finally:
            cursor.close()

    finally:
        if connection:
            connection.close()


if __name__ == "__main__":
    test_snowflake_connection()

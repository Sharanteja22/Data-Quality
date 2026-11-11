
import os
from pathlib import Path

import snowflake.connector
from dotenv import load_dotenv


# Locate the project-root .env file.
PROJECT_ROOT = Path(__file__).resolve().parents[3]
ENV_FILE = PROJECT_ROOT / ".env"

load_dotenv(ENV_FILE)


def get_snowflake_connection():
    """Create and return a Snowflake database connection."""

    required_settings = [
        "SNOWFLAKE_ACCOUNT",
        "SNOWFLAKE_USER",
        "SNOWFLAKE_PASSWORD",
        "SNOWFLAKE_WAREHOUSE",
        "SNOWFLAKE_DATABASE",
        "SNOWFLAKE_SCHEMA",
    ]

    missing = [
        setting
        for setting in required_settings
        if not os.getenv(setting)
    ]

    if missing:
        raise ValueError(
            f"Missing Snowflake environment settings: {missing}"
        )

    connection_config = {
        "account": os.getenv("SNOWFLAKE_ACCOUNT"),
        "user": os.getenv("SNOWFLAKE_USER"),
        "password": os.getenv("SNOWFLAKE_PASSWORD"),
        "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE"),
        "database": os.getenv("SNOWFLAKE_DATABASE"),
        "schema": os.getenv("SNOWFLAKE_SCHEMA"),
    }

    role = os.getenv("SNOWFLAKE_ROLE")
    if role:
        connection_config["role"] = role

    return snowflake.connector.connect(**connection_config)


import pandas as pd

from app.storage.snowflake_connection import get_snowflake_connection


def fetch_batch_records(run_id: str) -> pd.DataFrame:
    """
    Fetch transaction records for a particular batch run
    from Snowflake.
    """

    if not run_id or not run_id.strip():
        raise ValueError("run_id is required.")

    connection = get_snowflake_connection()

    try:
        query = """
            SELECT
                RECORD_ID AS record_id,
                RUN_ID AS run_id,
                SOURCE_ROW_NUMBER AS source_row_number,
                TRANSACTION_ID AS transaction_id,
                CUSTOMER_ID AS customer_id,
                ACCOUNT_ID AS account_id,
                TRANSACTION_DATE AS transaction_date,
                AMOUNT AS amount,
                CURRENCY AS currency,
                COUNTRY AS country,
                TRANSACTION_TYPE AS transaction_type,
                STATUS AS status,
                CREATED_AT AS created_at
            FROM BATCH_RECORDS
            WHERE RUN_ID = %s
            ORDER BY SOURCE_ROW_NUMBER
        """

        cursor = connection.cursor()

        try:
            cursor.execute(query, (run_id,))
            records = cursor.fetch_pandas_all()
            if records is not None:
                records.columns = records.columns.str.lower()
        finally:
            cursor.close()

        if records is None or records.empty:
            raise ValueError(
                f"No transaction records found for run: {run_id}"
            )

        return records

    finally:
        connection.close()

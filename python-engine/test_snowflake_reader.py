
from app.storage.snowflake_reader import fetch_batch_records


def test_fetch_batch_records():

    run_id = "BATCH001_RUN001"

    records = fetch_batch_records(run_id)

    print("\nSnowflake records fetched successfully!")
    print("Run ID:", run_id)
    print("Total records:", len(records))
    print("Columns:", records.columns.tolist())

    print("\nFirst 5 records:")
    print(records.head())

    print("\nRecord ID null count:", records["record_id"].isna().sum())
    print("Unique Record IDs:", records["record_id"].nunique())

    assert len(records) == 500
    assert records["record_id"].notna().all()
    assert records["record_id"].nunique() == 500


if __name__ == "__main__":
    test_fetch_batch_records()

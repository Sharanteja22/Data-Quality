
from pathlib import Path
from tempfile import TemporaryDirectory

from app.ingestion.csv_loader import load_csv


def expect_ingestion_rejection(
    test_name: str,
    file_path: Path,
    run_id: str,
):
    print("\n" + "=" * 60)
    print(test_name)
    print("=" * 60)

    try:
        records, metadata = load_csv(
            file_path=file_path,
            run_id=run_id,
        )

        # If the loader returns normally, it must not report success.
        if metadata.get("ingestion_status") == "SUCCESS":
            raise AssertionError(
                f"{test_name}: invalid file was accepted!"
            )

        print("Result: REJECTED")
        print("Ingestion status:", metadata.get("ingestion_status"))

    except AssertionError:
        raise

    except Exception as exc:
        print("Result: REJECTED")
        print("Exception type:", type(exc).__name__)
        print("Error message:", str(exc))


def main():
    with TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Test 1: Missing required CSV columns.
        missing_schema_file = temp_path / "missing_columns.csv"
        missing_schema_file.write_text(
            "transaction_id,customer_id,account_id\n"
            "TX001,CUST001,ACC001\n",
            encoding="utf-8",
        )

        # Test 2: Empty CSV file.
        empty_file = temp_path / "empty.csv"
        empty_file.write_text("", encoding="utf-8")

        # Test 3: Invalid UTF-8 content.
        unreadable_file = temp_path / "unreadable.csv"
        unreadable_file.write_bytes(b"\xff\xfe\xfa\xff\x80")

        expect_ingestion_rejection(
            "TEST 1 - Missing required columns",
            missing_schema_file,
            "FAIL_TEST_001",
        )

        expect_ingestion_rejection(
            "TEST 2 - Empty CSV file",
            empty_file,
            "FAIL_TEST_002",
        )

        expect_ingestion_rejection(
            "TEST 3 - Unreadable file",
            unreadable_file,
            "FAIL_TEST_003",
        )

    print("\n" + "=" * 60)
    print("INGESTION FAILURE TESTS COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    main()

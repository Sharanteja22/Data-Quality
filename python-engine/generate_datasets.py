import csv
import random
from datetime import datetime, timedelta
from pathlib import Path


SEED = 37037
RECORD_COUNT = 500

random_generator = random.Random(SEED)

PROJECT_ROOT = Path(__file__).resolve().parents[1]

GENERATED_DIR = PROJECT_ROOT / "data" / "generated"
CORRECTED_DIR = PROJECT_ROOT / "data" / "corrected"

GENERATED_DIR.mkdir(parents=True, exist_ok=True)
CORRECTED_DIR.mkdir(parents=True, exist_ok=True)

COLUMNS = [
    "transaction_id",
    "customer_id",
    "account_id",
    "transaction_date",
    "amount",
    "currency",
    "country",
    "transaction_type",
    "status",
    "created_at",
]

COUNTRY_CURRENCY = {
    "India": "INR",
    "USA": "USD",
    "UK": "EUR",
}

COUNTRIES = list(COUNTRY_CURRENCY.keys())
TRANSACTION_TYPES = ["CREDIT", "DEBIT"]
STATUSES = ["PENDING", "COMPLETED", "FAILED"]

# CLEAN BASE DATA

def generate_clean_records():

    records = []

    base_time = datetime(2026, 11, 9, 8, 0, 0)

    for index in range(RECORD_COUNT):

        transaction_date = base_time + timedelta(
            minutes=random_generator.randint(0, 480)
        )

        created_at = transaction_date + timedelta(
            minutes=random_generator.randint(1, 10)
        )

        country = random_generator.choice(COUNTRIES)

        record = {
            "transaction_id": f"TX{100001 + index}",
            "customer_id": f"C{101 + index}",
            "account_id": f"A{9001 + index}",
            "transaction_date": transaction_date.strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            "amount": f"{random_generator.uniform(100, 50000):.2f}",
            "currency": COUNTRY_CURRENCY[country],
            "country": country,
            "transaction_type": random_generator.choice(
                TRANSACTION_TYPES
            ),
            "status": random_generator.choice(STATUSES),
            "created_at": created_at.strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
        }

        records.append(record)

    return records



def write_csv(file_path, records):

    with file_path.open(
        mode="w",
        newline="",
        encoding="utf-8"
    ) as csv_file:

        writer = csv.DictWriter(
            csv_file,
            fieldnames=COLUMNS
        )

        writer.writeheader()
        writer.writerows(records)

    print(f"Created: {file_path}")
    print(f"Records: {len(records)}")




def generate_scenario_a(clean_records):
    
    records = [record.copy() for record in clean_records]
    records[499]["transaction_id"] = records[0]["transaction_id"]
    for index in range(10, 15):
        records[index]["transaction_type"] = "TRANSFERX"
    for index in range(20, 25):
        # records[index]["currency"] = "USD"
        country = records[index]["country"]
        records[index]["currency"] = (
            "USD" if country != "USA" else "INR"
        )
    return records



def generate_scenario_b(clean_records):

    records = [record.copy() for record in clean_records]
    for index in range(65):
        records[index]["transaction_type"] = "TRANSFERX"

    for index in range(65, 130):
        # records[index]["currency"] = "USD"
        country = records[index]["country"]
        records[index]["currency"] = (
            "USD" if country != "USA" else "INR"
        )

    return records

def generate_scenario_c(scenario_a_records):

    records = [record.copy() for record in scenario_a_records]
    records[499]["transaction_id"] = "TX100500"
    for index in range(10, 15):
        records[index]["transaction_type"] = "CREDIT"
    for index in range(20, 25):
        country = records[index]["country"]
        records[index]["currency"] = COUNTRY_CURRENCY[country]

    return records


def main():

    print("=" * 60)
    print("CAP-37 DATASET GENERATION")
    print("=" * 60)

    print(f"Random seed: {SEED}")
    print(f"Expected records per dataset: {RECORD_COUNT}")
    clean_records = generate_clean_records()
    scenario_a = generate_scenario_a(clean_records)
    scenario_b = generate_scenario_b(clean_records)
    scenario_c = generate_scenario_c(scenario_a)
    write_csv(
        GENERATED_DIR / "scenario_a_high_score_critical_block.csv",
        scenario_a
    )
    write_csv(
        GENERATED_DIR / "scenario_b_warning_only.csv",
        scenario_b
    )
    write_csv(
        CORRECTED_DIR / "scenario_c_corrected_replay.csv",
        scenario_c
    )

    print("\n" + "=" * 60)
    print("DATASET GENERATION COMPLETED")
    print("=" * 60)

    print("Scenario A: Critical duplicate + warnings")
    print("Scenario B: Nonblocking warnings only")
    print("Scenario C: Corrected Scenario A")

    print("\nTotal records generated:", RECORD_COUNT * 3)


if __name__ == "__main__":
    main()

import copy
import json
import sys
from pathlib import Path

import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PYTHON_ENGINE = PROJECT_ROOT / "python-engine"

sys.path.insert(0, str(PYTHON_ENGINE))

from app.ingestion.csv_loader import load_csv
from app.rules.batch_rules import evaluate_batch_rules
from app.rules.record_rules import evaluate_record_rules
from app.rules.rule_engine import evaluate_all_rules
from app.scoring.score_calculator import calculate_data_quality_score
from app.blocking.decision_engine import make_batch_decision
from app.exceptions.exception_manager import generate_exceptions
from app.pipeline import process_batch


CONFIG_PATH = PYTHON_ENGINE / "config" / "rules.json"

with CONFIG_PATH.open("r", encoding="utf-8") as file:
    CONFIG = json.load(file)


SCENARIOS = [
    {
        "name": "critical_block",
        "file": PROJECT_ROOT / "data/generated/scenario_a_high_score_critical_block.csv",
        "expected_status": "BLOCK",
        "publication": False,
        "failures": 11,
        "exceptions": 11,
    },
    {
        "name": "warning_only",
        "file": PROJECT_ROOT / "data/generated/scenario_b_warning_only.csv",
        "expected_status": "WARN",
        "publication": True,
        "failures": 130,
        "exceptions": 130,
    },
    {
        "name": "corrected_replay",
        "file": PROJECT_ROOT / "data/corrected/scenario_c_corrected_replay.csv",
        "expected_status": "PASS",
        "publication": True,
        "failures": 0,
        "exceptions": 0,
    },
]


def load_scenario(scenario, run_id="PYTEST_RUN"):
    records, metadata = load_csv(
        file_path=scenario["file"],
        run_id=run_id,
    )
    assert metadata["ingestion_status"] == "SUCCESS"
    assert not records.empty
    return records


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s["name"])
def test_all_nine_rules_evaluate_expected_failure_count(scenario):
    records = load_scenario(scenario)

    results = evaluate_all_rules(
        records=records,
        rules_config=CONFIG,
        batch_created_at="2026-11-10T09:00:00",
        batch_received_at="2026-11-10T09:30:00",
    )

    assert len(results) == 9
    assert sum(item["failed_count"] for item in results) == scenario["failures"]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s["name"])
def test_record_rules_return_expected_failures(scenario):
    records = load_scenario(scenario)

    results = evaluate_record_rules(records, CONFIG)

    assert len(results) == 8
    assert sum(item["failed_count"] for item in results) == scenario["failures"]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s["name"])
def test_batch_decision_and_publication_gate(scenario):
    records = load_scenario(scenario)

    rule_results = evaluate_all_rules(
        records=records,
        rules_config=CONFIG,
        batch_created_at="2026-11-10T09:00:00",
        batch_received_at="2026-11-10T09:30:00",
    )

    score_result = calculate_data_quality_score(rule_results, CONFIG)

    decision = make_batch_decision(
        rule_results=rule_results,
        score_result=score_result,
        rules_config=CONFIG,
    )

    assert decision["final_status"] == scenario["expected_status"]
    assert decision["publication_allowed"] is scenario["publication"]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s["name"])
def test_exception_generation(scenario):
    records = load_scenario(scenario)

    rule_results = evaluate_all_rules(
        records=records,
        rules_config=CONFIG,
        batch_created_at="2026-11-10T09:00:00",
        batch_received_at="2026-11-10T09:30:00",
    )

    exceptions = generate_exceptions(
        records=records,
        rule_results=rule_results,
    )

    exception_ids = [item["exception_id"] for item in exceptions]

    assert len(exceptions) == scenario["exceptions"]
    assert len(exception_ids) == len(set(exception_ids))


@pytest.mark.parametrize(
    ("received", "expected_failures"),
    [
        ("2026-11-10T09:30:00", 0),
        ("2026-11-10T10:00:00", 0),
        ("2026-11-10T10:30:00", 1),
    ],
)
def test_dq009_sla_boundary(received, expected_failures):
    results = evaluate_batch_rules(
        batch_created_at="2026-11-10T09:00:00",
        batch_received_at=received,
        rules_config=CONFIG,
    )

    assert len(results) == 1
    assert results[0]["failed_count"] == expected_failures


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s["name"])
def test_complete_pipeline(scenario):
    records = load_scenario(scenario)

    result = process_batch(
        records=records,
        run_id="PYTEST_PIPELINE",
        rules_config=CONFIG,
        batch_created_at="2026-11-10T09:00:00",
        batch_received_at="2026-11-10T09:30:00",
    )

    assert result["pipeline_status"] != "FAILED"
    assert result["decision_result"]["final_status"] == scenario["expected_status"]
    assert result["publication_allowed"] is scenario["publication"]
    assert result["exception_count"] == scenario["exceptions"]


@pytest.mark.parametrize(
    "invalid_content",
    [
        "transaction_id,customer_id,account_id\nTX001,CUST001,ACC001\n",
        "",
        None,
    ],
    ids=["missing-columns", "empty-file", "invalid-utf8"],
)
def test_invalid_csv_ingestion_is_rejected(tmp_path, invalid_content):
    file_path = tmp_path / "invalid.csv"

    if invalid_content is None:
        file_path.write_bytes(b"\xff\xfe\xfa\xff\x80")
    else:
        file_path.write_text(invalid_content, encoding="utf-8")

    try:
        _, metadata = load_csv(file_path=file_path, run_id="INVALID_TEST")
        assert metadata.get("ingestion_status") != "SUCCESS"
    except Exception:
        pass


@pytest.mark.parametrize("failure_type", [
    "empty_records",
    "empty_config",
    "missing_columns",
    "missing_dimension",
])
def test_pipeline_failure_never_allows_publication(failure_type):
    sample = SCENARIOS[2]
    records = load_scenario(sample)

    config = copy.deepcopy(CONFIG)

    if failure_type == "empty_records":
        records = pd.DataFrame()
    elif failure_type == "empty_config":
        config = {}
    elif failure_type == "missing_columns":
        records = pd.DataFrame({
            "transaction_id": ["TX001"],
            "customer_id": ["CUST001"],
        })
    elif failure_type == "missing_dimension":
        for rule in config["rules"]:
            if rule["dimension"].upper() == "TIMELINESS":
                rule["is_active"] = False

    result = process_batch(
        records=records,
        run_id=f"PYTEST_FAILURE_{failure_type}",
        rules_config=config,
        batch_created_at="2026-11-10T09:00:00",
        batch_received_at="2026-11-10T09:30:00",
    )

    assert result["pipeline_status"] == "FAILED"
    assert result["publication_allowed"] is False

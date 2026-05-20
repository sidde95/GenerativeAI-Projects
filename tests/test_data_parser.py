from __future__ import annotations

import io
import json

import pandas as pd
import pytest

from ui.data_parser import (
    build_sample_csv_template,
    build_sample_excel_template,
    list_excel_sheets,
    normalize_budgets,
    normalize_json_payload,
    normalize_portfolio,
    normalize_transactions,
    parse_uploaded_file,
    parse_uploaded_file_with_details,
    suggest_mapping,
    to_backend_workflow_payload,
)


class UploadedStub:
    def __init__(self, name: str, payload: bytes):
        self.name = name
        self._payload = payload

    def getvalue(self) -> bytes:
        return self._payload



def test_suggest_mapping_from_aliases():
    columns = ["txn_date", "merchant", "txn_amount", "expense_category"]
    mapping = suggest_mapping(columns, "transactions")

    assert mapping["date"] == "txn_date"
    assert mapping["description"] == "merchant"
    assert mapping["amount"] == "txn_amount"
    assert mapping["category"] == "expense_category"



def test_normalize_transactions_and_bad_rows():
    frame = pd.DataFrame(
        [
            {"date": "2026-05-01", "merchant": "Store", "value": -12.5, "type": "Food"},
            {"date": "bad", "merchant": "Store", "value": "oops", "type": "Food"},
        ]
    )
    mapping = {"date": "date", "description": "merchant", "amount": "value", "category": "type"}

    normalized = normalize_transactions(frame, mapping)

    assert len(normalized) == 1
    assert normalized[0]["description"] == "Store"
    assert normalized[0]["amount"] == -12.5



def test_normalize_budgets_and_portfolio():
    budgets = pd.DataFrame([{"category": "Rent", "budget": 1200}])
    portfolio = pd.DataFrame([{"ticker": "AAPL", "units": 2, "buy_price": 150}])

    normalized_budgets = normalize_budgets(budgets, {"category": "category", "budget_amount": "budget"})
    normalized_portfolio = normalize_portfolio(portfolio, {"symbol": "ticker", "quantity": "units", "avg_price": "buy_price"})

    assert normalized_budgets == [{"category": "Rent", "budget_amount": 1200.0}]
    assert normalized_portfolio == [{"symbol": "AAPL", "quantity": 2.0, "avg_price": 150.0}]



def test_parse_uploaded_csv_with_mapping():
    csv_payload = "txn_date,merchant,value,type\n2026-05-01,Coffee,-4.2,Food\n".encode("utf-8")
    uploaded = UploadedStub("transactions.csv", csv_payload)

    outcome = parse_uploaded_file_with_details(
        uploaded,
        {
            "file_type": "csv",
            "csv_data_type": "transactions",
            "mappings": {
                "transactions": {
                    "date": "txn_date",
                    "description": "merchant",
                    "amount": "value",
                    "category": "type",
                }
            },
        },
    )

    assert len(outcome.data["transactions"]) == 1
    assert outcome.data["transactions"][0]["description"] == "Coffee"
    assert outcome.row_errors["transactions"] == []



def test_parse_uploaded_empty_csv_has_no_valid_rows():
    uploaded = UploadedStub("transactions.csv", "date,merchant\n".encode("utf-8"))

    with pytest.raises(ValueError):
        parse_uploaded_file(
            uploaded,
            {
                "file_type": "csv",
                "csv_data_type": "transactions",
                "mappings": {"transactions": {"date": "date", "description": "merchant"}},
            },
        )



def test_parse_uploaded_json_and_backend_transform():
    payload = {
        "transactions": [{"date": "2026-05-01", "merchant": "A", "amount": -10, "category": "Food"}],
        "budgets": {"Food": 200},
        "portfolio": {"holdings": [{"symbol": "MSFT", "shares": 2, "cost_basis": 100}]},
    }
    uploaded = UploadedStub("input.json", json.dumps(payload).encode("utf-8"))

    normalized = parse_uploaded_file(uploaded, {"file_type": "json"})
    backend = to_backend_workflow_payload(normalized)

    assert normalized["budgets"][0]["category"] == "Food"
    assert backend["budgets"]["Food"] == 200.0
    assert backend["portfolio"]["holdings"][0]["shares"] == 2.0



def test_excel_template_and_sheet_listing():
    excel_payload = build_sample_excel_template()
    uploaded = UploadedStub("sample.xlsx", excel_payload)

    sheets = list_excel_sheets(uploaded)

    assert set(sheets) == {"transactions", "budgets", "portfolio"}



def test_csv_template_generation():
    csv_template = build_sample_csv_template("transactions").decode("utf-8")
    assert "date" in csv_template
    assert "description" in csv_template

from __future__ import annotations

from copy import deepcopy

import pytest

from graph.state import create_initial_state


@pytest.fixture
def sample_transactions() -> dict:
    return {
        "transactions": [
            {"date": "2026-05-01", "amount": -45.32, "merchant": "Whole Foods", "category": "Groceries"},
            {"date": "2026-05-02", "amount": -1200.0, "merchant": "Landlord", "category": "Housing"},
            {"date": "2026-05-03", "amount": -89.99, "merchant": "Amazon", "category": "Shopping"},
            {"date": "2026-05-04", "amount": -2500.0, "merchant": "Unknown Wire", "category": "Unknown"},
        ],
        "budgets": {
            "Groceries": 500,
            "Housing": 1500,
            "Shopping": 300,
            "Entertainment": 200,
        },
        "portfolio": {
            "holdings": [
                {"symbol": "AAPL", "shares": 10, "cost_basis": 150.0, "current_price": 175.0},
                {"symbol": "MSFT", "shares": 5, "cost_basis": 300.0, "current_price": 350.0},
            ]
        },
    }


@pytest.fixture
def empty_transactions() -> dict:
    return {"transactions": [], "budgets": {}, "portfolio": {"holdings": []}}


@pytest.fixture
def invalid_raw_data() -> dict:
    return {"transactions": [1, 2, 3], "budgets": [], "portfolio": "invalid"}


@pytest.fixture
def sample_state(sample_transactions: dict) -> dict:
    state = create_initial_state(deepcopy(sample_transactions))
    state["run_id"] = "fc-test-123"
    state["started_at"] = "2026-05-20T00:00:00"
    return state


@pytest.fixture
def empty_state(empty_transactions: dict) -> dict:
    state = create_initial_state(deepcopy(empty_transactions))
    state["run_id"] = "fc-empty-123"
    return state

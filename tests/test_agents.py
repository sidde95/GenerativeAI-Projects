from __future__ import annotations

from copy import deepcopy
import sys
import types

import pytest

import agents
from agents.budget_monitoring.agent import run_budget_agent
from agents.budget_monitoring.calculators import compute_budget_vs_actual
from agents.ingestion.agent import run_ingestion_agent
from agents.ingestion.validators import normalize_input, validate_input_schema
from agents.orchestrator.agent import run_orchestrator_finalize, run_orchestrator_init
from agents.portfolio_insight.agent import run_portfolio_agent
from agents.portfolio_insight.portfolio_analysis import summarize_holdings_performance
from agents.reporting.agent import run_reporting_agent
from agents.reporting.report_generator import build_final_report
from agents.transaction_intelligence.agent import run_transaction_agent
from agents.transaction_intelligence.analyzers import categorize_transactions, detect_simple_anomalies
from utils.config import Config


def test_orchestrator_init_and_finalize(sample_state):
    init_result = run_orchestrator_init(sample_state)
    assert init_result["status"] == "RUNNING"
    assert init_result["started_at"]

    final_success = run_orchestrator_finalize({"errors": []})
    final_failure = run_orchestrator_finalize({"errors": ["boom"]})
    assert final_success["status"] == "SUCCESS"
    assert final_failure["status"] == "FAILED"
    assert final_success["completed_at"]


def test_agent_type_validation_errors():
    with pytest.raises(TypeError):
        run_orchestrator_init(None)
    with pytest.raises(TypeError):
        run_orchestrator_finalize(None)
    with pytest.raises(TypeError):
        run_ingestion_agent(None)
    with pytest.raises(TypeError):
        run_transaction_agent(None)
    with pytest.raises(TypeError):
        run_budget_agent(None)
    with pytest.raises(TypeError):
        run_portfolio_agent(None)
    with pytest.raises(TypeError):
        run_reporting_agent(None)


def test_config_validation_and_create_agent(monkeypatch):
    monkeypatch.setattr(Config, "GROQ_API_KEY", None)
    assert Config.validate(required=False) is False
    with pytest.raises(ValueError):
        Config.validate(required=True)

    fake_langchain_groq = types.ModuleType("langchain_groq")
    fake_prompts = types.ModuleType("langchain_core.prompts")

    class FakeLLM:
        def __init__(self, api_key, model, temperature):
            self.api_key = api_key
            self.model = model
            self.temperature = temperature
            self.bound_tools = None

        def bind_tools(self, tools):
            self.bound_tools = tools
            return self

    class FakePrompt:
        @classmethod
        def from_messages(cls, messages):
            instance = cls()
            instance.messages = messages
            return instance

        def __or__(self, other):
            return {"prompt": self.messages, "llm": other}

    fake_langchain_groq.ChatGroq = FakeLLM
    fake_prompts.ChatPromptTemplate = FakePrompt
    fake_langchain_core = types.ModuleType("langchain_core")
    fake_langchain_core.prompts = fake_prompts

    monkeypatch.setitem(sys.modules, "langchain_groq", fake_langchain_groq)
    monkeypatch.setitem(sys.modules, "langchain_core", fake_langchain_core)
    monkeypatch.setitem(sys.modules, "langchain_core.prompts", fake_prompts)
    monkeypatch.setattr(Config, "GROQ_API_KEY", "test-key")
    monkeypatch.setattr(Config, "GROQ_MODEL", "test-model")

    agent = agents.create_agent("demo", "system prompt", tools=[lambda value: value], temperature=0.1)
    assert agent["llm"].api_key == "test-key"
    assert agent["llm"].bound_tools is not None


def test_ingestion_agent_happy_path(sample_state, sample_transactions):
    original = deepcopy(sample_state)
    result = run_ingestion_agent(sample_state)

    assert result["ingestion_result"]["status"] == "SUCCESS"
    assert result["ingestion_result"]["normalized_data"] == sample_transactions
    assert sample_state == original


def test_ingestion_agent_validation_failure(invalid_raw_data):
    result = run_ingestion_agent({"raw_data": invalid_raw_data})

    assert result["ingestion_result"]["status"] == "FAILED"
    assert result["errors"]


def test_ingestion_agent_missing_keys():
    result = run_ingestion_agent({"raw_data": {"transactions": []}})

    assert result["ingestion_result"]["status"] == "FAILED"
    assert "missing keys" in result["ingestion_result"]["error"]


def test_ingestion_schema_helpers(sample_transactions, invalid_raw_data):
    assert validate_input_schema(sample_transactions)["is_valid"] is True
    assert validate_input_schema(invalid_raw_data)["is_valid"] is False
    assert validate_input_schema(None)["is_valid"] is False
    normalized = normalize_input(sample_transactions)
    assert normalized["transactions"]
    assert normalized["budgets"]
    assert normalized["portfolio"]


def test_transaction_agent_happy_path(sample_state):
    sample_state["ingestion_result"] = {"normalized_data": deepcopy(sample_state["raw_data"])}
    result = run_transaction_agent(sample_state)

    insights = result["transaction_insights"]
    assert insights["status"] == "SUCCESS"
    assert insights["transaction_count"] == 4
    assert len(insights["category_breakdown"]) == 4
    assert len(insights["anomalies"]) == 2


def test_transaction_agent_empty_input(empty_state):
    empty_state["ingestion_result"] = {"normalized_data": {"transactions": []}}
    result = run_transaction_agent(empty_state)

    assert result["transaction_insights"]["status"] == "EMPTY"
    assert result["transaction_insights"]["category_breakdown"] == {}
    assert result["transaction_insights"]["anomalies"] == []


def test_transaction_analyzers(sample_transactions):
    transactions = sample_transactions["transactions"]
    assert categorize_transactions(transactions)["Housing"] == -1200.0
    assert detect_simple_anomalies(transactions) == [transactions[1], transactions[3]]


def test_transaction_analyzers_ignore_bad_records():
    bad_transactions = [
        {"amount": "bad", "category": "Food"},
        "not-a-dict",
        {"amount": -999999, "category": None},
    ]

    assert categorize_transactions(bad_transactions) == {"Unknown": -999999.0}
    assert detect_simple_anomalies(bad_transactions) == [{"amount": -999999, "category": None}]


def test_budget_agent_happy_path(sample_state):
    sample_state["ingestion_result"] = {"normalized_data": deepcopy(sample_state["raw_data"])}
    result = run_budget_agent(sample_state)

    analysis = result["budget_analysis"]
    assert analysis["status"] == "SUCCESS"
    assert analysis["budget_count"] == 4
    assert analysis["budget_vs_actual"]["Groceries"]["overrun"] is False
    assert analysis["budget_vs_actual"]["Housing"]["overrun"] is False


def test_budget_agent_empty_budget(empty_state):
    empty_state["ingestion_result"] = {"normalized_data": {"transactions": [], "budgets": {}}}
    result = run_budget_agent(empty_state)

    assert result["budget_analysis"]["status"] == "EMPTY"
    assert result["budget_analysis"]["budget_vs_actual"] == {}


def test_budget_calculator(sample_transactions):
    result = compute_budget_vs_actual(sample_transactions["transactions"], sample_transactions["budgets"])
    assert result["Housing"]["actual"] == 1200.0
    assert result["Shopping"]["utilization_percent"] == pytest.approx(30.0, rel=1e-3)


def test_budget_calculator_skips_invalid_entries():
    result = compute_budget_vs_actual(
        [
            {"category": "Groceries", "amount": "bad"},
            "not-a-dict",
            {"category": "Groceries", "amount": -0.0},
        ],
        {"Groceries": 0, "Ignore": "bad"},
    )

    assert result["Groceries"]["actual"] == 0.0
    assert result["Groceries"]["utilization_percent"] == 0


def test_portfolio_agent_happy_path(sample_state):
    sample_state["ingestion_result"] = {"normalized_data": deepcopy(sample_state["raw_data"])}
    result = run_portfolio_agent(sample_state)

    insights = result["portfolio_insights"]
    assert insights["status"] == "SUCCESS"
    assert insights["holdings_count"] == 2
    assert insights["summary"]["holdings_count"] == 2
    assert insights["summary"]["total_value"] == 3500.0


def test_portfolio_agent_empty_portfolio(empty_state):
    empty_state["ingestion_result"] = {"normalized_data": {"portfolio": {"holdings": []}}}
    result = run_portfolio_agent(empty_state)

    assert result["portfolio_insights"]["status"] == "EMPTY"
    assert result["portfolio_insights"]["summary"]["holdings_summary"] == []


def test_portfolio_analysis(sample_transactions):
    summary = summarize_holdings_performance(sample_transactions["portfolio"]["holdings"])
    assert summary["holdings_count"] == 2
    assert summary["holdings_summary"][0]["symbol"] == "AAPL"


def test_portfolio_analysis_skips_bad_holdings():
    summary = summarize_holdings_performance([
        {"symbol": None, "shares": "bad", "cost_basis": 10, "current_price": 20},
        "not-a-holding",
    ])

    assert summary["total_value"] == 0.0
    assert summary["holdings_summary"] == []


def test_reporting_agent_and_builder(sample_state):
    sample_state["transaction_insights"] = {"status": "SUCCESS", "category_breakdown": {"Groceries": 1}, "anomalies": []}
    sample_state["budget_analysis"] = {"status": "SUCCESS", "budget_vs_actual": {"Groceries": {"budget": 10, "actual": 5}}}
    sample_state["portfolio_insights"] = {"status": "SUCCESS", "summary": {"total_value": 1}}

    report = build_final_report(
        sample_state["transaction_insights"],
        sample_state["budget_analysis"],
        sample_state["portfolio_insights"],
    )
    result = run_reporting_agent(sample_state)

    assert report["sections"] == ["transaction_insights", "budget_analysis", "portfolio_insights", "recommendations"]
    assert result["status"] == "SUCCESS"
    assert result["final_report"]["transaction_insights"]["status"] == "SUCCESS"

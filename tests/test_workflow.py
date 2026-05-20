from __future__ import annotations

from types import SimpleNamespace

from graph.workflow import build_workflow


def test_workflow_success_path(sample_state):
    final_state = build_workflow().invoke(sample_state)

    assert final_state["run_id"] == "fc-test-123"
    assert final_state["status"] == "SUCCESS"
    assert final_state["final_report"]["sections"] == ["transaction_insights", "budget_analysis", "portfolio_insights", "recommendations"]
    assert final_state["transaction_insights"]["transaction_count"] == 4
    assert final_state["budget_analysis"]["budget_count"] == 4
    assert final_state["portfolio_insights"]["holdings_count"] == 2


def test_workflow_ingestion_failure_short_circuits(sample_state, monkeypatch):
    calls = []

    def fake_ingestion(state):
        calls.append("ingestion")
        return {
            "ingestion_result": {"status": "FAILED", "error": "invalid"},
            "errors": ["invalid"],
        }

    def should_not_run(state):
        calls.append("downstream")
        raise AssertionError("Downstream node should not run after ingestion failure")

    monkeypatch.setattr("graph.workflow.run_ingestion_agent", fake_ingestion)
    monkeypatch.setattr("graph.workflow.run_transaction_agent", should_not_run)
    monkeypatch.setattr("graph.workflow.run_budget_agent", should_not_run)
    monkeypatch.setattr("graph.workflow.run_portfolio_agent", should_not_run)
    monkeypatch.setattr("graph.workflow.run_reporting_agent", should_not_run)

    final_state = build_workflow().invoke(sample_state)

    assert final_state["status"] == "FAILED"
    assert final_state["errors"] == ["invalid"]
    assert calls == ["ingestion"]


def test_workflow_regression_non_empty_outputs(sample_state):
    final_state = build_workflow().invoke(sample_state)

    assert len(final_state["transaction_insights"]["category_breakdown"]) > 0
    assert len(final_state["transaction_insights"]["anomalies"]) > 0
    assert final_state["portfolio_insights"]["summary"]["holdings_count"] > 0

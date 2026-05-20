from typing import Any, Dict

from agents.reporting.report_generator import build_final_report
from utils.logger import logger

def run_reporting_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(state, dict):
        raise TypeError("reporting agent expects a state dictionary")

    logger.log_agent_start("reporting")

    tx = state.get("transaction_insights", {})
    budget = state.get("budget_analysis", {})
    portfolio = state.get("portfolio_insights", {})

    final_report = build_final_report(tx, budget, portfolio)

    logger.log_agent_detail("reporting", "sections", "transaction,budget,portfolio,recommendations")
    logger.log_agent_success("reporting", 0.2)

    return {
        "final_report": final_report,
        "status": "SUCCESS",
    }
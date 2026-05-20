from typing import Any, Dict

from agents.budget_monitoring.calculators import compute_budget_vs_actual
from utils.logger import logger

def run_budget_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(state, dict):
        raise TypeError("budget agent expects a state dictionary")

    logger.log_agent_start("budget_monitoring")

    normalized = state.get("ingestion_result", {}).get("normalized_data", {})
    transactions = normalized.get("transactions", []) if isinstance(normalized, dict) else []
    budgets = normalized.get("budgets", {}) if isinstance(normalized, dict) else {}

    if not isinstance(transactions, list):
        transactions = []
    if not isinstance(budgets, dict):
        budgets = {}

    budget_result = compute_budget_vs_actual(transactions, budgets)

    logger.log_agent_detail("budget_monitoring", "categories", str(len(budget_result)))
    logger.log_agent_success("budget_monitoring", 0.2)

    return {
        "budget_analysis": {
            "status": "SUCCESS" if budgets else "EMPTY",
            "budget_vs_actual": budget_result,
            "budget_count": len(budgets),
        }
    }
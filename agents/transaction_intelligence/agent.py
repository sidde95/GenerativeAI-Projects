from typing import Any, Dict

from agents.transaction_intelligence.analyzers import categorize_transactions, detect_simple_anomalies
from utils.logger import logger

def run_transaction_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(state, dict):
        raise TypeError("transaction agent expects a state dictionary")

    logger.log_agent_start("transaction_intelligence")

    normalized = state.get("ingestion_result", {}).get("normalized_data", {})
    transactions = normalized.get("transactions", []) if isinstance(normalized, dict) else []

    if not isinstance(transactions, list):
        transactions = []

    category_breakdown = categorize_transactions(transactions)
    anomalies = detect_simple_anomalies(transactions)

    logger.log_agent_detail("transaction_intelligence", "categories", str(len(category_breakdown)))
    logger.log_agent_detail("transaction_intelligence", "anomalies", str(len(anomalies)))
    logger.log_agent_success("transaction_intelligence", 0.2)

    return {
        "transaction_insights": {
            "status": "SUCCESS" if transactions else "EMPTY",
            "category_breakdown": category_breakdown,
            "anomalies": anomalies,
            "transaction_count": len(transactions),
        }
    }
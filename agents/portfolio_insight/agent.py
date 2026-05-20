from typing import Any, Dict

from agents.portfolio_insight.portfolio_analysis import summarize_holdings_performance
from utils.logger import logger

def run_portfolio_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(state, dict):
        raise TypeError("portfolio agent expects a state dictionary")

    logger.log_agent_start("portfolio_insight")

    normalized = state.get("ingestion_result", {}).get("normalized_data", {})
    portfolio = normalized.get("portfolio", {}) if isinstance(normalized, dict) else {}
    holdings = portfolio.get("holdings", []) if isinstance(portfolio, dict) else []

    if not isinstance(holdings, list):
        holdings = []

    summary = summarize_holdings_performance(holdings)

    logger.log_agent_detail("portfolio_insight", "holdings", str(len(holdings)))
    logger.log_agent_success("portfolio_insight", 0.2)

    return {
        "portfolio_insights": {
            "status": "SUCCESS" if holdings else "EMPTY",
            "summary": summary,
            "holdings_count": len(holdings),
        }
    }
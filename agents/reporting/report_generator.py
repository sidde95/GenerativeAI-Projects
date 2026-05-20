from typing import Any, Dict

def build_final_report(tx: Dict[str, Any], budget: Dict[str, Any], portfolio: Dict[str, Any]) -> Dict[str, Any]:
    """Build final comprehensive report from agent outputs
    
    Args:
        tx: Transaction insights from transaction_intelligence agent
        budget: Budget analysis from budget_monitoring agent  
        portfolio: Portfolio insights from portfolio_insight agent
        
    Returns:
        Dictionary containing structured final report with all sections
    """
    transaction_section = tx if tx else {"status": "EMPTY", "details": "No transaction data available"}
    budget_section = budget if budget else {"status": "EMPTY", "details": "No budget data available"}
    portfolio_section = portfolio if portfolio else {"status": "EMPTY", "details": "No portfolio data available"}

    return {
        "executive_summary": "Financial analysis completed successfully.",
        "sections": ["transaction_insights", "budget_analysis", "portfolio_insights", "recommendations"],
        "transaction_insights": transaction_section,
        "budget_analysis": budget_section,
        "portfolio_insights": portfolio_section,
        "recommendations": [
            "Review flagged anomalies.",
            "Investigate over-budget categories.",
            "Rebalance portfolio if concentration risk is high.",
        ],
    }
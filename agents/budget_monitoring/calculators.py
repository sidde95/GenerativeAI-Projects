from typing import Any, Dict, List

def compute_budget_vs_actual(transactions: List[Dict[str, Any]], budgets: Dict[str, float]) -> Dict[str, Any]:
    """Compare actual spending against budgets
    
    Args:
        transactions: List of transaction dicts
        budgets: Dictionary mapping categories to budget amounts
        
    Returns:
        Dictionary with budget vs actual analysis for each category
    """
    if not transactions or not budgets:
        return {}
    
    # Aggregate actual spending by category
    actuals = {}
    for t in transactions:
        if not isinstance(t, dict):
            continue
        cat = t.get("category") or "Unknown"
        try:
            amt = abs(float(t.get("amount", 0)))
            actuals[cat] = actuals.get(cat, 0) + amt
        except (ValueError, TypeError):
            continue
    
    # Compare against budgets
    result = {}
    for cat, budget in budgets.items():
        if not isinstance(budget, (int, float)):
            continue
        actual = actuals.get(cat, 0.0)
        try:
            utilization = (actual / budget) * 100 if budget > 0 else 0
        except (ValueError, ZeroDivisionError):
            utilization = 0
        
        result[cat] = {
            "budget": budget,
            "actual": round(actual, 2),
            "utilization_percent": round(utilization, 2),
            "overrun": actual > budget
        }

    return result
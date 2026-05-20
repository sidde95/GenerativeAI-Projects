from typing import Any, Dict, List

def categorize_transactions(transactions: list[Dict[str, Any]]) -> Dict[str, float]:
    """Categorize transactions by amount
    
    Args:
        transactions: List of transaction dicts with 'category' and 'amount' keys
        
    Returns:
        Dictionary mapping category names to total amounts
    """
    if not transactions:
        return {}
    
    category_totals = {}
    for t in transactions:
        if not isinstance(t, dict):
            continue
        cat = t.get("category") or "Unknown"
        try:
            amt = float(t.get("amount", 0))
            category_totals[cat] = category_totals.get(cat, 0) + amt
        except (ValueError, TypeError):
            # Skip transactions with invalid amounts
            continue
    
    return category_totals


def detect_simple_anomalies(transactions: List[Dict[str, Any]], threshold: float = -1000.0) -> List[Dict[str, Any]]:
    """Flag large outflows as anomalies
    
    Args:
        transactions: List of transaction dicts
        threshold: Amount threshold (negative value for outflows)
        
    Returns:
        List of anomalous transactions
    """
    if not transactions:
        return []
    
    anomalies = []
    for t in transactions:
        if not isinstance(t, dict):
            continue
        try:
            amt = float(t.get("amount", 0))
            if amt <= threshold:
                anomalies.append(t)
        except (ValueError, TypeError):
            continue
    
    return anomalies


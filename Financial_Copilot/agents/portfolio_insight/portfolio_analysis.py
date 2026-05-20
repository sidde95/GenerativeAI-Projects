from typing import Any, Dict, List

def summarize_holdings_performance(holdings: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Summarize portfolio holdings and their performance
    
    Args:
        holdings: List of holding dicts with symbol, shares, cost_basis, current_price
        
    Returns:
        Dictionary with total portfolio value and individual holdings summary
    """
    if not holdings:
        return {"total_value": 0.0, "holdings_summary": []}
    
    summary = []
    total_value = 0.0
    
    for h in holdings:
        if not isinstance(h, dict):
            continue
        
        try:
            shares = float(h.get("shares", 0))
            cp = float(h.get("current_price", 0))
            cb = float(h.get("cost_basis", 0))
            value = shares * cp
            pnl = (cp - cb) * shares
            total_value += value
            
            summary.append({
                "symbol": h.get("symbol", "NA") or "NA",
                "shares": round(shares, 2),
                "cost_basis": round(cb, 2),
                "current_price": round(cp, 2),
                "value": round(value, 2),
                "pnl": round(pnl, 2),
                "pnl_percent": round((pnl / (cb * shares) * 100) if (cb * shares) > 0 else 0, 2)
            })
        except (ValueError, TypeError, ZeroDivisionError):
            continue

    return {
        "total_value": round(total_value, 2),
        "holdings_count": len(summary),
        "holdings_summary": summary
    }
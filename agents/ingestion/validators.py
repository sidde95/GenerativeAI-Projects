from copy import deepcopy
from typing import Any, Dict, List

REQUIRED_TOP_LEVEL_KEYS = ["transactions", "budgets", "portfolio"]

def validate_input_schema(data: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(data, dict):
        return {
            "is_valid": False,
            "missing_keys": REQUIRED_TOP_LEVEL_KEYS,
            "invalid_types": ["raw input must be a JSON object"],
        }

    missing = [k for k in REQUIRED_TOP_LEVEL_KEYS if k not in data]
    invalid_types: List[str] = []

    if "transactions" in data and not isinstance(data.get("transactions"), list):
        invalid_types.append("transactions must be a list")
    if "budgets" in data and not isinstance(data.get("budgets"), dict):
        invalid_types.append("budgets must be an object")
    if "portfolio" in data and not isinstance(data.get("portfolio"), dict):
        invalid_types.append("portfolio must be an object")

    return {
        "is_valid": len(missing) == 0 and not invalid_types,
        "missing_keys": missing,
        "invalid_types": invalid_types,
    }

def normalize_input(data: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize raw payload into the canonical workflow shape."""

    transactions = deepcopy(data.get("transactions", [])) if isinstance(data.get("transactions", []), list) else []
    budgets = deepcopy(data.get("budgets", {})) if isinstance(data.get("budgets", {}), dict) else {}
    portfolio = deepcopy(data.get("portfolio", {})) if isinstance(data.get("portfolio", {}), dict) else {}

    return {
        "transactions": transactions,
        "budgets": budgets,
        "portfolio": portfolio
    }




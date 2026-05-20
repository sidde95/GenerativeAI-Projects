from typing import Any, Dict

from agents.ingestion.validators import validate_input_schema, normalize_input
from utils.logger import logger

def run_ingestion_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(state, dict):
        raise TypeError("ingestion agent expects a state dictionary")

    logger.log_agent_start("ingestion")
    raw_data = state.get("raw_data", {})

    validation = validate_input_schema(raw_data)
    if not validation["is_valid"]:
        issues = []
        if validation.get("missing_keys"):
            issues.append(f"missing keys: {validation['missing_keys']}")
        if validation.get("invalid_types"):
            issues.append(f"invalid types: {validation['invalid_types']}")
        error_msg = "; ".join(issues) if issues else "Input schema validation failed"
        logger.log_agent_error("ingestion", error_msg)
        return {
            "ingestion_result": {
                "status": "FAILED",
                "error": error_msg
            },
            "errors": [error_msg]
        }

    normalized = normalize_input(raw_data)
    logger.log_agent_detail("ingestion", "records", str(len(normalized.get("transactions", []))))
    logger.log_agent_success("ingestion", 0.1)

    return {
        "ingestion_result": {
            "status": "SUCCESS",
            "normalized_data": normalized
        },
        "status": "RUNNING",
    }
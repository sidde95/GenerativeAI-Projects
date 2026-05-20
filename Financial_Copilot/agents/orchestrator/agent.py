from typing import Any, Dict

from utils.logger import logger
from utils.helper import get_timestamp

def run_orchestrator_init(state: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(state, dict):
        raise TypeError("orchestrator_init expects a state dictionary")

    logger.log_agent_start("orchestrator_init")
    logger.log_agent_detail("orchestrator_init", "run_id", state.get("run_id", "NA"))
    logger.log_agent_success("orchestrator_init", 0.05)
    return {
        "status": "RUNNING",
        "started_at": state.get("started_at", get_timestamp())
    }

def run_orchestrator_finalize(state: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(state, dict):
        raise TypeError("orchestrator_finalize expects a state dictionary")

    logger.log_agent_start("orchestrator_finalize")
    logger.log_agent_success("orchestrator_finalize", 0.05)
    return {
        "status": "SUCCESS" if not state.get("errors") else "FAILED",
        "completed_at": get_timestamp()
    }
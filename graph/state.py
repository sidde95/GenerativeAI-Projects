"""State schema for the workflow."""

from typing import Annotated, Any, Dict, List, TypedDict
import operator

class FinancialCopilotState(TypedDict, total=False):
    """State schema for Financial Copilot workflow
    
    This state is passed between all agents in the graph.
    Each agent read from and writes to this shared state.
    """

    # Execution metadata
    run_id: str
    status: str  # PENDING, RUNNING, SUCCESS, FAILED
    started_at: str
    completed_at: str

    # Input Data
    raw_data: Dict[str, Any]

    # Agent Results
    ingestion_result: Dict[str, Any]
    transaction_insights: Dict[str, Any]
    budget_analysis: Dict[str, Any]
    portfolio_insights: Dict[str, Any]
    final_report: Dict[str, Any]

    errors: Annotated[List[str], operator.add]
    retries: Dict[str, int]

    checkpoints: Annotated[List[Dict[str, Any]], operator.add]

def create_initial_state(raw_data: Dict[str, Any]) -> FinancialCopilotState:
    """Create initial workflow state."""

    from utils.helper import generate_run_id, get_timestamp

    return FinancialCopilotState(
        run_id=generate_run_id(),
        status="PENDING",
        started_at=get_timestamp(),
        completed_at="",
        raw_data=raw_data,
        ingestion_result={},
        transaction_insights={},
        budget_analysis={},
        portfolio_insights={},
        final_report={},
        errors=[],
        retries={},
        checkpoints=[]
    )
from langgraph.graph import END, StateGraph
from graph.state import FinancialCopilotState

from agents.orchestrator.agent import run_orchestrator_init, run_orchestrator_finalize
from agents.ingestion.agent import run_ingestion_agent
from agents.transaction_intelligence.agent import run_transaction_agent
from agents.budget_monitoring.agent import run_budget_agent
from agents.portfolio_insight.agent import run_portfolio_agent
from agents.reporting.agent import run_reporting_agent


def ingestion_route(state):
    status = state.get("ingestion_result", {}).get("status", "FAILED")
    return "ingestion_ok" if status == "SUCCESS" else "ingestion_failed"


def build_workflow():
    graph = StateGraph(FinancialCopilotState)

    # nodes
    graph.add_node("orchestrator_init", run_orchestrator_init)
    graph.add_node("ingestion", run_ingestion_agent)
    graph.add_node("transaction", run_transaction_agent)
    graph.add_node("budget", run_budget_agent)
    graph.add_node("portfolio", run_portfolio_agent)
    graph.add_node("reporting", run_reporting_agent)
    graph.add_node("orchestrator_finalize", run_orchestrator_finalize)

    # entry
    graph.set_entry_point("orchestrator_init")
    graph.add_edge("orchestrator_init", "ingestion")

    # conditional after ingestion
    graph.add_conditional_edges(
        "ingestion",
        ingestion_route,
        {
            "ingestion_ok": "transaction",
            "ingestion_failed": "orchestrator_finalize",
        },
    )

    # sequential joins (simple version)
    graph.add_edge("transaction", "budget")
    graph.add_edge("budget", "portfolio")
    graph.add_edge("portfolio", "reporting")
    graph.add_edge("reporting", "orchestrator_finalize")

    graph.add_edge("orchestrator_finalize", END)

    return graph.compile()
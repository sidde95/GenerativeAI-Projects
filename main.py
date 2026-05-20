"""CLI entrypoint for Financial Copilot."""

from __future__ import annotations

import sys
from pathlib import Path

# Add project root to path
project_root_path = Path(__file__).parent
sys.path.insert(0, str(project_root_path))

from utils.helper import ensure_dir, load_json_file, project_root, save_json_file
from utils.logger import logger
from graph.state import create_initial_state
from graph.workflow import build_workflow


def load_default_input() -> dict:
    """Load the bundled sample input."""

    return load_json_file(project_root() / "data" / "sample_transactions.json")


def persist_outputs(final_state: dict) -> dict:
    """Persist the final state and report to outputs/."""

    outputs_dir = ensure_dir(project_root() / "outputs")
    run_id = final_state.get("run_id", "unknown-run")
    report_path = outputs_dir / f"{run_id}_final_report.json"
    state_path = outputs_dir / f"{run_id}_final_state.json"

    save_json_file(final_state.get("final_report", {}), report_path)
    save_json_file(final_state, state_path)

    return {
        "report_path": str(report_path),
        "state_path": str(state_path),
    }


def run_pipeline(raw_data: dict) -> dict:
    """Execute the workflow for the supplied payload."""

    state = create_initial_state(raw_data)
    logger.log_run_id(state.get("run_id", "unknown-run"))
    app = build_workflow()
    return app.invoke(state)


def main():
    try:
        logger.log_header("Intelligent Finance Copilot", "LangGraph Multi-Agent Demo")

        raw_data = load_default_input()
        final_state = run_pipeline(raw_data)
        artifacts = persist_outputs(final_state)

        report = final_state.get("final_report", {})
        status = final_state.get("status", "UNKNOWN")

        logger.log_info(f"Final Status: {status}")
        logger.log_info("Report generated successfully." if report else "No report generated.")
        logger.log_info(f"Artifacts written to {artifacts['report_path']} and {artifacts['state_path']}")

        if report:
            logger.log_table(
                "Top-Level Report Keys",
                {k: "available" for k in report.keys()}
            )
        
        # Log any errors
        errors = final_state.get("errors", [])
        if errors:
            logger.log_error(f"Execution completed with {len(errors)} error(s):")
            for err in errors:
                logger.log_error(f"  - {err}")
        
        return 0 if status == "SUCCESS" else 1

    except FileNotFoundError as e:
        logger.log_error(f"File not found: {e}")
        return 1
    except Exception as e:
        logger.log_error(f"Execution failed: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
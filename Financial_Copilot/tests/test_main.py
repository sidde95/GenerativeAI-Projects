from __future__ import annotations

import json

import main


def test_main_runs_and_writes_outputs(tmp_path, monkeypatch, sample_transactions, capsys):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "sample_transactions.json").write_text(json.dumps(sample_transactions), encoding="utf-8")

    monkeypatch.setattr(main, "project_root", lambda: tmp_path)

    exit_code = main.main()
    captured = capsys.readouterr().out

    assert exit_code == 0
    outputs_dir = tmp_path / "outputs"
    report_files = list(outputs_dir.glob("*_final_report.json"))
    state_files = list(outputs_dir.glob("*_final_state.json"))
    assert report_files
    assert state_files
    assert "ORCHESTRATOR_INIT" in captured
    assert "INGESTION" in captured
    assert "TRANSACTION_INTELLIGENCE" in captured
    assert "BUDGET_MONITORING" in captured
    assert "PORTFOLIO_INSIGHT" in captured
    assert "REPORTING" in captured


def test_persist_outputs_writes_artifacts(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "project_root", lambda: tmp_path)
    final_state = {"run_id": "fc-test-999", "final_report": {"executive_summary": "ok"}}

    artifacts = main.persist_outputs(final_state)

    assert (tmp_path / "outputs" / "fc-test-999_final_report.json").exists()
    assert (tmp_path / "outputs" / "fc-test-999_final_state.json").exists()
    assert artifacts["report_path"].endswith("_final_report.json")


def test_main_handles_missing_sample_file(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "project_root", lambda: tmp_path)
    monkeypatch.setattr(main, "load_default_input", lambda: (_ for _ in ()).throw(FileNotFoundError("missing")))

    assert main.main() == 1

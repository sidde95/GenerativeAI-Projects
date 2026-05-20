from __future__ import annotations

import json

import pytest

from utils import helper


def test_load_json_file_reads_relative_path(tmp_path, monkeypatch):
    monkeypatch.setattr(helper, "project_root", lambda: tmp_path)
    payload = {"alpha": 1, "beta": [1, 2, 3]}
    target = tmp_path / "data" / "sample.json"
    target.parent.mkdir(parents=True)
    target.write_text(json.dumps(payload), encoding="utf-8")

    assert helper.load_json_file("data/sample.json") == payload


def test_load_json_file_raises_for_missing_file(tmp_path, monkeypatch):
    monkeypatch.setattr(helper, "project_root", lambda: tmp_path)

    with pytest.raises(FileNotFoundError):
        helper.load_json_file("data/missing.json")


def test_load_json_file_requires_object(tmp_path, monkeypatch):
    monkeypatch.setattr(helper, "project_root", lambda: tmp_path)
    target = tmp_path / "list.json"
    target.write_text(json.dumps([1, 2, 3]), encoding="utf-8")

    with pytest.raises(ValueError):
        helper.load_json_file(target)


def test_save_json_file_creates_parent_directories(tmp_path, monkeypatch):
    monkeypatch.setattr(helper, "project_root", lambda: tmp_path)
    payload = {"run_id": "fc-1", "status": "SUCCESS"}
    target = "outputs/nested/result.json"

    helper.save_json_file(payload, target)

    saved_path = tmp_path / target
    assert saved_path.exists()
    assert json.loads(saved_path.read_text(encoding="utf-8")) == payload


def test_utility_functions():
    assert helper.ensure_dir is not None
    assert helper.format_currency(1234.5) == "$1,234.50"
    assert helper.calculate_percentage(25, 100) == 25.0
    assert helper.calculate_percentage(1, 0) == 0.0
    assert helper.project_root().exists()
    assert helper.generate_run_id().startswith("fc-")
    assert "T" in helper.get_timestamp()

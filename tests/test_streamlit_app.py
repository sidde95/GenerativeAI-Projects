from __future__ import annotations

import io
import json

import ui.streamlit_app as streamlit_app


def test_streamlit_module_import_is_safe():
    assert hasattr(streamlit_app, "load_input_data")
    assert hasattr(streamlit_app, "render_app")


def test_streamlit_load_input_data_missing_sample(tmp_path, monkeypatch):
    monkeypatch.setattr(streamlit_app, "SAMPLE_INPUT_PATH", tmp_path / "missing.json")

    data, source, warning = streamlit_app.load_input_data(use_sample=True)

    assert data is None
    assert source is None
    assert "Sample data not found" in warning


def test_streamlit_load_input_data_from_upload(sample_transactions):
    uploaded_file = io.StringIO(json.dumps(sample_transactions))
    data, source, warning = streamlit_app.load_input_data(uploaded_file=uploaded_file, use_sample=False)

    assert warning is None
    assert source == "Uploaded JSON"
    assert data["transactions"]


def test_streamlit_run_workflow(sample_transactions):
    final_state = streamlit_app.run_workflow(sample_transactions)

    assert final_state["status"] == "SUCCESS"
    assert final_state["final_report"]["sections"]


def test_streamlit_formatters():
    assert streamlit_app.format_currency(1234.56) == "$1,234.56"
    assert streamlit_app.format_percent(12.34) == "12.3%"
    assert streamlit_app.format_signed(-12.345) == "-12.35"
    assert streamlit_app.safe_get({"a": {"b": 1}}, "a", "b") == 1


class _DummyBlock:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def metric(self, *args, **kwargs):
        return None


class _DummyStatus(_DummyBlock):
    def write(self, *args, **kwargs):
        return None

    def update(self, *args, **kwargs):
        return None


class _DummyStreamlit:
    def __init__(self, run_clicked: bool):
        self.run_clicked = run_clicked

    def set_page_config(self, *args, **kwargs):
        return None

    def markdown(self, *args, **kwargs):
        return None

    def columns(self, sizes, gap=None):
        count = sizes if isinstance(sizes, int) else len(sizes)
        return [_DummyBlock() for _ in range(count)]

    def file_uploader(self, *args, **kwargs):
        return None

    def checkbox(self, *args, **kwargs):
        return False

    def selectbox(self, label, options, **kwargs):
        return options[0]

    def radio(self, label, options, **kwargs):
        return options[0]

    def caption(self, *args, **kwargs):
        return None

    def expander(self, *args, **kwargs):
        return _DummyBlock()

    def download_button(self, *args, **kwargs):
        return None

    def button(self, *args, **kwargs):
        return self.run_clicked

    def status(self, *args, **kwargs):
        return _DummyStatus()

    def tabs(self, labels):
        return [_DummyBlock() for _ in labels]

    def json(self, *args, **kwargs):
        return None

    def dataframe(self, *args, **kwargs):
        return None

    def info(self, *args, **kwargs):
        return None

    def success(self, *args, **kwargs):
        return None

    def warning(self, *args, **kwargs):
        return None

    def error(self, *args, **kwargs):
        return None

    def subheader(self, *args, **kwargs):
        return None

    def write(self, *args, **kwargs):
        return None

    def stop(self):
        raise RuntimeError("stop should not be called in this test")


def test_streamlit_render_app_no_click(monkeypatch):
    monkeypatch.setattr(streamlit_app, "st", _DummyStreamlit(run_clicked=False))
    streamlit_app.render_app()


def test_streamlit_render_app_with_run(monkeypatch, sample_transactions):
    monkeypatch.setattr(streamlit_app, "st", _DummyStreamlit(run_clicked=True))
    monkeypatch.setattr(streamlit_app, "build_sample_csv_template", lambda data_type: b"date")
    monkeypatch.setattr(streamlit_app, "build_sample_excel_template", lambda: b"excel")
    monkeypatch.setattr(streamlit_app, "_build_upload_options", lambda uploaded_file=None: None)
    monkeypatch.setattr(
        streamlit_app,
        "load_input_data",
        lambda uploaded_file=None, use_sample=True, parsed_upload=None: (sample_transactions, "Sample JSON", None),
    )
    monkeypatch.setattr(
        streamlit_app,
        "run_workflow",
        lambda raw_data: {
            "run_id": "fc-ui-1",
            "status": "SUCCESS",
            "transaction_insights": {"status": "SUCCESS"},
            "budget_analysis": {"status": "SUCCESS"},
            "portfolio_insights": {"status": "SUCCESS"},
            "final_report": {"sections": ["transaction_insights"]},
            "errors": [],
        },
    )
    streamlit_app.render_app()

"""Streamlit UI for Financial Copilot."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Iterable

import pandas as pd
import streamlit as st

# Add project root to path when the app is executed directly by Streamlit.
project_root_path = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root_path))

from graph.state import create_initial_state
from graph.workflow import build_workflow
from ui.data_parser import (
    FIELD_ALIASES,
    INTERNAL_SCHEMA_KEYS,
    REQUIRED_FIELDS,
    ParseOutcome,
    build_sample_csv_template,
    build_sample_excel_template,
    list_excel_sheets,
    load_table_from_uploaded_file,
    normalize_json_payload,
    parse_uploaded_file_with_details,
    suggest_mapping,
    to_backend_workflow_payload,
)


class ParsedUploadBundle(dict):
    """Container for pre-parsed upload data."""


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def safe_get(data: Any, *keys: Any, default: Any = "N/A") -> Any:
    """Safely walk nested dict-like structures."""
    current = data
    for key in keys:
        if isinstance(current, dict):
            current = current.get(key, default)
        else:
            return default
    return default if current is None else current


def format_currency(value: Any) -> str:
    try:
        return f"${float(value):,.2f}"
    except (TypeError, ValueError):
        return "N/A"


def format_percent(value: Any) -> str:
    try:
        return f"{float(value):.1f}%"
    except (TypeError, ValueError):
        return "N/A"


def format_signed(value: Any) -> str:
    try:
        numeric = float(value)
        return f"{numeric:+,.2f}"
    except (TypeError, ValueError):
        return "N/A"


def _format_file_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    return f"{size_bytes / (1024 * 1024):.2f} MB"


def _count_valid_rows(
    parsed_upload: ParsedUploadBundle | None,
    raw_data: dict[str, Any] | None = None,
) -> int:
    if isinstance(parsed_upload, dict):
        internal_payload = parsed_upload.get("internal_payload", {})
        if isinstance(internal_payload, dict):
            return sum(
                len(rows)
                for rows in internal_payload.values()
                if isinstance(rows, list)
            )
    if isinstance(raw_data, dict):
        total = 0
        transactions = raw_data.get("transactions")
        if isinstance(transactions, list):
            total += len(transactions)
        budgets = raw_data.get("budgets")
        if isinstance(budgets, dict):
            total += len(budgets)
        portfolio = raw_data.get("portfolio")
        if isinstance(portfolio, dict):
            holdings = portfolio.get("holdings")
            if isinstance(holdings, list):
                total += len(holdings)
        return total
    return 0


def has_renderable_content(data: Any, *keys: str) -> bool:
    """Return True if the nested key path leads to non-empty content."""
    current = data
    for key in keys:
        if not isinstance(current, dict):
            return False
        current = current.get(key)
        if current is None:
            return False
    if isinstance(current, (list, dict)):
        return len(current) > 0
    return bool(current)


def load_input_data(
    uploaded_file: Any = None,
    parsed_upload: ParsedUploadBundle | None = None,
):
    """Load input payload from uploaded content only."""
    if parsed_upload is not None:
        backend_payload = parsed_upload.get("backend_payload")
        if backend_payload:
            return backend_payload, parsed_upload.get("source", "Uploaded File"), None
        return None, None, "No valid rows found in uploaded data after mapping and validation."
    if uploaded_file is not None:
        try:
            payload = json.load(uploaded_file)
            normalized = normalize_json_payload(payload)
            return to_backend_workflow_payload(normalized), "Uploaded JSON", None
        except json.JSONDecodeError as exc:
            return None, None, f"Invalid JSON file: {exc}"
    return None, None, "Please upload a JSON, CSV, or Excel file to run analysis."


def run_workflow(raw_data: dict) -> dict:
    """Run the LangGraph workflow and return the final state."""
    state = create_initial_state(raw_data)
    app = build_workflow()
    return app.invoke(state)


# ---------------------------------------------------------------------------
# CSS — all classes prefixed fc- to avoid collisions with Streamlit internals
# ---------------------------------------------------------------------------

def _render_css() -> None:
    st.markdown(
        """
        <style>
        :root {
            --bg-1: #060b16;
            --bg-2: #0a1326;
            --fc-panel: rgba(10, 18, 34, 0.82);
            --fc-panel-soft: rgba(15, 23, 42, 0.66);
            --fc-border: rgba(148, 163, 184, 0.20);
            --fc-text-1: #f8fafc;
            --fc-text-2: #a8b3c7;
            --fc-ok: #34d399;
            --fc-warn: #fbbf24;
            --fc-err: #f87171;
            --fc-info: #60a5fa;
        }

        [data-testid="stAppViewContainer"] {
            background:
                radial-gradient(900px 500px at 8% 0%, rgba(59,130,246,0.16), transparent 65%),
                radial-gradient(800px 480px at 100% 0%, rgba(16,185,129,0.10), transparent 60%),
                linear-gradient(180deg, var(--bg-2) 0%, var(--bg-1) 100%);
        }

        .main .block-container {
            max-width: 100% !important;
            width: 100% !important;
            padding-top: clamp(2.2rem, 4.5vh, 3.5rem) !important;
            padding-bottom: 1.4rem;
            padding-left: clamp(1rem, 2.2vw, 2.4rem) !important;
            padding-right: clamp(1rem, 2.2vw, 2.4rem) !important;
        }

        /* ---- Hero header ---- */
        .fc-hero {
            background: linear-gradient(180deg, rgba(15,23,42,0.72), rgba(2,6,23,0.64));
            border: 1px solid var(--fc-border);
            border-radius: 16px;
            padding: 18px 22px;
            margin-bottom: 18px;
        }
        .fc-title {
            color: var(--fc-text-1);
            font-size: clamp(1.75rem, 2.1vw, 2.35rem);
            font-weight: 800;
            letter-spacing: -0.02em;
            line-height: 1.2;
            margin: 0;
        }
        .fc-subtitle {
            color: var(--fc-text-2);
            font-size: 0.97rem;
            margin-top: 0.45rem;
            margin-bottom: 0;
        }
        .fc-status-pill {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            margin-top: 0.85rem;
            border-radius: 999px;
            padding: 0.3rem 0.72rem;
            font-size: 0.79rem;
            font-weight: 700;
            border: 1px solid rgba(148,163,184,0.35);
            color: #cbd5e1;
            background: rgba(15,23,42,0.70);
        }
        .fc-status-pill.ready { border-color: rgba(52,211,153,0.38); color: #bbf7d0; }
        .fc-status-pill.done  { border-color: rgba(96,165,250,0.42);  color: #bfdbfe; }

        /* ---- Storyline strip ---- */
        .fc-storyline {
            background: var(--fc-panel);
            border: 1px solid var(--fc-border);
            border-radius: 14px;
            padding: 14px 16px;
            margin-bottom: 18px;
        }
        .fc-section-title {
            color: #e2e8f0;
            font-size: 1.05rem;
            font-weight: 700;
            margin: 0 0 0.65rem 0;
        }
        .fc-storyline-row {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            align-items: center;
            justify-content: center;
        }
        .fc-chip {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            min-height: 38px;
            padding: 0.55rem 0.88rem;
            border-radius: 999px;
            color: #0b1220;
            font-size: 0.81rem;
            font-weight: 800;
            border: 1px solid rgba(255,255,255,0.46);
            box-shadow: 0 6px 14px rgba(0,0,0,0.16);
            white-space: nowrap;
        }
        .fc-c1 { background: linear-gradient(135deg,#fda4af,#fbcfe8); }
        .fc-c2 { background: linear-gradient(135deg,#86efac,#99f6e4); }
        .fc-c3 { background: linear-gradient(135deg,#93c5fd,#c4b5fd); }
        .fc-c4 { background: linear-gradient(135deg,#fde68a,#fcd34d); }
        .fc-c5 { background: linear-gradient(135deg,#fdba74,#fca5a5); }
        .fc-c6 { background: linear-gradient(135deg,#67e8f9,#60a5fa); }
        .fc-arrow { color: #94a3b8; font-size: 1rem; font-weight: 900; }
        .fc-muted {
            margin-top: 9px;
            text-align: center;
            color: #93a4be;
            font-size: 0.81rem;
            font-weight: 500;
        }

        /* ---- File meta pills ---- */
        .fc-file-meta {
            display: flex;
            flex-wrap: wrap;
            gap: 7px;
            margin-top: 9px;
            margin-bottom: 2px;
        }
        .fc-meta-pill {
            border-radius: 999px;
            padding: 0.22rem 0.56rem;
            font-size: 0.75rem;
            font-weight: 700;
            border: 1px solid rgba(148,163,184,0.32);
            color: #cbd5e1;
            background: rgba(2,6,23,0.45);
        }

        /* ---- Run panel checklist ---- */
        .fc-checklist {
            margin-bottom: 14px;
            display: flex;
            flex-direction: column;
            gap: 7px;
        }
        .fc-check-item {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 0.86rem;
            color: #dbe4f3;
        }
        .fc-dot {
            width: 9px;
            height: 9px;
            border-radius: 999px;
            display: inline-block;
            flex-shrink: 0;
        }
        .fc-dot-ok   { background: var(--fc-ok); }
        .fc-dot-warn { background: var(--fc-warn); }
        .fc-dot-err  { background: var(--fc-err); }

        /* ---- KPI strip ---- */
        .fc-kpi-strip { margin-top: 16px; margin-bottom: 8px; }
        .fc-metric-card {
            background: rgba(2,6,23,0.42);
            border: 1px solid rgba(148,163,184,0.22);
            border-radius: 12px;
            padding: 12px;
        }
        .fc-metric-label {
            color: #93a4be;
            font-size: 0.77rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.08em;
        }
        .fc-metric-value {
            color: #f8fafc;
            font-size: 1.32rem;
            font-weight: 800;
            line-height: 1.1;
        }
        .fc-metric-sub {
            color: #cbd5e1;
            font-size: 0.79rem;
            margin-top: 2px;
        }

        /* ---- Coverage badges ---- */
        .fc-coverage {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: 12px;
            margin-bottom: 4px;
        }
        .fc-badge {
            display: inline-flex;
            align-items: center;
            gap: 5px;
            border-radius: 999px;
            padding: 0.24rem 0.64rem;
            font-size: 0.75rem;
            font-weight: 700;
        }
        .fc-badge-ok   { background: rgba(52,211,153,0.14); border: 1px solid rgba(52,211,153,0.34); color: #6ee7b7; }
        .fc-badge-miss { background: rgba(100,116,139,0.14); border: 1px solid rgba(100,116,139,0.28); color: #94a3b8; }

        /* ---- Insight sections ---- */
        .fc-section-pill {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            margin-right: 8px;
            padding: 0.30rem 0.62rem;
            border-radius: 999px;
            background: rgba(30,41,59,0.9);
            color: #e2e8f0;
            font-size: 0.77rem;
            font-weight: 700;
        }
        .fc-rec-item {
            display: flex;
            gap: 10px;
            align-items: flex-start;
            margin: 0.45rem 0;
            color: #e2e8f0;
        }
        .fc-priority-pill {
            min-width: 70px;
            text-align: center;
            border-radius: 999px;
            padding: 0.16rem 0.52rem;
            font-size: 0.71rem;
            font-weight: 800;
            color: #0f172a;
            flex: 0 0 auto;
        }
        .fc-priority-high   { background: #fecaca; }
        .fc-priority-medium { background: #fde68a; }
        .fc-priority-low    { background: #bbf7d0; }

        /* ---- Empty state ---- */
        .fc-empty-state {
            color: #64748b;
            font-size: 0.92rem;
            padding: 2rem 0;
            text-align: center;
        }

        /* ---- Scoped output tabs (.safe-output-tabs wrapper) ---- */
        .safe-output-tabs {
            margin-top: 20px;
        }

        /* Tab bar spacing and label readability */
        .safe-output-tabs [data-baseweb="tab-list"] {
            gap: 4px;
            border-bottom: 1px solid rgba(148, 163, 184, 0.18);
            padding-bottom: 0;
            flex-wrap: wrap;
        }

        /* Individual tab button — readable, not cramped */
        .safe-output-tabs [data-baseweb="tab"] {
            font-size: 14px !important;
            font-weight: 500 !important;
            padding: 10px 18px !important;
            min-height: 42px !important;
            min-width: 0 !important;
            width: auto !important;
            flex: 0 0 auto !important;
            white-space: nowrap;
            color: #94a3b8 !important;
            background: transparent !important;
            border: none !important;
            border-bottom: 2px solid transparent !important;
            border-radius: 0 !important;
            transition: color 0.15s ease, border-color 0.15s ease;
        }

        /* Active tab */
        .safe-output-tabs [aria-selected="true"][data-baseweb="tab"] {
            color: #f8fafc !important;
            border-bottom: 2px solid #60a5fa !important;
            font-weight: 600 !important;
        }

        /* Hover state */
        .safe-output-tabs [data-baseweb="tab"]:hover {
            color: #e2e8f0 !important;
            border-bottom-color: rgba(96, 165, 250, 0.40) !important;
        }

        /* Focus ring — keep accessible */
        .safe-output-tabs [data-baseweb="tab"]:focus-visible {
            outline: 2px solid #60a5fa;
            outline-offset: 2px;
        }

        /* Tab content area */
        .safe-output-tabs [data-baseweb="tab-panel"] {
            padding-top: 1.1rem !important;
        }

        /* Dataframes */
        div[data-testid="stDataFrame"] { width: 100%; }
        .stButton > button {
            border-radius: 10px;
            font-weight: 700;
            min-height: 46px;
            width: 100%;
        }

        @media (max-width: 1024px) {
            .fc-title { font-size: 1.7rem; }
            .main .block-container {
                padding-left: 0.9rem !important;
                padding-right: 0.9rem !important;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

def render_header(run_completed: bool = False) -> None:
    """Render executive hero header — always fully visible."""
    cls = "done" if run_completed else "ready"
    text = "Run completed" if run_completed else "Ready for analysis"
    st.markdown(
        f"""
        <div class="fc-hero">
          <h1 class="fc-title">Intelligent Finance Copilot</h1>
          <p class="fc-subtitle">Executive-grade multi-agent intelligence for transactions, budgeting, portfolio risk, and reporting.</p>
          <span class="fc-status-pill {cls}">{text}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Storyline
# ---------------------------------------------------------------------------

def render_storyline() -> None:
    """Compact workflow storyline — all HTML in one markdown call (no ghost boxes)."""
    st.markdown(
        """
        <div class="fc-storyline">
          <div class="fc-section-title">Workflow Storyline</div>
          <div class="fc-storyline-row">
            <span class="fc-chip fc-c1">Orchestrator Init</span>
            <span class="fc-arrow">&#8594;</span>
            <span class="fc-chip fc-c2">Ingestion Agent</span>
            <span class="fc-arrow">&#8594;</span>
            <span class="fc-chip fc-c3">Transaction Intelligence</span>
            <span class="fc-arrow">&#8594;</span>
            <span class="fc-chip fc-c4">Budget Monitoring</span>
            <span class="fc-arrow">&#8594;</span>
            <span class="fc-chip fc-c5">Portfolio Insight</span>
            <span class="fc-arrow">&#8594;</span>
            <span class="fc-chip fc-c6">Reporting + Finalize</span>
          </div>
          <div class="fc-muted">If ingestion validation fails, downstream agents do not execute.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# KPI helper
# ---------------------------------------------------------------------------

def _render_kpis(columns: Iterable[Any], metrics: list[dict[str, str]]) -> None:
    for column, metric in zip(columns, metrics):
        with column:
            sub_html = (
                f'<div class="fc-metric-sub">{metric["sub"]}</div>' if metric.get("sub") else ""
            )
            st.markdown(
                f"""
                <div class="fc-metric-card">
                  <div class="fc-metric-label">{metric["label"]}</div>
                  <div class="fc-metric-value">{metric["value"]}</div>
                  {sub_html}
                </div>
                """,
                unsafe_allow_html=True,
            )


# ---------------------------------------------------------------------------
# Mapping helpers
# ---------------------------------------------------------------------------

def _render_mapping_controls(
    data_type: str, dataframe: pd.DataFrame, prefix: str
) -> dict[str, str]:
    st.markdown(f"**Map columns for {data_type.title()}**")
    st.caption(f"Detected columns: {', '.join(str(c) for c in dataframe.columns)}")
    suggestions = suggest_mapping([str(c) for c in dataframe.columns], data_type)
    mapping: dict[str, str] = {}
    selectable = ["-- Unmapped --", *[str(c) for c in dataframe.columns]]
    for field in REQUIRED_FIELDS[data_type]:
        suggested = suggestions.get(field)
        default_index = selectable.index(suggested) if suggested in selectable else 0
        selection = st.selectbox(
            f"{data_type}: {field}",
            selectable,
            index=default_index,
            key=f"{prefix}_{data_type}_{field}",
            help=f"Aliases: {', '.join(FIELD_ALIASES[field])}",
        )
        if selection != "-- Unmapped --":
            mapping[field] = selection
    return mapping


def _has_ambiguous_mapping(mapping: dict[str, str]) -> bool:
    mapped = [v for v in mapping.values() if v]
    return len(mapped) != len(set(mapped))


def _render_parsed_preview(parse_result: ParseOutcome) -> None:
    """Compact row-count stats outside + collapsed nested expander for full tables."""
    stats_parts: list[str] = []
    for data_type in INTERNAL_SCHEMA_KEYS:
        rows = parse_result.data.get(data_type, [])
        if rows:
            stats_parts.append(f"{data_type.title()}: **{len(rows)}** valid rows")
    if stats_parts:
        st.markdown("  ·  ".join(stats_parts))
    else:
        st.markdown("_No valid rows parsed._")

    total_errors = sum(
        len(parse_result.row_errors.get(dt, [])) for dt in INTERNAL_SCHEMA_KEYS
    )
    if total_errors:
        st.warning(f"{total_errors} row(s) failed validation.")

    preview_open = bool(st.session_state.get("normalized_preview_expanded", False))
    with st.expander("Preview normalized data", expanded=preview_open):
        for data_type in INTERNAL_SCHEMA_KEYS:
            rows = parse_result.data.get(data_type, [])
            errors = parse_result.row_errors.get(data_type, [])
            if rows:
                st.markdown(f"**{data_type.title()} — valid rows ({len(rows)})**")
                st.dataframe(rows, use_container_width=True, hide_index=True)
            if errors:
                st.markdown(f"**{data_type.title()} — row errors ({len(errors)})**")
                st.dataframe(errors, use_container_width=True, hide_index=True)


# ---------------------------------------------------------------------------
# Mapping panel
# ---------------------------------------------------------------------------

def render_mapping_panel(uploaded_file: Any) -> ParsedUploadBundle | None:
    """Render advanced Excel/CSV mapping panel — collapsed by default."""
    if uploaded_file is None:
        return None

    file_name = str(getattr(uploaded_file, "name", "")).lower()
    file_type = Path(file_name).suffix.lstrip(".")

    if file_type == "json":
        return None

    if file_type not in {"csv", "xlsx", "xls"}:
        st.error("Unsupported file type. Please upload json, csv, xlsx, or xls.")
        return ParsedUploadBundle(
            {"backend_payload": None, "source": None, "has_mapping_issues": True}
        )

    should_expand = bool(st.session_state.get("advanced_mapping_expanded", False))
    options: dict[str, Any] = {"file_type": file_type, "mappings": {}}
    panel_messages: list[tuple[str, str]] = []
    parse_result: ParseOutcome | None = None

    with st.expander("Advanced column mapping (Excel/CSV)", expanded=should_expand):
        try:
            if file_type == "csv":
                csv_data_type = st.selectbox(
                    "CSV data type",
                    ["transactions", "budgets", "portfolio"],
                    key="csv_data_type",
                    help="Select what this CSV file represents.",
                )
                dataframe = load_table_from_uploaded_file(uploaded_file, "csv")
                options["csv_data_type"] = csv_data_type
                options["mappings"][csv_data_type] = _render_mapping_controls(
                    csv_data_type, dataframe, "csv_map"
                )

            elif file_type in {"xlsx", "xls"}:
                sheet_names = list_excel_sheets(uploaded_file)
                excel_mode = st.radio(
                    "Excel import mode",
                    ["Single sheet", "Multiple sheets"],
                    horizontal=True,
                    key="excel_mode",
                    help="Single sheet: one data type. Multiple sheets: one per data type.",
                )
                if excel_mode == "Single sheet":
                    options["excel_mode"] = "single"
                    options["excel_sheet"] = st.selectbox(
                        "Excel sheet", sheet_names, key="excel_single_sheet"
                    )
                    options["excel_data_type"] = st.selectbox(
                        "Sheet represents",
                        ["transactions", "budgets", "portfolio"],
                        key="excel_single_type",
                    )
                    dataframe = load_table_from_uploaded_file(
                        uploaded_file, file_type, sheet_name=options["excel_sheet"]
                    )
                    options["mappings"][options["excel_data_type"]] = (
                        _render_mapping_controls(
                            options["excel_data_type"], dataframe, "excel_single_map"
                        )
                    )
                else:
                    options["excel_mode"] = "multi"
                    options["sheet_selection"] = {}
                    for data_type in INTERNAL_SCHEMA_KEYS:
                        selected = st.selectbox(
                            f"{data_type.title()} sheet",
                            ["-- Skip --", *sheet_names],
                            key=f"excel_multi_sheet_{data_type}",
                        )
                        if selected != "-- Skip --":
                            options["sheet_selection"][data_type] = selected
                    for data_type, sheet_name in options.get(
                        "sheet_selection", {}
                    ).items():
                        dataframe = load_table_from_uploaded_file(
                            uploaded_file, file_type, sheet_name=sheet_name
                        )
                        options["mappings"][data_type] = _render_mapping_controls(
                            data_type, dataframe, f"excel_multi_map_{data_type}"
                        )

            parse_result = parse_uploaded_file_with_details(uploaded_file, options)

            valid_total_rows = sum(
                len(rows) for rows in parse_result.data.values()
            )
            backend_payload = (
                to_backend_workflow_payload(parse_result.data)
                if valid_total_rows > 0
                else None
            )
            has_row_errors = any(
                len(e) > 0 for e in parse_result.row_errors.values()
            )
            missing_required = False
            ambiguous_columns = False
            for data_type, mapping in options.get("mappings", {}).items():
                required = REQUIRED_FIELDS.get(data_type, [])
                if any(f not in mapping for f in required):
                    missing_required = True
                if _has_ambiguous_mapping(mapping):
                    ambiguous_columns = True

            if missing_required:
                panel_messages.append((
                    "error",
                    "Required mappings are missing. Please complete all required field mappings.",
                ))
            if ambiguous_columns:
                panel_messages.append((
                    "warning",
                    "Ambiguous column mapping detected. Please review and adjust mappings.",
                ))
            if valid_total_rows == 0:
                panel_messages.append((
                    "error",
                    "Parsing/validation failed. Please review mapping and source columns.",
                ))
            elif has_row_errors:
                panel_messages.append((
                    "warning",
                    "Some rows failed validation. Review the row errors shown below.",
                ))

            if panel_messages:
                st.session_state["advanced_mapping_expanded"] = True
                st.session_state["mapping_has_issues"] = True
                for level, message in panel_messages:
                    if level == "error":
                        st.error(message)
                    else:
                        st.warning(message)
            else:
                st.session_state["advanced_mapping_expanded"] = False
                st.session_state["mapping_has_issues"] = False

        except Exception as exc:
            st.session_state["advanced_mapping_expanded"] = True
            st.session_state["mapping_has_issues"] = True
            st.error(f"Failed to parse uploaded file: {exc}")
            return ParsedUploadBundle(
                {"backend_payload": None, "source": None, "has_mapping_issues": True}
            )

    if parse_result is None:
        return ParsedUploadBundle(
            {"backend_payload": None, "source": None, "has_mapping_issues": True}
        )

    _render_parsed_preview(parse_result)

    valid_total_rows = sum(len(rows) for rows in parse_result.data.values())
    backend_payload = (
        to_backend_workflow_payload(parse_result.data) if valid_total_rows > 0 else None
    )
    return ParsedUploadBundle(
        {
            "backend_payload": backend_payload,
            "internal_payload": parse_result.data,
            "row_errors": parse_result.row_errors,
            "source": f"Uploaded {file_type.upper()}",
            "has_mapping_issues": bool(panel_messages),
        }
    )


# ---------------------------------------------------------------------------
# Input panel  (no open/close HTML div wrappers — eliminates ghost boxes)
# ---------------------------------------------------------------------------

def render_input_panel() -> tuple[Any, ParsedUploadBundle | None]:
    """Render upload area, file meta, mapping panel, and template downloads."""
    st.markdown("**Input Data**")
    uploaded_file = st.file_uploader(
        "Upload data file",
        type=["json", "csv", "xlsx", "xls"],
        help="Upload a JSON, CSV, or Excel file. Advanced mapping is available if needed.",
    )

    parsed_upload: ParsedUploadBundle | None = None

    if uploaded_file is not None:
        file_name = str(getattr(uploaded_file, "name", "uploaded_file"))
        file_size = int(getattr(uploaded_file, "size", 0) or 0)
        file_ext = Path(file_name).suffix.lower().lstrip(".")
        st.markdown(
            f"""
            <div class="fc-file-meta">
              <span class="fc-meta-pill">{file_name}</span>
              <span class="fc-meta-pill">{_format_file_size(file_size)}</span>
              <span class="fc-meta-pill">{file_ext.upper()}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    parsed_upload = render_mapping_panel(uploaded_file)

    if (
        uploaded_file is not None
        and isinstance(parsed_upload, dict)
        and parsed_upload.get("backend_payload") is not None
        and not parsed_upload.get("has_mapping_issues")
    ):
        st.success("Columns auto-mapped successfully. Expand Advanced mapping to edit.")

    with st.expander("📄 Download sample templates", expanded=False):
        t1, t2 = st.columns(2)
        with t1:
            ttype = st.selectbox(
                "Select template",
                ["transactions", "budgets", "portfolio"],
                key="template_type",
            )
            st.download_button(
                "Download CSV template",
                data=build_sample_csv_template(ttype),
                file_name=f"sample_{ttype}.csv",
                mime="text/csv",
            )
        with t2:
            st.download_button(
                "Download Excel template",
                data=build_sample_excel_template(),
                file_name="sample_financial_template.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        st.caption("Template download only — not required for analysis.")

    return uploaded_file, parsed_upload


# ---------------------------------------------------------------------------
# Run panel  (no open/close HTML div wrappers — eliminates ghost boxes)
# ---------------------------------------------------------------------------

def render_run_panel(
    uploaded_file: Any, parsed_upload: ParsedUploadBundle | None
) -> bool:
    """Render run CTA with pre-run checklist — compact, no empty containers."""
    has_file = uploaded_file is not None
    schema_mapped = has_file and (
        parsed_upload is None
        or (
            isinstance(parsed_upload, dict)
            and parsed_upload.get("backend_payload") is not None
        )
    )
    ready_to_run = has_file and schema_mapped

    dot_file = "fc-dot-ok" if has_file else "fc-dot-err"
    dot_schema = "fc-dot-ok" if schema_mapped else "fc-dot-warn"
    dot_ready = "fc-dot-ok" if ready_to_run else "fc-dot-warn"

    st.markdown("**Run Analysis**")
    # All checklist items in ONE markdown call — no ghost box from open/close divs
    st.markdown(
        f"""
        <div class="fc-checklist">
          <div class="fc-check-item">
            <span class="fc-dot {dot_file}"></span>File uploaded
          </div>
          <div class="fc-check-item">
            <span class="fc-dot {dot_schema}"></span>Schema mapped
          </div>
          <div class="fc-check-item">
            <span class="fc-dot {dot_ready}"></span>Ready to run
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    return st.button("Run Analysis", use_container_width=True, type="primary")


# ---------------------------------------------------------------------------
# Run summary
# ---------------------------------------------------------------------------

def render_run_summary(
    final_state: dict[str, Any],
    input_source: str,
    valid_rows: int,
    raw_data: dict | None = None,
) -> None:
    """4-KPI strip + compact data coverage badges."""
    st.markdown('<div class="fc-kpi-strip">', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    _render_kpis(
        [c1, c2, c3, c4],
        [
            {
                "label": "Run ID",
                "value": str(final_state.get("run_id", "N/A")),
                "sub": "Execution identifier",
            },
            {
                "label": "Input Source",
                "value": str(input_source),
                "sub": "Uploaded format",
            },
            {
                "label": "Valid Rows",
                "value": str(valid_rows),
                "sub": "Rows used in analysis",
            },
            {
                "label": "Final Status",
                "value": str(final_state.get("status", "UNKNOWN")),
                "sub": "Workflow outcome",
            },
        ],
    )
    st.markdown("</div>", unsafe_allow_html=True)

    if raw_data is not None:
        def _badge(label: str, present: bool) -> str:
            cls = "fc-badge-ok" if present else "fc-badge-miss"
            icon = "✓" if present else "—"
            status = "Available" if present else "Missing"
            return f'<span class="fc-badge {cls}">{icon} {label}: {status}</span>'

        has_tx = bool(raw_data.get("transactions"))
        has_bud = bool(raw_data.get("budgets"))
        has_port = bool(raw_data.get("portfolio"))
        badges = _badge("Transactions", has_tx) + _badge("Budgets", has_bud) + _badge("Portfolio", has_port)
        st.markdown(
            f'<div class="fc-coverage">{badges}</div>',
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------
# Insight renderers
# ---------------------------------------------------------------------------

def render_transaction_insights(data: dict[str, Any]) -> None:
    if not isinstance(data, dict) or not data:
        st.markdown(
            '<div class="fc-empty-state">Transaction insights are not available for this dataset.</div>',
            unsafe_allow_html=True,
        )
        return

    anomalies = safe_get(data, "anomalies", default=[])
    anomaly_count = len(anomalies) if isinstance(anomalies, list) else 0
    breakdown = safe_get(data, "category_breakdown", default={}) or {}
    total_outflow = 0.0
    if isinstance(breakdown, dict):
        total_outflow = abs(
            sum(float(v) for v in breakdown.values() if isinstance(v, (int, float)))
        )

    k1, k2, k3 = st.columns(3)
    _render_kpis(
        [k1, k2, k3],
        [
            {
                "label": "Transactions",
                "value": str(safe_get(data, "transaction_count", default=0)),
                "sub": "Processed records",
            },
            {
                "label": "Categories",
                "value": str(len(breakdown) if isinstance(breakdown, dict) else 0),
                "sub": "Detected spend buckets",
            },
            {
                "label": "Total Outflow",
                "value": format_currency(total_outflow),
                "sub": "Absolute spend across categories",
            },
        ],
    )

    st.markdown('<div style="height:0.75rem;"></div>', unsafe_allow_html=True)
    left, right = st.columns([1.1, 0.9])

    with left:
        st.markdown("**Category Breakdown**")
        breakdown_rows = [
            {
                "Category": cat,
                "Amount": format_currency(amt),
                "Signed": format_signed(amt),
            }
            for cat, amt in sorted(
                breakdown.items() if isinstance(breakdown, dict) else [],
                key=lambda x: abs(float(x[1])) if isinstance(x[1], (int, float)) else 0,
                reverse=True,
            )
        ]
        if breakdown_rows:
            st.dataframe(breakdown_rows, use_container_width=True, hide_index=True)
        else:
            st.markdown(
                '<div class="fc-empty-state">No category data available.</div>',
                unsafe_allow_html=True,
            )

    with right:
        st.markdown("**Anomalies**")
        anomaly_rows = []
        if isinstance(anomalies, list):
            for item in anomalies:
                if isinstance(item, dict):
                    anomaly_rows.append(
                        {
                            "Date": safe_get(item, "date", default="N/A"),
                            "Merchant": safe_get(item, "merchant", default="N/A"),
                            "Category": safe_get(item, "category", default="N/A"),
                            "Amount": format_currency(
                                safe_get(item, "amount", default=0)
                            ),
                        }
                    )
        if anomaly_rows:
            st.dataframe(anomaly_rows, use_container_width=True, hide_index=True)
        else:
            st.markdown(
                '<div class="fc-empty-state">No anomalies detected.</div>',
                unsafe_allow_html=True,
            )

    # Conditional: only show anomaly recommendation when anomalies exist
    if anomaly_count > 0:
        st.markdown("**Recommendations**")
        label = "anomaly" if anomaly_count == 1 else "anomalies"
        st.markdown(
            f'<div class="fc-rec-item">' 
            f'<span class="fc-priority-pill fc-priority-high">High</span>' 
            f'<span>Review {anomaly_count} flagged {label} for potential fraud or data errors.</span>' 
            f'</div>',
            unsafe_allow_html=True,
        )


def render_budget_analysis(data: dict[str, Any]) -> None:
    if not isinstance(data, dict) or not data:
        st.markdown(
            '<div class="fc-empty-state">Budget data was not included in this analysis. ' 
            'Upload a file with budget rows to enable this view.</div>',
            unsafe_allow_html=True,
        )
        return

    budget_vs_actual = safe_get(data, "budget_vs_actual", default={}) or {}
    if not budget_vs_actual:
        st.markdown(
            '<div class="fc-empty-state">No budget vs actual data computed.</div>',
            unsafe_allow_html=True,
        )
        return

    over_budget = sum(
        1
        for v in budget_vs_actual.values()
        if isinstance(v, dict) and v.get("overrun")
    )
    total_budget = sum(
        float(v.get("budget", 0))
        for v in budget_vs_actual.values()
        if isinstance(v, dict)
    )
    total_actual = sum(
        float(v.get("actual", 0))
        for v in budget_vs_actual.values()
        if isinstance(v, dict)
    )

    k1, k2, k3 = st.columns(3)
    _render_kpis(
        [k1, k2, k3],
        [
            {
                "label": "Budget Categories",
                "value": str(safe_get(data, "budget_count", default=len(budget_vs_actual))),
                "sub": "Tracked categories",
            },
            {
                "label": "Over Budget",
                "value": str(over_budget),
                "sub": "Categories with overruns",
            },
            {
                "label": "Utilization",
                "value": format_percent(
                    (total_actual / total_budget) * 100 if total_budget else 0
                ),
                "sub": "Actual vs budget",
            },
        ],
    )

    rows = []
    for category, payload in sorted(budget_vs_actual.items()):
        if not isinstance(payload, dict):
            continue
        utilization = float(payload.get("utilization_percent", 0) or 0)
        rows.append(
            {
                "Category": category,
                "Budget": format_currency(payload.get("budget")),
                "Actual": format_currency(payload.get("actual")),
                "Utilization": format_percent(utilization),
                "Variance": format_currency(
                    float(payload.get("budget", 0)) - float(payload.get("actual", 0))
                ),
                "Status": "Over budget" if payload.get("overrun") else "On track",
            }
        )

    st.markdown("**Budget vs Actual**")
    if rows:
        st.dataframe(rows, use_container_width=True, hide_index=True)
    else:
        st.markdown(
            '<div class="fc-empty-state">No budget rows to display.</div>',
            unsafe_allow_html=True,
        )


def render_portfolio_insights(data: dict[str, Any]) -> None:
    if not isinstance(data, dict) or not data:
        st.markdown(
            '<div class="fc-empty-state">Portfolio data was not included in this analysis. ' 
            'Upload a file with portfolio holdings to enable this view.</div>',
            unsafe_allow_html=True,
        )
        return

    summary = safe_get(data, "summary", default={}) or {}
    holdings = safe_get(summary, "holdings_summary", default=[])
    if not holdings:
        st.markdown(
            '<div class="fc-empty-state">No holdings data available in portfolio summary.</div>',
            unsafe_allow_html=True,
        )
        return

    total_value = float(safe_get(summary, "total_value", default=0) or 0)
    holdings_count = int(
        safe_get(summary, "holdings_count", default=len(holdings)) or 0
    )
    total_pnl = sum(
        float(item.get("pnl", 0)) for item in holdings if isinstance(item, dict)
    )

    k1, k2, k3 = st.columns(3)
    _render_kpis(
        [k1, k2, k3],
        [
            {
                "label": "Holdings",
                "value": str(holdings_count),
                "sub": "Tracked positions",
            },
            {
                "label": "Portfolio Value",
                "value": format_currency(total_value),
                "sub": "Current market value",
            },
            {
                "label": "PnL",
                "value": format_signed(total_pnl),
                "sub": "Total unrealized gain/loss",
            },
        ],
    )

    rows = []
    for item in holdings if isinstance(holdings, list) else []:
        if not isinstance(item, dict):
            continue
        value = float(item.get("value", 0) or 0)
        rows.append(
            {
                "Symbol": safe_get(item, "symbol", default="N/A"),
                "Shares": float(safe_get(item, "shares", default=0) or 0),
                "Current Price": format_currency(
                    safe_get(item, "current_price", default=0)
                ),
                "Value": format_currency(value),
                "PnL": format_signed(item.get("pnl", 0)),
                "Allocation": format_percent(
                    (value / total_value) * 100 if total_value else 0
                ),
            }
        )

    st.markdown("**Holdings Table**")
    if rows:
        st.dataframe(rows, use_container_width=True, hide_index=True)
    else:
        st.markdown(
            '<div class="fc-empty-state">No holdings rows to display.</div>',
            unsafe_allow_html=True,
        )


def render_final_report(data: dict[str, Any]) -> None:
    if not isinstance(data, dict) or not data:
        st.markdown(
            '<div class="fc-empty-state">Final report is unavailable.</div>',
            unsafe_allow_html=True,
        )
        return

    executive_summary = safe_get(
        data, "executive_summary", default="No executive summary available."
    )
    sections = safe_get(data, "sections", default=[])
    recommendations = safe_get(data, "recommendations", default=[])

    st.markdown("**Executive Summary**")
    st.markdown(
        f'<div style="color:#e2e8f0;font-size:1.02rem;font-weight:600;margin-bottom:0.7rem;">' 
        f'{executive_summary}</div>',
        unsafe_allow_html=True,
    )

    section_items = sections if isinstance(sections, list) else []
    if section_items:
        st.markdown("**Sections Covered**")
        pills = "".join(
            f'<span class="fc-section-pill">{s}</span>' for s in section_items
        )
        st.markdown(pills, unsafe_allow_html=True)

    recs = recommendations if isinstance(recommendations, list) else []
    if recs:
        st.markdown("**Top 3 Recommendations**")
        priorities = [
            ("High", "fc-priority-high"),
            ("Medium", "fc-priority-medium"),
            ("Low", "fc-priority-low"),
        ]
        for idx, item in enumerate(recs[:3]):
            plabel, pcls = priorities[idx] if idx < len(priorities) else ("Low", "fc-priority-low")
            text = item if isinstance(item, str) else str(item)
            st.markdown(
                f'<div class="fc-rec-item"><span class="fc-priority-pill {pcls}">{plabel}</span><span>{text}</span></div>',
                unsafe_allow_html=True,
            )


# ---------------------------------------------------------------------------
# Outputs tabs
# ---------------------------------------------------------------------------

def render_outputs_tabs(final_state: dict[str, Any]) -> None:
    # Spacing separator between KPI strip and tabs
    st.markdown('<div style="height: 22px;"></div>', unsafe_allow_html=True)

    # Open scoped wrapper — scopes all tab CSS rules to avoid Streamlit-wide breakage
    st.markdown('<div class="safe-output-tabs">', unsafe_allow_html=True)

    tab_tx, tab_bud, tab_port, tab_rep = st.tabs(
        ["Transaction Insights", "Budget Analysis", "Portfolio Insights", "Final Report"]
    )
    with tab_tx:
        render_transaction_insights(final_state.get("transaction_insights", {}))
    with tab_bud:
        render_budget_analysis(final_state.get("budget_analysis", {}))
    with tab_port:
        render_portfolio_insights(final_state.get("portfolio_insights", {}))
    with tab_rep:
        render_final_report(final_state.get("final_report", {}))

    st.markdown('</div>', unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# App entrypoint
# ---------------------------------------------------------------------------

def render_app() -> None:
    st.set_page_config(page_title="Intelligent Finance Copilot", layout="wide")
    _render_css()

    run_completed = bool(st.session_state.get("last_run_completed", False))
    render_header(run_completed=run_completed)
    render_storyline()

    left, right = st.columns([7, 5], gap="large")
    with left:
        uploaded_file, parsed_upload = render_input_panel()
    with right:
        run_clicked = render_run_panel(uploaded_file, parsed_upload)

    if not run_clicked:
        return

    if uploaded_file is None:
        st.warning("Please upload a JSON, CSV, or Excel file to run analysis.")
        st.session_state["last_run_completed"] = False
        return

    try:
        raw_data, input_source, warning = load_input_data(uploaded_file, parsed_upload)
        if warning:
            st.warning(warning)
            st.session_state["last_run_completed"] = False
            return

        if not isinstance(raw_data, dict):
            st.warning("Unable to parse uploaded input into a valid payload.")
            st.session_state["last_run_completed"] = False
            return

        with st.status("Executing multi-agent workflow...", expanded=True) as status:
            st.write("1/6 Orchestrator Init")
            st.write("2/6 Ingestion Agent")
            st.write("3/6 Transaction Intelligence")
            st.write("4/6 Budget Monitoring")
            st.write("5/6 Portfolio Insight")
            st.write("6/6 Reporting + Finalize")
            final_state = run_workflow(raw_data)
            final_status = final_state.get("status", "UNKNOWN")
            if final_status == "SUCCESS":
                status.update(label="Execution completed successfully", state="complete")
            else:
                status.update(label="Execution completed with issues", state="error")

        st.session_state["last_run_completed"] = True
        valid_rows = _count_valid_rows(parsed_upload, raw_data)
        render_run_summary(final_state, str(input_source), valid_rows, raw_data=raw_data)
        render_outputs_tabs(final_state)

        errors = final_state.get("errors", [])
        if errors:
            st.markdown("<br/>", unsafe_allow_html=True)
            st.subheader("Execution Errors")
            for idx, err in enumerate(errors, start=1):
                st.error(f"{idx}. {err}")

    except Exception as exc:
        st.session_state["last_run_completed"] = False
        st.error(f"Execution failed: {exc}")


def main() -> None:
    render_app()


if __name__ == "__main__":
    main()

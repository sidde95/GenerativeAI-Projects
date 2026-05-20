"""Data parsing and normalization helpers for Streamlit uploads."""

from __future__ import annotations

import json
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Any

import pandas as pd

INTERNAL_SCHEMA_KEYS = ("transactions", "budgets", "portfolio")

REQUIRED_FIELDS: dict[str, list[str]] = {
    "transactions": ["date", "description", "amount", "category"],
    "budgets": ["category", "budget_amount"],
    "portfolio": ["symbol", "quantity", "avg_price"],
}

FIELD_ALIASES: dict[str, list[str]] = {
    "date": ["date", "txn_date", "transaction_date"],
    "description": ["description", "merchant", "narration", "details"],
    "amount": ["amount", "txn_amount", "value"],
    "category": ["category", "type", "expense_category"],
    "budget_amount": ["budget", "budget_amount", "limit"],
    "symbol": ["symbol", "ticker", "asset"],
    "quantity": ["qty", "quantity", "units"],
    "avg_price": ["avg_price", "average_price", "cost_basis", "buy_price"],
}


@dataclass
class ParseOutcome:
    """Structured parse result used by the UI."""

    data: dict[str, list[dict[str, Any]]]
    row_errors: dict[str, list[dict[str, Any]]]



def normalize_column_name(value: str) -> str:
    """Convert raw column names to normalized tokens."""

    return str(value).strip().lower().replace(" ", "_")



def suggest_mapping(columns: list[str], data_type: str) -> dict[str, str | None]:
    """Suggest source->target column mappings using configured aliases."""

    normalized_index = {normalize_column_name(column): column for column in columns}
    mapping: dict[str, str | None] = {}

    for field in REQUIRED_FIELDS[data_type]:
        candidate = None
        for alias in FIELD_ALIASES[field]:
            if alias in normalized_index:
                candidate = normalized_index[alias]
                break
        mapping[field] = candidate

    return mapping



def _ensure_mapping(data_type: str, mapping: dict[str, str]) -> None:
    missing = [field for field in REQUIRED_FIELDS[data_type] if not mapping.get(field)]
    if missing:
        raise ValueError(f"Missing required mappings for {data_type}: {missing}")



def _coerce_date(value: Any) -> str | None:
    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        return None
    return parsed.strftime("%Y-%m-%d")



def _coerce_float(value: Any) -> float | None:
    parsed = pd.to_numeric(value, errors="coerce")
    if pd.isna(parsed):
        return None
    return float(parsed)



def _normalize_transactions_with_errors(
    dataframe: pd.DataFrame,
    mapping: dict[str, str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    _ensure_mapping("transactions", mapping)
    rows: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []

    for row_index, row in dataframe.iterrows():
        date_value = _coerce_date(row.get(mapping["date"]))
        amount_value = _coerce_float(row.get(mapping["amount"]))
        description = str(row.get(mapping["description"], "")).strip()
        category = str(row.get(mapping["category"], "")).strip()

        row_issues = []
        if not date_value:
            row_issues.append("invalid date")
        if amount_value is None:
            row_issues.append("invalid amount")
        if not description:
            row_issues.append("missing description")
        if not category:
            row_issues.append("missing category")

        if row_issues:
            errors.append({"row": int(row_index) + 2, "issues": ", ".join(row_issues)})
            continue

        rows.append(
            {
                "date": date_value,
                "description": description,
                "amount": amount_value,
                "category": category,
            }
        )

    return rows, errors



def _normalize_budgets_with_errors(
    dataframe: pd.DataFrame,
    mapping: dict[str, str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    _ensure_mapping("budgets", mapping)
    rows: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []

    for row_index, row in dataframe.iterrows():
        category = str(row.get(mapping["category"], "")).strip()
        budget_amount = _coerce_float(row.get(mapping["budget_amount"]))

        row_issues = []
        if not category:
            row_issues.append("missing category")
        if budget_amount is None:
            row_issues.append("invalid budget_amount")

        if row_issues:
            errors.append({"row": int(row_index) + 2, "issues": ", ".join(row_issues)})
            continue

        rows.append({"category": category, "budget_amount": budget_amount})

    return rows, errors



def _normalize_portfolio_with_errors(
    dataframe: pd.DataFrame,
    mapping: dict[str, str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    _ensure_mapping("portfolio", mapping)
    rows: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []

    for row_index, row in dataframe.iterrows():
        symbol = str(row.get(mapping["symbol"], "")).strip().upper()
        quantity = _coerce_float(row.get(mapping["quantity"]))
        avg_price = _coerce_float(row.get(mapping["avg_price"]))

        row_issues = []
        if not symbol:
            row_issues.append("missing symbol")
        if quantity is None:
            row_issues.append("invalid quantity")
        if avg_price is None:
            row_issues.append("invalid avg_price")

        if row_issues:
            errors.append({"row": int(row_index) + 2, "issues": ", ".join(row_issues)})
            continue

        rows.append({"symbol": symbol, "quantity": quantity, "avg_price": avg_price})

    return rows, errors



def normalize_transactions(dataframe: pd.DataFrame, mapping: dict[str, str]) -> list[dict[str, Any]]:
    """Normalize transactions dataframe to the internal transactions schema."""

    rows, _ = _normalize_transactions_with_errors(dataframe, mapping)
    return rows



def normalize_budgets(dataframe: pd.DataFrame, mapping: dict[str, str]) -> list[dict[str, Any]]:
    """Normalize budgets dataframe to the internal budgets schema."""

    rows, _ = _normalize_budgets_with_errors(dataframe, mapping)
    return rows



def normalize_portfolio(dataframe: pd.DataFrame, mapping: dict[str, str]) -> list[dict[str, Any]]:
    """Normalize portfolio dataframe to the internal portfolio schema."""

    rows, _ = _normalize_portfolio_with_errors(dataframe, mapping)
    return rows



def uploaded_file_bytes(uploaded_file: Any) -> bytes:
    """Read file bytes from Streamlit UploadedFile-like inputs."""

    if hasattr(uploaded_file, "getvalue"):
        return uploaded_file.getvalue()
    if isinstance(uploaded_file, bytes):
        return uploaded_file
    if hasattr(uploaded_file, "read"):
        return uploaded_file.read()
    raise ValueError("Unsupported uploaded file object")



def list_excel_sheets(uploaded_file: Any) -> list[str]:
    """Return sheet names from an uploaded Excel file."""

    raw_bytes = uploaded_file_bytes(uploaded_file)
    workbook = pd.ExcelFile(BytesIO(raw_bytes))
    return workbook.sheet_names



def load_table_from_uploaded_file(
    uploaded_file: Any,
    file_type: str,
    *,
    sheet_name: str | None = None,
) -> pd.DataFrame:
    """Load a table from uploaded file bytes into a DataFrame."""

    raw_bytes = uploaded_file_bytes(uploaded_file)
    if file_type == "csv":
        return pd.read_csv(BytesIO(raw_bytes))
    if file_type in {"xlsx", "xls"}:
        return pd.read_excel(BytesIO(raw_bytes), sheet_name=sheet_name)
    raise ValueError(f"Unsupported tabular file type: {file_type}")



def normalize_json_payload(payload: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    """Normalize JSON payloads into the list-based internal schema."""

    if not isinstance(payload, dict):
        raise ValueError("JSON payload must be an object")

    transactions: list[dict[str, Any]] = []
    budgets: list[dict[str, Any]] = []
    portfolio: list[dict[str, Any]] = []

    raw_transactions = payload.get("transactions", [])
    if isinstance(raw_transactions, list):
        for row in raw_transactions:
            if not isinstance(row, dict):
                continue
            transactions.append(
                {
                    "date": row.get("date", ""),
                    "description": row.get("description") or row.get("merchant") or "",
                    "amount": float(pd.to_numeric(row.get("amount", 0), errors="coerce") or 0),
                    "category": row.get("category", ""),
                }
            )

    raw_budgets = payload.get("budgets", [])
    if isinstance(raw_budgets, dict):
        for category, amount in raw_budgets.items():
            numeric = pd.to_numeric(amount, errors="coerce")
            if pd.isna(numeric):
                continue
            budgets.append({"category": str(category), "budget_amount": float(numeric)})
    elif isinstance(raw_budgets, list):
        for row in raw_budgets:
            if not isinstance(row, dict):
                continue
            category = str(row.get("category", "")).strip()
            amount = pd.to_numeric(row.get("budget_amount", row.get("budget", 0)), errors="coerce")
            if not category or pd.isna(amount):
                continue
            budgets.append({"category": category, "budget_amount": float(amount)})

    raw_portfolio = payload.get("portfolio", [])
    if isinstance(raw_portfolio, dict):
        holdings = raw_portfolio.get("holdings", [])
    elif isinstance(raw_portfolio, list):
        holdings = raw_portfolio
    else:
        holdings = []

    if isinstance(holdings, list):
        for row in holdings:
            if not isinstance(row, dict):
                continue
            symbol = str(row.get("symbol", "")).strip().upper()
            qty = pd.to_numeric(row.get("quantity", row.get("shares", 0)), errors="coerce")
            avg_price = pd.to_numeric(row.get("avg_price", row.get("cost_basis", 0)), errors="coerce")
            if not symbol or pd.isna(qty) or pd.isna(avg_price):
                continue
            portfolio.append(
                {
                    "symbol": symbol,
                    "quantity": float(qty),
                    "avg_price": float(avg_price),
                }
            )

    return {
        "transactions": transactions,
        "budgets": budgets,
        "portfolio": portfolio,
    }



def _normalize_data_type_table(
    data_type: str,
    dataframe: pd.DataFrame,
    mapping: dict[str, str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if data_type == "transactions":
        return _normalize_transactions_with_errors(dataframe, mapping)
    if data_type == "budgets":
        return _normalize_budgets_with_errors(dataframe, mapping)
    if data_type == "portfolio":
        return _normalize_portfolio_with_errors(dataframe, mapping)
    raise ValueError(f"Unsupported data_type: {data_type}")



def parse_uploaded_file_with_details(uploaded_file: Any, options: dict[str, Any]) -> ParseOutcome:
    """Parse JSON/CSV/Excel uploads and return normalized records and row errors."""

    file_type = str(options.get("file_type") or Path(getattr(uploaded_file, "name", "")).suffix.lower().lstrip("."))

    data: dict[str, list[dict[str, Any]]] = {key: [] for key in INTERNAL_SCHEMA_KEYS}
    errors: dict[str, list[dict[str, Any]]] = {key: [] for key in INTERNAL_SCHEMA_KEYS}

    if file_type == "json":
        payload = json.loads(uploaded_file_bytes(uploaded_file).decode("utf-8"))
        data = normalize_json_payload(payload)
        return ParseOutcome(data=data, row_errors=errors)

    if file_type == "csv":
        data_type = options.get("csv_data_type")
        mapping = options.get("mappings", {}).get(data_type, {})
        dataframe = load_table_from_uploaded_file(uploaded_file, "csv")
        valid_rows, row_errors = _normalize_data_type_table(str(data_type), dataframe, mapping)
        data[str(data_type)] = valid_rows
        errors[str(data_type)] = row_errors
        return ParseOutcome(data=data, row_errors=errors)

    if file_type in {"xlsx", "xls"}:
        excel_mode = options.get("excel_mode", "single")
        mappings = options.get("mappings", {})

        if excel_mode == "single":
            data_type = str(options.get("excel_data_type"))
            sheet_name = options.get("excel_sheet")
            dataframe = load_table_from_uploaded_file(uploaded_file, file_type, sheet_name=sheet_name)
            valid_rows, row_errors = _normalize_data_type_table(data_type, dataframe, mappings.get(data_type, {}))
            data[data_type] = valid_rows
            errors[data_type] = row_errors
            return ParseOutcome(data=data, row_errors=errors)

        sheet_selection: dict[str, str] = options.get("sheet_selection", {})
        for data_type in INTERNAL_SCHEMA_KEYS:
            selected_sheet = sheet_selection.get(data_type)
            if not selected_sheet:
                continue
            dataframe = load_table_from_uploaded_file(uploaded_file, file_type, sheet_name=selected_sheet)
            valid_rows, row_errors = _normalize_data_type_table(data_type, dataframe, mappings.get(data_type, {}))
            data[data_type] = valid_rows
            errors[data_type] = row_errors
        return ParseOutcome(data=data, row_errors=errors)

    raise ValueError("Unsupported file type. Please upload json, csv, xlsx, or xls.")



def parse_uploaded_file(uploaded_file: Any, options: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    """Parse uploaded input and return internal schema payload."""

    return parse_uploaded_file_with_details(uploaded_file, options).data



def to_backend_workflow_payload(internal_payload: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    """Convert list-based internal payload to the existing backend workflow shape."""

    transactions = internal_payload.get("transactions", [])

    budgets_dict: dict[str, float] = {}
    for row in internal_payload.get("budgets", []):
        if not isinstance(row, dict):
            continue
        category = str(row.get("category", "")).strip()
        amount = pd.to_numeric(row.get("budget_amount", 0), errors="coerce")
        if not category or pd.isna(amount):
            continue
        budgets_dict[category] = float(amount)

    holdings: list[dict[str, Any]] = []
    for row in internal_payload.get("portfolio", []):
        if not isinstance(row, dict):
            continue
        symbol = str(row.get("symbol", "")).strip().upper()
        quantity = pd.to_numeric(row.get("quantity", 0), errors="coerce")
        avg_price = pd.to_numeric(row.get("avg_price", 0), errors="coerce")
        if not symbol or pd.isna(quantity) or pd.isna(avg_price):
            continue
        holdings.append(
            {
                "symbol": symbol,
                "shares": float(quantity),
                "cost_basis": float(avg_price),
                "current_price": float(avg_price),
            }
        )

    return {
        "transactions": transactions,
        "budgets": budgets_dict,
        "portfolio": {"holdings": holdings},
    }



def build_sample_csv_template(data_type: str) -> bytes:
    """Build downloadable CSV template bytes for selected data type."""

    if data_type == "transactions":
        frame = pd.DataFrame(
            [
                {
                    "date": "2026-05-01",
                    "description": "Whole Foods",
                    "amount": -45.32,
                    "category": "Groceries",
                }
            ]
        )
    elif data_type == "budgets":
        frame = pd.DataFrame([{"category": "Groceries", "budget_amount": 500.0}])
    elif data_type == "portfolio":
        frame = pd.DataFrame([{"symbol": "AAPL", "quantity": 10, "avg_price": 150.0}])
    else:
        raise ValueError("Unknown data_type for CSV template")

    return frame.to_csv(index=False).encode("utf-8")



def build_sample_excel_template() -> bytes:
    """Build downloadable Excel template bytes with all required sheets."""

    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        pd.DataFrame(
            [
                {
                    "date": "2026-05-01",
                    "description": "Whole Foods",
                    "amount": -45.32,
                    "category": "Groceries",
                }
            ]
        ).to_excel(writer, index=False, sheet_name="transactions")
        pd.DataFrame([{"category": "Groceries", "budget_amount": 500.0}]).to_excel(
            writer,
            index=False,
            sheet_name="budgets",
        )
        pd.DataFrame([{"symbol": "AAPL", "quantity": 10, "avg_price": 150.0}]).to_excel(
            writer,
            index=False,
            sheet_name="portfolio",
        )
    buffer.seek(0)
    return buffer.read()

"""CSV/XLSX parser — header parsing with field(comment) convention and type inference."""
import csv
import io
import re
from datetime import datetime
from typing import Any

HEADER_RE = re.compile(r"^(.+?)\((.+?)\)$")
MAX_INFER_ROWS = 10


def parse_headers(raw_header: str) -> list[dict]:
    """Parse CSV header with field(comment) convention.

    Args:
        raw_header: Raw column header text, e.g. "amount(补贴金额)"

    Returns:
        dict with keys: name (column_name), display_name, extra_desc
    """
    out = []
    for col in [h.strip().strip('"').strip("'") for h in raw_header.split(",")]:
        m = HEADER_RE.match(col)
        if m:
            out.append({"name": sanitize_column(m.group(1)), "display_name": m.group(2), "extra_desc": ""})
        else:
            out.append({"name": sanitize_column(col), "display_name": col, "extra_desc": ""})
    return out


def sanitize_column(name: str) -> str:
    """Convert to safe MySQL column name: lowercase, replace spaces/punctuation."""
    name = name.strip().lower()
    name = re.sub(r"[^\w]+", "_", name)
    name = name.strip("_")
    return name or "col_unknown"


def infer_types(rows: list[list[str]]) -> list[str]:
    """Infer column types from first MAX_INFER_ROWS rows.

    Returns MySQL types: integer, decimal(18,2), date, text
    """
    if not rows or not rows[0]:
        return []
    ncols = len(rows[0])
    types = ["text"] * ncols
    for col_idx in range(ncols):
        values = [r[col_idx].strip() for r in rows[:MAX_INFER_ROWS] if col_idx < len(r)]
        if not values:
            continue
        if all(_is_integer(v) for v in values if v):
            types[col_idx] = "integer"
        elif all(_is_float(v) for v in values if v):
            types[col_idx] = "decimal(18,2)"
        elif all(_is_date(v) for v in values if v):
            types[col_idx] = "date"
    return types


COLUMN_TYPE_MAP = {
    "integer": "INT",
    "decimal(18,2)": "DECIMAL(18,2)",
    "date": "DATE",
    "text": "TEXT",
}


def _is_integer(v: str) -> bool:
    try:
        int(v.replace(",", ""))
        return True
    except ValueError:
        return False


def _is_float(v: str) -> bool:
    try:
        float(v.replace(",", ""))
        return True
    except ValueError:
        return False


def _is_date(v: str) -> bool:
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d", "%d-%m-%Y"):
        try:
            datetime.strptime(v, fmt)
            return True
        except ValueError:
            continue
    return False


def read_csv(file_content: bytes, filename: str) -> dict[str, Any]:
    """Read CSV or XLSX file and return parsed data.

    Returns:
        dict with sheets (list of {name, headers, rows, types})
    """
    if filename.lower().endswith(".csv"):
        text = file_content.decode("utf-8-sig")
        reader = csv.reader(io.StringIO(text))
        rows = list(reader)
        if not rows:
            raise ValueError("CSV is empty")
        header_row = rows[0]
        headers = parse_headers(",".join(header_row))
        data_rows = rows[1:]
        types = infer_types(data_rows)
        return {"sheets": [{"name": "Sheet1", "headers": headers, "rows": data_rows, "types": types}]}

    if filename.lower().endswith((".xlsx", ".xls")):
        try:
            import openpyxl
            wb = openpyxl.load_workbook(io.BytesIO(file_content), read_only=True, data_only=True)
            sheets = []
            for ws in wb.worksheets:
                rows = [[str(c.value) if c.value is not None else "" for c in row] for row in ws.iter_rows(max_row=MAX_INFER_ROWS * 2)]
                if not rows:
                    continue
                header_row = rows[0]
                headers = parse_headers(",".join(header_row))
                data_rows = rows[1:]
                types = infer_types(data_rows)
                sheets.append({"name": ws.title, "headers": headers, "rows": data_rows, "types": types})
            wb.close()
            return {"sheets": sheets}
        except ImportError:
            raise ValueError("openpyxl not installed — use CSV format or install openpyxl")

    raise ValueError(f"Unsupported file format: {filename}")

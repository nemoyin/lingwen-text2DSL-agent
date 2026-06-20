"""CSV export utility — converts query results to CSV format."""

import csv
import io
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def export_csv(
    data: List[Dict[str, Any]],
    columns: Optional[List[str]] = None,
    delimiter: str = ",",
    encoding: str = "utf-8-sig",
) -> str:
    """Export a list of row-dicts as a CSV string.

    Args:
        data: A list of dicts, each representing one row.
        columns: Optional explicit column ordering.  When omitted, columns
            are inferred from the first row's keys.
        delimiter: Field delimiter character (default: comma).
        encoding: Output encoding (default: ``utf-8-sig`` for Excel
            compatibility).

    Returns:
        A CSV-formatted string.
    """
    if not data:
        return ""

    # Infer columns from the first row if not specified
    if columns is None and data:
        columns = list(data[0].keys())

    if columns is None:
        columns = []

    output = io.StringIO()
    writer = csv.writer(output, delimiter=delimiter)

    # Write header
    writer.writerow(columns)

    # Write data rows
    for row in data:
        values = [str(row.get(col, "")) for col in columns]
        writer.writerow(values)

    result = output.getvalue()
    output.close()

    logger.debug("Exported CSV: %d columns × %d rows", len(columns), len(data))
    return result


def export_csv_bytes(
    data: List[Dict[str, Any]],
    columns: Optional[List[str]] = None,
) -> bytes:
    """Export data as CSV bytes (useful for streaming responses).

    Args:
        data: A list of dicts.
        columns: Optional explicit column ordering.

    Returns:
        CSV bytes encoded as UTF-8 with BOM.
    """
    csv_str = export_csv(data, columns)
    return csv_str.encode("utf-8-sig")

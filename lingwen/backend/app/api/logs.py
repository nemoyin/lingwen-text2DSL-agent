"""Online log viewer — read and filter backend service logs."""

import logging
import os
import re
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()

LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logs")
LOG_FILE = os.path.join(LOG_DIR, "lingwen.log")

# Uvicorn log pattern: LEVEL:     message
_LOG_LINE_RE = re.compile(
    r"^(\w+):\s+(.+)"
)

# Uvicorn date-time prefix: 2026-06-05 15:07:11,231
_DATETIME_RE = re.compile(
    r"^(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}(?:,\d{3})?)\s+"
)


def _parse_log_line(line: str) -> Optional[dict]:
    """Parse a single log line into {level, message, timestamp}.

    Handles these formats:
        INFO:     message
        WARNING:  message
        ERROR:    message
        DEBUG:    message
        CRITICAL: message
        2026-06-05 15:07:11,231 message  (plain text / access log)
        INFO:     127.0.0.1:12345 - "GET /api/health HTTP/1.1" 200 OK
    """
    line = line.rstrip("\n\r")
    if not line:
        return None

    # Try uvicorn format: LEVEL:     message
    m = _LOG_LINE_RE.match(line)
    if m:
        level = m.group(1).upper()
        msg = m.group(2).strip()
        # Valid levels
        if level in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"):
            return {"level": level, "message": msg, "timestamp": None}
        # Might be an access log line that didn't match
        return {"level": "INFO", "message": line, "timestamp": None}

    # Try date-prefixed line
    m = _DATETIME_RE.match(line)
    if m:
        ts = m.group(1)
        rest = line[m.end():]
        # Check if rest has a log level
        lm = _LOG_LINE_RE.match(rest)
        if lm:
            level = lm.group(1).upper()
            msg = lm.group(2).strip()
            return {"level": level, "message": msg, "timestamp": ts}
        return {"level": "INFO", "message": rest.strip(), "timestamp": ts}

    # Everything else: treat as INFO
    return {"level": "INFO", "message": line, "timestamp": None}


@router.get("/logs")
async def read_logs(
    level: Optional[str] = Query(None, description="Filter by level: DEBUG, INFO, WARNING, ERROR"),
    lines: int = Query(200, ge=10, le=2000, description="Number of lines to return"),
    offset: int = Query(0, ge=0, description="Skip first N lines from end"),
    user: dict = Depends(get_current_user),
) -> dict:
    """Read recent backend log entries with optional level filtering.

    Lines are returned from newest to oldest.  'offset' lets you paginate
    backward through the log file.  'lines' controls the page size.

    Response::
        {
            "code": 200,
            "data": {
                "entries": [{"level": "INFO", "message": "...", "timestamp": "..."}, ...],
                "total_lines": 15234,
                "file": "lingwen.log"
            }
        }
    """
    if not os.path.isfile(LOG_FILE):
        return {
            "code": 200,
            "data": {"entries": [], "total_lines": 0, "file": "lingwen.log"},
        }

    # Read file
    with open(LOG_FILE, "r", encoding="utf-8", errors="replace") as f:
        all_lines = f.readlines()

    total_lines = len(all_lines)
    # Take last N lines, then offset
    start = max(0, total_lines - lines - offset)
    end = max(0, total_lines - offset)
    selected = all_lines[start:end]

    # Parse and filter
    entries = []
    for raw in reversed(selected):  # newest first
        entry = _parse_log_line(raw)
        if entry is None:
            continue
        if level and entry["level"] != level.upper():
            continue
        entries.append(entry)

    return {
        "code": 200,
        "data": {
            "entries": entries,
            "total_lines": total_lines,
            "file": "lingwen.log",
        },
    }


@router.get("/logs/levels")
async def log_levels(user: dict = Depends(get_current_user)) -> dict:
    """Return available log levels and their counts."""
    if not os.path.isfile(LOG_FILE):
        return {"code": 200, "data": {"counts": {}, "levels": []}}

    counts = {"DEBUG": 0, "INFO": 0, "WARNING": 0, "ERROR": 0, "CRITICAL": 0}
    with open(LOG_FILE, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            m = _LOG_LINE_RE.match(line)
            if m:
                lvl = m.group(1).upper()
                if lvl in counts:
                    counts[lvl] += 1

    return {
        "code": 200,
        "data": {"counts": counts, "levels": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]},
    }

"""SQL security guard — intercept dangerous operations and SQL injection."""

import re
from typing import Tuple


class SqlGuard:
    """Validates SQL safety before execution on user data sources.

    Applies three layers of protection:
    1.  **Dangerous operation detection** — blocks DML/DDL that could modify data.
    2.  **SQL injection pattern detection** — flags common injection signatures.
    3.  **Row limit enforcement** — injects ``LIMIT <max_rows>`` if absent.

    Usage::

        guard = SqlGuard()
        is_safe, error_msg = guard.validate(sql)
        if is_safe:
            safe_sql = guard.inject_limit(sql)
    """

    # Patterns that indicate data-modifying or schema-modifying operations
    DANGEROUS_PATTERNS: list[str] = [
        r"\bDROP\b",
        r"\bDELETE\b",
        r"\bUPDATE\b",
        r"\bINSERT\b",
        r"\bALTER\b",
        r"\bTRUNCATE\b",
        r"\bCREATE\b",
        r"\bGRANT\b",
        r"\bREVOKE\b",
        r"\bREPLACE\b",
        r"\bRENAME\b",
    ]

    # Patterns that may indicate SQL injection attempts
    INJECTION_PATTERNS: list[str] = [
        r"--\s*(?:\bSELECT\b|\bDROP\b|\bDELETE\b|\bUNION\b|\bOR\b\s*\d)",  # inline injection via comment
        r";\s*\w",
        r"/\*.*\*/",
        r"\bUNION\s+SELECT\b",
        r"\bEXEC\b",
        r"\bEXECUTE\b",
        r"\bSLEEP\s*\([^)]*\)",
        r"\bBENCHMARK\s*\([^)]*\)",
        r"\bOR\s+['\"]?\d['\"]?\s*=\s*['\"]?\d['\"]?",
    ]

    # Maximum rows to return from any query
    MAX_ROWS: int = 1000

    def __init__(self) -> None:
        self._dangerous_re = [
            re.compile(p, re.IGNORECASE) for p in self.DANGEROUS_PATTERNS
        ]
        self._injection_re = [
            re.compile(p, re.IGNORECASE) for p in self.INJECTION_PATTERNS
        ]

    def is_readonly(self, sql: str) -> bool:
        """Check whether the SQL contains only read operations.

        Args:
            sql: The SQL string to inspect.

        Returns:
            ``True`` if no dangerous patterns are detected.
        """
        for pattern in self._dangerous_re:
            if pattern.search(sql):
                return False
        return True

    def _check_dangerous(self, sql: str) -> Tuple[bool, str]:
        """Scan for data-modifying operations."""
        for i, pattern in enumerate(self._dangerous_re):
            match = pattern.search(sql)
            if match:
                keyword = match.group(0).upper()
                return False, f"禁止的 SQL 操作: {keyword}"
        return True, ""

    def _check_injection(self, sql: str) -> Tuple[bool, str]:
        """Scan for SQL injection signatures."""
        for i, pattern in enumerate(self._injection_re):
            match = pattern.search(sql)
            if match:
                return False, f"检测到 SQL 注入特征: {match.group(0)[:50]}"
        return True, ""

    def validate(self, sql: str) -> Tuple[bool, str]:
        """Run all security checks on the given SQL.

        Args:
            sql: The SQL string to validate.

        Returns:
            A ``(is_safe, error_message)`` tuple.  When ``is_safe`` is
            ``True`` the error message is an empty string.
        """
        if not sql or not sql.strip():
            return False, "SQL 语句为空"

        is_safe, error = self._check_dangerous(sql)
        if not is_safe:
            return False, error

        is_safe, error = self._check_injection(sql)
        if not is_safe:
            return False, error

        return True, ""

    def inject_limit(self, sql: str, max_rows: int = MAX_ROWS) -> str:
        """Inject a ``LIMIT`` clause into the SQL if one is not already present.

        Args:
            sql: The (already validated) SQL string.
            max_rows: The maximum number of rows to return.

        Returns:
            The SQL with a ``LIMIT`` clause appended.
        """
        cleaned = sql.strip().rstrip(";").strip()

        # Avoid double-injection
        if re.search(r"\bLIMIT\s+\d+", cleaned, re.IGNORECASE):
            return cleaned

        return f"{cleaned} LIMIT {max_rows}"

    def sanitize_identifiers(self, sql: str) -> str:
        """Strip or escape suspicious identifier characters.

        This is a best-effort sanitisation; the primary defence remains
        the regex-based checks above.

        Args:
            sql: The raw SQL string.

        Returns:
            A sanitised SQL string.
        """
        # Remove inline comments
        sanitized = re.sub(r"--.*$", "", sql, flags=re.MULTILINE)
        # Remove block comments
        sanitized = re.sub(r"/\*.*?\*/", "", sanitized, flags=re.DOTALL)
        return sanitized.strip()

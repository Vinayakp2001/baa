"""Employee value normaliser.

Handles:
  - Exact integer/float-string: Vancouver "385.0" → employee_exact=True
  - Range string: "10 to 19", "55 to 99" → employee_exact=False
  - Unbounded: "500 plus", "500+" → employee_min=500, employee_max=None
  - None/absent → all derived fields None, no estimation

"55 to 99" triggers EMPLOYEE_RANGE_AMBIGUITY data_quality_flag (it's not
the standard "50 to 99" bracket from most sources).

Requirements: 7.1–7.7
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# 9-bucket label system (+ "500+" for unbounded)
_BUCKETS: list[tuple[int, int | None, str]] = [
    (1, 4, "1-4"),
    (5, 9, "5-9"),
    (10, 19, "10-19"),
    (20, 49, "20-49"),
    (50, 99, "50-99"),
    (100, 199, "100-199"),
    (200, 499, "200-499"),
    (500, 999, "500-999"),
    (1000, None, "1000+"),
]

# Patterns
_EXACT_RE = re.compile(r"^\d+(?:\.\d+)?$")                         # "42", "385.0"
_RANGE_RE = re.compile(r"^(\d+)\s*(?:to|-)\s*(\d+)$", re.I)       # "10 to 19", "10-19"
_PLUS_RE = re.compile(r"^(\d+)\s*(?:plus|\+)$", re.I)              # "500 plus", "500+"

# Known ambiguous ranges that fall between standard bucket boundaries
_AMBIGUOUS_RANGES: frozenset[tuple[int, int]] = frozenset({
    (55, 99),   # BC Indigenous "55 to 99" — not the standard 50-99 bracket
})


@dataclass
class EmployeeResult:
    raw_employee_value: str | None
    employee_min: int | None
    employee_max: int | None       # None for "500+" (unbounded)
    employee_bucket: str | None    # canonical bucket label or None
    employee_exact: bool           # True only when source gave a single integer
    data_quality_flag: str | None  # "EMPLOYEE_RANGE_AMBIGUITY" or None


def _assign_bucket(min_val: int, max_val: int | None) -> str | None:
    """Assign canonical bucket label from min/max values."""
    if max_val is None:
        # Unbounded — use 500+ convention
        return "500+"

    midpoint = (min_val + max_val) / 2
    for low, high, label in _BUCKETS:
        if high is None:
            if midpoint >= low:
                return label
        elif low <= midpoint <= high:
            return label
    return None


def normalise_employee(raw: str | int | float | None) -> EmployeeResult:
    """Normalise an employee count or range value.

    Args:
        raw: Employee value as received from source. May be None, int, float,
             or string (e.g. "385.0", "10 to 19", "500 plus").

    Returns:
        EmployeeResult. None/absent input → all derived fields None.
    """
    # Absent / null
    if raw is None:
        return EmployeeResult(
            raw_employee_value=None,
            employee_min=None,
            employee_max=None,
            employee_bucket=None,
            employee_exact=False,
            data_quality_flag=None,
        )

    raw_str = str(raw).strip()
    if not raw_str or raw_str.lower() in {"n/a", "na", "none", "null", "unknown", ""}:
        return EmployeeResult(
            raw_employee_value=None,
            employee_min=None,
            employee_max=None,
            employee_bucket=None,
            employee_exact=False,
            data_quality_flag=None,
        )

    # --- Exact integer/float ---
    if _EXACT_RE.match(raw_str):
        exact_int = int(float(raw_str))
        bucket = _assign_bucket(exact_int, exact_int)
        return EmployeeResult(
            raw_employee_value=raw_str,
            employee_min=exact_int,
            employee_max=exact_int,
            employee_bucket=bucket,
            employee_exact=True,
            data_quality_flag=None,
        )

    # --- Unbounded "500 plus" / "500+" ---
    plus_m = _PLUS_RE.match(raw_str)
    if plus_m:
        min_val = int(plus_m.group(1))
        return EmployeeResult(
            raw_employee_value=raw_str,
            employee_min=min_val,
            employee_max=None,
            employee_bucket="500+",
            employee_exact=False,
            data_quality_flag=None,
        )

    # --- Range "10 to 19" / "10-19" ---
    range_m = _RANGE_RE.match(raw_str)
    if range_m:
        min_val = int(range_m.group(1))
        max_val = int(range_m.group(2))
        bucket = _assign_bucket(min_val, max_val)

        # Flag ambiguous ranges (e.g. "55 to 99" — not a standard bucket boundary)
        flag = None
        if (min_val, max_val) in _AMBIGUOUS_RANGES:
            flag = "EMPLOYEE_RANGE_AMBIGUITY"

        return EmployeeResult(
            raw_employee_value=raw_str,
            employee_min=min_val,
            employee_max=max_val,
            employee_bucket=bucket,
            employee_exact=False,
            data_quality_flag=flag,
        )

    # --- Unrecognised format ---
    return EmployeeResult(
        raw_employee_value=raw_str,
        employee_min=None,
        employee_max=None,
        employee_bucket=None,
        employee_exact=False,
        data_quality_flag=None,
    )

"""
Pure logic for the "compute a stat" endpoint. No FastAPI/SQLAlchemy
imports on purpose -- trivial to unit test with plain lists/dicts, and
separates "what does a stat mean" from "how does a request reach here."

Operation validity (min/max/sum) is no longer this module's job -- the
schema's Literal["min","max","sum"] handles that before a request gets
here. This only guards things that depend on the *data*.
"""


class ComputeError(ValueError):
    """Raised for any dataset/column state that can't be computed on.
    The router catches this and returns a 400."""


def _to_float_or_none(value):
    if value is None:
        return None
    if isinstance(value, str):
        value = value.strip()
        if value == "":
            return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def compute_stat(rows: list[dict], columns: list[str], column: str, operation: str) -> dict:
    """Compute min/max/sum over `column` across `rows`.

    Edge cases handled (map to the spec's required test cases):
      1. Column doesn't exist at all              -> ComputeError
      2. Column exists but all values empty/null   -> ComputeError
      3. Column exists but holds non-numeric data   -> ComputeError
      4. Mixed numeric/non-numeric values            -> non-numeric
         values are skipped, not a hard failure (mirrors how a
         spreadsheet SUM/MIN/MAX ignores blank/text cells).
    """
    if column not in columns:
        raise ComputeError(f"Column '{column}' does not exist on this dataset.")

    if not rows:
        raise ComputeError("Dataset has no rows to compute over.")

    raw_values = [row.get(column) for row in rows]

    non_empty = [v for v in raw_values if v is not None and str(v).strip() != ""]
    if not non_empty:
        raise ComputeError(f"Column '{column}' is empty (all values are null/blank).")

    numeric_values = [_to_float_or_none(v) for v in non_empty]
    numeric_values = [v for v in numeric_values if v is not None]

    if not numeric_values:
        raise ComputeError(
            f"Column '{column}' is not numeric; cannot compute '{operation}' on it."
        )

    if operation == "min":
        result = min(numeric_values)
    elif operation == "max":
        result = max(numeric_values)
    else:  # "sum"
        result = sum(numeric_values)

    return {
        "column": column,
        "operation": operation,
        "result": result,
        "values_considered": len(numeric_values),
        "values_skipped": len(raw_values) - len(numeric_values),
    }
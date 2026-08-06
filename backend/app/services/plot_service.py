"""Pure logic for the "plot two columns" endpoint."""

# Take-home-scoped cap on points shipped per request -- not a real
# solution for huge datasets, documented as a technical assumption.
MAX_PLOT_POINTS = 30


class PlotError(ValueError):
    """Raised for column names that don't exist on the dataset."""


def build_plot_points(rows: list[dict], columns: list[str], col1: str, col2: str) -> list[dict]:
    if col1 not in columns or col2 not in columns:
        raise PlotError("One or both columns do not exist on this dataset.")

    subset = rows[:MAX_PLOT_POINTS]
    return [{"x": row.get(col1), "y": row.get(col2)} for row in subset]
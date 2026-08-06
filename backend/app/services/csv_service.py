"""
Parses an uploaded CSV file into (columns, rows) that the rest of the
app works with. Kept separate from the upload router so the parsing
logic is testable without spinning up FastAPI's UploadFile machinery.
"""
import csv
import io


def parse_csv(raw_bytes: bytes) -> tuple[list[str], list[dict]]:
    # utf-8-sig eats a BOM if Excel exported one; errors="replace" means
    # one weird byte doesn't nuke the entire upload documented as a
    # technical assumption in the README.
    text = raw_bytes.decode("utf-8-sig", errors="replace")
    reader = csv.DictReader(io.StringIO(text))
    columns = reader.fieldnames or []
    rows = [dict(row) for row in reader]
    return columns, rows
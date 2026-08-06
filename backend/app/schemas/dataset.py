from datetime import datetime
from pydantic import BaseModel

# No upload-request schema here -- FastAPI takes `file`/`name` as
# File(...)/Form(...) route params directly since multipart uploads
# aren't a single JSON body. These models are for JSON responses only.


class DatasetSummary(BaseModel):
    id: int
    name: str
    filename: str
    columns: list[str]
    row_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class DatasetListResponse(BaseModel):
    items: list[DatasetSummary]
    page: int
    limit: int
    total: int
    total_pages: int


class DatasetPreview(BaseModel):
    columns: list[str]
    rows: list[dict]
    row_count: int
    previewed: int


class DeleteResponse(BaseModel):
    deleted: int